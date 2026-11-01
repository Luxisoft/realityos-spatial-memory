package com.luxisoft.realityos

import android.app.Activity
import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.annotation.StringRes
import androidx.camera.core.Preview
import androidx.camera.core.ViewPort
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.luxisoft.realityos.host.operations.*
import com.meta.wearable.dat.camera.Camera
import com.meta.wearable.dat.camera.addCamera
import com.meta.wearable.dat.camera.removeCamera
import com.meta.wearable.dat.camera.types.AudioCodec
import com.meta.wearable.dat.camera.types.AudioSampleRate
import com.meta.wearable.dat.camera.types.PhotoData
import com.meta.wearable.dat.camera.types.StreamConfiguration
import com.meta.wearable.dat.camera.types.VideoQuality
import com.meta.wearable.dat.core.Wearables
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
import java.time.Instant
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull

data class WearableState(
    val registration: String = RegistrationState.UNAVAILABLE.name,
    val transportReady: Boolean = false,
    val deviceAvailable: Boolean = false,
    val sessionActive: Boolean = false,
    val displayReady: Boolean = false,
    val cameraActive: Boolean = false,
    val speechActive: Boolean = false,
    val inputRoute: InputRoute = InputRoute.PHONE
)

data class RealityUiState(
    val provisioning: DeviceProvisioning? = null,
    val virtualProfileLoading: Boolean = false,
    val virtualProfileError: String? = null,
    val wearable: WearableState = WearableState(),
    val captureSessionId: String? = null,
    val recording: Boolean = false,
    val busy: Boolean = false,
    val processingJobs: Int = 0,
    val message: String = "",
    val meta: MetaDisplayState = MetaDisplayState(),
    val phonePreview: PhonePreviewState = PhonePreviewState(),
    val queryResult: QueryEvidence? = null
)

/** A Display host with explicit phone and wearable input routes. */
class RealityViewModel(application: Application) : AndroidViewModel(application) {
    internal val app = application
    internal val store = DeviceProvisioningStore(application)
    internal val recorder = HevcMp4Recorder(application.cacheDir)
    internal val storedProvisioning = store.read()
    internal val mutableUiState = MutableStateFlow(
        RealityUiState(
            provisioning = storedProvisioning,
            message = app.getString(R.string.status_initial)
        )
    )
    val state: StateFlow<RealityUiState> = mutableUiState.asStateFlow()

    internal val permissionIds = AtomicLong(0)
    internal val mutablePermissionRequest = MutableStateFlow<RealityPermissionRequest?>(null)
    val permissionRequest: StateFlow<RealityPermissionRequest?> = mutablePermissionRequest.asStateFlow()
    internal val mutableSpeechRequests = MutableSharedFlow<LocalizedSpeech>(extraBufferCapacity = 1)
    val speechRequests: SharedFlow<LocalizedSpeech> = mutableSpeechRequests.asSharedFlow()
    private val _speechStopRequests = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val speechStopRequests: SharedFlow<Unit> = _speechStopRequests.asSharedFlow()
    private val _speaking = MutableStateFlow(false)
    val speaking: StateFlow<Boolean> = _speaking.asStateFlow()

    /** Speak a short reply on the active audio route (phone or glasses). */
    fun speak(text: String, language: String = RealityExperienceStore(app).selectedLanguage().languageTag) {
        if (text.isNotBlank()) mutableSpeechRequests.tryEmit(LocalizedSpeech(text, language))
    }

    fun stopSpeak() {
        _speechStopRequests.tryEmit(Unit)
        _speaking.value = false
    }

    fun onSpeechStarted() {
        _speaking.value = true
    }

    fun onSpeechDone() {
        _speaking.value = false
    }

    internal var session: DeviceSession? = null
    internal var display: Display? = null
    internal var camera: Camera? = null
    internal var speech: Speech? = null
    internal var phoneCapture: PhoneCaptureSource? = null
    internal var phoneSpeech: PhoneSpeechSource? = null
    internal var selectedZone: RemoteZone? = null
    internal var inputRoute = InputRoute.PHONE
    internal var pendingAction: PendingAction? = null
    internal var wearablesObservationStarted = false
    internal var sessionStateJob: Job? = null
    internal var sessionErrorsJob: Job? = null
    internal var displayStateJob: Job? = null
    internal var frameJob: Job? = null
    internal var audioFrameJob: Job? = null
    internal var streamStateJob: Job? = null
    internal var cameraErrorJob: Job? = null
    internal var speechJob: Job? = null
    internal var speechErrorJob: Job? = null
    internal var phoneSpeechJob: Job? = null
    internal var phonePreviewSurfaceJob: Job? = null
    internal var captureOperationJob: Job? = null
    internal var queryJob: Job? = null
    internal var galleryImageJob: Job? = null
    internal var recordingLimitJob: Job? = null
    internal val renderMutex = Mutex()
    internal var renderRevision = 0L
    internal val processingJobIds = linkedSetOf<String>()
    internal var pendingUpload: PendingUpload? = null

