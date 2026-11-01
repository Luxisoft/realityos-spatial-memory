package com.luxisoft.realityos.host.operations

import androidx.lifecycle.viewModelScope
import com.luxisoft.realityos.*
import com.luxisoft.realityos.RealityViewModel.Companion.CAMERA_START_TIMEOUT_MS
import com.luxisoft.realityos.RealityViewModel.Companion.MAX_VIDEO_SECONDS
import com.luxisoft.realityos.RealityViewModel.PendingAction
import com.luxisoft.realityos.RealityViewModel.PendingUpload
import com.meta.wearable.dat.camera.Camera
import com.meta.wearable.dat.camera.addCamera
import com.meta.wearable.dat.camera.removeCamera
import com.meta.wearable.dat.camera.types.AudioCodec
import com.meta.wearable.dat.camera.types.AudioSampleRate
import com.meta.wearable.dat.camera.types.PhotoData
import com.meta.wearable.dat.camera.types.StreamConfiguration
import com.meta.wearable.dat.camera.types.VideoQuality
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.display.Display
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull

internal fun RealityViewModel.beginRegisterOperation() {
    if (mutableUiState.value.provisioning == null) return showError(copy(R.string.status_device_provisioning_missing))
    if (mutableUiState.value.busy || mutableUiState.value.wearable.cameraActive || mutableUiState.value.meta.pendingMime != null) return
    setBusy(true)
    viewModelScope.launch {
        try {
            val zones = withContext(Dispatchers.IO) { withRealityApi { it.listZones() } }
            if (zones.isEmpty()) showError(copy(R.string.status_no_locations)) else renderZonePicker(zones)
        } catch (error: Exception) {
            showError(error.message ?: copy(R.string.status_locations_failed), retry = ::beginRegister)
        } finally {
            setBusy(false)
        }
    }
}

internal fun RealityViewModel.chooseZoneOperation(zone: RemoteZone) {
    if (mutableUiState.value.busy) return
    selectedZone = zone
    pendingAction = PendingAction.PrepareCapture
    if (inputRoute == InputRoute.WEARABLE) {
        requestDatPermission(Permission.CAMERA)
        renderNotice(copy(R.string.status_camera_permission, zone.name))
    } else {
        requestPhonePermission(PhonePermission.CAMERA)
        renderNotice(copy(R.string.status_phone_camera_permission, zone.name))
    }
}

internal fun RealityViewModel.openCaptureSessionAndCameraOperation() {
    val captureRevision = metaController.generation.revision
    captureOperationJob = viewModelScope.launch {
        setBusy(true)
        var openedCaptureSessionId: String? = null
        try {
            if (!state.value.meta.captureForPublication && !state.value.meta.captureForSearch) {
                val captureSession = withContext(Dispatchers.IO) {
                    withRealityApi { it.openCaptureSession(selectedZone?.id) }
                }
                openedCaptureSessionId = captureSession.id
                mutableUiState.update { it.copy(captureSessionId = captureSession.id) }
            }
            when (inputRoute) {
                InputRoute.PHONE -> {
                    mutableUiState.update { current ->
                        current.copy(phonePreview = current.phonePreview.open(), wearable = current.wearable.copy(cameraActive = true))
                    }
                    val previewController = (app as RealityOsApplication).developerPreviewController
                    phoneCapture?.selectCamera(previewController.state.value.phoneCamera ?: PreviewPhoneCamera.BACK)
                    checkNotNull(phoneCapture) { copy(R.string.status_phone_source_unavailable) }
                        .startPreview()
                    renderCapture()
                }
                InputRoute.WEARABLE -> attachWearableCamera()
            }
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            openedCaptureSessionId?.let(::closeCaptureSessionOnServer)
            mutableUiState.update { it.copy(captureSessionId = null) }
            if (inputRoute == InputRoute.PHONE) {
                runCatching { phoneCapture?.stopPreview() }
                onPhonePreviewFailure(state.value.phonePreview.generation, error.message ?: copy(R.string.status_camera_not_ready))
                return@launch
            }
            showError(
                error.message ?: copy(R.string.status_capture_session_failed),
                retry = ::openCaptureSessionAndCamera
            )
        } finally {
            if (metaController.generation.accepts(captureRevision)) setBusy(false)
        }
    }
}

