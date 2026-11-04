package com.luxisoft.realityos

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Remote response audio; the existing Android voice remains the last fallback. */
internal class AgentSpeechPlayer(
    private val context: Context,
    private val scope: CoroutineScope,
    private val provisioning: () -> DeviceProvisioning?,
    private val started: () -> Unit,
    private val done: () -> Unit,
    private val fallback: (LocalizedSpeech) -> Unit,
    private val notice: () -> Unit,
    private val openConnection: (String) -> HttpURLConnection = { URL(it).openConnection() as HttpURLConnection }
) {
    private var generation = 0L
    private var job: Job? = null
    private var player: MediaPlayer? = null
    private var temporary: File? = null

    @Volatile private var connection: HttpURLConnection? = null

    fun stop() {
        generation++
        job?.cancel()
        job = null
        connection?.disconnect()
        connection = null
        player?.release()
        player = null
        temporary?.delete()
        temporary = null
    }

    fun speak(request: LocalizedSpeech) {
        stop()
        val revision = generation
        val token = SocialSession.token
        val identity = SocialSession.identity
        val device = if (token == null) provisioning() else null
        fun current() = generation == revision &&
            request.matches(RealityExperienceStore(context).selectedLanguage().languageTag) &&
            SocialSession.isCurrent(identity)
        if (!current() || request.text.isBlank()) {
            done()
            return
        }
        if (token == null && device == null) {
            fallback(request)
            return
        }
        val file = File.createTempFile("agent-speech-", ".wav", context.cacheDir)
        temporary = file
        var usedFallback = false
        fun useDeviceVoice() {
            if (!current() || usedFallback) return
            usedFallback = true
            player?.release()
            player = null
            file.delete()
            notice()
            fallback(request)
        }
        // Include the download in the speaking state so Stop cancels pending audio.
        started()
        job = scope.launch {
            try {
                val status = withContext(Dispatchers.IO) {
                    fun download(access: String?): Int {
                        if (!current()) throw CancellationException("Speech request replaced")
                        SocialSession.requireCurrent(identity)
                        val base = device?.apiBaseUrl ?: BuildConfig.DEFAULT_REALITYOS_API_BASE_URL
                        val http = openConnection("${base.trimEnd('/')}/tts")
                        connection = http
                        return try {
                            http.requestMethod = "POST"
                            http.connectTimeout = 5000
                            http.readTimeout = 33000
                            http.instanceFollowRedirects = false
                            http.doOutput = true
                            http.setRequestProperty("Content-Type", "application/json")
                            if (access != null) {
                                http.setRequestProperty("Authorization", "Bearer $access")
                            } else if (device != null) {
                                http.setRequestProperty("X-RealityOS-Device-ID", device.deviceId)
                                http.setRequestProperty("X-RealityOS-Device-Key", device.deviceKey)
                            }
                            val payload = JSONObject().put("text", request.text).put("language", request.language)
                            http.outputStream.bufferedWriter().use { it.write(payload.toString()) }
                            val code = http.responseCode
                            if (code == 200) {
                                check(http.contentType?.startsWith("audio/wav") == true)
                                http.inputStream.use { input ->
                                    file.outputStream().use { output ->
                                        val buffer = ByteArray(16384)
                                        var size = 0
                                        while (true) {
                                            val count = input.read(buffer)
                                            if (count < 0) break
                                            size += count
                                            check(size <= 16 * 1024 * 1024)
                                            output.write(buffer, 0, count)
                                        }
                                        check(size > 44)
                                    }
                                }
                            }
                            code
                        } finally {
                            http.disconnect()
                            if (connection === http) connection = null
                        }
                    }
                    val result = download(token)
                    if (result == 401 && token != null) download(SocialSession.refreshAccess(identity, token)) else result
                }
                if (!current()) {
                    file.delete()
                    return@launch
                }
                if (status == 401 || status == 403) {
                    file.delete()
                    done()
                    return@launch
                }
                if (status != 200) {
                    useDeviceVoice()
                    return@launch
                }
                val audio = MediaPlayer()
                player = audio
                audio.setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()
                )
                audio.setDataSource(file.absolutePath)
                audio.setOnPreparedListener { if (current()) it.start() }
                audio.setOnCompletionListener {
                    if (current()) {
                        stop()
                        done()
                    }
                }
                audio.setOnErrorListener { _, _, _ ->
                    useDeviceVoice()
                    true
                }
                audio.prepareAsync()
            } catch (error: CancellationException) {
                file.delete()
                throw error
            } catch (_: Exception) {
                if (!SocialSession.isCurrent(identity)) {
                    if (generation == revision) done()
                } else {
                    useDeviceVoice()
                }
            }
        }
    }
}
