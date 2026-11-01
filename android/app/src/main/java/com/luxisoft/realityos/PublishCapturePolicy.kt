package com.luxisoft.realityos

/**
 * Chooses which camera serves a publish capture: the wearable camera only
 * when the wearable route is active and its camera is ready, otherwise the
 * phone camera intent.
 */
internal object PublishCapturePolicy {
    fun useWearable(route: InputRoute, wearableCameraReady: Boolean): Boolean =
        route == InputRoute.WEARABLE && wearableCameraReady
}
