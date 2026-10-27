package com.luxisoft.realityos

import android.app.Activity
import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.meta.wearable.dat.camera.Camera
import com.meta.wearable.dat.camera.addCamera
import com.meta.wearable.dat.camera.removeCamera
import com.meta.wearable.dat.camera.types.PhotoData
import com.meta.wearable.dat.camera.types.StreamConfiguration
import com.meta.wearable.dat.camera.types.VideoQuality
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.selectors.AutoDeviceSelector
import com.meta.wearable.dat.core.selectors.SpecificDeviceSelector
import com.meta.wearable.dat.core.session.DeviceSession
import com.meta.wearable.dat.core.session.DeviceSessionState
import com.meta.wearable.dat.core.types.DeviceIdentifier
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.core.types.RegistrationState
import com.meta.wearable.dat.display.Display
import com.meta.wearable.dat.display.addDisplay
import com.meta.wearable.dat.display.removeDisplay
import com.meta.wearable.dat.display.types.DisplayState
import com.meta.wearable.dat.display.views.ButtonStyle
import com.meta.wearable.dat.display.views.Direction
import com.meta.wearable.dat.display.views.FlexBoxBackground
import com.meta.wearable.dat.display.views.IconName
import com.meta.wearable.dat.display.views.ImageSize
import com.meta.wearable.dat.display.views.TextColor
import com.meta.wearable.dat.display.views.TextStyle
import com.meta.wearable.dat.speech.Speech
import com.meta.wearable.dat.speech.addSpeech
import com.meta.wearable.dat.speech.removeSpeech
import java.io.ByteArrayOutputStream
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class WearableState(
    val registration: String = RegistrationState.UNAVAILABLE.name,
    val deviceAvailable: Boolean = false,
    val sessionActive: Boolean = false,
    val displayReady: Boolean = false,
    val cameraActive: Boolean = false,
    val speechActive: Boolean = false,
)

data class RealityUiState(
    val provisioning: DeviceProvisioning? = null,
    val wearable: WearableState = WearableState(),
    val captureSessionId: String? = null,
    val recording: Boolean = false,
    val busy: Boolean = false,
    val message: String = "Complete administrator provisioning, then connect RealityOS to Display.",
    val queryResult: QueryEvidence? = null,
)

/**
 * A DAT host with no field-worker phone workflow. The phone exists only because
 * Meta's SDK needs it for registration, Bluetooth transport, and audio routing;
 * once connected, all operational controls are rendered on Ray-Ban Display.
 */
class RealityViewModel(application: Application) : AndroidViewModel(application) {
    private val store = DeviceProvisioningStore(application)
    private val recorder = HevcMp4Recorder(application.cacheDir)
    private val _state = MutableStateFlow(RealityUiState(provisioning = store.read()))
    val state: StateFlow<RealityUiState> = _state.asStateFlow()

    private val _permissionRequests = MutableSharedFlow<Permission>(extraBufferCapacity = 1)
    val permissionRequests: SharedFlow<Permission> = _permissionRequests.asSharedFlow()
    private val _speechRequests = MutableSharedFlow<String>(extraBufferCapacity = 1)
    val speechRequests: SharedFlow<String> = _speechRequests.asSharedFlow()

    private var session: DeviceSession? = null
    private var display: Display? = null
    private var camera: Camera? = null
    private var speech: Speech? = null
    private var selectedZone: RemoteZone? = null
    private var pendingCameraPermission = false
    private var pendingMicrophonePermission = false
    private var sessionStateJob: Job? = null
    private var sessionErrorsJob: Job? = null
    private var displayStateJob: Job? = null
    private var frameJob: Job? = null
    private var speechJob: Job? = null
    private var recordingLimitJob: Job? = null

