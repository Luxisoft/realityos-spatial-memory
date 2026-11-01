package com.luxisoft.realityos

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaRecorder
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File

/** Image bytes waiting for an optional note before publishing. */
internal data class PendingPublishPhoto(val bytes: ByteArray, val mimeType: String, val name: String)

/**
 * Optional note step after choosing publish media (mobile only): record a
 * voice note transcribed by the server, or write the note directly.
 */
@Composable
internal fun PublishNoteDialog(
    onPublish: (noteText: String, noteSource: String) -> Unit,
    onDismiss: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var note by remember { mutableStateOf("") }
    var voiceUsed by remember { mutableStateOf(false) }
    var recording by remember { mutableStateOf(false) }
    var transcribing by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var recorder by remember { mutableStateOf<MediaRecorder?>(null) }
    var audioFile by remember { mutableStateOf<File?>(null) }

    fun releaseRecorder() {
        try { recorder?.release() } catch (_: Exception) { }
        recorder = null
    }
    DisposableEffect(Unit) { onDispose { releaseRecorder() } }

    fun transcribe(file: File) {
        scope.launch {
            transcribing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) { file.readBytes() }
                val response = withContext(Dispatchers.IO) {
                    JSONObject(
                        SocialSession.requestMultipart(
                            "notes/transcribe",
                            emptyMap(),
                            bytes,
                            "nota.m4a",
                            "audio/mp4",
                            fieldName = "audio",
                        ),
                    )
                }
                note = response.optString("text")
                voiceUsed = true
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                transcribing = false
            }
        }
    }

    fun stopRecording() {
        val file = audioFile
        recording = false
        try { recorder?.stop() } catch (_: Exception) { error = localizedText(R.string.ui_could_not_record_the_note) }
        releaseRecorder()
        if (file != null && error.isEmpty()) transcribe(file)
    }

    fun startRecording() {
        error = ""
        try {
            val file = File(File(context.cacheDir, "notes").apply { mkdirs() }, "nota-${System.currentTimeMillis()}.m4a")
            audioFile = file
            recorder = MediaRecorder(context).apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            recording = true
        } catch (_: Exception) {
            error = localizedText(R.string.ui_could_not_record_the_note)
            releaseRecorder()
        }
    }
    val askAudio = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) startRecording() else error = localizedText(R.string.ui_microphone_permission_is_required)
    }

    AlertDialog(
        onDismissRequest = { if (!recording && !transcribing) onDismiss() },
        title = { Text(localizedText(R.string.ui_add_note)) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    IconButton(
                        onClick = {
                            if (recording) stopRecording()
                            else if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) startRecording()
                            else askAudio.launch(Manifest.permission.RECORD_AUDIO)
                        },
                        enabled = !transcribing,
                    ) {
                        Icon(
                            if (recording) Icons.Filled.Stop else Icons.Filled.Mic,
                            contentDescription = if (recording) localizedText(R.string.ui_stop_recording) else localizedText(R.string.ui_record_voice_note),
                            tint = if (recording) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                        )
                    }
                    Text(
                        if (recording) localizedText(R.string.ui_recording_tap_to_stop)
                        else if (transcribing) localizedText(R.string.ui_transcribing)
                        else localizedText(R.string.ui_record_your_voice_or_type_directly),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
                if (transcribing) LinearProgressIndicator(Modifier.fillMaxWidth())
                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = { Text(localizedText(R.string.ui_note_optional)) },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2,
                )
                if (error.isNotEmpty()) Text(error, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { onPublish("", "") }) { Text(localizedText(R.string.ui_no_note)) }
                    Spacer(Modifier.weight(1f))
                    TextButton(onClick = onDismiss) { Text(localizedText(R.string.ui_cancel)) }
                    Button(onClick = {
                        val text = note.trim()
                        onPublish(text, if (text.isEmpty()) "" else if (voiceUsed) "voice" else "text")
                    }) { Text(localizedText(R.string.ui_publish)) }
                }
            }
        },
        confirmButton = {},
    )
}
