package com.luxisoft.realityos

import android.content.Context
import android.graphics.Color
import android.media.MediaExtractor
import android.net.Uri
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebView
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.selectors.SpecificDeviceSelector
import com.meta.wearable.dat.core.types.DeviceIdentifier
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.core.types.PermissionStatus
import com.meta.wearable.dat.core.types.RegistrationState
import com.meta.wearable.dat.mockdevice.MockDeviceKit
import com.meta.wearable.dat.mockdevice.api.GlassesModel
import com.meta.wearable.dat.mockdevice.api.MockDeviceKitConfig
import com.meta.wearable.dat.mockdevice.api.MockDeviceKitInterface
import com.meta.wearable.dat.mockdevice.api.MockGlasses
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
    private val applicationContext: Context
) : DeveloperPreviewController {
    private val mock: MockDeviceKitInterface = MockDeviceKit.getInstance(applicationContext)
    private val _state = MutableStateFlow(DeveloperPreviewState(available = true))
    override val state: StateFlow<DeveloperPreviewState> = _state.asStateFlow()

    private var glasses: MockGlasses? = null
    private val simulatedIdentifiers = mutableSetOf<DeviceIdentifier>()

    override fun isSimulatedDevice(identifier: DeviceIdentifier): Boolean = identifier in simulatedIdentifiers

    override suspend fun start(mode: DeveloperPreviewMode): DeviceIdentifier? {
        if (_state.value.active) stop()
        clearError()

        return try {
            mock.enable(
                MockDeviceKitConfig(
                    initiallyRegistered = true,
                    initialPermissionsGranted = true
                )
            )
            val registered = withTimeoutOrNull(REGISTRATION_TIMEOUT_MS) {
                Wearables.registrationState.first { it == RegistrationState.REGISTERED }
            }
            if (registered == null) {
                fail(localizedText(R.string.debug_registration_failed))
                releaseMockDevice()
                return null
            }
            val pairing = mock.pairGlasses(GlassesModel.META_RAYBAN_DISPLAY)
            if (!pairing.isSuccess) {
                pairing.fold(
                    onSuccess = {},
                    onFailure = { error, _ -> fail(localizedText(R.string.debug_operation_failed)) }
                )
                releaseMockDevice()
                return null
            }
            val paired = pairing.getOrThrow()
            simulatedIdentifiers += paired.deviceIdentifier
            glasses = paired
            paired.powerOn()
            paired.unfold()
            paired.don()
            paired.services.speech.setLocale(if (LocalizedText.languageTag == "es") "es-ES" else "en-US")
            if (!awaitEligibleDevice(paired.deviceIdentifier)) {
                fail(localizedText(R.string.debug_virtual_display_not_ready))
                releaseMockDevice()
                return null
            }
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
                        messageResource = R.string.debug_display_ready,
                        error = null,
                        previewGeneration = it.previewGeneration + 1
                    )
                }
                paired.deviceIdentifier
            }
        } catch (error: Exception) {
            fail(localizedText(R.string.debug_start_failed))
            releaseMockDevice()
            null
        }
    }

    override suspend fun stop() {
        releaseMockDevice()
        _state.update {
            DeveloperPreviewState(
                available = true,
                messageResource = R.string.debug_preview_stopped,
                previewGeneration = it.previewGeneration + 1
            )
        }
    }

    override fun powerOn() = withGlasses(localizedText(R.string.debug_start_first)) { device ->
        device.powerOn()
        _state.update { it.copy(poweredOn = true, messageResource = R.string.debug_powered_on) }
    }

    override fun powerOff() = withGlasses(localizedText(R.string.debug_start_first)) { device ->
        device.powerOff()
        _state.update { it.copy(poweredOn = false, worn = false, messageResource = R.string.debug_powered_off) }
    }

    override fun unfold() = withGlasses(localizedText(R.string.debug_start_first)) { device ->
        device.unfold()
        _state.update { it.copy(unfolded = true, messageResource = R.string.debug_unfolded) }
    }

    override fun fold() = withGlasses(localizedText(R.string.debug_start_first)) { device ->
        device.fold()
        _state.update { it.copy(unfolded = false, worn = false, messageResource = R.string.debug_folded) }
    }

    override fun don() = withGlasses(localizedText(R.string.debug_start_first)) { device ->
        device.don()
        _state.update { it.copy(worn = true, messageResource = R.string.debug_status_worn) }
    }

    override fun doff() = withGlasses(localizedText(R.string.debug_start_first)) { device ->
        device.doff()
        _state.update { it.copy(worn = false, messageResource = R.string.debug_removed) }
    }

    override fun setDatPermission(permission: Permission, granted: Boolean) {
        if (!mock.isEnabled) return fail(localizedText(R.string.debug_start_first))
        val status = if (granted) PermissionStatus.Granted else PermissionStatus.Denied
        mock.permissions.set(permission, status)
        mock.permissions.setRequestResult(permission, status)
        _state.update {
            it.copy(
                messageResource = if (granted) R.string.debug_permission_granted else R.string.debug_permission_denied,
                messageArguments = listOf(if (permission == Permission.CAMERA) R.string.permission_camera else R.string.permission_microphone),
                error = null
            )
        }
    }

    override fun setCapturedPhoto(uri: Uri?) {
        if (uri == null) return
        val mime = applicationContext.contentResolver.getType(uri)
        if (mime !in SUPPORTED_IMAGE_TYPES) return fail(localizedText(R.string.debug_photo_format))
        withGlasses(localizedText(R.string.debug_start_first)) { device ->
            device.services.camera.setCapturedImage(uri)
            _state.update {
                it.copy(
                    capturedPhotoName = displayName(uri),
                    messageResource = R.string.debug_photo_ready,
                    error = null
                )
            }
        }
    }

    override fun setVideoFeed(uri: Uri?) {
        if (uri == null) return
        if (!hasSupportedVideoCodec(uri)) {
            return fail(localizedText(R.string.debug_video_format))
        }
        withGlasses(localizedText(R.string.debug_start_first)) { device ->
            device.services.camera.setCameraFeed(uri)
            _state.update {
                it.copy(
                    videoFeedName = displayName(uri),
                    phoneCamera = null,
                    messageResource = R.string.debug_video_ready,
                    error = null
                )
            }
        }
    }

    override fun setPhoneCamera(camera: PreviewPhoneCamera) = withGlasses(
        localizedText(R.string.debug_start_first)
    ) { device ->
        // CameraX owns the phone sensors. Opening a second phone feed in the
        // SDK would compete with the actual photo/video source.
        _state.update {
            it.copy(
                phoneCamera = camera,
                videoFeedName = null,
                messageResource = if (camera == PreviewPhoneCamera.FRONT) R.string.debug_front_camera_selected else R.string.debug_back_camera_selected,
                error = null
            )
        }
    }

    override fun simulateTranscription(text: String, isFinal: Boolean) = withGlasses(
        localizedText(R.string.debug_start_first)
    ) { device ->
        val normalized = text.trim()
        if (normalized.isBlank()) return@withGlasses fail(localizedText(R.string.debug_query_required))
        device.services.speech.simulateTranscription(normalized, isFinal, DEFAULT_CONFIDENCE)
        _state.update {
            it.copy(
                messageResource = if (isFinal) R.string.debug_speech_final else R.string.debug_speech_partial,
                error = null
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
            ?.let(::prepareTransparentDisplayPreview)
    }

    /**
     * Meta's Debug renderer is a WebView whose document and host are already
     * transparent, but its app root intentionally defaults to a black display
     * window. The photographic lens preview has its own scene behind that
     * renderer, so make only this Debug presentation surface transparent while
     * retaining the SDK's controls, bridge, and WebViewClient unchanged.
     */
    private fun prepareTransparentDisplayPreview(view: View): View {
        val webView = view as? WebView ?: return view
        webView.setBackgroundColor(Color.TRANSPARENT)
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, newProgress: Int) {
                super.onProgressChanged(view, newProgress)
                if (newProgress == 100) {
                    view.post { makeDisplayRootTransparent(view) }
                }
            }
        }
        // Covers the case where the SDK page completed before the Chrome
        // client was installed. The script retries until React creates its
        // display root, without replacing the SDK's WebViewClient.
        webView.post { makeDisplayRootTransparent(webView) }
        return webView
    }

    private fun makeDisplayRootTransparent(webView: WebView) {
        webView.evaluateJavascript(TRANSPARENT_DISPLAY_ROOT_SCRIPT, null)
    }

    /**
     * Mock Device Kit publishes lifecycle changes asynchronously. Do not hand
     * RealityViewModel an identifier until DAT sees its link as connected,
     * otherwise createSession can reject it as ineligible.
     */
    private suspend fun awaitEligibleDevice(deviceIdentifier: DeviceIdentifier): Boolean {
        val selector = SpecificDeviceSelector(deviceIdentifier)
        return withTimeoutOrNull(DEVICE_READY_TIMEOUT_MS) {
            selector.activeDeviceFlow().first { it == deviceIdentifier }
        } == deviceIdentifier
    }

    private fun startChromeServer(): ChromePreviewInfo? = mock.startTestServer(0).fold(
        onSuccess = { port ->
            ChromePreviewInfo(
                port = port,
                adbForwardCommand = "adb forward tcp:$port tcp:$port",
                url = "http://127.0.0.1:$port/"
            )
        },
        onFailure = { error, _ ->
            fail(localizedText(R.string.debug_operation_failed))
            null
        }
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
        runCatching { action(device) }.onFailure { error -> fail(localizedText(R.string.debug_operation_failed)) }
    }

    private fun displayName(uri: Uri): String = uri.lastPathSegment?.substringAfterLast('/') ?: localizedText(R.string.debug_selected_media)

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
        _state.update { it.copy(error = message) }
    }

    private companion object {
        const val DEFAULT_CONFIDENCE = 0.92f
        const val REGISTRATION_TIMEOUT_MS = 3_000L
        const val DEVICE_READY_TIMEOUT_MS = 3_000L
        val SUPPORTED_IMAGE_TYPES = setOf("image/jpeg", "image/png")
        val SUPPORTED_VIDEO_CODECS = setOf("video/avc", "video/hevc")
        val TRANSPARENT_DISPLAY_ROOT_SCRIPT =
            """
            (() => {
              let attempts = 0;
              const apply = () => {
                const root = document.querySelector('[data-app-root]');
                if (!root) {
                  if (++attempts < 180) requestAnimationFrame(apply);
                  return;
                }
                [document.documentElement, document.body, document.getElementById('app'), root]
                  .filter(Boolean)
                  .forEach((node) => {
                    node.style.setProperty('background', 'transparent', 'important');
                    node.style.setProperty('background-color', 'transparent', 'important');
                  });
                document.documentElement.style.setProperty(
                  '--wui-color-background-window', 'transparent', 'important'
                );
              };
              apply();
            })();
            """.trimIndent()
    }
}
