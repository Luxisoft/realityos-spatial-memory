package com.luxisoft.realityos.host.operations

import androidx.lifecycle.viewModelScope
import com.luxisoft.realityos.*
import com.luxisoft.realityos.RealityViewModel.Companion.SPEECH_START_TIMEOUT_MS
import com.luxisoft.realityos.RealityViewModel.PendingAction
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.speech.Speech
import com.meta.wearable.dat.speech.addSpeech
import com.meta.wearable.dat.speech.removeSpeech
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull

internal fun RealityViewModel.beginQueryOperation() {
    if (mutableUiState.value.captureSessionId != null || state.value.wearable.cameraActive || state.value.meta.captureForPublication || state.value.meta.captureForSearch || state.value.meta.pendingMime != null) {
        renderNotice(copy(R.string.status_stop_capture_before_query))
        return
    }
    if (processingJobIds.isNotEmpty()) {
        renderNotice(
            copy(R.string.status_evidence_processing),
            actionLabel = copy(R.string.display_retry),
            action = ::beginQuery
        )
        return
    }
    if (mutableUiState.value.busy || mutableUiState.value.wearable.speechActive || mutablePermissionRequest.value != null) return
    pendingAction = PendingAction.StartQuery
    if (inputRoute == InputRoute.WEARABLE) {
        requestDatPermission(Permission.MICROPHONE)
        renderNotice(copy(R.string.status_microphone_permission))
    } else {
        requestPhonePermission(PhonePermission.MICROPHONE)
        renderNotice(copy(R.string.status_phone_microphone_permission))
    }
}

internal fun RealityViewModel.startSpeechQueryOperation() {
    if (inputRoute == InputRoute.PHONE) {
        startPhoneSpeechQuery()
    } else {
        startWearableSpeechQuery()
    }
}

internal fun RealityViewModel.startPhoneSpeechQueryOperation() {
    val source = phoneSpeech ?: return showError(copy(R.string.status_phone_source_unavailable))
    if (phoneSpeechJob != null) return
    mutableUiState.update { current -> current.copy(wearable = current.wearable.copy(speechActive = true)) }
    renderListening(copy(R.string.display_listening_phone))
    phoneSpeechJob = viewModelScope.launch {
        val partials = launch {
            source.partialText.collectLatest { partial ->
                if (partial.isNotBlank()) renderListening(partial)
            }
        }
        try {
            val text = source.listen()
            mutableUiState.update { current -> current.copy(wearable = current.wearable.copy(speechActive = false)) }
            executeQuery(text)
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            showError(error.message ?: copy(R.string.status_query_failed), retry = ::beginQuery)
        } finally {
            partials.cancel()
            phoneSpeechJob = null
            mutableUiState.update { current -> current.copy(wearable = current.wearable.copy(speechActive = false)) }
        }
    }
}

internal fun RealityViewModel.startWearableSpeechQueryOperation() {
    val activeSession = session ?: return showError(copy(R.string.status_display_not_connected))
    if (speech != null) return
    var attached: Speech? = null
    var failure: String? = null
    activeSession.addSpeech().fold(
        onSuccess = { attached = it },
        onFailure = { error, _ -> failure = error.description }
    )
    val activeSpeech = attached ?: return showError(failure ?: copy(R.string.status_microphone_not_ready))
    var startFailure: String? = null
    activeSpeech.start().fold(
        onSuccess = {},
        onFailure = { error, _ -> startFailure = error.description }
    )
    if (startFailure != null) {
        runCatching { activeSession.removeSpeech() }
        showError(startFailure ?: copy(R.string.status_microphone_not_ready), retry = ::beginQuery)
        return
    }
    speech = activeSpeech
    mutableUiState.update { current -> current.copy(wearable = current.wearable.copy(speechActive = true)) }
    speechJob = viewModelScope.launch {
        val started = withTimeoutOrNull(SPEECH_START_TIMEOUT_MS) {
            activeSpeech.state.first { it.name == "STARTED" }
        }
        if (started == null) {
            stopSpeech()
            showError(copy(R.string.status_microphone_start_timeout), retry = ::beginQuery)
            return@launch
        }
        renderListening(copy(R.string.display_listening))
        activeSpeech.transcriptions.collect { transcription ->
            val text = transcription?.text?.takeIf { it.isNotBlank() } ?: return@collect
            if (transcription.isFinal) {
                // Stop the remote microphone before the network query but
                // keep this coroutine alive long enough to launch it.
                releaseWearableSpeech()
                executeQuery(text)
                return@collect
            }
            renderListening(text)
        }
    }
    speechErrorJob?.cancel()
    speechErrorJob = viewModelScope.launch {
        activeSpeech.errorDetails.collectLatest { details ->
            if (!details.isNullOrBlank() && speech === activeSpeech) {
                releaseWearableSpeech()
                showError(details, retry = ::beginQuery)
            }
        }
    }
}

internal fun RealityViewModel.stopSpeechOperation() {
    phoneSpeechJob?.cancel()
    phoneSpeechJob = null
    phoneSpeech?.cancel()
    releaseWearableSpeech()
    mutableUiState.update { current ->
        current.copy(wearable = current.wearable.copy(speechActive = false))
    }
}

internal fun RealityViewModel.releaseWearableSpeechOperation() {
    speechJob?.cancel()
    speechJob = null
    speechErrorJob?.cancel()
    speechErrorJob = null
    runCatching { speech?.stop() }
    session?.removeSpeech()
    speech = null
}

internal fun RealityViewModel.executeQueryOperation(question: String) {
    if (state.value.meta.searchScope == MetaSearchScope.GALLERY) {
        executeVoiceQuery(question)
        return
    }
    if (state.value.busy) return
    val revision = metaController.generation.revision
    setBusy(true)
    queryJob = viewModelScope.launch {
        try {
            val language = RealityExperienceStore(app).syncAccountLanguage().languageTag
            val answer = withContext(Dispatchers.IO) { withRealityApi { it.query(question, language) } }
            if (!metaController.generation.accepts(revision)) return@launch
            if (language != RealityExperienceStore(app).selectedLanguage().languageTag) return@launch
            mutableUiState.update { it.copy(queryResult = answer, message = answer.message) }
            val imageUrl = answer.displayMediaPath?.let { path ->
                mutableUiState.value.provisioning?.let(::RealityApi)?.absoluteUrl(path)
            }
            renderQueryResult(answer, imageUrl, language)
            speak(answer.ttsText, language)
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            showError(error.message ?: copy(R.string.status_query_failed), retry = { executeQuery(question) })
        } finally {
            if (metaController.generation.accepts(revision)) setBusy(false)
        }
    }
}