    internal sealed interface PendingAction {
        data object PrepareCapture : PendingAction
        data object PrepareWearableCaptureAudio : PendingAction
        data object PrepareWearablePhoneAudio : PendingAction
        data object StartPhoneVideo : PendingAction
        data object StartQuery : PendingAction
    }

    internal data class PendingUpload(
        val captureSessionId: String,
        val file: File,
        val mimeType: String,
        @param:StringRes val successMessage: Int,
        // Once the server has accepted the media, retries must reuse that
        // capture and only retry job creation. This avoids duplicate evidence
        // when the network fails between upload and process acknowledgement.
        var remoteCaptureId: String? = null
    )

    internal val metaController = MetaDisplayController(this)

    fun refreshMetaConfiguration() = metaController.refresh()
    fun selectMetaDestination(destination: MetaDestination) = metaController.selectDestination(destination)
    fun selectMetaSearch(scope: MetaSearchScope) = metaController.selectScope(scope)
    fun beginMetaCapture() = metaController.beginCapture()
    fun beginMetaPhotoSearch(kind: MetaPhotoSearchKind = MetaPhotoSearchKind.OBJECT) = metaController.beginPhotoSearch(kind)
    fun beginMetaObjectSearch() = metaController.beginPhotoSearch(MetaPhotoSearchKind.OBJECT)
    fun beginMetaPersonSearch() = metaController.beginPhotoSearch(MetaPhotoSearchKind.PERSON)
    fun publishMetaCapture() = metaController.submit()
    fun retryMetaPublication() = metaController.submit(if (state.value.meta.uploadStatus == "failed") "retry" else null)
    fun replaceMetaPublication() = metaController.submit("confirm")
    fun discardMetaCapture() = metaController.discard()
    fun clearMetaAccount() = metaController.clear()

    init {
        viewModelScope.launch {
            val experience = RealityExperienceStore(app)
            var previous = experience.selectedLanguage()
            experience.language.collect { selected ->
                if (selected != previous) {
                    previous = selected
                    refreshDisplayLanguage()
                }
            }
        }
        val liveCredentialNearExpiry = storedProvisioning?.source == ProvisioningSource.VIRTUAL_LIVE &&
            storedProvisioning.expiresAt?.isBefore(Instant.now().plusSeconds(5 * 60)) == true
        if (!BuildConfig.LOCAL_DEVELOPMENT && (storedProvisioning == null || liveCredentialNearExpiry)) {
            loadVirtualDeviceProfile(saveAutomatically = true)
        }
    }

    /** Refresh Display copy while retaining an active capture and pending upload. */
    private fun refreshDisplayLanguage() {
        stopSpeak()
        val queryActive = queryJob?.isActive == true
        queryJob?.cancel()
        queryJob = null
        val current = state.value
        if (!current.meta.captureForPublication && !current.meta.captureForSearch && current.meta.pendingMime == null) metaController.generation.invalidate()
        mutableUiState.update { it.copy(queryResult = null, message = copy(R.string.status_ready), busy = if (queryActive) false else it.busy) }
        if (!current.wearable.displayReady) return
        when {
            current.wearable.cameraActive -> renderCapture()
            current.meta.pendingMime != null -> renderPublicationReview()
            current.wearable.speechActive -> renderListening("")
            else -> renderHome()
        }
    }