    init {
        viewModelScope.launch {
            Wearables.registrationState.collectLatest { registration ->
                _state.update { current ->
                    current.copy(wearable = current.wearable.copy(registration = registration.name))
                }
            }
        }
        viewModelScope.launch {
            Wearables.devices.collectLatest { devices ->
                _state.update { current ->
                    current.copy(wearable = current.wearable.copy(deviceAvailable = devices.isNotEmpty()))
                }
            }
        }
    }

    fun saveProvisioning(endpoint: String, workspaceId: String, deviceId: String, deviceKey: String) {
        if (endpoint.isBlank() || workspaceId.isBlank() || deviceId.isBlank() || deviceKey.isBlank()) {
            showStatus("Server URL, workspace ID, device ID and device key are required.")
            return
        }
        store.save(DeviceProvisioning(endpoint, workspaceId, deviceId, deviceKey))
        _state.update { it.copy(provisioning = store.read(), message = "Device provisioning saved.") }
    }

    fun registerWithMeta(activity: Activity) {
        Wearables.startRegistration(activity)
        showStatus("Complete Meta AI registration and grant the requested device permissions.")
    }

    /**
     * Uses automatic selection for physical glasses. Developer Preview passes
     * the identifier of Meta's display-capable mock so all other app behavior
     * remains identical.
     */
    fun connectDisplay(deviceIdentifier: DeviceIdentifier? = null) {
        if (_state.value.provisioning == null) {
            showStatus("An administrator must provision this device before it can use RealityOS.")
            return
        }
        if (Wearables.registrationState.value != RegistrationState.REGISTERED) {
            showStatus("Register RealityOS in Meta AI before connecting Display.")
            return
        }
        if (session != null) return
        val selector = deviceIdentifier?.let(::SpecificDeviceSelector)
            ?: AutoDeviceSelector(filter = { it.isDisplayCapable() })
        Wearables.createSession(selector).fold(
            onSuccess = { created ->
                session = created
                _state.update { current ->
                    current.copy(wearable = current.wearable.copy(sessionActive = true))
                }
                sessionErrorsJob = viewModelScope.launch {
                    created.errors.collect { error -> showError(error.description) }
                }
                sessionStateJob = viewModelScope.launch {
                    created.state.collect { sessionState ->
                        if (sessionState == DeviceSessionState.STARTED && display == null) attachDisplay(created)
                        if (sessionState == DeviceSessionState.STOPPED) cleanupStoppedSession(created)
                    }
                }
                created.start()
                showStatus("Connecting to Meta Ray-Ban Display…")
            },
            onFailure = { error, _ -> showError(error.description) },
        )
    }

    /**
     * A session with an active capture is intentionally not torn down: callers
     * must stop and finish capture so no evidence upload is silently lost.
     */
    fun disconnectDisplay(): Boolean {
        if (_state.value.recording || _state.value.captureSessionId != null || _state.value.busy) {
            showStatus("Finish or stop capture before disconnecting Display.")
            return false
        }
        stopSpeech()
        stopCamera()
        val activeSession = session
        session = null
        sessionStateJob?.cancel()
        sessionStateJob = null
        sessionErrorsJob?.cancel()
        sessionErrorsJob = null
        displayStateJob?.cancel()
        displayStateJob = null
        runCatching { activeSession?.removeDisplay() }
        runCatching { activeSession?.stop() }
        cleanupStoppedSession()
        showStatus("Display disconnected.")
        return true
    }

    fun onPermissionResult(permission: Permission, granted: Boolean) {
        if (!granted) {
            pendingCameraPermission = false
            pendingMicrophonePermission = false
            showError("${permission.name.lowercase().replaceFirstChar(Char::uppercase)} permission was not granted.")
            return
        }
        when (permission) {
            Permission.CAMERA -> if (pendingCameraPermission) {
                pendingCameraPermission = false
                openCaptureSessionAndCamera()
            }
            Permission.MICROPHONE -> if (pendingMicrophonePermission) {
                pendingMicrophonePermission = false
                startSpeechQuery()
            }
        }
    }

