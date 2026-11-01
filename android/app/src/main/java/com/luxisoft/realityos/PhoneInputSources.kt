package com.luxisoft.realityos

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.core.UseCase
import androidx.camera.core.UseCaseGroup
import androidx.camera.core.ViewPort
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.video.FallbackStrategy
import androidx.camera.video.FileOutputOptions
import androidx.camera.video.Quality
import androidx.camera.video.QualitySelector
import androidx.camera.video.Recorder
import androidx.camera.video.Recording
import androidx.camera.video.VideoCapture
import androidx.camera.video.VideoRecordEvent
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import java.io.File
import java.util.Locale
import java.util.concurrent.Executor
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** A locally captured file ready for RealityOS's existing upload pipeline. */
data class PhoneMedia(
    val file: File,
    val mimeType: String
)

/**
 * Phone-only media source. Callers request CAMERA and RECORD_AUDIO before
 * invoking these operations; this class deliberately does not prompt for
 * permissions so the display can explain why an action is blocked.
 */
interface PhoneCaptureSource : AutoCloseable {
    suspend fun selectCamera(camera: PreviewPhoneCamera) = Unit

    /**
     * Supplies the Compose-owned preview target. A null surface deliberately
     * keeps capture available for non-Debug hosts while removing the live feed.
     */
    suspend fun setPreviewSurface(
        surfaceProvider: Preview.SurfaceProvider?,
        viewPort: ViewPort? = null
    )

    /** Starts the persistent camera feed used by the Register capture screen. */
    suspend fun startPreview()

    /** Stops the feed and releases the phone camera when no video is finalizing. */
    suspend fun stopPreview()

    suspend fun takePhoto(): PhoneMedia

    suspend fun startVideo()

    suspend fun stopVideo(): PhoneMedia

    fun cancelVideo()

    override fun close()
}

/**
 * CameraX owns the phone camera for the active Register session. It is kept
 * separate from Mock Device Kit so a virtual camera feed cannot race the real
 * image/video capture use cases. The host owns the PreviewView; CameraX only
 * receives its surface and uses the same ViewPort for preview and capture.
 */
