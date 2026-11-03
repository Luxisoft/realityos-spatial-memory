package com.luxisoft.realityos

import androidx.lifecycle.viewModelScope
import com.meta.wearable.dat.display.views.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

internal fun RealityViewModel.renderMetaHome() {
    cancelDisplayImageLoad()
    metaController.clearResultImages()
    sendDisplay {
        val meta = state.value.meta
        flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
            text("RealityOS", style = TextStyle.HEADING)
            button(copy(R.string.meta_search), style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::renderSearchMenu)
            if (meta.pendingMime != null) {
                text(meta.pendingDestination.orEmpty(), style = TextStyle.BODY)
                button(copy(R.string.meta_pending_capture), style = ButtonStyle.PRIMARY, iconName = IconName.VIDEO_CAMERA, onClick = ::renderPublicationReview)
            } else {
                button(copy(R.string.meta_capture), style = ButtonStyle.SECONDARY, iconName = IconName.VIDEO_CAMERA, onClick = ::beginMetaCapture)
            }
        }
    }
}

internal fun RealityViewModel.renderSearchMenu() {
    cancelDisplayImageLoad()
    metaController.clearResultImages()
    sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
            text(copy(R.string.meta_search), style = TextStyle.HEADING)
            button(copy(R.string.meta_search_object), style = ButtonStyle.PRIMARY, iconName = IconName.VIDEO_CAMERA, onClick = ::beginMetaObjectSearch)
            button(copy(R.string.meta_search_person), style = ButtonStyle.PRIMARY, iconName = IconName.VIDEO_CAMERA, onClick = ::beginMetaPersonSearch)
            button(copy(R.string.meta_voice_command), style = ButtonStyle.SECONDARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
            button(copy(R.string.display_back), style = ButtonStyle.OUTLINE, iconName = IconName.ARROW_LEFT, onClick = ::renderHome)
        }
    }
}

internal fun RealityViewModel.renderPublicationReview(): Unit = sendDisplay {
    val meta = state.value.meta
    flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
        text(copy(if (meta.uploadStatus == "duplicate") R.string.meta_duplicate else R.string.meta_review_capture), style = TextStyle.HEADING)
        text(meta.pendingDestination.orEmpty(), style = TextStyle.BODY)
        text(copy(if (meta.pendingMime == "video/mp4") R.string.meta_video else R.string.meta_photo), style = TextStyle.META)
        when {
            meta.error != null -> {
                text(meta.error, style = TextStyle.BODY)
                button(copy(R.string.display_retry), style = ButtonStyle.PRIMARY, iconName = IconName.TWO_ARROWS_CLOCKWISE, onClick = ::retryMetaPublication)
            }
            meta.uploadStatus == "pending" -> {
                text(copy(R.string.meta_processing), style = TextStyle.BODY)
                button(copy(R.string.display_retry), style = ButtonStyle.SECONDARY, iconName = IconName.TWO_ARROWS_CLOCKWISE, onClick = ::retryMetaPublication)
                button(copy(R.string.display_home), style = ButtonStyle.OUTLINE, iconName = IconName.HOUSE, onClick = ::renderHome)
            }
            meta.uploadStatus == "duplicate" -> {
                text(copy(R.string.meta_duplicate_body), style = TextStyle.BODY)
                button(copy(R.string.meta_replace), style = ButtonStyle.PRIMARY, iconName = IconName.CHECKMARK, onClick = ::replaceMetaPublication)
            }
            meta.uploadStatus != null -> {
                text(copy(R.string.meta_resume_upload), style = TextStyle.BODY)
                button(copy(R.string.display_retry), style = ButtonStyle.PRIMARY, iconName = IconName.TWO_ARROWS_CLOCKWISE, onClick = ::retryMetaPublication)
            }
            else -> {
                text(copy(R.string.meta_confirm_destination), style = TextStyle.BODY)
                button(copy(R.string.meta_publish), style = ButtonStyle.PRIMARY, iconName = IconName.CHECKMARK, onClick = ::publishMetaCapture)
            }
        }
        if (meta.uploadStatus != "pending") button(copy(R.string.meta_discard), style = ButtonStyle.OUTLINE, iconName = IconName.X, onClick = ::discardMetaCapture)
    }
}