    /** Restores the project-owned live profile from the configured server. */
    fun loadVirtualDeviceProfile(saveAutomatically: Boolean = true) {
        if (mutableUiState.value.virtualProfileLoading) return
        val bootstrapUrl = BuildConfig.DEFAULT_REALITYOS_API_BASE_URL
        mutableUiState.update { it.copy(virtualProfileLoading = true, virtualProfileError = null) }
        viewModelScope.launch {
            val result = withContext(Dispatchers.IO) {
                runCatching {
                    VirtualDeviceBootstrapApi.fetch(
                        bootstrapUrl,
                        store.installationId()
                    )
                }
            }
            result.onSuccess { profile ->
                if (SocialSession.active) return@onSuccess
                if (profile.processingMode.lowercase() != "live") {
                    mutableUiState.update {
                        it.copy(
                            virtualProfileLoading = false,
                            virtualProfileError = copy(R.string.status_live_not_confirmed),
                            message = copy(R.string.status_enrollment_incomplete)
                        )
                    }
                    return@onSuccess
                }
                val provisioning = profile.toProvisioning()
                if (saveAutomatically) store.save(provisioning)
                mutableUiState.update {
                    it.copy(
                        provisioning = if (saveAutomatically) provisioning else it.provisioning,
                        virtualProfileLoading = false,
                        virtualProfileError = null,
                        message = copy(R.string.status_live_connection_ready)
                    )
                }
            }.onFailure { error ->
                mutableUiState.update {
                    it.copy(
                        virtualProfileLoading = false,
                        virtualProfileError = error.message ?: copy(R.string.status_load_live_failed),
                        message = copy(R.string.status_enter_custom_or_retry)
                    )
                }
            }
        }
    }

    fun useFacebookCaptureProfile(profile: DeviceProvisioning) {
        stopCamera()
        store.save(profile)
        mutableUiState.update { it.copy(provisioning = profile, virtualProfileError = null) }
    }

    fun registerWithMeta(activity: Activity) {
        if (!mutableUiState.value.wearable.transportReady) {
            showStatus(copy(R.string.status_wearables_not_ready))
            return
        }
        Wearables.startRegistration(activity)
        showStatus(copy(R.string.status_meta_registration))
    }

    /** MainActivity supplies lifecycle-bound phone sensors after it is created. */
    fun setPhoneInputSources(capture: PhoneCaptureSource, speech: PhoneSpeechSource) {
        if (phoneCapture != null && phoneCapture !== capture) onPhonePreviewHidden()
        if (phoneCapture !== capture) phoneCapture?.close()
        if (phoneSpeech !== speech) phoneSpeech?.close()
        phoneCapture = capture
        phoneSpeech = speech
    }

    /**
     * The Debug optical shell owns the Android view, while the phone source
     * owns CameraX. Keeping that boundary here avoids retaining a View or an
     * Activity in the ViewModel and lets the same source work without the
     * Debug simulator in release builds.
     */
    fun setPhonePreviewSurface(
        surfaceProvider: Preview.SurfaceProvider?,
        viewPort: ViewPort? = null,
        generation: Long = state.value.phonePreview.generation
    ) {
        val source = phoneCapture ?: return
        phonePreviewSurfaceJob?.cancel()
        phonePreviewSurfaceJob = viewModelScope.launch {
            if (generation != state.value.phonePreview.generation) return@launch
            try {
                source.setPreviewSurface(surfaceProvider, viewPort)
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                if (
                    surfaceProvider != null &&
                    inputRoute == InputRoute.PHONE &&
                    mutableUiState.value.wearable.cameraActive
                ) {
                    onPhonePreviewFailure(generation, error.message ?: copy(R.string.status_camera_not_ready))
                }
            }
        }
    }

    fun onPhonePreviewStreaming(generation: Long, streaming: Boolean) {
        if (inputRoute != InputRoute.PHONE || !state.value.wearable.cameraActive) return
        mutableUiState.update { it.copy(phonePreview = it.phonePreview.streaming(generation, streaming)) }
    }

    fun onPhonePreviewFailure(generation: Long, message: String) {
        if (inputRoute != InputRoute.PHONE || !state.value.wearable.cameraActive || generation != state.value.phonePreview.generation) return
        mutableUiState.update { it.copy(phonePreview = it.phonePreview.fail(generation, message), message = message) }
    }

    /** Navigation closes local sensors; staged media and its upload are retained. */
    fun onPhonePreviewHidden() {
        if (inputRoute != InputRoute.PHONE) return
        if (state.value.meta.pendingMime != null) {
            stopCamera()
            stopSpeech()
        } else if (state.value.wearable.cameraActive || state.value.wearable.speechActive || pendingAction != null) {
            cancelPendingActionAndRenderHome()
        }
    }