    private fun attachDisplay(activeSession: DeviceSession) {
        activeSession.addDisplay().fold(
            onSuccess = { attached ->
                display = attached
                displayStateJob = viewModelScope.launch {
                    attached.state.collect { displayState ->
                        val ready = displayState == DisplayState.STARTED
                        _state.update { current ->
                            current.copy(wearable = current.wearable.copy(displayReady = ready))
                        }
                        if (ready) renderHome()
                    }
                }
            },
            onFailure = { error, _ -> showError(error.description) },
        )
    }

    private fun beginRegister() {
        val provisioning = _state.value.provisioning ?: return showError("Device provisioning is missing.")
        viewModelScope.launch {
            setBusy(true)
            try {
                val zones = withContext(Dispatchers.IO) { RealityApi(provisioning).listZones() }
                if (zones.isEmpty()) showError("No locations are configured for this workspace.") else renderZonePicker(zones)
            } catch (error: Exception) {
                showError(error.message ?: "Could not load locations.")
            } finally {
                setBusy(false)
            }
        }
    }

    private fun chooseZone(zone: RemoteZone) {
        selectedZone = zone
        pendingCameraPermission = true
        _permissionRequests.tryEmit(Permission.CAMERA)
        renderNotice("Allow camera access in Meta AI to register evidence in ${zone.name}.")
    }

    private fun openCaptureSessionAndCamera() {
        val provisioning = _state.value.provisioning ?: return showError("Device provisioning is missing.")
        val activeSession = session ?: return showError("Display is not connected.")
        viewModelScope.launch {
            setBusy(true)
            try {
                val captureSession = withContext(Dispatchers.IO) {
                    RealityApi(provisioning).openCaptureSession(selectedZone?.id)
                }
                _state.update { it.copy(captureSessionId = captureSession.id) }
                activeSession.addCamera(
                    StreamConfiguration(
                        videoQuality = VideoQuality.MEDIUM,
                        frameRate = 15,
                        compressVideo = true,
                    ),
                ).fold(
                    onSuccess = { attached ->
                        camera = attached
                        frameJob = viewModelScope.launch(Dispatchers.Default) {
                            attached.stream.videoStream.collect { frame ->
                                recorder.observe(frame)
                                if (_state.value.recording) recorder.append(frame)
                            }
                        }
                        attached.stream.start().onFailure { error, _ -> showError(error.description) }
                        _state.update { current ->
                            current.copy(wearable = current.wearable.copy(cameraActive = true))
                        }
                        renderCapture()
                    },
                    onFailure = { error, _ ->
                        closeCaptureSessionOnServer(captureSession.id)
                        showError(error.description)
                    },
                )
            } catch (error: Exception) {
                showError(error.message ?: "Could not open the capture session.")
            } finally {
                setBusy(false)
            }
        }
    }

    private fun takePhoto() {
        val activeCamera = camera ?: return showError("Camera is not ready.")
        val captureSessionId = _state.value.captureSessionId ?: return showError("Open capture mode first.")
        val provisioning = _state.value.provisioning ?: return
        viewModelScope.launch {
            setBusy(true)
            try {
                activeCamera.stream.capturePhoto().fold(
                    onSuccess = { photo ->
                        val jpeg = photo.asJpegBytes()
                        if (jpeg == null) {
                            showError("The glasses returned an unreadable photo.")
                            return@fold
                        }
                        viewModelScope.launch {
                            try {
                                withContext(Dispatchers.IO) {
                                    val api = RealityApi(provisioning)
                                    val capture = api.uploadCapture(
                                        captureSessionId,
                                        jpeg,
                                        "realityos-${System.currentTimeMillis()}.jpg",
                                        "image/jpeg",
                                    )
                                    api.requestProcessing(capture.id, detailed = false)
                                }
                                showStatus("Photo stored. Basic visual analysis is queued.")
                                renderCapture()
                            } catch (error: Exception) {
                                showError(error.message ?: "Photo upload failed.")
                            } finally {
                                setBusy(false)
                            }
                        }
                    },
                    onFailure = { error, _ ->
                        showError(error.description)
                        setBusy(false)
                    },
                )
            } catch (error: Exception) {
                showError(error.message ?: "Photo capture failed.")
                setBusy(false)
            }
        }
    }

