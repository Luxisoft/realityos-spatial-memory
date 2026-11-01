package com.luxisoft.realityos

import android.util.Base64
import androidx.lifecycle.viewModelScope
import java.io.File
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

/** Owns human-authenticated Display work, independently of device Register. */
internal class MetaDisplayController(private val vm: RealityViewModel) {
    private val preferences = vm.app.getSharedPreferences("meta-display", 0)
    private var owner: String? = null
    private var pending: File? = null
    internal val previewFile: File? get() = pending
    private var key: String? = null
    private var uploadId: String? = null
    private var target: MetaDestination? = null
    private var job: Job? = null
    private var configurationJob: Job? = null
    internal val generation = MetaDisplayGeneration()
    internal var matches: List<GalleryThumb> = emptyList()
    internal var answer: LocalizedSpeech? = null
    internal val answerText: String get() = answer?.text.orEmpty()
    internal var resultStatus: String = ""
    internal var lastQuestion: String = ""
    internal var faceGroupUrl: String? = null
    private val meta get() = vm.state.value.meta

    private fun subject(): String? = runCatching {
        val encoded = SocialSession.token?.split('.')?.getOrNull(1) ?: return null
        JSONObject(String(Base64.decode(encoded, Base64.URL_SAFE or Base64.NO_WRAP))).getString("sub")
    }.getOrNull()

    internal fun authenticated(): Boolean = owner != null && owner == subject()

    private fun update(block: (MetaDisplayState) -> MetaDisplayState) {
        vm.mutableUiState.update { it.copy(meta = block(it.meta)) }
    }

