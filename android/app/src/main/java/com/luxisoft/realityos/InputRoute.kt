package com.luxisoft.realityos

/**
 * The source used for an explicit capture or spoken query.
 *
 * PHONE is also the route used by the Debug optical-display preview: the mock
 * owns only the Display transport while the phone owns its local sensors.
 */
enum class InputRoute {
    PHONE,
    WEARABLE
}

/** Keeps simulator-specific device selection out of capture and query code. */
object InputRoutePolicy {
    /** Eligible physical hardware wins; a remembered or explicitly selected mock stays virtual. */
    fun <T> selectDevice(eligible: List<T>, requested: T?, isSimulated: (T) -> Boolean): T? = eligible.firstOrNull { !isSimulated(it) }
        ?: requested?.takeIf { it in eligible }
        ?: eligible.firstOrNull()

    fun forConnectedDevice(isSimulated: Boolean): InputRoute = if (isSimulated) InputRoute.PHONE else InputRoute.WEARABLE
}

enum class PhonePermission {
    CAMERA,
    MICROPHONE
}

/** A lifecycle-safe permission request consumed by MainActivity. */
sealed interface RealityPermissionRequest {
    val id: Long

    data class Dat(
        override val id: Long,
        val permission: com.meta.wearable.dat.core.types.Permission
    ) : RealityPermissionRequest

    data class Android(
        override val id: Long,
        val permission: PhonePermission
    ) : RealityPermissionRequest
}
