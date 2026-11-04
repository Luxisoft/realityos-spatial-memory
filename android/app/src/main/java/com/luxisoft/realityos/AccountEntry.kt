package com.luxisoft.realityos

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import kotlinx.coroutines.CancellationException

@Composable
internal fun AccountEntry(viewModel: RealityViewModel, onSuccess: () -> Unit, onBack: () -> Unit) {
    val repository = remember(SocialSession.identity) { AccountRepository() }
    AccountForm(onBack = onBack) { mode, payload ->
        var identity = SocialSession.identity
        try {
            val login = repository.submit(mode, payload)
            if (login != null) {
                SocialSession.requireCurrent(identity)
                SocialSession.workspaceId = login.captureProfile.workspaceId
                SocialSession.remember(login.credentials)
                identity = SocialSession.identity
                viewModel.useFacebookCaptureProfile(login.captureProfile)
                SocialSession.active = true
                onSuccess()
            }
        } catch (cancelled: CancellationException) {
            if (mode == "login" && !SocialSession.active) SocialSession.clearIfCurrent(identity)
            throw cancelled
        } catch (error: Exception) {
            if (mode == "login") SocialSession.clearIfCurrent(identity)
            throw error
        }
    }
}

internal object AccountRequestLanguage {
    var value: String = "en"
}