internal fun RealityViewModel.executeVoiceQuery(question: String) {
    if (!metaController.authenticated()) {
        showError(copy(R.string.meta_login_required))
        return
    }
    if (state.value.busy) return
    if (question.trim().length < 2) {
        renderNotice(copy(R.string.chat_voice_missing), copy(R.string.display_new_query), ::beginQuery)
        return
    }
    val revision = metaController.generation.revision
    queryJob = viewModelScope.launch {
        renderNotice(copy(R.string.meta_searching), showHome = false)
        try {
            val target = withContext(Dispatchers.IO) {
                JSONObject(SocialSession.request("search/route", JSONObject().put("text", question))).optText("target") ?: "ask"
            }
            if (!metaController.generation.accepts(revision) || !metaController.authenticated()) return@launch
            when (MetaDisplayPolicy.voiceSearchRoute(target, SocialSession.isGuest)) {
                MetaVoiceSearch.PERSON_TEXT -> executePersonTextQuery(question)
                MetaVoiceSearch.OBJECT_QUERY -> executeGalleryQuery(question)
                MetaVoiceSearch.CHAT -> {
                    val language = RealityExperienceStore(app).selectedLanguage().languageTag
                    val greeting = ChatRoutePolicy.greeting(language)
                    metaController.answer = LocalizedSpeech(greeting, language)
                    renderNotice(greeting, copy(R.string.display_new_query), ::beginQuery)
                    speak(greeting, language)
                }
                MetaVoiceSearch.PERSON_BLOCKED -> renderNotice(copy(R.string.meta_guest_no_person), copy(R.string.display_new_query), ::beginQuery)
            }
        } catch (failure: Exception) {
            if (failure is CancellationException) throw failure
            showError(copy(R.string.chat_route_failed), retry = { executeVoiceQuery(question) })
        }
    }
}

internal fun RealityViewModel.executePersonTextQuery(question: String) {
    if (!metaController.authenticated()) {
        showError(copy(R.string.meta_login_required))
        return
    }
    if (state.value.busy) return
    metaController.clearResultImages()
    val revision = metaController.generation.revision
    setBusy(true)
    queryJob = viewModelScope.launch {
        renderNotice(copy(R.string.meta_searching_person), showHome = false)
        try {
            val language = RealityExperienceStore(app).syncAccountLanguage().languageTag
            val raw = withContext(Dispatchers.IO) {
                JSONObject(SocialSession.searchWorkspaceRecords((SocialSession.workWorkspaceId ?: SocialSession.workspaceId).orEmpty(), JSONObject().put("question", question).put("language", language)))
            }
            if (!metaController.generation.accepts(revision) || !metaController.authenticated()) return@launch
            val responseLanguage = raw.optText("response_language") ?: language
            if (responseLanguage != RealityExperienceStore(app).selectedLanguage().languageTag) return@launch
            val answer = raw.optText("answer")?.ifBlank { copy(R.string.chat_no_answer) } ?: copy(R.string.chat_no_answer)
            val profiles = raw.optJSONArray("profiles")?.let { array ->
                (0 until array.length()).mapNotNull { array.optJSONObject(it) }
            }.orEmpty()
            metaController.answer = LocalizedSpeech(answer, responseLanguage)
            metaController.resultStatus = ""
            metaController.lastQuestion = question
            renderPersonTextResult(answer, profiles.mapNotNull { it.optText("display_name") }, profiles.firstOrNull()?.optText("picture_url"), raw.optBoolean("simulated"), responseLanguage)
            speak(answer, responseLanguage)
        } catch (failure: Exception) {
            if (failure is CancellationException) throw failure
            showError(copy(R.string.status_query_failed), retry = { executePersonTextQuery(question) })
        } finally {
            if (metaController.generation.accepts(revision)) setBusy(false)
        }
    }
}

