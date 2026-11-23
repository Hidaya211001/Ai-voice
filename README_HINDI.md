# AI Voice Cartoon Maker — Android Starter Project

यह एक Android Studio source project + Python backend है। मोबाइल में बोलकर command दें;
Android Speech Recognizer उसे text में बदलता है; backend OpenAI से script, scene images,
voiceover बनाता है और MoviePy से MP4 जोड़ता है।

## यह क्या करता है
- Android app में microphone button और Generate button
- Hindi/English voice input (फोन की speech-recognition language settings पर निर्भर)
- डिफॉल्ट output: English, 3D-cartoon style, लगभग 5 मिनट
- OpenAI से कहानी और 10 scene prompts
- हर scene के लिए image और narration
- subtitles और MP4 assembly using MoviePy
- MP4 Android Downloads folder में download

## जरूरी सीमा
यह शुरुआती संस्करण generated still images + narration + captions का cartoon animatic बनाता है।
यह full 3D character animation, lip-sync या frame-by-frame movement नहीं बनाता।
5 मिनट लक्ष्य है; वास्तविक अवधि narration के अनुसार बदल सकती है। Background music अभी शामिल नहीं है।

## सुरक्षा
OpenAI API key Android APK में न रखें। Key केवल backend की `.env` file में रखें।
यह starter backend development/testing के लिए है; public internet पर deploy करने से पहले
authentication, per-user quotas, HTTPS, rate limiting, persistent job storage और cleanup जोड़ें।
API usage की लागत अलग से लगेगी।

## Backend चलाना (Windows / macOS / Linux)
1. Python 3.10+ और FFmpeg install करें।
2. `backend` folder में जाएँ:
   `python -m venv .venv`
3. Windows: `.venv\\Scripts\\activate`
   macOS/Linux: `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `.env.example` की copy बनाकर `.env` नाम दें और OpenAI API key भरें।
6. चलाएँ:
   `uvicorn server:app --host 0.0.0.0 --port 8000`

## Android Studio
1. Android Studio में `android_app` folder खोलें।
2. Gradle sync होने दें और Android SDK 35 install करें।
3. फोन और backend computer एक ही Wi-Fi पर हों।
4. App में Backend server address में computer का LAN IP डालें, जैसे:
   `http://192.168.1.20:8000`
   Android Emulator में `http://10.0.2.2:8000` इस्तेमाल करें।
5. फोन पर app चलाएँ, microphone permission दें, command बोलें और Generate दबाएँ।

## APK बनाना
Android Studio > Build > Build Bundle(s) / APK(s) > Build APK(s).
यह source project है; इस environment में signed/verified APK build नहीं किया गया।

## Troubleshooting
- Connection refused: backend चालू है और सही IP/port है, जाँचें।
- OpenAI model access error: `.env` में अपने API project के लिए उपलब्ध model names रखें।
- Image verification/billing: OpenAI developer account में image model access और billing जाँचें।
- FFmpeg error: FFmpeg PATH में install होना चाहिए।
- Speech recognition: Android device पर speech recognition service और internet उपलब्ध होना चाहिए।
