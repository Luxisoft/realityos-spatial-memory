package com.luxisoft.realityos.host.operations

import androidx.lifecycle.viewModelScope
import com.luxisoft.realityos.*
import com.luxisoft.realityos.RealityViewModel.Companion.PROCESSING_POLL_INTERVAL_MS
import com.luxisoft.realityos.RealityViewModel.Companion.PROCESSING_STATUS_NOTICE_EVERY
import com.luxisoft.realityos.RealityViewModel.PendingUpload
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

internal fun RealityViewModel.completePendingUploadOperation(pending: PendingUpload) {
    if (pendingUpload === pending) pendingUpload = null
    pending.file.delete()
}

internal fun RealityViewModel.retryPendingUploadOperation() {
    val pending = pendingUpload ?: return renderCapture()
    if (mutableUiState.value.busy) return
    setBusy(true)
    viewModelScope.launch {
        var stored = false
        try {
            val job = uploadPendingCapture(pending)
            completePendingUpload(pending)
            watchProcessing(job)
            showStatus(copy(pending.successMessage))
            stored = true
        } catch (error: Exception) {
            showError(error.message ?: copy(R.string.status_capture_upload_failed), retry = ::retryPendingUpload)
        } finally {
            setBusy(false)
            if (stored && inputRoute == InputRoute.PHONE) {
                finishPhoneCaptureAfterStored()
            } else if (stored) {
                renderCapture()
            }
        }
    }
}

internal fun RealityViewModel.persistCaptureBytesOperation(bytes: ByteArray, extension: String): File {
    val directory = File(app.cacheDir, "realityos-pending-uploads").apply { mkdirs() }
    return File.createTempFile("realityos-", ".${extension.trimStart('.')}", directory).also { file ->
        file.outputStream().buffered().use { output -> output.write(bytes) }
    }
}

internal fun RealityViewModel.watchProcessingOperation(initial: RemoteJob) {
    if (!initial.isPending) {
        if (initial.isFailed) showStatus(initial.errorMessage ?: copy(R.string.status_processing_failed))
        return
    }
    processingJobIds += initial.id
    updateProcessingCount()
    viewModelScope.launch {
        var current = initial
        var attempts = 0
        var consecutiveStatusFailures = 0
        try {
            while (current.isPending) {
                delay(PROCESSING_POLL_INTERVAL_MS)
                current = try {
                    withContext(Dispatchers.IO) {
                        withRealityApi { it.getProcessingJob(initial.id) }
                    }
                } catch (error: Exception) {
                    // A missing secure job endpoint used to create an
                    // infinite loop of raw "Not Found" messages. The
                    // media is already safely stored at this point, so
                    // stop the loop and let the person explicitly retry
                    // only the status request after connectivity or a
                    // deployment issue is corrected.
                    consecutiveStatusFailures += 1
                    if (ProcessingStatusRetryPolicy.shouldStop(error, consecutiveStatusFailures)) {
                        showError(
                            copy(R.string.status_processing_status_unavailable),
                            retry = { watchProcessing(initial) }
                        )
                        return@launch
                    }
                    showStatus(copy(R.string.status_processing_status_failed))
                    continue
                }
                consecutiveStatusFailures = 0
                attempts += 1
                if (current.isPending && attempts % PROCESSING_STATUS_NOTICE_EVERY == 0) {
                    showStatus(copy(R.string.status_evidence_still_processing))
                }
            }
            when {
                current.status.equals("completed", ignoreCase = true) ->
                    showStatus(copy(R.string.status_evidence_ready))
                current.isFailed ->
                    showStatus(current.errorMessage ?: copy(R.string.status_processing_failed))
                else -> showStatus(copy(R.string.status_evidence_still_processing))
            }
        } catch (error: Exception) {
            showStatus(error.message ?: copy(R.string.status_processing_status_failed))
        } finally {
            processingJobIds.remove(initial.id)
            updateProcessingCount()
        }
    }
}

internal fun RealityViewModel.updateProcessingCountOperation() {
    mutableUiState.update { it.copy(processingJobs = processingJobIds.size) }
}