internal fun RealityViewModel.renderPersonTextResult(answer: String, names: List<String>, portraitUrl: String?, simulated: Boolean, language: String): Unit = sendDisplay {
    flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
        text(copy(R.string.meta_search_person), style = TextStyle.HEADING)
        portraitUrl?.takeIf { it.startsWith("http") }?.let { portrait ->
            image(uri = portrait, sizePreset = ImageSize.FILL)
        }
        text(answer.take(RealityViewModel.MAX_DISPLAY_TEXT), style = TextStyle.BODY)
        names.take(3).forEach { name ->
            text("• $name".take(120), style = TextStyle.META, color = TextColor.SECONDARY)
        }
        if (simulated) text(copy(R.string.meta_simulated), style = TextStyle.META)
        button(copy(R.string.display_hear_again), style = ButtonStyle.SECONDARY, iconName = IconName.SPEAKER_WITH_TWO_ARCS, onClick = { speak(answer, language) })
        button(copy(R.string.display_new_query), style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
        button(copy(R.string.display_home), style = ButtonStyle.OUTLINE, iconName = IconName.HOUSE, onClick = ::renderHome)
    }
}

internal fun RealityViewModel.executeGalleryQuery(question: String, photo: ByteArray? = null) {
    if (!metaController.authenticated()) {
        showError(copy(R.string.meta_login_required))
        return
    }
    if (state.value.busy) return
    mutableUiState.value = state.value.copy(meta = state.value.meta.copy(photoSearchKind = MetaPhotoSearchKind.OBJECT))
    metaController.clearResultImages()
    val revision = metaController.generation.revision
    setBusy(true)
    queryJob = viewModelScope.launch {
        renderNotice(copy(R.string.meta_searching), showHome = false)
        val screen = renderRevision
        try {
            val language = RealityExperienceStore(app).syncAccountLanguage().languageTag
            val raw = withContext(Dispatchers.IO) {
                JSONObject(
                    if (photo != null) {
                        SocialSession.requestMultipart(
                            "queries/image",
                            mapOf("workspace_id" to checkNotNull(SocialSession.workspaceId), "language" to language),
                            photo,
                            "busqueda.jpg",
                            "image/jpeg",
                            fieldName = "image"
                        )
                    } else {
                        SocialSession.request(
                            "queries",
                            JSONObject()
                                .put("workspace_id", checkNotNull(SocialSession.workspaceId))
                                .put("question", question).put("language", language).put("search_scope", "gallery")
                        )
                    }
                )
            }
            if (!acceptsDisplayImage(revision, screen)) return@launch
            val responseLanguage = raw.optText("response_language") ?: language
            if (responseLanguage != RealityExperienceStore(app).selectedLanguage().languageTag) return@launch
            metaController.matches = orderedEvidence(
                raw.optJSONArray("gallery_matches")?.let { array ->
                    (0 until array.length()).mapNotNull { decodeGalleryThumb(array.getJSONObject(it)) }
                }.orEmpty()
            )
            metaController.answer = LocalizedSpeech(raw.optText("message").orEmpty(), responseLanguage)
            metaController.resultStatus = raw.optText("gallery_search_status").orEmpty()
            metaController.lastQuestion = question
            mutableUiState.value = state.value.copy(meta = state.value.meta.copy(resultIndex = 0, resultCount = metaController.matches.size))
            if (photo != null && metaController.matches.isEmpty() && raw.optBoolean("found")) {
                val observation = raw.optJSONObject("observation")
                renderQueryResult(
                    QueryEvidence(
                        found = true, ambiguous = raw.optBoolean("ambiguous"),
                        message = metaController.answerText, ttsText = raw.optText("tts_text") ?: metaController.answerText,
                        highlightedPath = raw.optText("highlighted_media_url"), displayMediaPath = null,
                        seenAt = observation?.optText("seen_at"),
                        visualConfidence = observation?.let { if (it.isNull("visual_confidence")) null else it.optDouble("visual_confidence") },
                        simulated = raw.optBoolean("simulated")
                    ),
                    null,
                    responseLanguage
                )
            } else if (metaController.matches.isEmpty()) {
                renderNotice(metaController.answerText, copy(R.string.display_new_query), ::beginQuery)
            } else {
                loadGalleryResult(0, revision)
            }
            speak(raw.optText("tts_text") ?: metaController.answerText, responseLanguage)
        } catch (failure: Exception) {
            if (failure is CancellationException) throw failure
            if (acceptsDisplayImage(revision, screen)) showError(copy(R.string.status_query_failed), retry = if (photo == null) ({ executeGalleryQuery(question) }) else ::beginMetaObjectSearch)
        } finally {
            if (metaController.generation.accepts(revision)) setBusy(false)
        }
    }
}