internal suspend fun RealityViewModel.attachWearableCameraOperation() {
    val activeSession = session ?: throw IllegalStateException(copy(R.string.status_display_not_connected))
    var attached: Camera? = null
    var failure: String? = null
    activeSession.addCamera(
        StreamConfiguration(
            audioCodec = AudioCodec.PCM(AudioSampleRate.RATE_44100, 1),
            videoQuality = VideoQuality.MEDIUM,
            frameRate = 15,
            compressVideo = true
        )
    ).fold(
        onSuccess = { attached = it },
        onFailure = { error, _ -> failure = error.description }
    )
    val activeCamera = attached ?: throw IllegalStateException(failure ?: copy(R.string.status_camera_not_ready))
    // DAT's camera streams are non-replaying. Subscribe before starting
    // the stream, otherwise a VPS/SPS/PPS configuration frame can be
    // missed and a later HEVC recording has no decodable video track.
    val videoCollector = viewModelScope.launch(Dispatchers.Default, start = CoroutineStart.UNDISPATCHED) {
        activeCamera.stream.videoStream.collect { frame ->
            recorder.observe(frame)
            if (mutableUiState.value.recording) recorder.append(frame)
        }
    }
    val audioCollector = viewModelScope.launch(Dispatchers.Default, start = CoroutineStart.UNDISPATCHED) {
        activeCamera.stream.audioStream.collect { frame ->
            if (mutableUiState.value.recording) recorder.appendAudio(frame)
        }
    }
    try {
        var startFailure: String? = null
        activeCamera.stream.start().fold(
            onSuccess = {},
            onFailure = { error, _ -> startFailure = error.description }
        )
        if (startFailure != null) throw IllegalStateException(startFailure)
        val started = withTimeoutOrNull(CAMERA_START_TIMEOUT_MS) {
            activeCamera.stream.state.first { state ->
                state.name == "STARTED" || state.name == "STREAMING"
            }
        }
        if (started == null) throw IllegalStateException(copy(R.string.status_camera_start_timeout))
    } catch (error: Exception) {
        videoCollector.cancel()
        audioCollector.cancel()
        runCatching { activeCamera.stop() }
        runCatching { activeSession.removeCamera() }
        recorder.clearCodecConfiguration()
        throw error
    }
    camera = activeCamera
    frameJob = videoCollector
    audioFrameJob = audioCollector
    streamStateJob?.cancel()
    streamStateJob = viewModelScope.launch {
        activeCamera.stream.state.collect { streamState ->
            if (
                camera === activeCamera &&
                (streamState.name == "STOPPED" || streamState.name == "CLOSED")
            ) {
                stopCamera()
                showError(copy(R.string.status_camera_stream_stopped), retry = ::retryCurrentWearableCamera)
            }
        }
    }
    cameraErrorJob?.cancel()
    cameraErrorJob = viewModelScope.launch {
        activeCamera.stream.errorStream.collect { error ->
            if (camera === activeCamera) {
                // STREAM_ERROR can be informational (for example a user
                // pause). Stream state decides whether the capability is
                // terminal; keep this message visible without tearing
                // down a healthy stream.
                showStatus(error.description)
            }
        }
    }
    mutableUiState.update { current ->
        current.copy(wearable = current.wearable.copy(cameraActive = true))
    }
    renderCapture()
}

internal fun RealityViewModel.retryCurrentWearableCameraOperation() {
    if (inputRoute != InputRoute.WEARABLE || mutableUiState.value.captureSessionId == null) {
        openCaptureSessionAndCamera()
        return
    }
    if (mutableUiState.value.busy) return
    setBusy(true)
    viewModelScope.launch {
        try {
            attachWearableCamera()
        } catch (error: Exception) {
            showError(
                error.message ?: copy(R.string.status_camera_not_ready),
                retry = ::retryCurrentWearableCamera
            )
        } finally {
            setBusy(false)
        }
    }
}