    fun refresh() {
        val current = subject()
        if (current == null) {
            clear()
            return
        }
        if (configurationJob?.isActive == true) return
        if (owner != current) {
            clear()
            owner = current
        }
        restore(current)
        update { it.copy(loading = true, error = null) }
        configurationJob = vm.viewModelScope.launch {
            try {
                val groups = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("workspaces")) }
                if (subject() != current) return@launch
                val options = listOf(MetaDestination("home", vm.copy(R.string.meta_profile_private), "home")) +
                    (0 until groups.length()).map { groups.getJSONObject(it) }.filter { !it.getString("name").startsWith("home:") }.map {
                        MetaDestination(it.optText("workspace_id") ?: it.getString("id"), it.getString("name"), "work")
                    }
                val saved = preferences.getString("$current.destination", null)
                update { it.copy(destinations = options, destination = options.find { d -> d.id == saved }) }
                restore(current)
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                update { it.copy(error = vm.copy(R.string.meta_configuration_failed)) }
            } finally {
                update { it.copy(loading = false) }
            }
        }
    }

    fun selectDestination(destination: MetaDestination) {
        if (!authenticated() || !MetaDisplayPolicy.canChangeDestination(
                meta.captureForPublication || meta.captureForSearch || vm.state.value.wearable.cameraActive,
                pending != null,
                vm.state.value.busy
            ) || !MetaDisplayPolicy.destinationAllowed(destination, meta.destinations)
        ) {
            return
        }
        preferences.edit().putString("$owner.destination", destination.id).apply()
        update { it.copy(destination = destination, error = null) }
        if (vm.display != null) vm.renderHome()
    }

    fun selectScope(scope: MetaSearchScope) {
        if (vm.state.value.busy || vm.state.value.wearable.speechActive ||
            vm.state.value.wearable.cameraActive || meta.captureForSearch || pending != null
        ) {
            return
        }
        update { it.copy(searchScope = scope, resultIndex = 0, resultCount = 0) }
        matches = emptyList()
    }

    fun beginCapture() {
        if (vm.state.value.busy || vm.state.value.wearable.speechActive ||
            vm.state.value.captureSessionId != null || vm.state.value.wearable.cameraActive ||
            vm.mutablePermissionRequest.value != null || meta.captureForSearch
        ) {
            return
        }
        if (pending != null) {
            vm.renderPublicationReview()
            return
        }
        val profile = MetaDisplayPolicy.profileDestination(meta.destinations)
        if (!authenticated() || profile == null) {
            vm.renderNotice(vm.copy(R.string.meta_profile_required))
            return
        }
        target = profile
        update { it.copy(captureForPublication = true, pendingDestination = target?.name, error = null) }
        vm.pendingAction = RealityViewModel.PendingAction.PrepareCapture
        if (vm.inputRoute == InputRoute.PHONE) {
            vm.requestPhonePermission(PhonePermission.CAMERA)
        } else {
            vm.requestDatPermission(com.meta.wearable.dat.core.types.Permission.CAMERA)
        }
    }

    fun beginPhotoSearch(kind: MetaPhotoSearchKind = MetaPhotoSearchKind.OBJECT) {
        if (vm.state.value.busy || vm.state.value.wearable.speechActive ||
            vm.state.value.wearable.cameraActive || vm.state.value.captureSessionId != null ||
            vm.mutablePermissionRequest.value != null || meta.captureForPublication || pending != null
        ) {
            return
        }
        if (!authenticated()) {
            vm.renderNotice(vm.copy(R.string.meta_login_required))
            return
        }
        update { it.copy(captureForSearch = true, photoSearchKind = kind, error = null) }
        vm.pendingAction = RealityViewModel.PendingAction.PrepareCapture
        if (vm.inputRoute == InputRoute.PHONE) {
            vm.requestPhonePermission(PhonePermission.CAMERA)
        } else {
            vm.requestDatPermission(com.meta.wearable.dat.core.types.Permission.CAMERA)
        }
    }

    internal suspend fun stage(media: PhoneMedia, revision: Long) {
        val current = owner
        if (!generation.accepts(revision) || !authenticated() || current == null || target == null || !meta.captureForPublication) {
            media.file.delete()
            return
        }
        val folder = File(vm.app.filesDir, "meta-captures/$current").apply { mkdirs() }
        val stored = File(folder, "${UUID.randomUUID()}.${if (media.mimeType == "video/mp4") "mp4" else "jpg"}")
        withContext(Dispatchers.IO) {
            media.file.copyTo(stored)
            media.file.delete()
        }
        if (!generation.accepts(revision) || owner != current || !authenticated() || !meta.captureForPublication) {
            stored.delete()
            return
        }
        pending = stored
        key = UUID.randomUUID().toString()
        uploadId = null
        update { it.copy(pendingMime = media.mimeType, uploadStatus = null, captureForPublication = false) }
        save()
        vm.stopCamera()
        vm.renderNotice(vm.copy(R.string.meta_sending_profile), showHome = false)
    }

    private fun save() {
        val file = pending ?: return
        val destination = target ?: return
        val value = JSONObject().put("file", file.name).put("key", key).put("upload", uploadId)
            .put("mime", meta.pendingMime).put("target", destination.id)
            .put("name", destination.name).put("audience", destination.audience)
        preferences.edit().putString("$owner.pending", value.toString()).apply()
    }

    private fun restore(current: String) {
        if (pending != null || job?.isActive == true) return
        val saved = preferences.getString("$current.pending", null) ?: return
        runCatching {
            val value = JSONObject(saved)
            val filename = value.getString("file")
            require(filename == File(filename).name)
            val file = File(vm.app.filesDir, "meta-captures/$current/$filename")
            if (!file.isFile) {
                preferences.edit().remove("$current.pending").apply()
                return
            }
            pending = file
            key = value.getString("key")
            uploadId = value.optText("upload")
            target = MetaDestination(value.getString("target"), value.getString("name"), value.getString("audience"))
            update {
                it.copy(
                    pendingMime = value.getString("mime"),
                    pendingDestination = target?.name,
                    uploadStatus = if (uploadId == null) null else "paused"
                )
            }
        }
    }

    fun submit(action: String? = null) {
        if (job?.isActive == true || vm.state.value.busy || !authenticated()) return
        val file = pending ?: return
        val destination = target ?: return
        val current = owner
        val revision = generation.revision
        job = vm.viewModelScope.launch {
            vm.setBusy(true)
            update { it.copy(error = null) }
            try {
                var response = withContext(Dispatchers.IO) {
                    if (uploadId != null) {
                        JSONObject(
                            SocialSession.request(
                                "me/publication-uploads/$uploadId${action?.let { "/$it" }.orEmpty()}",
                                if (action == null) null else JSONObject()
                            )
                        )
                    } else {
                        val fields = mutableMapOf("request_key" to checkNotNull(key), "audience" to destination.audience)
                        if (destination.audience == "work") fields["workspace_id"] = destination.id
                        JSONObject(
                            SocialSession.requestMultipartFile(
                                "me/publication-uploads",
                                fields,
                                file,
                                checkNotNull(meta.pendingMime)
                            )
                        )
                    }
                }
                if (subject() != current) return@launch
                uploadId = response.getString("id")
                save()
                var polls = 0
                if (response.optString("status") == "pending") {
                    update { it.copy(uploadStatus = "pending") }
                    vm.renderPublicationReview()
                }
                while (response.optString("status") == "pending" && polls++ < 120) {
                    delay(1500)
                    response = withContext(Dispatchers.IO) {
                        JSONObject(SocialSession.request("me/publication-uploads/$uploadId"))
                    }
                    if (subject() != current) return@launch
                }
                val status = response.getString("status")
                update { it.copy(uploadStatus = status, duplicatePreview = response.optText("duplicate_preview_url"), error = if (status == "failed") vm.copy(R.string.meta_upload_failed) else null) }
                if (status == "published" || status == "cancelled") {
                    removePending()
                    vm.renderNotice(vm.copy(if (status == "published") R.string.meta_published else R.string.meta_discarded))
                } else {
                    vm.renderPublicationReview()
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                update { it.copy(error = vm.copy(R.string.meta_upload_failed)) }
                vm.renderPublicationReview()
            } finally {
                if (generation.accepts(revision)) vm.setBusy(false)
            }
        }
    }

    fun discard() {
        if (vm.state.value.busy || job?.isActive == true) return
        if (uploadId != null) {
            submit("cancel")
            return
        }
        removePending()
        vm.stopCamera()
        update { it.copy(captureForPublication = false, pendingDestination = null) }
        vm.renderHome()
    }

    private fun removePending() {
        pending?.delete()
        pending = null
        uploadId = null
        key = null
        target = null
        preferences.edit().remove("$owner.pending").apply()
        update { it.copy(pendingMime = null, uploadStatus = null, pendingDestination = null, duplicatePreview = null, captureForPublication = false, error = null) }
    }

    internal fun pause() {
        generation.invalidate()
        vm.captureOperationJob?.cancel()
        vm.captureOperationJob = null
        vm.queryJob?.cancel()
        vm.queryJob = null
        vm.galleryImageJob?.cancel()
        vm.galleryImageJob = null
        // Network cancellation retains the request key and private original for a safe retry.
        job?.cancel()
        job = null
        if (pending != null) update { it.copy(uploadStatus = if (uploadId == null) null else "paused") }
        update { it.copy(captureForPublication = false, captureForSearch = false, recordingSeconds = 0) }
    }

    fun clear() {
        configurationJob?.cancel()
        configurationJob = null
        pause()
        vm.stopSpeech()
        vm.stopSpeak()
        vm.state.value.captureSessionId?.let(vm::closeCaptureSessionOnServer)
        vm.stopCamera()
        vm.mutableUiState.update { it.copy(captureSessionId = null, queryResult = null, message = "") }
        vm.pendingAction = null
        vm.mutablePermissionRequest.value = null
        vm.setBusy(false)
        pending = null
        key = null
        uploadId = null
        target = null
        owner = null
        matches = emptyList()
        answer = null
        lastQuestion = ""
        faceGroupUrl = null
        update { MetaDisplayState() }
        vm.renderHome()
    }
}