    /**
     * Native controls in the Debug optical shell use the same explicit
     * capture path as the Display buttons. They are deliberately restricted
     * to the phone route so a physical Display keeps its own controls.
     */
    fun capturePhotoFromPreview() {
        if (inputRoute == InputRoute.PHONE && mutableUiState.value.wearable.cameraActive) takePhoto()
    }

    /**
     * Captures a still photo from the wearable camera for publishing. Returns
     * null when the phone camera intent should be used instead. Callers must
     * invoke this off the main thread.
     */
    suspend fun captureStillForPublish(): ByteArray? {
        if (!PublishCapturePolicy.useWearable(inputRoute, camera != null)) return null
        val activeCamera = camera ?: return null
        var photo: PhotoData? = null
        var failure: String? = null
        activeCamera.stream.capturePhoto().fold(
            onSuccess = { photo = it },
            onFailure = { error, _ -> failure = error.description }
        )
        return photo?.asJpegBytes() ?: throw IllegalStateException(failure ?: localizedText(R.string.ui_could_not_capture_the_photo))
    }

    /** Starts a phone video or finalizes the active one; no capture is implicit. */
    fun togglePreviewVideo() {
        if (inputRoute != InputRoute.PHONE || !mutableUiState.value.wearable.cameraActive || state.value.meta.captureForSearch) return
        if (mutableUiState.value.recording) stopVideo() else startVideo()
    }

    fun cancelPhoneCapture() {
        if (inputRoute != InputRoute.PHONE) return
        if (state.value.meta.pendingMime != null) {
            metaController.discard()
            return
        }
        cancelPendingActionAndRenderHome()
    }

    fun retryPhonePreview() {
        if (inputRoute != InputRoute.PHONE || !mutableUiState.value.wearable.cameraActive) return
        viewModelScope.launch {
            mutableUiState.update { it.copy(phonePreview = it.phonePreview.copy(phase = PhonePreviewPhase.OPENING, error = null)) }
            runCatching { phoneCapture?.startPreview() }
                .onFailure { onPhonePreviewFailure(state.value.phonePreview.generation, it.message ?: copy(R.string.status_camera_not_ready)) }
        }
    }

    fun onWearablesInitializationFailure(message: String) {
        mutableUiState.update { current ->
            current.copy(wearable = current.wearable.copy(transportReady = false), message = message)
        }
    }

    fun showWearablesNotReady() {
        showStatus(copy(R.string.status_wearables_not_ready))
    }

    fun onWearablesInitialized() {
        if (!wearablesObservationStarted) {
            wearablesObservationStarted = true
            viewModelScope.launch {
                Wearables.registrationState.collectLatest { registration ->
                    mutableUiState.update { current ->
                        current.copy(wearable = current.wearable.copy(registration = registration.name))
                    }
                }
            }
            viewModelScope.launch {
                Wearables.devices.collectLatest { devices ->
                    mutableUiState.update { current ->
                        current.copy(wearable = current.wearable.copy(deviceAvailable = devices.isNotEmpty()))
                    }
                }
            }
        }
        mutableUiState.update { current -> current.copy(wearable = current.wearable.copy(transportReady = true)) }
    }

    internal fun eligibleDisplayDevices(): List<DeviceIdentifier> = if (!state.value.wearable.transportReady) {
        emptyList()
    } else {
        runCatching {
            Wearables.devicesMetadata.entries.filter { (identifier, metadata) ->
                metadata.value.isDisplayCapable() && SpecificDeviceSelector(identifier).activeDevice() == identifier
            }.map { it.key }
        }.getOrDefault(emptyList())
    }

    /** Mock Display metadata must never count as connected physical glasses. */
    fun hasAvailableWearableDisplay(): Boolean = eligibleDisplayDevices().any {
        !(app as RealityOsApplication).developerPreviewController.isSimulatedDevice(it)
    }

    /**
     * Uses automatic selection for physical glasses. Developer Preview passes
     * the identifier of Meta's display-capable mock so all other app behavior
     * remains identical.
     */
    fun connectDisplay(deviceIdentifier: DeviceIdentifier? = null) = connectDisplayOperation(deviceIdentifier)

    /**
     * A session with an active capture is intentionally not torn down: callers
     * must stop and finish capture so no evidence upload is silently lost.
     */
    fun disconnectDisplay(): Boolean = disconnectDisplayOperation()

    fun onDatPermissionResult(
        requestId: Long,
        permission: Permission,
        granted: Boolean,
        failureMessage: String? = null
    ) = onDatPermissionResultOperation(requestId, permission, granted, failureMessage)