internal fun RealityViewModel.takePhotoOperation() {
    val captureSessionId = mutableUiState.value.captureSessionId
    if (captureSessionId == null && !state.value.meta.captureForPublication && !state.value.meta.captureForSearch) return showError(copy(R.string.status_capture_mode_first))
    if (mutableUiState.value.busy || mutableUiState.value.recording) return
    if (inputRoute == InputRoute.PHONE && !state.value.phonePreview.ready) return
    setBusy(true)
    val captureRevision = metaController.generation.revision
    captureOperationJob = viewModelScope.launch {
        var stored = false
        var publish = false
        var searchPhoto: ByteArray? = null
        var searchKind = MetaPhotoSearchKind.OBJECT
        try {
            val job = when (inputRoute) {
                InputRoute.PHONE -> {
                    checkNotNull(phoneCapture) { copy(R.string.status_phone_source_unavailable) }.takePhoto()
                }
                InputRoute.WEARABLE -> {
                    val activeCamera = camera ?: throw IllegalStateException(copy(R.string.status_camera_not_ready))
                    var photo: PhotoData? = null
                    var failure: String? = null
                    activeCamera.stream.capturePhoto().fold(
                        onSuccess = { photo = it },
                        onFailure = { error, _ -> failure = error.description }
                    )
                    val jpeg = photo?.asJpegBytes()
                        ?: throw IllegalStateException(failure ?: copy(R.string.status_unreadable_photo))
                    PhoneMedia(persistCaptureBytes(jpeg, "jpg"), "image/jpeg")
                }
            }
            if (state.value.meta.captureForSearch) {
                searchKind = state.value.meta.photoSearchKind
                try {
                    searchPhoto = withContext(Dispatchers.IO) { job.file.readBytes() }
                } finally {
                    job.file.delete()
                }
                stopCamera()
                mutableUiState.update { it.copy(meta = it.meta.copy(captureForSearch = false)) }
                return@launch
            }
            if (state.value.meta.captureForPublication) {
                metaController.stage(job, captureRevision)
                publish = true
                return@launch
            }
            val pending = PendingUpload(
                captureSessionId = checkNotNull(captureSessionId),
                file = job.file,
                mimeType = job.mimeType,
                successMessage = R.string.status_photo_stored
            )
            pendingUpload = pending
            val processingJob = uploadPendingCapture(pending)
            completePendingUpload(pending)
            watchProcessing(processingJob)
            showStatus(copy(R.string.status_photo_stored))
            stored = true
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            showError(
                error.message ?: copy(R.string.status_photo_capture_failed),
                retry = if (pendingUpload != null) ::retryPendingUpload else ::takePhoto
            )
        } finally {
            if (metaController.generation.accepts(captureRevision)) {
                setBusy(false)
                if (publish) metaController.submit()
                searchPhoto?.let {
                    if (searchKind == MetaPhotoSearchKind.PERSON) executeFaceQuery(it) else executeGalleryQuery("", it)
                }
            }
            if (stored && inputRoute == InputRoute.PHONE) {
                // Phone Debug capture is intentionally one evidence item
                // per explicit camera entry. Finish only after the media
                // and durable processing job both exist on the server.
                finishPhoneCaptureAfterStored()
            } else if (stored) {
                renderCapture()
            }
        }
    }
}