internal fun RealityViewModel.executeFaceQuery(photo: ByteArray) {
    if (!metaController.authenticated()) {
        showError(copy(R.string.meta_login_required))
        return
    }
    if (state.value.busy) return
    mutableUiState.value = state.value.copy(meta = state.value.meta.copy(photoSearchKind = MetaPhotoSearchKind.PERSON))
    metaController.clearResultImages()
    val revision = metaController.generation.revision
    setBusy(true)
    queryJob = viewModelScope.launch {
        renderNotice(copy(R.string.meta_searching_person), showHome = false)
        val screen = renderRevision
        try {
            val raw = withContext(Dispatchers.IO) {
                JSONObject(
                    SocialSession.requestMultipart(
                        MetaDisplayPolicy.photoSearchPath(MetaPhotoSearchKind.PERSON),
                        mapOf("workspace_id" to checkNotNull(SocialSession.workspaceId)),
                        photo,
                        "busqueda.jpg",
                        "image/jpeg"
                    )
                )
            }
            if (!acceptsDisplayImage(revision, screen)) return@launch
            val userMatches = raw.optJSONArray("matches")?.let { array ->
                (0 until array.length()).mapNotNull {
                    val match = array.optJSONObject(it) ?: return@mapNotNull null
                    decodeFaceThumb(match)?.copy(
                        faceEnrollmentId = match.optString("user_id"),
                        probeBox = faceMatchProbeBox(match)
                    )
                }
            }.orEmpty()
            val recordMatches = raw.optJSONArray("matches_records")?.let { array ->
                (0 until array.length()).mapNotNull {
                    val match = array.optJSONObject(it) ?: return@mapNotNull null
                    decodeRecordFaceThumb(match)?.copy(
                        faceEnrollmentId = faceMatchEnrollmentId(match),
                        probeBox = faceMatchProbeBox(match)
                    )
                }
            }.orEmpty()
            metaController.matches = orderedEvidence(userMatches + recordMatches)
            val names = metaController.matches.joinToString { faceMatchLabel(it.caption, it.confidence) }
            val answerText = if (metaController.matches.isEmpty()) {
                copy(R.string.chat_face_none)
            } else {
                localizedQuantityText(R.plurals.chat_face_found, metaController.matches.size, metaController.matches.size, names)
            }
            metaController.answer = LocalizedSpeech(answerText, RealityExperienceStore(app).selectedLanguage().languageTag)
            metaController.resultStatus = ""
            metaController.lastQuestion = ""
            mutableUiState.value = state.value.copy(meta = state.value.meta.copy(resultIndex = 0, resultCount = metaController.matches.size))
            metaController.clearResultImages()
            if (metaController.matches.isEmpty()) {
                renderNotice(metaController.answerText, copy(R.string.display_new_query), ::beginQuery)
            } else {
                val marks = faceGroupMarks(faceGroupRows(metaController.matches, MetaDisplayPolicy.faceGroupPalette()))
                val groupLink = if (marks.isEmpty()) {
                    null
                } else {
                    try {
                        withContext(Dispatchers.IO) {
                            DisplayImageLink.decode(
                                JSONObject(
                                    SocialSession.requestMultipart(
                                        "display/face-group-links",
                                        mapOf("marks" to faceGroupMarksJson(marks)),
                                        photo,
                                        "grupo.jpg",
                                        "image/jpeg"
                                    )
                                )
                            )
                        }
                    } catch (failure: Exception) {
                        if (failure is CancellationException) throw failure
                        null
                    }
                }
                if (!acceptsDisplayImage(revision, screen)) return@launch
                metaController.faceGroupLink = groupLink
                try {
                    if (groupLink != null) loadFaceGroup(revision) else loadFaceResult(0, revision)
                } catch (failure: Exception) {
                    if (failure is CancellationException) throw failure
                    if (acceptsDisplayImage(revision, screen)) {
                        showError(copy(R.string.meta_image_failed), retry = if (groupLink != null) ::renderFaceGroup else ({ renderFaceResult(0) }))
                    }
                }
            }
            speakDisplayAnswer()
        } catch (failure: Exception) {
            if (failure is CancellationException) throw failure
            if (acceptsDisplayImage(revision, screen)) showError(copy(R.string.status_query_failed), retry = ::beginMetaPersonSearch)
        } finally {
            if (metaController.generation.accepts(revision)) setBusy(false)
        }
    }
}

