package com.luxisoft.realityos.host.operations

import androidx.lifecycle.viewModelScope
import com.luxisoft.realityos.*
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.selectors.SpecificDeviceSelector
import com.meta.wearable.dat.core.session.DeviceSessionState
import com.meta.wearable.dat.core.types.DeviceIdentifier
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.core.types.RegistrationState
import com.meta.wearable.dat.display.removeDisplay
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

internal fun RealityViewModel.connectDisplayOperation(deviceIdentifier: DeviceIdentifier? = null) {
    if (mutableUiState.value.provisioning == null) {
        showStatus(copy(R.string.status_admin_provisioning_required))
        return
    }
    if (!mutableUiState.value.wearable.transportReady) {
        showStatus(copy(R.string.status_wearables_not_ready))
        return
    }
    if (Wearables.registrationState.value != RegistrationState.REGISTERED) {
        showStatus(copy(R.string.status_register_meta_first))
        return
    }
    if (session != null) return
    val previewController = (app as RealityOsApplication).developerPreviewController
    val selected = InputRoutePolicy.selectDevice(eligibleDisplayDevices(), deviceIdentifier, previewController::isSimulatedDevice)
        ?: return showStatus(copy(R.string.status_display_not_connected))
    val route = InputRoutePolicy.forConnectedDevice(previewController.isSimulatedDevice(selected))
    val selector = SpecificDeviceSelector(selected)
    Wearables.createSession(selector).fold(
        onSuccess = { created ->
            session = created
            mutableUiState.update { current ->
                current.copy(wearable = current.wearable.copy(sessionActive = true))
            }
            sessionErrorsJob = viewModelScope.launch {
                created.errors.collect { error -> showError(copy(R.string.status_display_failed)) }
            }
            sessionStateJob = viewModelScope.launch {
                created.state.collect { sessionState ->
                    if (session !== created) return@collect
                    if (sessionState == DeviceSessionState.STARTED && display == null) {
                        inputRoute = route
                        mutableUiState.update { it.copy(wearable = it.wearable.copy(inputRoute = route)) }
                        attachDisplay(created)
                    }
                    if (sessionState == DeviceSessionState.STOPPED) cleanupStoppedSession(created)
                }
            }
            created.start()
            showStatus(copy(R.string.status_connecting_display))
        },
        onFailure = { error, _ -> showError(copy(R.string.status_display_failed)) }
    )
}

internal fun RealityViewModel.disconnectDisplayOperation(): Boolean {
    if (mutableUiState.value.recording || mutableUiState.value.captureSessionId != null || mutableUiState.value.busy) {
        showStatus(copy(R.string.status_finish_capture_first))
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
    showStatus(copy(R.string.status_display_disconnected))
    return true
}

internal fun RealityViewModel.onDatPermissionResultOperation(
    requestId: Long,
    permission: Permission,
    granted: Boolean,
    failureMessage: String? = null
) {
    val request = mutablePermissionRequest.value as? RealityPermissionRequest.Dat ?: return
    if (request.id != requestId || request.permission != permission) return
    mutablePermissionRequest.value = null
    if (!granted) {
        if (state.value.meta.captureForPublication || state.value.meta.captureForSearch) metaController.pause()
        pendingAction = null
        showError(
            failureMessage ?: copy(
                R.string.status_permission_denied,
                if (permission == Permission.CAMERA) copy(R.string.permission_camera) else copy(R.string.permission_microphone)
            )
        )
        return
    }
    continueAfterPermission()
}

internal fun RealityViewModel.onPhonePermissionResultOperation(requestId: Long, permission: PhonePermission, granted: Boolean) {
    val request = mutablePermissionRequest.value as? RealityPermissionRequest.Android ?: return
    if (request.id != requestId || request.permission != permission) return
    mutablePermissionRequest.value = null
    if (!granted) {
        if (state.value.meta.captureForPublication || state.value.meta.captureForSearch) metaController.pause()
        pendingAction = null
        showError(
            copy(
                R.string.status_permission_denied,
                if (permission == PhonePermission.CAMERA) copy(R.string.permission_camera) else copy(R.string.permission_microphone)
            )
        )
        return
    }
    continueAfterPermission()
}