    fun onPhonePermissionResult(requestId: Long, permission: PhonePermission, granted: Boolean) = onPhonePermissionResultOperation(requestId, permission, granted)

    internal fun requestDatPermission(permission: Permission) {
        mutablePermissionRequest.value = RealityPermissionRequest.Dat(permissionIds.incrementAndGet(), permission)
    }

    internal fun requestPhonePermission(permission: PhonePermission) {
        mutablePermissionRequest.value = RealityPermissionRequest.Android(permissionIds.incrementAndGet(), permission)
    }

    internal fun continueAfterPermission() {
        when (val action = pendingAction) {
            PendingAction.PrepareCapture -> {
                if (inputRoute == InputRoute.WEARABLE) {
                    pendingAction = PendingAction.PrepareWearableCaptureAudio
                    requestDatPermission(Permission.MICROPHONE)
                } else {
                    pendingAction = null
                    openCaptureSessionAndCamera()
                }
            }
            PendingAction.PrepareWearableCaptureAudio -> {
                // DAT grants access to the glasses microphone; Android still
                // requires RECORD_AUDIO before this phone can receive and mux
                // its PCM stream into a sound-bearing evidence clip.
                pendingAction = PendingAction.PrepareWearablePhoneAudio
                requestPhonePermission(PhonePermission.MICROPHONE)
                renderNotice(copy(R.string.status_phone_microphone_permission))
            }
            PendingAction.PrepareWearablePhoneAudio -> {
                pendingAction = null
                openCaptureSessionAndCamera()
            }
            PendingAction.StartPhoneVideo -> {
                pendingAction = null
                beginPhoneVideo()
            }
            PendingAction.StartQuery -> {
                pendingAction = null
                startSpeechQuery()
            }
            null -> Unit
        }
    }

    internal fun attachDisplay(activeSession: DeviceSession) {
        activeSession.addDisplay().fold(
            onSuccess = { attached ->
                display = attached
                displayStateJob = viewModelScope.launch {
                    attached.state.collect { displayState ->
                        val ready = displayState == DisplayState.STARTED
                        mutableUiState.update { current ->
                            current.copy(wearable = current.wearable.copy(displayReady = ready))
                        }
                        if (ready) renderHome()
                    }
                }
            },
            onFailure = { error, _ -> showError(error.description) }
        )
    }

    internal fun beginRegister() = beginRegisterOperation()

    internal fun chooseZone(zone: RemoteZone) = chooseZoneOperation(zone)

    internal fun openCaptureSessionAndCamera() = openCaptureSessionAndCameraOperation()

    internal suspend fun attachWearableCamera() = attachWearableCameraOperation()

    /** Reattach only the wearable camera; preserve the active server capture session. */
    internal fun retryCurrentWearableCamera() = retryCurrentWearableCameraOperation()

    internal fun takePhoto() = takePhotoOperation()

    internal fun startVideo() = startVideoOperation()

    internal fun beginPhoneVideo() = beginPhoneVideoOperation()

    internal fun beginRecordingUi() = beginRecordingUiOperation()

    internal fun stopVideo() = stopVideoOperation()

    internal fun finishRegister() = finishRegisterOperation()

    /**
     * Phone Debug capture exits immediately after the explicit media action
     * succeeds. This intentionally skips the Display's finishing card: the
     * native shell has already removed its controls and goes straight home.
     */
    internal fun finishPhoneCaptureAfterStored() = finishPhoneCaptureAfterStoredOperation()

    internal fun stopCamera() = stopCameraOperation()

    internal fun beginQuery() = beginQueryOperation()

    internal fun startSpeechQuery() = startSpeechQueryOperation()

    internal fun startPhoneSpeechQuery() = startPhoneSpeechQueryOperation()

    internal fun startWearableSpeechQuery() = startWearableSpeechQueryOperation()

    internal fun stopSpeech() = stopSpeechOperation()

    internal fun releaseWearableSpeech() = releaseWearableSpeechOperation()

    internal fun executeQuery(question: String) = executeQueryOperation(question)

    internal suspend fun uploadPendingCapture(pending: PendingUpload): RemoteJob = withContext(Dispatchers.IO) {
        withRealityApi { api ->
            val captureId = pending.remoteCaptureId ?: api
                .uploadCaptureFile(pending.captureSessionId, pending.file, pending.mimeType)
                .id
                .also { pending.remoteCaptureId = it }
            api.requestProcessing(captureId, detailed = false)
        }
    }

