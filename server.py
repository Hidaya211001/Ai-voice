import os
import re
import json
import uuid
import base64
import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

load_dotenv()
app = FastAPI(title="AI Voice Cartoon Backend")

ROOT = Path(__file__).resolve().parent
JOBS_DIR = ROOT / "jobs"
JOBS_DIR.mkdir(exist_ok=True)
jobs = {}
lock = threading.Lock()

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "marin")
SCENE_COUNT = 10
W, H = 1920, 1080


class GenerateRequest(BaseModel):
    command: str = Field(min_length=2, max_length=1000)
    output_language: str = "English"
    style: str = "3D cartoon"
    target_minutes: int = Field(default=5, ge=1, le=10)


def update(job_id, **kwargs):
    with lock:
        jobs[job_id].update(kwargs)


def font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def caption_png(text, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(40)
    words, lines, cur = text.split(), [], ""
    for word in words:
        candidate = (cur + " " + word).strip()
        if d.textbbox((0, 0), candidate, font=f)[2] <= W - 160:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    lines = lines[:3]
    heights = [d.textbbox((0, 0), x, font=f)[3] for x in lines]
    top = H - sum(heights) - 24 * len(lines) - 80
    d.rounded_rectangle((55, top - 20, W - 55, H - 45), radius=20, fill=(0, 0, 0, 175))
    y = top
    for line, h in zip(lines, heights):
        b = d.textbbox((0, 0), line, font=f)
        x = (W - (b[2] - b[0])) // 2
        d.text((x, y), line, font=f, fill="white", stroke_width=2, stroke_fill="black")
        y += h + 12
    d.rounded_rectangle((W - 365, 25, W - 45, 72), radius=14, fill=(0, 0, 0, 150))
    d.text((W - 345, 34), "AI-GENERATED VOICE", font=font(22), fill="white")
    im.save(path)


def generate_job(job_id, request_data):
    work = JOBS_DIR / job_id
    images, audios = work / "images", work / "audio"
    images.mkdir(parents=True, exist_ok=True)
    audios.mkdir(parents=True, exist_ok=True)
    clips, audio_clips, final = [], [], None
    try:
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not configured on the backend.")
        client = OpenAI(api_key=key)

        update(job_id, status="running", message="Writing cartoon story and scene prompts...")
        prompt = f"""
Create an original child-friendly {request_data['style']} story based on this spoken command:
{request_data['command']}

Write in {request_data['output_language']}. Return JSON only:
{{
 "title":"title",
 "characters":[{{"name":"name","visual_description":"fixed visual appearance"}}],
 "scenes":[
  {{"scene_number":1,"voiceover":"spoken narration and dialogue","image_prompt":"detailed image prompt"}}
 ]
}}
Create exactly {SCENE_COUNT} scenes and around {request_data['target_minutes'] * 125} spoken words.
Use a beginning, problem, adventure, climax and satisfying ending.
Keep character design consistent. Repeat character descriptions in relevant prompts.
Each image is one widescreen cinematic frame, polished family-friendly 3D animation,
expressive characters, detailed environment, cinematic lighting, no text/logos/watermarks.
Do not use existing copyrighted characters. Keep each voiceover under 3500 characters.
"""
        result = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": "You are an animation screenwriter. Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        story = json.loads(result.choices[0].message.content)
        scenes = story.get("scenes", [])
        if len(scenes) != SCENE_COUNT:
            raise ValueError(f"Expected {SCENE_COUNT} scenes, got {len(scenes)}.")
        (work / "cartoon_script.json").write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        for index, scene in enumerate(scenes, 1):
            scene["scene_number"] = index
            image_path = images / f"scene_{index:02d}.png"
            audio_path = audios / f"scene_{index:02d}.mp3"
            caption_path = images / f"caption_{index:02d}.png"

            update(job_id, message=f"Generating scene image {index}/{SCENE_COUNT}...")
            if not image_path.exists():
                img = client.images.generate(
                    model=IMAGE_MODEL,
                    prompt=scene["image_prompt"],
                    size="1536x1024",
                    quality="medium",
                    output_format="png",
                )
                image_path.write_bytes(base64.b64decode(img.data[0].b64_json))

            update(job_id, message=f"Generating voiceover {index}/{SCENE_COUNT}...")
            if not audio_path.exists():
                speech = client.audio.speech.create(
                    model=TTS_MODEL,
                    voice=TTS_VOICE,
                    input=scene["voiceover"],
                    instructions="Speak clear, warm, expressive narration for a family cartoon.",
                    response_format="mp3",
                )
                speech.stream_to_file(str(audio_path))

            caption_png(scene["voiceover"], caption_path)
            audio = AudioFileClip(str(audio_path))
            audio_clips.append(audio)
            duration = audio.duration
            bg = ImageClip(str(image_path)).with_duration(duration).resized((W, H))
            cap = ImageClip(str(caption_path), transparent=True).with_duration(duration)
            clips.append(
                CompositeVideoClip([bg, cap], size=(W, H))
                .with_audio(audio).with_duration(duration)
            )

        update(job_id, message="Combining scenes into MP4...")
        final = concatenate_videoclips(clips, method="compose")
        title = re.sub(r"[^A-Za-z0-9_-]+", "_", story.get("title", "cartoon"))[:50]
        output = work / f"{title or 'cartoon'}.mp4"
        final.write_videofile(
            str(output), fps=24, codec="libx264", audio_codec="aac",
            bitrate="6500k", logger=None
        )
        update(job_id, status="completed", message="Cartoon video is ready.",
               output=str(output), duration=final.duration)
    except Exception as exc:
        update(job_id, status="failed", message="Video generation failed.", error=str(exc))
    finally:
        if final:
            final.close()
        for clip in clips:
            clip.close()
        for audio in audio_clips:
            audio.close()


@app.get("/")
def home():
    return {"service": "AI Voice Cartoon Backend", "status": "online"}


@app.post("/generate")
def generate(req: GenerateRequest):
    job_id = uuid.uuid4().hex[:12]
    with lock:
        jobs[job_id] = {"status": "queued", "message": "Job queued"}
    thread = threading.Thread(
        target=generate_job, args=(job_id, req.model_dump()), daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    with lock:
        data = jobs.get(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {k: v for k, v in data.items() if k != "output"}


@app.get("/jobs/{job_id}/download")
def download(job_id: str):
    with lock:
        data = jobs.get(job_id)
    if not data or data.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Video is not ready")
    path = Path(data["output"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(path, media_type="video/mp4", filename=path.name)