internal fun RealityViewModel.renderFaceGroup(): Unit = launchDisplayImageLoad(retry = ::renderFaceGroup) { revision ->
    val link = metaController.faceGroupLink
    if (link != null && !displayResultImages.valid(link)) {
        metaController.faceGroupImage = null
        renderNotice(copy(R.string.meta_image_failed), copy(R.string.display_new_query), ::beginMetaPersonSearch)
    } else {
        loadFaceGroup(revision)
    }
}

private suspend fun RealityViewModel.loadFaceGroup(revision: Long) {
    val link = checkNotNull(metaController.faceGroupLink)
    val screen = renderRevision
    val cached = metaController.faceGroupImage?.takeIf { it.link == link && displayResultImages.valid(it) }
    val bitmap = cached?.bitmap ?: displayResultImages.load(link)
    if (!acceptsDisplayImage(revision, screen)) return
    metaController.faceGroupImage = LoadedDisplayImage(link, bitmap)
    val rows = faceGroupRows(metaController.matches, MetaDisplayPolicy.faceGroupPalette())
    if (rows.isEmpty()) return
    val language = RealityExperienceStore(app).language.value.languageTag
    val profileTargets = displayProfileTargets(metaController.matches)
    sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 8, padding = 20, background = FlexBoxBackground.CARD) {
            text(copy(R.string.meta_search_person), style = TextStyle.HEADING)
            image(bitmap = bitmap, sizePreset = ImageSize.FILL)
            rows.take(MetaDisplayPolicy.FACE_GROUP_MAX_ROWS).forEach { row ->
                val color = copy(MetaDisplayPolicy.faceMarkColorName(row.colorIndex))
                val confidence = evidencePercent(row.thumb.confidence, language).orEmpty()
                text(
                    "${row.number} · ${row.thumb.caption.take(40)} · $confidence · $color",
                    style = TextStyle.META,
                    color = TextColor.SECONDARY
                )
            }
            val overflow = rows.size - MetaDisplayPolicy.FACE_GROUP_MAX_ROWS
            if (overflow > 0) text(copy(R.string.meta_face_group_more, overflow), style = TextStyle.META)
            if (rows.any { it.thumb.simulated }) text(copy(R.string.meta_simulated), style = TextStyle.META)
            buttonGroup(alignment = ButtonGroupAlignment.CENTER) {
                if (profileTargets.isNotEmpty()) {
                    button(copy(if (profileTargets.size == 1) R.string.meta_open_profile else R.string.meta_open_profiles), style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = { openMatchedProfiles(revision = revision) })
                }
                button(copy(R.string.meta_face_group_photos), style = ButtonStyle.SECONDARY, iconName = IconName.VIDEO_CAMERA, onClick = { renderFaceResult(0) })
            }
            buttonGroup(alignment = ButtonGroupAlignment.CENTER) {
                button(copy(R.string.display_hear_again), style = ButtonStyle.SECONDARY, iconName = IconName.SPEAKER_WITH_TWO_ARCS, onClick = ::speakDisplayAnswer)
                button(copy(R.string.display_new_query), style = ButtonStyle.SECONDARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
                button(copy(R.string.display_home), style = ButtonStyle.OUTLINE, iconName = IconName.HOUSE, onClick = ::renderHome)
            }
        }
    }
}