    private fun startVideo() {
        if (camera == null) return showError("Camera is not ready.")
        if (_state.value.recording) return
        recorder.begin()
        _state.update { it.copy(recording = true, message = "Recording video from glasses.") }
        recordingLimitJob?.cancel()
        recordingLimitJob = viewModelScope.launch {
            kotlinx.coroutines.delay(MAX_VIDEO_SECONDS * 1_000L)
            if (_state.value.recording) stopVideo()
        }
        renderCapture()
    }

    private fun stopVideo() {
        if (!_state.value.recording) return
        _state.update { it.copy(recording = false) }
        recordingLimitJob?.cancel()
        val captureSessionId = _state.value.captureSessionId ?: return
        val provisioning = _state.value.provisioning ?: return
        viewModelScope.launch {
            setBusy(true)
            val clip = withContext(Dispatchers.Default) { recorder.finish() }
            if (clip == null) {
                showError("No playable video was captured. Try recording for a few more seconds.")
                setBusy(false)
                renderCapture()
                return@launch
            }
            try {
                withContext(Dispatchers.IO) {
                    val api = RealityApi(provisioning)
                    val capture = api.uploadCaptureFile(captureSessionId, clip, "video/mp4")
                    api.requestProcessing(capture.id, detailed = false)
                }
                showStatus("Video stored. Representative-frame analysis is queued.")
            } catch (error: Exception) {
                showError(error.message ?: "Video upload failed.")
            } finally {
                clip.delete()
                setBusy(false)
                renderCapture()
            }
        }
    }

    private fun finishRegister() {
        if (_state.value.recording) {
            stopVideo()
            renderNotice("Video upload is finishing. Select Finish capture when it is complete.")
            return
        }
        val captureSessionId = _state.value.captureSessionId
        stopCamera()
        if (captureSessionId == null) {
            renderHome()
            return
        }
        val provisioning = _state.value.provisioning ?: return
        viewModelScope.launch {
            try {
                withContext(Dispatchers.IO) { RealityApi(provisioning).closeCaptureSession(captureSessionId) }
                _state.update { it.copy(captureSessionId = null, message = "Capture stopped. Evidence remains in RealityOS.") }
            } catch (error: Exception) {
                showError(error.message ?: "Could not close capture mode.")
            }
            renderHome()
        }
    }

    private fun stopCamera() {
        frameJob?.cancel()
        frameJob = null
        runCatching { camera?.stop() }
        session?.removeCamera()
        camera = null
        recorder.clearCodecConfiguration()
        _state.update { current ->
            current.copy(recording = false, wearable = current.wearable.copy(cameraActive = false))
        }
    }

    private fun beginQuery() {
        if (_state.value.captureSessionId != null) {
            renderNotice("Stop capture before querying stored memory.")
            return
        }
        pendingMicrophonePermission = true
        _permissionRequests.tryEmit(Permission.MICROPHONE)
        renderNotice("Allow microphone access in Meta AI, then ask for an object.")
    }

    private fun startSpeechQuery() {
        val activeSession = session ?: return showError("Display is not connected.")
        if (speech != null) return
        activeSession.addSpeech().fold(
            onSuccess = { attached ->
                speech = attached
                _state.update { current ->
                    current.copy(wearable = current.wearable.copy(speechActive = true))
                }
                speechJob = viewModelScope.launch {
                    attached.transcriptions.collect { transcription ->
                        val text = transcription?.text?.takeIf { it.isNotBlank() } ?: return@collect
                        if (transcription.isFinal) {
                            stopSpeech()
                            executeQuery(text)
                        } else {
                            renderListening(text)
                        }
                    }
                }
                attached.start().onFailure { error, _ -> showError(error.description) }
                renderListening("Listening…")
            },
            onFailure = { error, _ -> showError(error.description) },
        )
    }