internal fun RealityViewModel.startVideoOperation() {
    if (state.value.meta.captureForSearch) return
    if (inputRoute == InputRoute.PHONE && !state.value.phonePreview.ready) return
    if (mutableUiState.value.recording || mutableUiState.value.busy || mutablePermissionRequest.value != null) return
    if (inputRoute == InputRoute.PHONE) {
        pendingAction = PendingAction.StartPhoneVideo
        requestPhonePermission(PhonePermission.MICROPHONE)
        // The native phone capture shell remains visually clean while
        // Android presents its own permission dialog.
        showStatus(copy(R.string.status_phone_microphone_permission))
        return
    }
    if (camera == null) return showError(copy(R.string.status_camera_not_ready))
    setBusy(true)
    val captureRevision = metaController.generation.revision
    captureOperationJob = viewModelScope.launch {
        try {
            withContext(Dispatchers.Default) { recorder.begin() }
            beginRecordingUi()
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            recorder.close(deleteIncomplete = true)
            showError(error.message ?: copy(R.string.status_video_start_failed), retry = ::startVideo)
        } finally {
            if (metaController.generation.accepts(captureRevision)) setBusy(false)
        }
    }
}

internal fun RealityViewModel.beginPhoneVideoOperation() {
    if (mutableUiState.value.recording || mutableUiState.value.busy) return
    setBusy(true)
    val captureRevision = metaController.generation.revision
    captureOperationJob = viewModelScope.launch {
        try {
            checkNotNull(phoneCapture) { copy(R.string.status_phone_source_unavailable) }.startVideo()
            beginRecordingUi()
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            showError(error.message ?: copy(R.string.status_video_start_failed), retry = ::startVideo)
        } finally {
            if (metaController.generation.accepts(captureRevision)) setBusy(false)
        }
    }
}

internal fun RealityViewModel.beginRecordingUiOperation() {
    mutableUiState.update { it.copy(meta = it.meta.copy(recordingSeconds = 0), recording = true, message = copy(R.string.status_recording_video)) }
    recordingLimitJob?.cancel()
    recordingLimitJob = viewModelScope.launch {
        for (seconds in 1..MAX_VIDEO_SECONDS.toInt()) {
            delay(1000)
            if (!state.value.recording) break
            mutableUiState.update { it.copy(meta = it.meta.copy(recordingSeconds = seconds)) }
            if (inputRoute == InputRoute.WEARABLE) renderCapture()
        }
        if (mutableUiState.value.recording) stopVideo()
    }
    renderCapture()
}

internal fun RealityViewModel.stopVideoOperation() {
    if (!mutableUiState.value.recording) return
    mutableUiState.update { it.copy(recording = false) }
    recordingLimitJob?.cancel()
    val captureSessionId = mutableUiState.value.captureSessionId
    if (captureSessionId == null && !state.value.meta.captureForPublication) return
    setBusy(true)
    val captureRevision = metaController.generation.revision
    captureOperationJob = viewModelScope.launch {
        var stored = false
        var publish = false
        try {
            val clip = when (inputRoute) {
                InputRoute.PHONE -> checkNotNull(phoneCapture) { copy(R.string.status_phone_source_unavailable) }.stopVideo()
                InputRoute.WEARABLE -> {
                    val file = withContext(Dispatchers.Default) { recorder.finish() }
                        ?: throw IllegalStateException(copy(R.string.status_no_playable_video))
                    PhoneMedia(file, "video/mp4")
                }
            }
            if (state.value.meta.captureForPublication) {
                metaController.stage(clip, captureRevision)
                publish = true
                return@launch
            }
            val pending = PendingUpload(
                captureSessionId = checkNotNull(captureSessionId),
                file = clip.file,
                mimeType = clip.mimeType,
                successMessage = R.string.status_video_stored
            )
            pendingUpload = pending
            val processingJob = uploadPendingCapture(pending)
            completePendingUpload(pending)
            watchProcessing(processingJob)
            showStatus(copy(R.string.status_video_stored))
            stored = true
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            showError(
                error.message ?: copy(R.string.status_video_upload_failed),
                retry = if (pendingUpload != null) ::retryPendingUpload else ::startVideo
            )
        } finally {
            if (metaController.generation.accepts(captureRevision)) {
                setBusy(false)
                if (publish) metaController.submit()
            }
            if (stored && inputRoute == InputRoute.PHONE) {
                finishPhoneCaptureAfterStored()
            } else if (stored) {
                renderCapture()
            }
        }
    }
}