internal fun RealityViewModel.renderFaceResult(index: Int): Unit = launchDisplayImageLoad(retry = { renderFaceResult(index) }) { revision ->
    loadFaceResult(index, revision)
}

private suspend fun RealityViewModel.loadFaceResult(index: Int, revision: Long) {
    val item = metaController.matches.getOrNull(index) ?: return
    val screen = renderRevision
    val bitmap = displayResultImages.match(item.faceDisplayKind, item.faceEnrollmentId)
    if (!acceptsDisplayImage(revision, screen)) return
    mutableUiState.value = state.value.copy(meta = state.value.meta.copy(resultIndex = index))
    val language = RealityExperienceStore(app).language.value.languageTag
    sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 8, padding = 20, background = FlexBoxBackground.CARD) {
            text(copy(R.string.meta_person_position, index + 1, metaController.matches.size), style = TextStyle.META)
            image(bitmap = bitmap, sizePreset = ImageSize.FILL)
            text(item.caption.take(120), style = TextStyle.HEADING)
            val badge = if (item.matchedLabels.contains("record_candidate")) {
                copy(R.string.face_badge_record)
            } else if (item.matchedLabels.contains("possible_acquaintance")) {
                copy(R.string.face_badge_knows)
            } else {
                copy(R.string.face_badge_direct)
            }
            text("$badge · ${evidencePercent(item.confidence, language).orEmpty()}", style = TextStyle.META, color = TextColor.SECONDARY)
            if (item.simulated) text(copy(R.string.meta_simulated), style = TextStyle.META)
            if (normalizedProfileId(item.profileUserId) != null) {
                button(copy(R.string.meta_open_profile), style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = { openMatchedProfiles(item.profileUserId, revision) })
            }
            buttonGroup(alignment = ButtonGroupAlignment.CENTER) {
                if (index > 0) button(copy(R.string.meta_previous), style = ButtonStyle.OUTLINE, iconName = IconName.ARROW_LEFT, onClick = { renderFaceResult(index - 1) })
                if (index < metaController.matches.lastIndex) button(copy(R.string.meta_next), style = ButtonStyle.SECONDARY, iconName = IconName.CHECKMARK, onClick = { renderFaceResult(index + 1) })
                button(copy(R.string.meta_result_actions), style = ButtonStyle.OUTLINE, iconName = IconName.SPEECH_BUBBLE, onClick = ::renderResultActions)
            }
        }
    }
}

internal fun RealityViewModel.renderGalleryResult(index: Int): Unit = launchDisplayImageLoad(retry = { renderGalleryResult(index) }) { revision ->
    loadGalleryResult(index, revision)
}

private suspend fun RealityViewModel.loadGalleryResult(index: Int, revision: Long) {
    val item = metaController.matches.getOrNull(index) ?: return
    val screen = renderRevision
    val bitmap = displayResultImages.match("evidence", item.evidenceId, item.matchedLabels)
    if (!acceptsDisplayImage(revision, screen)) return
    mutableUiState.value = state.value.copy(meta = state.value.meta.copy(resultIndex = index))
    val language = RealityExperienceStore(app).language.value.languageTag
    sendDisplay {
        flexBox(direction = Direction.COLUMN, gap = 8, padding = 20, background = FlexBoxBackground.CARD) {
            text(copy(R.string.meta_result_position, index + 1, metaController.matches.size), style = TextStyle.META)
            image(bitmap = bitmap, sizePreset = ImageSize.FILL)
            val confidence = evidencePercent(item.confidence, language).orEmpty()
            text(copy(R.string.meta_evidence_details, item.publishedAt.take(10), confidence), style = TextStyle.META, color = TextColor.SECONDARY)
            if (item.simulated) text(copy(R.string.meta_simulated), style = TextStyle.META)
            if (metaController.resultStatus == "partial") text(copy(R.string.meta_partial_results), style = TextStyle.META)
            buttonGroup(alignment = ButtonGroupAlignment.CENTER) {
                if (index > 0) button(copy(R.string.meta_previous), style = ButtonStyle.OUTLINE, iconName = IconName.ARROW_LEFT, onClick = { renderGalleryResult(index - 1) })
                if (index < metaController.matches.lastIndex) button(copy(R.string.meta_next), style = ButtonStyle.SECONDARY, iconName = IconName.CHECKMARK, onClick = { renderGalleryResult(index + 1) })
                button(copy(R.string.meta_result_actions), style = ButtonStyle.OUTLINE, iconName = IconName.SPEECH_BUBBLE, onClick = ::renderResultActions)
            }
        }
    }
}