    private fun stopSpeech() {
        speechJob?.cancel()
        speechJob = null
        runCatching { speech?.stop() }
        session?.removeSpeech()
        speech = null
        _state.update { current ->
            current.copy(wearable = current.wearable.copy(speechActive = false))
        }
    }

    private fun executeQuery(question: String) {
        val provisioning = _state.value.provisioning ?: return showError("Device provisioning is missing.")
        viewModelScope.launch {
            setBusy(true)
            try {
                val answer = withContext(Dispatchers.IO) { RealityApi(provisioning).query(question) }
                _state.update { it.copy(queryResult = answer, message = answer.message) }
                val imageUrl = answer.displayMediaPath?.let { RealityApi(provisioning).absoluteUrl(it) }
                renderQueryResult(answer, imageUrl)
                if (answer.ttsText.isNotBlank()) _speechRequests.tryEmit(answer.ttsText)
            } catch (error: Exception) {
                showError(error.message ?: "Could not query RealityOS.")
            } finally {
                setBusy(false)
            }
        }
    }

    private fun renderHome() = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.CARD) {
            text("RealityOS", style = TextStyle.HEADING)
            text("Spatial memory", style = TextStyle.META, color = TextColor.SECONDARY)
            button("Register", style = ButtonStyle.PRIMARY, iconName = IconName.VIDEO_CAMERA, onClick = ::beginRegister)
            button("Find an object", style = ButtonStyle.SECONDARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
        }
    }

    private fun renderZonePicker(zones: List<RemoteZone>) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
            text("Choose location", style = TextStyle.HEADING)
            text("Capture starts only after you select one.", style = TextStyle.META, color = TextColor.SECONDARY)
            zones.take(MAX_DISPLAY_ZONES).forEach { zone ->
                button(zone.name, style = ButtonStyle.SECONDARY, iconName = IconName.CONTAINER_WITH_LID, onClick = { chooseZone(zone) })
            }
            button("Back", style = ButtonStyle.OUTLINE, iconName = IconName.ARROW_LEFT, onClick = ::renderHome)
        }
    }

    private fun renderCapture() = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.CARD) {
            text("Register evidence", style = TextStyle.HEADING)
            text(selectedZone?.name ?: "Selected location", style = TextStyle.META, color = TextColor.SECONDARY)
            button("Take photo", style = ButtonStyle.PRIMARY, iconName = IconName.VIDEO_CAMERA, onClick = ::takePhoto)
            if (_state.value.recording) {
                button("Stop video", style = ButtonStyle.PRIMARY, iconName = IconName.X, onClick = ::stopVideo)
                text("Video recording (up to 2 minutes)", style = TextStyle.META, color = TextColor.SECONDARY)
            } else {
                button("Record video", style = ButtonStyle.SECONDARY, iconName = IconName.VIDEO_CAMERA, onClick = ::startVideo)
            }
            button("Finish capture", style = ButtonStyle.OUTLINE, iconName = IconName.CHECKMARK, onClick = ::finishRegister)
        }
    }

    private fun renderListening(partial: String) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.CARD) {
            text("Ask RealityOS", style = TextStyle.HEADING)
            text(partial.take(MAX_DISPLAY_TEXT), style = TextStyle.BODY)
            text("Listening on the glasses…", style = TextStyle.META, color = TextColor.SECONDARY)
            button("Cancel", style = ButtonStyle.OUTLINE, iconName = IconName.X, onClick = {
                stopSpeech()
                renderHome()
            })
        }
    }

    private fun renderQueryResult(answer: QueryEvidence, imageUrl: String?) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 10, padding = 20, background = FlexBoxBackground.CARD) {
            text(if (answer.found) "Last seen" else if (answer.ambiguous) "More detail needed" else "No evidence", style = TextStyle.HEADING)
            imageUrl?.let { image(uri = it, sizePreset = ImageSize.FILL) }
            text(answer.message.take(MAX_DISPLAY_TEXT), style = TextStyle.BODY)
            button("Hear again", style = ButtonStyle.SECONDARY, iconName = IconName.SPEAKER_WITH_TWO_ARCS, onClick = { _speechRequests.tryEmit(answer.ttsText) })
            button("New query", style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
            button("Home", style = ButtonStyle.OUTLINE, iconName = IconName.HOUSE, onClick = ::renderHome)
        }
    }

    private fun renderNotice(message: String) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.CARD) {
            text("RealityOS", style = TextStyle.HEADING)
            text(message.take(MAX_DISPLAY_TEXT), style = TextStyle.BODY)
            button("Home", style = ButtonStyle.PRIMARY, iconName = IconName.HOUSE, onClick = ::renderHome)
        }
    }

    private fun sendDisplay(content: com.meta.wearable.dat.display.views.ContentScope.() -> Unit) {
        val currentDisplay = display ?: return
        viewModelScope.launch {
            currentDisplay.sendContent(content).onFailure { error, _ -> showError(error.description) }
        }
    }

    private fun closeCaptureSessionOnServer(sessionId: String) {
        val provisioning = _state.value.provisioning ?: return
        viewModelScope.launch(Dispatchers.IO) { runCatching { RealityApi(provisioning).closeCaptureSession(sessionId) } }
    }

    private fun showStatus(message: String) {
        _state.update { it.copy(message = message) }
    }

    private fun showError(message: String) {
        _state.update { it.copy(message = message, busy = false) }
        renderNotice(message)
    }

    private fun setBusy(value: Boolean) {
        _state.update { it.copy(busy = value) }
    }

    private fun cleanupStoppedSession(stoppedSession: DeviceSession? = null) {
        // A delayed state event from an old session must not reset a newly
        // connected physical or virtual device.
        if (stoppedSession != null && session != null && session !== stoppedSession) return
        _state.value.captureSessionId?.let(::closeCaptureSessionOnServer)
        session = null
        display = null
        camera = null
        speech = null
        frameJob?.cancel()
        speechJob?.cancel()
        _state.update { current ->
            current.copy(
                captureSessionId = null,
                recording = false,
                wearable = current.wearable.copy(
                    sessionActive = false,
                    displayReady = false,
                    cameraActive = false,
                    speechActive = false,
                ),
            )
        }
    }

    override fun onCleared() {
        recorder.close(deleteIncomplete = true)
        recordingLimitJob?.cancel()
        stopSpeech()
        stopCamera()
        runCatching { session?.removeDisplay() }
        runCatching { session?.stop() }
        sessionStateJob?.cancel()
        sessionErrorsJob?.cancel()
        displayStateJob?.cancel()
        super.onCleared()
    }

    private fun PhotoData.asJpegBytes(): ByteArray? = when (this) {
        is PhotoData.Bitmap -> bitmap.toJpeg()
        is PhotoData.HEIC -> {
            val copy = data.duplicate().let { buffer -> ByteArray(buffer.remaining()).also(buffer::get) }
            BitmapFactory.decodeByteArray(copy, 0, copy.size)?.toJpeg()
        }
    }

    private fun Bitmap.toJpeg(): ByteArray = ByteArrayOutputStream().use { output ->
        compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, output)
        output.toByteArray()
    }

    private companion object {
        const val MAX_VIDEO_SECONDS = 120L
        const val MAX_DISPLAY_ZONES = 8
        const val MAX_DISPLAY_TEXT = 360
        const val JPEG_QUALITY = 92
    }
}
