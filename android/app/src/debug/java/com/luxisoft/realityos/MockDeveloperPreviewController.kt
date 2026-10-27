package com.luxisoft.realityos

import android.content.Context
import android.media.MediaExtractor
import android.net.Uri
import android.view.View
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.types.DeviceIdentifier
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.core.types.PermissionStatus
import com.meta.wearable.dat.core.types.RegistrationState
import com.meta.wearable.dat.mockdevice.MockDeviceKit
import com.meta.wearable.dat.mockdevice.api.GlassesModel
import com.meta.wearable.dat.mockdevice.api.MockDeviceKitConfig
import com.meta.wearable.dat.mockdevice.api.MockDeviceKitInterface
import com.meta.wearable.dat.mockdevice.api.MockGlasses
import com.meta.wearable.dat.mockdevice.api.camera.CameraFacing
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.withTimeoutOrNull

/**
 * Adapter over Meta's official Mock Device Kit. It intentionally owns only
 * simulated-device state; RealityViewModel remains the sole owner of the
 * RealityOS capture and query workflow.
 */
class MockDeveloperPreviewController(
    private val applicationContext: Context,
) : DeveloperPreviewController {
    private val mock: MockDeviceKitInterface = MockDeviceKit.getInstance(applicationContext)
    private val _state = MutableStateFlow(DeveloperPreviewState(available = true))
    override val state: StateFlow<DeveloperPreviewState> = _state.asStateFlow()

    private var glasses: MockGlasses? = null

    override suspend fun start(mode: DeveloperPreviewMode): DeviceIdentifier? {
        if (_state.value.active) stop()
        clearError()

        return try {
            mock.enable(
                MockDeviceKitConfig(
                    initiallyRegistered = true,
                    initialPermissionsGranted = true,
                ),
            )
            val registered = withTimeoutOrNull(REGISTRATION_TIMEOUT_MS) {
                Wearables.registrationState.first { it == RegistrationState.REGISTERED }
            }
            if (registered == null) {
                fail("Mock Device Kit did not complete simulated Meta registration.")
                releaseMockDevice()
                return null
            }
            mock.pairGlasses(GlassesModel.META_RAYBAN_DISPLAY).fold(
                onSuccess = { paired ->
                    glasses = paired
                    paired.powerOn()
                    paired.unfold()
                    paired.don()
                    paired.services.speech.setLocale(DEFAULT_LOCALE)
                    val chrome = if (mode == DeveloperPreviewMode.CHROME) startChromeServer() else null
                    if (mode == DeveloperPreviewMode.CHROME && chrome == null) {
                        releaseMockDevice()
                        null
                    } else {
                        _state.update {
                            it.copy(
                                active = true,
                                mode = mode,
                                deviceIdentifier = paired.deviceIdentifier,
                                poweredOn = true,
                                unfolded = true,
                                worn = true,
                                chrome = chrome,
                                message = "Virtual Meta Ray-Ban Display is ready. Connect RealityOS Display.",
                                error = null,
                                previewGeneration = it.previewGeneration + 1,
                            )
                        }
                        paired.deviceIdentifier
                    }
                },
                onFailure = { error, _ ->
                    fail(error.description)
                    releaseMockDevice()
                    null
                },
            )
        } catch (error: Exception) {
            fail(error.message ?: "Could not start the virtual glasses.")
            releaseMockDevice()
            null
        }
    }

    override suspend fun stop() {
        releaseMockDevice()
        _state.update {
            DeveloperPreviewState(
                available = true,
                message = "Developer preview is stopped.",
                previewGeneration = it.previewGeneration + 1,
            )
        }
    }

    override fun powerOn() = withGlasses("Power on the virtual glasses first.") { device ->
        device.powerOn()
        _state.update { it.copy(poweredOn = true, message = "Virtual glasses are powered on.") }
    }

    override fun powerOff() = withGlasses("Power on the virtual glasses first.") { device ->
        device.powerOff()
        _state.update { it.copy(poweredOn = false, worn = false, message = "Virtual glasses are powered off.") }
    }

    override fun unfold() = withGlasses("Start the virtual glasses first.") { device ->
        device.unfold()
        _state.update { it.copy(unfolded = true, message = "Virtual glasses are unfolded.") }
    }

    override fun fold() = withGlasses("Start the virtual glasses first.") { device ->
        device.fold()
        _state.update { it.copy(unfolded = false, worn = false, message = "Virtual glasses are folded.") }
    }

    override fun don() = withGlasses("Start the virtual glasses first.") { device ->
        device.don()
        _state.update { it.copy(worn = true, message = "Virtual glasses are being worn.") }
    }

    override fun doff() = withGlasses("Start the virtual glasses first.") { device ->
        device.doff()
        _state.update { it.copy(worn = false, message = "Virtual glasses were removed.") }
    }

    override fun setDatPermission(permission: Permission, granted: Boolean) {
        if (!mock.isEnabled) return fail("Start the virtual glasses before changing DAT permissions.")
        val status = if (granted) PermissionStatus.Granted else PermissionStatus.Denied
        mock.permissions.set(permission, status)
        mock.permissions.setRequestResult(permission, status)
        _state.update {
            it.copy(
                message = "${permission.name.lowercase().replaceFirstChar(Char::uppercase)} permission is ${if (granted) "granted" else "denied"} in Mock Device Kit.",
                error = null,
            )
        }
    }

    override fun setCapturedPhoto(uri: Uri?) {
        if (uri == null) return
        val mime = applicationContext.contentResolver.getType(uri)
        if (mime !in SUPPORTED_IMAGE_TYPES) return fail("Choose a JPEG or PNG image for mock photo capture.")
        withGlasses("Start the virtual glasses before selecting a photo.") { device ->
            device.services.camera.setCapturedImage(uri)
            _state.update {
                it.copy(
                    capturedPhotoName = displayName(uri),
                    message = "Mock photo capture is configured.",
                    error = null,
                )
            }
        }
    }

    override fun setVideoFeed(uri: Uri?) {
        if (uri == null) return
        if (!hasSupportedVideoCodec(uri)) {
            return fail("Choose a video with AVC/H.264 or HEVC/H.265 video.")
        }
        withGlasses("Start the virtual glasses before selecting a video.") { device ->
            device.services.camera.setCameraFeed(uri)
            _state.update {
                it.copy(
                    videoFeedName = displayName(uri),
                    phoneCamera = null,
                    message = "Mock video feed is configured.",
                    error = null,
                )
            }
        }
    }

    override fun setPhoneCamera(camera: PreviewPhoneCamera) = withGlasses(
        "Start the virtual glasses before using the phone camera.",
    ) { device ->
        device.services.camera.setCameraFeed(
            if (camera == PreviewPhoneCamera.FRONT) CameraFacing.FRONT else CameraFacing.BACK,
        )
        _state.update {
            it.copy(
                phoneCamera = camera,
                videoFeedName = null,
                message = "${camera.name.lowercase().replaceFirstChar(Char::uppercase)} phone camera feeds the virtual glasses.",
                error = null,
            )
        }
    }

    override fun simulateTranscription(text: String, isFinal: Boolean) = withGlasses(
        "Start the virtual glasses before simulating speech.",
    ) { device ->
        val normalized = text.trim()
        if (normalized.isBlank()) return@withGlasses fail("Enter a query before simulating speech.")
        device.services.speech.simulateTranscription(normalized, isFinal, DEFAULT_CONFIDENCE)
        _state.update {
            it.copy(
                message = if (isFinal) "Sent final simulated speech." else "Sent partial simulated speech.",
                error = null,
            )
        }
    }

    override fun clearError() {
        _state.update { it.copy(error = null) }
    }

    override fun createInAppPreviewView(context: Context): View? {
        val current = _state.value
        if (!current.active || current.mode != DeveloperPreviewMode.IN_APP) return null
        return glasses?.services?.display?.createPreviewView(context)
    }

    private fun startChromeServer(): ChromePreviewInfo? = mock.startTestServer(0).fold(
        onSuccess = { port ->
            ChromePreviewInfo(
                port = port,
                adbForwardCommand = "adb forward tcp:$port tcp:$port",
                url = "http://127.0.0.1:$port/",
            )
        },
        onFailure = { error, _ ->
            fail(error.description)
            null
        },
    )

    private fun releaseMockDevice() {
        runCatching { mock.stopTestServer() }
        glasses?.let { device ->
            runCatching { device.doff() }
            runCatching { device.fold() }
            runCatching { device.powerOff() }
            runCatching { mock.unpairDevice(device) }
        }
        glasses = null
        if (mock.isEnabled) runCatching { mock.disable() }
    }

    private fun withGlasses(message: String, action: (MockGlasses) -> Unit) {
        val device = glasses ?: return fail(message)
        runCatching { action(device) }.onFailure { error -> fail(error.message ?: message) }
    }

    private fun displayName(uri: Uri): String = uri.lastPathSegment?.substringAfterLast('/') ?: "selected media"

    private fun hasSupportedVideoCodec(uri: Uri): Boolean = runCatching {
        val extractor = MediaExtractor()
        try {
            extractor.setDataSource(applicationContext, uri, null)
            (0 until extractor.trackCount).any { index ->
                val mime = extractor.getTrackFormat(index)
                    .getString(android.media.MediaFormat.KEY_MIME)
                    .orEmpty()
                    .lowercase()
                mime in SUPPORTED_VIDEO_CODECS
            }
        } finally {
            extractor.release()
        }
    }.getOrDefault(false)

    private fun fail(message: String) {
        _state.update { it.copy(error = message, message = message) }
    }

    private companion object {
        const val DEFAULT_LOCALE = "en-US"
        const val DEFAULT_CONFIDENCE = 0.92f
        const val REGISTRATION_TIMEOUT_MS = 3_000L
        val SUPPORTED_IMAGE_TYPES = setOf("image/jpeg", "image/png")
        val SUPPORTED_VIDEO_CODECS = setOf("video/avc", "video/hevc")
    }
}