internal fun RealityViewModel.finishRegisterOperation() {
    if (mutableUiState.value.busy) return
    if (mutableUiState.value.recording) {
        stopVideo()
        renderNotice(copy(R.string.status_video_finishing))
        return
    }
    if (state.value.meta.captureForPublication) {
        metaController.discard()
        return
    }
    if (state.value.meta.pendingMime != null) {
        renderPublicationReview()
        return
    }
    if (pendingUpload != null) {
        renderNotice(
            copy(R.string.status_capture_upload_failed),
            actionLabel = copy(R.string.display_retry),
            action = ::retryPendingUpload
        )
        return
    }
    val captureSessionId = mutableUiState.value.captureSessionId
    if (captureSessionId == null) {
        stopCamera()
        renderHome()
        return
    }
    // Make the close operation exclusive before the local camera is
    // released. Otherwise the old Capture screen can accept a photo/video
    // tap while its server-side session is being closed.
    setBusy(true)
    // Phone Debug capture has no textual Display controls. Avoid putting
    // a card back over its cleared camera shell while its server session
    // closes; physical glasses retain the explicit finishing notice.
    if (inputRoute != InputRoute.PHONE) {
        renderNotice(copy(R.string.status_capture_finishing), showHome = false)
    }
    stopCamera()
    viewModelScope.launch {
        var closed = false
        try {
            withContext(Dispatchers.IO) { withRealityApi { it.closeCaptureSession(captureSessionId) } }
            mutableUiState.update { it.copy(captureSessionId = null, message = copy(R.string.status_capture_stopped)) }
            selectedZone = null
            closed = true
        } catch (error: Exception) {
            showError(error.message ?: copy(R.string.status_close_capture_failed), retry = ::finishRegister)
        } finally {
            setBusy(false)
        }
        if (closed) renderHome()
    }
}

internal fun RealityViewModel.finishPhoneCaptureAfterStoredOperation() {
    if (inputRoute != InputRoute.PHONE || mutableUiState.value.busy) return
    val captureSessionId = mutableUiState.value.captureSessionId
    if (captureSessionId == null) {
        stopCamera()
        renderHome()
        return
    }
    setBusy(true)
    stopCamera()
    viewModelScope.launch {
        var closed = false
        try {
            withContext(Dispatchers.IO) { withRealityApi { it.closeCaptureSession(captureSessionId) } }
            mutableUiState.update { it.copy(captureSessionId = null, message = copy(R.string.status_capture_stopped)) }
            selectedZone = null
            closed = true
        } catch (error: Exception) {
            // An error is the exception to the clean capture shell: keep
            // the existing explicit retry so the server session is never
            // silently abandoned after evidence was stored.
            showError(error.message ?: copy(R.string.status_close_capture_failed), retry = ::finishPhoneCaptureAfterStored)
        } finally {
            setBusy(false)
        }
        if (closed) renderHome()
    }
}

internal fun RealityViewModel.stopCameraOperation() {
    phonePreviewSurfaceJob?.cancel()
    phonePreviewSurfaceJob = null
    frameJob?.cancel()
    frameJob = null
    audioFrameJob?.cancel()
    audioFrameJob = null
    streamStateJob?.cancel()
    streamStateJob = null
    cameraErrorJob?.cancel()
    cameraErrorJob = null
    if (inputRoute == InputRoute.PHONE) phoneCapture?.close()
    if (inputRoute == InputRoute.WEARABLE) recorder.close(deleteIncomplete = true)
    runCatching { camera?.stop() }
    runCatching { session?.removeCamera() }
    camera = null
    recorder.clearCodecConfiguration()
    mutableUiState.update { current ->
        current.copy(recording = false, phonePreview = current.phonePreview.close(), wearable = current.wearable.copy(cameraActive = false))
    }
}