    internal fun completePendingUpload(pending: PendingUpload) = completePendingUploadOperation(pending)

    internal fun retryPendingUpload() = retryPendingUploadOperation()

    internal fun persistCaptureBytes(bytes: ByteArray, extension: String): File = persistCaptureBytesOperation(bytes, extension)

    /** Polls only the device-owned job created by this capture. */
    internal fun watchProcessing(initial: RemoteJob) = watchProcessingOperation(initial)

    internal fun updateProcessingCount() = updateProcessingCountOperation()

    internal val RemoteJob.isPending: Boolean
        get() = status.equals("queued", ignoreCase = true) || status.equals("processing", ignoreCase = true)

    internal val RemoteJob.isFailed: Boolean
        get() = status.equals("failed", ignoreCase = true) || status.equals("uncertain", ignoreCase = true)

    /** Retries only an explicit 401 after replacing an expiring virtual profile. */
    internal suspend fun <T> withRealityApi(operation: (RealityApi) -> T): T {
        val provisioning = mutableUiState.value.provisioning
            ?: throw IllegalStateException(copy(R.string.status_device_provisioning_missing))
        try {
            return operation(RealityApi(provisioning))
        } catch (error: RealityApiException) {
            if (error.statusCode != 401 || provisioning.source != ProvisioningSource.VIRTUAL_LIVE) throw error
            val refreshed = refreshVirtualProvisioning()
            return operation(RealityApi(refreshed))
        }
    }

    internal fun refreshVirtualProvisioning(): DeviceProvisioning {
        val profile = VirtualDeviceBootstrapApi.fetch(
            BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
            store.installationId()
        )
        if (!profile.processingMode.equals("live", ignoreCase = true)) {
            throw IllegalStateException(copy(R.string.status_live_not_confirmed))
        }
        val refreshed = profile.toProvisioning()
        store.save(refreshed)
        mutableUiState.update {
            it.copy(
                provisioning = refreshed,
                virtualProfileError = null
            )
        }
        return refreshed
    }

    internal fun renderHome(): Unit = renderMetaHome()