class CameraXPhoneCaptureSource(
    context: Context,
    private val lifecycleOwner: LifecycleOwner,
    private val outputDirectory: File = context.cacheDir,
    private var cameraSelector: CameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
) : PhoneCaptureSource {
    private val appContext = context.applicationContext
    private val mainExecutor: Executor = ContextCompat.getMainExecutor(appContext)
    private val operations = Mutex()

    private var provider: ProcessCameraProvider? = null
    private var preview: Preview? = null
    private var imageCapture: ImageCapture? = null
    private var videoCapture: VideoCapture<Recorder>? = null
    private var previewSurfaceProvider: Preview.SurfaceProvider? = null
    private var previewViewPort: ViewPort? = null
    private var previewGeometry: PhonePreviewGeometry? = null
    private var selectedPhoneCamera = PreviewPhoneCamera.BACK
    private var previewRequested = false
    private var recording: Recording? = null
    private var recordingStarted: CompletableDeferred<Unit>? = null
    private var recordingResult: CompletableDeferred<PhoneMedia>? = null
    private var recordingFile: File? = null
    private var discardRecordingOnFinalize = false

    override suspend fun selectCamera(camera: PreviewPhoneCamera) = operations.withLock {
        withContext(Dispatchers.Main.immediate) {
            check(recording == null) { localizedText(R.string.ui_stop_the_video_before_switching_cameras) }
            if (camera != selectedPhoneCamera) {
                selectedPhoneCamera = camera
                cameraSelector = if (camera == PreviewPhoneCamera.FRONT) CameraSelector.DEFAULT_FRONT_CAMERA else CameraSelector.DEFAULT_BACK_CAMERA
                if (previewRequested) bindPhotoUseCase()
            }
            Unit
        }
    }

    override suspend fun setPreviewSurface(
        surfaceProvider: Preview.SurfaceProvider?,
        viewPort: ViewPort?
    ) = operations.withLock {
        withContext(Dispatchers.Main.immediate) {
            val geometry = viewPort?.let {
                PhonePreviewGeometry(it.aspectRatio.numerator, it.aspectRatio.denominator, it.rotation, it.scaleType, it.layoutDirection)
            }
            val changed = previewSurfaceProvider !== surfaceProvider || previewGeometry != geometry
            previewSurfaceProvider = surfaceProvider
            previewViewPort = viewPort
            previewGeometry = geometry
            // Rebinding while a recording is active would terminate the clip.
            // The stable Compose host normally retains its PreviewView through
            // recording; a replacement surface is adopted once it completes.
            if (changed && previewRequested && recording == null) bindPhotoUseCase()
            Unit
        }
    }

    override suspend fun startPreview() = operations.withLock {
        withContext(Dispatchers.Main.immediate) {
            check(recording == null) { localizedText(R.string.ui_stop_the_video_before_starting_the_preview) }
            previewRequested = true
            bindPhotoUseCase()
            Unit
        }
    }

    override suspend fun stopPreview() = operations.withLock {
        withContext(Dispatchers.Main.immediate) {
            previewRequested = false
            if (recording == null) {
                releaseUseCases()
            } else {
                // A close during recording is a cancellation, never a saved
                // clip with no active Register session behind it.
                cancelVideo()
            }
        }
    }

    override suspend fun takePhoto(): PhoneMedia = operations.withLock {
        withContext(Dispatchers.Main.immediate) {
            check(recording == null) { localizedText(R.string.ui_stop_the_video_before_taking_a_photo) }
            val capture = imageCapture ?: bindPhotoUseCase()
            val file = outputFile("jpg")
            try {
                suspendCancellableCoroutine { continuation ->
                    capture.takePicture(
                        ImageCapture.OutputFileOptions.Builder(file).build(),
                        mainExecutor,
                        object : ImageCapture.OnImageSavedCallback {
                            override fun onImageSaved(result: ImageCapture.OutputFileResults) {
                                if (continuation.isActive) {
                                    continuation.resume(PhoneMedia(file, "image/jpeg"))
                                } else {
                                    // Closing the viewfinder can race CameraX's
                                    // completion callback. Never leave that cancelled photo behind.
                                    file.delete()
                                }
                            }

                            override fun onError(error: ImageCaptureException) {
                                file.delete()
                                if (continuation.isActive) continuation.resumeWithException(error)
                            }
                        }
                    )
                    continuation.invokeOnCancellation { file.delete() }
                }
            } finally {
                if (!previewRequested) releaseUseCases()
            }
        }
    }

    override suspend fun startVideo() = operations.withLock {
        withContext(Dispatchers.Main.immediate) {
            check(recording == null) { localizedText(R.string.ui_a_video_is_already_being_recorded) }
            if (
                ContextCompat.checkSelfPermission(appContext, Manifest.permission.RECORD_AUDIO) !=
                PackageManager.PERMISSION_GRANTED
            ) {
                throw SecurityException(localizedText(R.string.ui_microphone_permission_is_required_to_record_video_with_audio))
            }
            val capture = bindVideoUseCase()
            val file = outputFile("mp4")
            val started = CompletableDeferred<Unit>()
            val result = CompletableDeferred<PhoneMedia>()
            recordingFile = file
            recordingStarted = started
            recordingResult = result
            discardRecordingOnFinalize = false
            try {
                recording = capture.output
                    .prepareRecording(appContext, FileOutputOptions.Builder(file).build())
                    .withAudioEnabled()
                    .start(mainExecutor) { event -> handleVideoEvent(event, file, started, result) }
                // Do not let the UI show an active recording until CameraX has
                // accepted both camera and microphone input.
                started.await()
            } catch (error: Exception) {
                discardRecordingOnFinalize = true
                recording?.stop()
                recording = null
                recordingFile = null
                recordingStarted = null
                recordingResult = null
                restorePhotoUseCase()
                file.delete()
                throw error
            }
        }
    }

    override suspend fun stopVideo(): PhoneMedia {
        val result = operations.withLock {
            withContext(Dispatchers.Main.immediate) {
                val activeRecording = checkNotNull(recording) { localizedText(R.string.ui_no_video_is_being_recorded) }
                val activeResult = checkNotNull(recordingResult) { localizedText(R.string.ui_no_video_result_is_pending) }
                activeRecording.stop()
                activeResult
            }
        }
        return result.await()
    }

    override fun cancelVideo() {
        val activeRecording = recording ?: return
        // A caller that cancels does not receive a PhoneMedia result, so leave
        // no completed clip in cache when CameraX delivers its final callback.
        discardRecordingOnFinalize = true
        activeRecording.stop()
    }

    override fun close() {
        previewRequested = false
        previewSurfaceProvider = null
        previewViewPort = null
        previewGeometry = null
        cancelVideo()
        runCatching {
            if (recording == null) releaseUseCases()
        }
    }

    private suspend fun bindPhotoUseCase(): ImageCapture {
        val activeProvider = provider ?: awaitProvider().also { provider = it }
        return bindPhotoUseCase(activeProvider)
    }

    private fun bindPhotoUseCase(activeProvider: ProcessCameraProvider): ImageCapture {
        releaseUseCases()
        val photo = ImageCapture.Builder()
            .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
            .build()
        bindWithOptionalPreview(activeProvider, photo)
        imageCapture = photo
        return photo
    }

    private suspend fun bindVideoUseCase(): VideoCapture<Recorder> {
        val activeProvider = provider ?: awaitProvider().also { provider = it }
        releaseUseCases()
        val recorder = Recorder.Builder()
            .setQualitySelector(
                QualitySelector.fromOrderedList(
                    listOf(Quality.HD, Quality.SD),
                    FallbackStrategy.lowerQualityOrHigherThan(Quality.SD)
                )
            )
            .build()
        val video = VideoCapture.withOutput(recorder)
        bindWithOptionalPreview(activeProvider, video)
        videoCapture = video
        return video
    }

    private fun bindWithOptionalPreview(
        activeProvider: ProcessCameraProvider,
        primaryUseCase: UseCase
    ) {
        val cameraPreview = if (previewRequested) {
            previewSurfaceProvider?.let { surfaceProvider ->
                Preview.Builder().build().also { it.setSurfaceProvider(surfaceProvider) }
            }
        } else {
            null
        }
        preview = cameraPreview
        if (cameraPreview == null) {
            activeProvider.bindToLifecycle(lifecycleOwner, cameraSelector, primaryUseCase)
            return
        }
        val group = UseCaseGroup.Builder()
            .addUseCase(cameraPreview)
            .addUseCase(primaryUseCase)
            .apply { previewViewPort?.let(::setViewPort) }
            .build()
        activeProvider.bindToLifecycle(lifecycleOwner, cameraSelector, group)
    }

    private suspend fun awaitProvider(): ProcessCameraProvider = suspendCancellableCoroutine { continuation ->
        val future = ProcessCameraProvider.getInstance(appContext)
        future.addListener(
            {
                try {
                    if (continuation.isActive) continuation.resume(future.get())
                } catch (error: Exception) {
                    if (continuation.isActive) continuation.resumeWithException(error)
                }
            },
            mainExecutor
        )
    }

    private fun handleVideoEvent(
        event: VideoRecordEvent,
        file: File,
        started: CompletableDeferred<Unit>,
        result: CompletableDeferred<PhoneMedia>
    ) {
        if (event is VideoRecordEvent.Start) {
            started.complete(Unit)
            return
        }
        if (event !is VideoRecordEvent.Finalize) return
        recording = null
        recordingFile = null
        recordingStarted = null
        recordingResult = null
        val discard = discardRecordingOnFinalize
        discardRecordingOnFinalize = false
        if (event.hasError() || discard) {
            file.delete()
            val error = if (discard) {
                IllegalStateException(localizedText(R.string.ui_video_recording_was_canceled))
            } else {
                IllegalStateException(localizedText(R.string.ui_could_not_save_the_video_code_1_d, event.error))
            }
            started.completeExceptionally(error)
            result.completeExceptionally(error)
        } else {
            started.complete(Unit)
            result.complete(PhoneMedia(file, "video/mp4"))
        }
        restorePhotoUseCase()
    }

    private fun restorePhotoUseCase() {
        val activeProvider = provider
        if (previewRequested && activeProvider != null && recording == null) {
            bindPhotoUseCase(activeProvider)
        } else if (recording == null) {
            releaseUseCases()
        }
    }

    private fun releaseUseCases() {
        val activeProvider = provider ?: return
        val uses = listOfNotNull<UseCase>(preview, imageCapture, videoCapture).toTypedArray()
        if (uses.isNotEmpty()) activeProvider.unbind(*uses)
        preview = null
        imageCapture = null
        videoCapture = null
    }

    private fun outputFile(extension: String): File {
        outputDirectory.mkdirs()
        return File(outputDirectory, "realityos-${System.currentTimeMillis()}.$extension")
    }
}

