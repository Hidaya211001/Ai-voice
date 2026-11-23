package com.example.aivoicecartoon

import android.Manifest
import android.app.Activity
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.speech.RecognizerIntent
import android.view.Gravity
import android.widget.*
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.Locale

class MainActivity : Activity() {
    private val http = OkHttpClient()
    private lateinit var serverInput: EditText
    private lateinit var commandInput: EditText
    private lateinit var statusText: TextView
    private lateinit var createButton: Button
    private lateinit var downloadButton: Button
    private var activeJobId: String? = null
    private val handler = android.os.Handler(mainLooper)

    private val speechLauncher =
        registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.StartActivityForResult()) { result ->
            if (result.resultCode == RESULT_OK) {
                val spoken = result.data
                    ?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                    ?.firstOrNull()
                if (!spoken.isNullOrBlank()) commandInput.setText(spoken)
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 35, 28, 24)
            gravity = Gravity.CENTER_HORIZONTAL
        }

        val title = TextView(this).apply {
            text = "AI VOICE CARTOON MAKER"
            textSize = 23f
            gravity = Gravity.CENTER
            setPadding(0, 8, 0, 12)
        }
        layout.addView(title)

        layout.addView(label("Backend server address"))
        serverInput = EditText(this).apply {
            setSingleLine(true)
            hint = "http://192.168.1.5:8000"
            setText("http://10.0.2.2:8000")
        }
        layout.addView(serverInput)

        layout.addView(label("Speak your cartoon command (Hindi or English)"))
        commandInput = EditText(this).apply {
            minLines = 3
            maxLines = 5
            hint = "Make a 5-minute cartoon about a brave little rabbit..."
        }
        layout.addView(commandInput)

        val micButton = Button(this).apply {
            text = "🎙 SPEAK COMMAND"
            setOnClickListener { startVoiceInput() }
        }
        layout.addView(micButton)

        createButton = Button(this).apply {
            text = "✨ GENERATE MY CARTOON"
            setOnClickListener { submitJob() }
        }
        layout.addView(createButton)

        statusText = TextView(this).apply {
            text = "Ready. Speak a command, then tap Generate."
            textSize = 16f
            setPadding(0, 22, 0, 18)
        }
        layout.addView(statusText)

        downloadButton = Button(this).apply {
            text = "⬇ DOWNLOAD MP4"
            isEnabled = false
            setOnClickListener { downloadVideo() }
        }
        layout.addView(downloadButton)

        val note = TextView(this).apply {
            text = "Default output: English 3D cartoon, about 5 minutes. Requires internet, an OpenAI API backend, and API billing."
            textSize = 12f
            setPadding(0, 22, 0, 0)
        }
        layout.addView(note)

        setContentView(ScrollView(this).apply { addView(layout) })
    }

    private fun label(text: String) = TextView(this).apply {
        this.text = text
        textSize = 14f
        setPadding(0, 15, 0, 4)
    }

    private fun startVoiceInput() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), 101)
            return
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Apna cartoon command boliye")
        }
        try {
            speechLauncher.launch(intent)
        } catch (_: Exception) {
            statusText.text = "Speech recognition service is not available on this phone."
        }
    }

    private fun submitJob() {
        val base = serverInput.text.toString().trim().trimEnd('/')
        val command = commandInput.text.toString().trim()
        if (base.isBlank() || command.isBlank()) {
            statusText.text = "Server address aur voice command dono zaroori hain."
            return
        }

        createButton.isEnabled = false
        downloadButton.isEnabled = false
        statusText.text = "Request bheji ja rahi hai..."

        val json = JSONObject().put("command", command)
            .put("output_language", "English")
            .put("style", "3D cartoon")
            .put("target_minutes", 5)
            .toString()
        val body = json.toRequestBody("application/json".toMediaType())
        val request = Request.Builder().url("$base/generate").post(body).build()

        http.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    createButton.isEnabled = true
                    statusText.text = "Connection error: ${e.message}. Check server address."
                }
            }
            override fun onResponse(call: Call, response: Response) {
                val text = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    runOnUiThread {
                        createButton.isEnabled = true
                        statusText.text = "Server error: $text"
                    }
                    return
                }
                val id = JSONObject(text).getString("job_id")
                activeJobId = id
                runOnUiThread { statusText.text = "Job started. Creating script, images, voice and video..." }
                pollJob(base, id)
            }
        })
    }

    private fun pollJob(base: String, id: String) {
        val request = Request.Builder().url("$base/jobs/$id").get().build()
        http.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                handler.postDelayed({ pollJob(base, id) }, 5000)
            }
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    runOnUiThread {
                        createButton.isEnabled = true
                        statusText.text = "Status error: $body"
                    }
                    return
                }
                val data = JSONObject(body)
                val state = data.optString("status")
                val message = data.optString("message", state)
                runOnUiThread { statusText.text = message }
                when (state) {
                    "completed" -> runOnUiThread {
                        createButton.isEnabled = true
                        downloadButton.isEnabled = true
                        statusText.text = "Your cartoon video is ready. Tap Download MP4."
                    }
                    "failed" -> runOnUiThread {
                        createButton.isEnabled = true
                        statusText.text = "Generation failed: ${data.optString("error")}"
                    }
                    else -> handler.postDelayed({ pollJob(base, id) }, 5000)
                }
            }
        })
    }

    private fun downloadVideo() {
        val id = activeJobId ?: return
        val base = serverInput.text.toString().trim().trimEnd('/')
        val request = DownloadManager.Request(Uri.parse("$base/jobs/$id/download"))
            .setTitle("AI Cartoon Video")
            .setDescription("Downloading your generated cartoon MP4")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "AI_Cartoon_$id.mp4")
            .setMimeType("video/mp4")
        val manager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        manager.enqueue(request)
        statusText.text = "Download started. Check your Downloads folder."
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 101 && grantResults.isNotEmpty() &&
            grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            startVoiceInput()
        } else if (requestCode == 101) {
            statusText.text = "Microphone permission is needed for voice commands."
        }
    }
}