    internal fun renderZonePicker(zones: List<RemoteZone>) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
            text(copy(R.string.display_choose_location), style = TextStyle.HEADING)
            text(copy(R.string.display_capture_after_location), style = TextStyle.META, color = TextColor.SECONDARY)
            zones.take(MAX_DISPLAY_ZONES).forEach { zone ->
                button(zone.name, style = ButtonStyle.SECONDARY, iconName = IconName.CONTAINER_WITH_LID, onClick = { chooseZone(zone) })
            }
            button(copy(R.string.display_back), style = ButtonStyle.OUTLINE, iconName = IconName.ARROW_LEFT, onClick = ::renderHome)
        }
    }

    internal fun renderCapture() = sendDisplay {
        if (inputRoute == InputRoute.PHONE) {
            // The Debug shell owns the compact icon controls. Leave the Meta
            // renderer fully transparent so it cannot paint text or a dark
            // card over the centered CameraX preview.
            flexBox(direction = Direction.COLUMN, gap = 0, padding = 0, background = FlexBoxBackground.NONE) {}
        } else {
            flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.NONE) {
                val searching = state.value.meta.captureForSearch
                text(
                    copy(
                        if (searching) {
                            MetaDisplayPolicy.photoSearchCaptureTitle(state.value.meta.photoSearchKind)
                        } else if (state.value.meta.captureForPublication) {
                            R.string.meta_capture
                        } else {
                            R.string.display_register_evidence
                        }
                    ),
                    style = TextStyle.HEADING
                )
                if (!searching) text(state.value.meta.pendingDestination ?: selectedZone?.name ?: copy(R.string.display_selected_location), style = TextStyle.META, color = TextColor.SECONDARY)
                if (!state.value.recording) button(copy(R.string.display_take_photo), style = ButtonStyle.PRIMARY, iconName = IconName.VIDEO_CAMERA, onClick = ::takePhoto)
                if (mutableUiState.value.recording) {
                    button(copy(R.string.display_stop_video), style = ButtonStyle.PRIMARY, iconName = IconName.X, onClick = ::stopVideo)
                    text(copy(R.string.meta_recording_duration, state.value.meta.recordingSeconds), style = TextStyle.META, color = TextColor.SECONDARY)
                } else if (!searching) {
                    button(copy(R.string.display_record_video), style = ButtonStyle.SECONDARY, iconName = IconName.VIDEO_CAMERA, onClick = ::startVideo)
                }
                if (!state.value.recording) button(copy(if (searching) R.string.display_cancel else R.string.display_finish_capture), style = ButtonStyle.OUTLINE, iconName = IconName.CHECKMARK, onClick = if (searching) ::cancelPendingActionAndRenderHome else ::finishRegister)
            }
        }
    }

    internal fun renderListening(partial: String) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.CARD) {
            text(copy(R.string.display_ask), style = TextStyle.HEADING)
            text(partial.take(MAX_DISPLAY_TEXT), style = TextStyle.BODY)
            text(copy(R.string.display_listening), style = TextStyle.META, color = TextColor.SECONDARY)
            button(copy(R.string.display_cancel), style = ButtonStyle.OUTLINE, iconName = IconName.X, onClick = {
                stopSpeech()
                renderHome()
            })
        }
    }

    internal fun renderQueryResult(answer: QueryEvidence, imageUrl: String?, language: String) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 10, padding = 20, background = FlexBoxBackground.CARD) {
            text(
                if (answer.found) {
                    copy(R.string.display_last_seen)
                } else if (answer.ambiguous) {
                    copy(R.string.display_more_detail)
                } else {
                    copy(R.string.display_no_evidence)
                },
                style = TextStyle.HEADING
            )
            imageUrl?.let { image(uri = it, sizePreset = ImageSize.FILL) }
            text(answer.message.take(180), style = TextStyle.BODY)
            if (answer.found) {
                text(copy(R.string.meta_evidence_details, answer.seenAt?.take(10).orEmpty(), evidencePercent(answer.visualConfidence, language).orEmpty()), style = TextStyle.META)
            }
            if (answer.simulated) text(copy(R.string.meta_simulated), style = TextStyle.META)
            button(copy(R.string.display_hear_again), style = ButtonStyle.SECONDARY, iconName = IconName.SPEAKER_WITH_TWO_ARCS, onClick = { speak(answer.ttsText, language) })
            button(copy(R.string.display_new_query), style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
            button(copy(R.string.display_home), style = ButtonStyle.OUTLINE, iconName = IconName.HOUSE, onClick = ::renderHome)
        }
    }

    internal fun renderNotice(
        message: String,
        actionLabel: String? = null,
        action: (() -> Unit)? = null,
        showHome: Boolean = true
    ) = sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 12, padding = 24, background = FlexBoxBackground.CARD) {
            text("RealityOS", style = TextStyle.HEADING)
            text(message.take(MAX_DISPLAY_TEXT), style = TextStyle.BODY)
            if (actionLabel != null && action != null) {
                button(actionLabel, style = ButtonStyle.SECONDARY, iconName = IconName.TWO_ARROWS_CLOCKWISE, onClick = action)
            }
            if (showHome) {
                button(
                    copy(R.string.display_home),
                    style = ButtonStyle.PRIMARY,
                    iconName = IconName.HOUSE,
                    onClick = ::cancelPendingActionAndRenderHome
                )
            }
        }
    }

    internal fun cancelPendingActionAndRenderHome() {
        if (state.value.meta.pendingMime != null) {
            renderPublicationReview()
            return
        }
        metaController.pause()
        setBusy(false)
        stopSpeech()
        pendingAction = null
        mutablePermissionRequest.value = null
        pendingUpload?.file?.delete()
        pendingUpload = null
        val captureSessionId = mutableUiState.value.captureSessionId
        stopCamera()
        selectedZone = null
        if (captureSessionId != null) {
            mutableUiState.update { it.copy(captureSessionId = null, recording = false) }
            closeCaptureSessionOnServer(captureSessionId)
        }
        renderHome()
    }

    internal fun sendDisplay(content: com.meta.wearable.dat.display.views.ContentScope.() -> Unit) {
        val currentDisplay = display ?: return
        val revision = ++renderRevision
        viewModelScope.launch {
            renderMutex.withLock {
                if (currentDisplay !== display || revision != renderRevision) return@withLock
                currentDisplay.sendContent(content).onFailure { error, _ ->
                    // A transport error cannot be rendered through the failed
                    // display; retain it on the phone host instead of replacing
                    // a newer screen with an obsolete callback map.
                    if (revision == renderRevision) showStatus(error.description)
                }
            }
        }
    }

    internal fun closeCaptureSessionOnServer(sessionId: String) {
        viewModelScope.launch(Dispatchers.IO) { runCatching { withRealityApi { it.closeCaptureSession(sessionId) } } }
    }

    internal fun showStatus(message: String) {
        mutableUiState.update { it.copy(message = message) }
    }

    internal fun copy(@StringRes id: Int, vararg arguments: Any): String = localizedText(id, *arguments)

    internal fun showError(message: String, retry: (() -> Unit)? = null) {
        mutableUiState.update { it.copy(message = message, busy = false) }
        renderNotice(message, retry?.let { copy(R.string.display_retry) }, retry)
    }

    internal fun setBusy(value: Boolean) {
        mutableUiState.update { it.copy(busy = value) }
    }

    internal fun cleanupStoppedSession(stoppedSession: DeviceSession? = null) {
        // A delayed state event from an old session must not reset a newly
        // connected physical or virtual device.
        if (stoppedSession != null && session != null && session !== stoppedSession) return
        mutableUiState.value.captureSessionId?.let(::closeCaptureSessionOnServer)
        metaController.pause()
        setBusy(false)
        renderRevision += 1
        pendingAction = null
        mutablePermissionRequest.value = null
        recordingLimitJob?.cancel()
        recorder.close(deleteIncomplete = true)
        pendingUpload?.file?.delete()
        pendingUpload = null
        sessionStateJob?.cancel()
        sessionStateJob = null
        sessionErrorsJob?.cancel()
        sessionErrorsJob = null
        displayStateJob?.cancel()
        displayStateJob = null
        session = null
        inputRoute = InputRoute.PHONE
        display = null
        camera = null
        speech = null
        frameJob?.cancel()
        frameJob = null
        audioFrameJob?.cancel()
        audioFrameJob = null
        streamStateJob?.cancel()
        streamStateJob = null
        cameraErrorJob?.cancel()
        cameraErrorJob = null
        speechJob?.cancel()
        speechJob = null
        speechErrorJob?.cancel()
        speechErrorJob = null
        phoneSpeechJob?.cancel()
        phoneSpeechJob = null
        phonePreviewSurfaceJob?.cancel()
        phonePreviewSurfaceJob = null
        phoneSpeech?.cancel()
        phoneCapture?.cancelVideo()
        viewModelScope.launch { runCatching { phoneCapture?.stopPreview() } }
        mutableUiState.update { current ->
            current.copy(
                captureSessionId = null,
                recording = false,
                phonePreview = current.phonePreview.close(),
                wearable = current.wearable.copy(
                    sessionActive = false,
                    displayReady = false,
                    cameraActive = false,
                    speechActive = false,
                    inputRoute = InputRoute.PHONE
                )
            )
        }
    }

    override fun onCleared() {
        metaController.pause()
        recorder.close(deleteIncomplete = true)
        pendingUpload?.file?.delete()
        pendingUpload = null
        recordingLimitJob?.cancel()
        stopSpeech()
        stopCamera()
        runCatching { session?.removeDisplay() }
        runCatching { session?.stop() }
        sessionStateJob?.cancel()
        sessionErrorsJob?.cancel()
        displayStateJob?.cancel()
        phoneCapture?.close()
        phoneSpeech?.close()
        super.onCleared()
    }

    internal fun PhotoData.asJpegBytes(): ByteArray? = when (this) {
        is PhotoData.Bitmap -> bitmap.toJpeg()
        is PhotoData.HEIC -> {
            val copy = data.duplicate().let { buffer -> ByteArray(buffer.remaining()).also(buffer::get) }
            uprightImageBytes(copy, maxSide = Int.MAX_VALUE, quality = JPEG_QUALITY)
                ?: BitmapFactory.decodeByteArray(copy, 0, copy.size)?.toJpeg()
        }
    }

    internal fun Bitmap.toJpeg(): ByteArray = ByteArrayOutputStream().use { output ->
        compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, output)
        output.toByteArray()
    }

    internal companion object {
        const val MAX_VIDEO_SECONDS = 120L
        const val CAMERA_START_TIMEOUT_MS = 10_000L
        const val SPEECH_START_TIMEOUT_MS = 8_000L
        const val PROCESSING_POLL_INTERVAL_MS = 1_500L
        const val PROCESSING_STATUS_NOTICE_EVERY = 40
        const val MAX_DISPLAY_ZONES = 8
        const val MAX_DISPLAY_TEXT = 360
        const val JPEG_QUALITY = 92
    }
}