interface PhoneSpeechSource : AutoCloseable {
    val partialText: StateFlow<String>

    suspend fun listen(): String

    fun cancel()

    override fun close()
}

/** Android's on-device/service speech path for the no-glasses preview route. */
class AndroidPhoneSpeechSource(
    context: Context,
    private val locale: Locale? = null
) : PhoneSpeechSource {
    private val appContext = context.applicationContext
    private val _partialText = MutableStateFlow("")
    override val partialText: StateFlow<String> = _partialText.asStateFlow()
    private var recognizer: SpeechRecognizer? = null
    private var result: CompletableDeferred<String>? = null

    override suspend fun listen(): String = withContext(Dispatchers.Main.immediate) {
        check(SpeechRecognizer.isRecognitionAvailable(appContext)) {
            localizedText(R.string.ui_speech_recognition_is_unavailable_on_this_phone)
        }
        check(result == null) { localizedText(R.string.ui_a_voice_search_is_already_in_progress) }
        _partialText.value = ""
        val deferred = CompletableDeferred<String>()
        result = deferred
        val activeRecognizer = SpeechRecognizer.createSpeechRecognizer(appContext)
        recognizer = activeRecognizer
        activeRecognizer.setRecognitionListener(listenerFor(deferred))
        activeRecognizer.startListening(
            Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, (locale ?: Locale.forLanguageTag(RealityExperienceStore(appContext).selectedLanguage().languageTag)).toLanguageTag())
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            }
        )
        try {
            deferred.await()
        } finally {
            if (result === deferred) result = null
            // A cancelled listen can finish after the next listen has already
            // installed a new recognizer. Never let the old coroutine destroy
            // that new retry.
            if (recognizer === activeRecognizer) {
                activeRecognizer.destroy()
                recognizer = null
            }
        }
    }

    override fun cancel() {
        val activeRecognizer = recognizer
        val activeResult = result
        result = null
        recognizer = null
        activeRecognizer?.cancel()
        activeResult?.completeExceptionally(IllegalStateException(localizedText(R.string.ui_voice_search_canceled)))
        activeRecognizer?.destroy()
        _partialText.value = ""
    }

    override fun close() = cancel()

    private fun listenerFor(deferred: CompletableDeferred<String>) = object : RecognitionListener {
        override fun onReadyForSpeech(params: android.os.Bundle?) = Unit

        override fun onBeginningOfSpeech() = Unit

        override fun onRmsChanged(rmsdB: Float) = Unit

        override fun onBufferReceived(buffer: ByteArray?) = Unit

        override fun onEndOfSpeech() = Unit

        override fun onError(error: Int) {
            if (result === deferred) {
                deferred.completeExceptionally(IllegalStateException(recognitionErrorMessage(error)))
            }
        }

        override fun onResults(results: android.os.Bundle?) {
            val text = results
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull { it.isNotBlank() }
                ?.trim()
            if (result !== deferred) return
            if (text == null) {
                deferred.completeExceptionally(IllegalStateException(localizedText(R.string.ui_no_voice_query_was_detected)))
            } else {
                deferred.complete(text)
            }
        }

        override fun onPartialResults(partialResults: android.os.Bundle?) {
            if (result !== deferred) return
            _partialText.value = partialResults
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()
                ?.trim()
                .orEmpty()
        }

        override fun onEvent(eventType: Int, params: android.os.Bundle?) = Unit
    }

    private fun recognitionErrorMessage(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_AUDIO -> localizedText(R.string.ui_could_not_access_the_phone_audio)
        SpeechRecognizer.ERROR_CLIENT -> localizedText(R.string.ui_voice_search_was_interrupted)
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> localizedText(R.string.ui_microphone_permission_is_required_for_voice_search)
        SpeechRecognizer.ERROR_NETWORK,
        SpeechRecognizer.ERROR_NETWORK_TIMEOUT
        -> localizedText(R.string.ui_voice_search_could_not_connect_try_again)
        SpeechRecognizer.ERROR_NO_MATCH,
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT
        -> localizedText(R.string.ui_no_voice_query_was_detected)
        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> localizedText(R.string.ui_speech_recognition_is_busy)
        SpeechRecognizer.ERROR_SERVER -> localizedText(R.string.ui_the_speech_recognition_service_failed)
        else -> localizedText(R.string.ui_voice_search_could_not_start)
    }
}