internal fun RealityViewModel.renderResultActions(): Unit = sendDisplay {
    flexBox(direction = Direction.COLUMN, gap = 10, padding = 24, background = FlexBoxBackground.CARD) {
        val item = metaController.matches.getOrNull(state.value.meta.resultIndex)
        val language = RealityExperienceStore(app).language.value.languageTag.take(2)
        val info = displayEvidenceInformation(item, language)
        text((info?.title ?: copy(R.string.evidence_title)).take(120), style = TextStyle.HEADING)
        if (item != null && info == null) text(copy(R.string.evidence_information_pending), style = TextStyle.META)
        val note = info?.note
        if (!note.isNullOrBlank()) text(note.take(180), style = TextStyle.BODY)
        button(copy(R.string.display_hear_again), style = ButtonStyle.SECONDARY, iconName = IconName.SPEAKER_WITH_TWO_ARCS, onClick = ::speakDisplayAnswer)
        button(copy(R.string.display_new_query), style = ButtonStyle.PRIMARY, iconName = IconName.SPEECH_BUBBLE, onClick = ::beginQuery)
        button(copy(R.string.display_back), style = ButtonStyle.OUTLINE, iconName = IconName.ARROW_LEFT, onClick = {
            if (state.value.meta.photoSearchKind == MetaPhotoSearchKind.PERSON) {
                if (metaController.faceGroupLink != null) renderFaceGroup() else renderFaceResult(state.value.meta.resultIndex)
            } else {
                renderGalleryResult(state.value.meta.resultIndex)
            }
        })
        button(copy(R.string.display_home), style = ButtonStyle.OUTLINE, iconName = IconName.HOUSE, onClick = ::renderHome)
    }
}

/** The source language travels with the stored answer through every replay button. */
internal fun RealityViewModel.speakDisplayAnswer() {
    metaController.answer?.let { speak(it.text, it.language) }
}

/** A result callback can originate on DAT's thread, so own its job on main. */
private fun RealityViewModel.launchDisplayImageLoad(retry: () -> Unit, load: suspend (Long) -> Unit) {
    viewModelScope.launch(Dispatchers.Main.immediate) {
        if (state.value.busy || !metaController.authenticated()) return@launch
        val revision = metaController.generation.revision
        val screen = renderRevision
        setBusy(true)
        val request = viewModelScope.launch(start = CoroutineStart.LAZY) {
            try {
                load(revision)
            } catch (failure: Exception) {
                if (failure is CancellationException) throw failure
                if (acceptsDisplayImage(revision, screen)) showError(copy(R.string.meta_image_failed), retry = retry)
            } finally {
                if (galleryImageJob === currentCoroutineContext()[Job]) {
                    galleryImageJob = null
                    setBusy(false)
                }
            }
        }
        galleryImageJob = request
        request.start()
    }
}

internal fun RealityViewModel.cancelDisplayImageLoad() {
    val request = galleryImageJob ?: return
    galleryImageJob = null
    request.cancel()
    setBusy(false)
}

private fun RealityViewModel.acceptsDisplayImage(revision: Long, screen: Long): Boolean = metaController.generation.accepts(revision) && metaController.authenticated() && renderRevision == screen
