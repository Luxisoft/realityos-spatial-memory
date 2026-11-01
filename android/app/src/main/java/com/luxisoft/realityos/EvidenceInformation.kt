package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.runInterruptible
import kotlinx.coroutines.withTimeout
import org.json.JSONArray
import org.json.JSONObject

internal data class EvidenceText(val title: String, val note: String, val labels: List<String>, val simulated: Boolean = false)

/** Person captions are proper names; object descriptions need a saved translation. */
internal fun displayEvidenceInformation(item: GalleryThumb?, language: String): EvidenceText? {
    if (item == null) return null
    return if (item.faceEnrollmentId.isNotBlank()) EvidenceText(item.caption, item.noteText, item.matchedLabels, item.simulated) else item.localizedInformation[language]
}

internal data class EvidenceTextState(val values: Map<String, EvidenceText> = emptyMap(), val loading: Boolean = true, val failed: Boolean = false, val pending: Boolean = false, val preparing: Boolean = false)

internal fun decodeEvidenceText(item: JSONObject, simulated: Boolean = false): EvidenceText {
    val labels = item.optJSONArray("matched_labels") ?: JSONArray()
    return EvidenceText(item.optText("title").orEmpty(), item.optText("note_text").orEmpty(), (0 until labels.length()).map { labels.getString(it) }, simulated || item.optBoolean("simulated"))
}

internal fun storedEvidenceText(items: List<GalleryThumb>, language: String): Map<String, EvidenceText> = items.mapNotNull { item ->
    item.localizedInformation[language]?.let { item.evidenceId to it }
}.toMap()

@Composable
internal fun rememberEvidenceText(items: List<GalleryThumb>, language: String, retry: Int): EvidenceTextState {
    val selections = items.filter { it.evidenceId.isNotBlank() && it.matchedLabels.isNotEmpty() }.distinctBy { it.evidenceId }.take(6)
    val cached = storedEvidenceText(selections, language)
    val missing = selections.filter { it.evidenceId !in cached }
    val initial = EvidenceTextState(cached, loading = missing.isNotEmpty())
    val state = produceState(initial, selections, language, retry) {
        value = initial
        if (missing.isEmpty()) return@produceState
        try {
            val body = JSONObject().put("language", language).put(
                "items",
                JSONArray().apply {
                    missing.forEach { item -> put(JSONObject().put("evidence_id", item.evidenceId).put("labels", JSONArray(item.matchedLabels))) }
                }
            )
            var response = withTimeout(8000) {
                runInterruptible(Dispatchers.IO) { JSONObject(SocialSession.publicationInformation(body)) }
            }
            if (response.optString("status") == "pending") {
                value = initial.copy(preparing = true)
                response = withTimeout(70000) {
                    runInterruptible(Dispatchers.IO) { JSONObject(SocialSession.publicationInformation(body, prepare = true)) }
                }
            }
            val translated = response.getJSONArray("items")
            val values = cached + (0 until translated.length()).associate { index ->
                val item = translated.getJSONObject(index)
                item.getString("evidence_id") to decodeEvidenceText(item, response.optBoolean("simulated"))
            }
            val incomplete = selections.any { it.evidenceId !in values }
            value = EvidenceTextState(values, loading = false, failed = incomplete, pending = response.optString("status") == "pending")
        } catch (_: TimeoutCancellationException) {
            value = EvidenceTextState(cached, loading = false, failed = true)
        } catch (cancelled: kotlinx.coroutines.CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            value = EvidenceTextState(cached, loading = false, failed = true)
        }
    }
    return state.value
}

@Composable
internal fun RowScope.EvidenceHeader(item: GalleryThumb, language: String) {
    val date = evidenceDate(item.publishedAt, language)
    val percent = evidencePercent(item.confidence, language)
    if (date == null && percent == null) Text(stringResource(R.string.evidence_show_information), color = Color.White)
    if (date != null) {
        Column(Modifier.weight(1f)) {
            Text(stringResource(R.string.evidence_published), style = MaterialTheme.typography.labelSmall, color = Color.LightGray)
            Text(date, style = MaterialTheme.typography.bodySmall, color = Color.White)
        }
    }
    if (percent != null) {
        Column(Modifier.weight(1f)) {
            Text(stringResource(R.string.evidence_confidence), style = MaterialTheme.typography.labelSmall, color = Color.LightGray)
            Text(percent, style = MaterialTheme.typography.bodySmall, color = Color.White)
        }
    }
}

@Composable
internal fun EvidenceInformationBody(item: GalleryThumb, text: EvidenceText?, loading: Boolean, failed: Boolean, pending: Boolean = false, preparing: Boolean = false, onRetry: () -> Unit) {
    var original by remember(evidenceIdentity(item)) { mutableStateOf(false) }
    if (loading && text == null && item.evidenceId.isNotBlank()) {
        val description = stringResource(R.string.evidence_loading)
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (preparing) Text(stringResource(R.string.evidence_preparing_history), color = Color.White, style = MaterialTheme.typography.bodySmall)
            Box(Modifier.clearAndSetSemantics { contentDescription = description }) { SkeletonLines(rows = 3) }
        }
        return
    }
    if (failed && text == null && item.evidenceId.isNotBlank() && !original) {
        Text(stringResource(if (pending) R.string.evidence_information_pending else R.string.evidence_translation_error), color = Color.White)
        Row {
            TextButton(onClick = onRetry) { Text(stringResource(R.string.evidence_retry)) }
            TextButton(onClick = { original = true }) { Text(stringResource(R.string.evidence_show_original)) }
        }
        return
    }
    val title = if (original) item.caption else text?.title.orEmpty()
    val labels = if (original) item.matchedLabels else text?.labels.orEmpty()
    val note = if (original) item.noteText else text?.note.orEmpty()
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        if (original) Text(stringResource(R.string.evidence_original), style = MaterialTheme.typography.labelSmall, color = Color.LightGray)
        Text(title.ifBlank { labels.joinToString().ifBlank { stringResource(R.string.evidence_title) } }, style = MaterialTheme.typography.titleSmall, color = Color.White)
        if (item.simulated || text?.simulated == true) InfoLine(stringResource(R.string.evidence_simulated))
        when (item.matchKind) {
            "exact" -> InfoLine(stringResource(R.string.evidence_exact))
            "family" -> InfoLine(stringResource(R.string.evidence_family))
            "similar" -> InfoLine(stringResource(R.string.evidence_similar))
        }
        if (item.localizationQuality == "approximate_box") InfoLine(stringResource(R.string.evidence_approximate))
        item.frameTimestampMs?.let { InfoLine(stringResource(R.string.evidence_frame_time, evidenceTime(it))) }
        if (labels.isNotEmpty()) InfoLine(stringResource(R.string.evidence_detected, labels.joinToString()))
        if (note.isNotBlank()) {
            InfoLine(stringResource(if (item.noteSource == "voice") R.string.evidence_voice_note else R.string.evidence_note))
            Text(note, style = MaterialTheme.typography.bodyMedium, color = Color.White)
        }
    }
}

@Composable
private fun InfoLine(text: String) {
    Text(text, style = MaterialTheme.typography.labelMedium, color = Color.White.copy(alpha = 0.8f))
}
