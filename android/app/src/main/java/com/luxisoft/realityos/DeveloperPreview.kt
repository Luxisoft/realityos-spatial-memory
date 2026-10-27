package com.luxisoft.realityos

import android.content.Context
import android.net.Uri
import android.view.View
import com.meta.wearable.dat.core.types.DeviceIdentifier
import com.meta.wearable.dat.core.types.Permission
import kotlinx.coroutines.flow.StateFlow

/**
 * Debug-only controls for Meta's official Mock Device Kit.
 *
 * The contract deliberately exposes no Mock Device Kit types. Production code
 * can therefore compile and ship without the simulator dependency while the
 * Debug variant can drive the same DAT session used by real glasses.
 */
enum class DeveloperPreviewMode {
    IN_APP,
    CHROME,
}

enum class PreviewPhoneCamera {
    FRONT,
    BACK,
}

data class ChromePreviewInfo(
    val port: Int,
    val adbForwardCommand: String,
    val url: String,
)

data class DeveloperPreviewState(
    val available: Boolean = false,
    val active: Boolean = false,
    val mode: DeveloperPreviewMode? = null,
    val deviceIdentifier: DeviceIdentifier? = null,
    val poweredOn: Boolean = false,
    val unfolded: Boolean = false,
    val worn: Boolean = false,
    val capturedPhotoName: String? = null,
    val videoFeedName: String? = null,
    val phoneCamera: PreviewPhoneCamera? = null,
    val chrome: ChromePreviewInfo? = null,
    val message: String = "Developer preview is stopped.",
    val error: String? = null,
    /** Causes Compose to build a fresh WebView after a preview lifecycle change. */
    val previewGeneration: Int = 0,
)

interface DeveloperPreviewController {
    val state: StateFlow<DeveloperPreviewState>

    /** Enables Mock Device Kit and returns its display-capable virtual device. */
    suspend fun start(mode: DeveloperPreviewMode): DeviceIdentifier?

    /** Stops the local preview server and releases the simulated glasses. */
    suspend fun stop()

    fun powerOn()
    fun powerOff()
    fun unfold()
    fun fold()
    fun don()
    fun doff()

    fun setDatPermission(permission: Permission, granted: Boolean)
    fun setCapturedPhoto(uri: Uri?)
    fun setVideoFeed(uri: Uri?)
    fun setPhoneCamera(camera: PreviewPhoneCamera)
    fun simulateTranscription(text: String, isFinal: Boolean)
    fun clearError()

    /**
     * Returns Meta's WebView-backed Display renderer in Debug builds. It must
     * be invoked on Android's main thread.
     */
    fun createInAppPreviewView(context: Context): View?
}
