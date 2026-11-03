package com.luxisoft.realityos

import org.json.JSONArray
import org.json.JSONObject

internal fun decodeGalleryThumb(item: JSONObject): GalleryThumb? {
    val thumb = item.optText("thumbnail_url") ?: return null
    return GalleryThumb(
        thumbnailUrl = thumb, mediaUrl = item.optText("media_url") ?: thumb,
        caption = item.optText("caption").orEmpty(), boxedUrl = item.optText("boxed_url").orEmpty(),
        imageUrl = item.optText("image_url").orEmpty(), mediaId = item.optText("media_id").orEmpty(),
        evidenceId = item.optText("evidence_id").orEmpty(), mimeType = item.optText("mime_type") ?: "image/jpeg",
        frameTimestampMs = if (item.isNull("frame_timestamp_ms")) null else item.optLong("frame_timestamp_ms"),
        noteText = item.optText("note_text").orEmpty(), noteSource = item.optText("note_source").orEmpty(),
        matchedLabels = item.optJSONArray("matched_labels")?.let { a -> (0 until a.length()).map { a.getString(it) } } ?: emptyList(),
        confidence = if (item.isNull("confidence")) null else item.optDouble("confidence"),
        publishedAt = item.optText("published_at").orEmpty(),
        simulated = item.optBoolean("simulated"),
        matchKind = item.optText("match_kind").orEmpty(),
        localizationQuality = item.optText("localization_quality").orEmpty(),
        localizedInformation = item.optJSONObject("localized_information")?.let { values ->
            listOf("en", "es").mapNotNull { language ->
                val info = values.optJSONObject(language) ?: return@mapNotNull null
                language to decodeEvidenceText(info)
            }.toMap()
        } ?: emptyMap()
    )
}

internal fun GalleryThumb.toJson(): JSONObject = JSONObject()
    .put(
        "localized_information",
        JSONObject().apply {
            localizedInformation.forEach { (language, info) -> put(language, JSONObject().put("title", info.title).put("note_text", info.note).put("matched_labels", JSONArray(info.labels)).put("simulated", info.simulated)) }
        }
    )
    .put("thumbnail_url", thumbnailUrl).put("media_url", mediaUrl).put("caption", caption.take(400))
    .put("boxed_url", boxedUrl).put("image_url", imageUrl).put("media_id", mediaId.ifBlank { null })
    .put("evidence_id", evidenceId.ifBlank { null }).put("mime_type", mimeType)
    .put("frame_timestamp_ms", frameTimestampMs ?: JSONObject.NULL).put("note_text", noteText)
    .put("note_source", noteSource).put("matched_labels", JSONArray(matchedLabels))
    .put("match_kind", matchKind.ifBlank { null }).put("localization_quality", localizationQuality.ifBlank { null })
    .put("confidence", confidence ?: JSONObject.NULL).put("published_at", publishedAt).put("simulated", simulated)

/** Map one `/v1/faces/search` match to an inline chat thumbnail. */
internal fun decodeFaceThumb(match: JSONObject?): GalleryThumb? {
    match ?: return null
    val evidence = match.optJSONObject("evidence") ?: return null
    val thumb = match.optText("picture_url") ?: return null
    val badge = if (match.optText("match_type") == "possible_acquaintance") "possible_acquaintance" else "direct"
    return GalleryThumb(
        thumbnailUrl = thumb,
        mediaUrl = thumb,
        caption = match.optText("display_name").orEmpty(),
        mediaId = "",
        profileUserId = normalizedProfileId(match.optText("user_id")).orEmpty(),
        matchedLabels = listOf(badge),
        confidence = if (match.isNull("similarity")) null else match.optDouble("similarity")
    )
}

/** Map one `/v1/faces/search` record match to an inline chat thumbnail. */
internal fun decodeRecordFaceThumb(match: JSONObject?): GalleryThumb? {
    match ?: return null
    val evidence = match.optJSONObject("evidence") ?: return null
    val thumb = evidence.optText("thumbnail_url") ?: return null
    return GalleryThumb(
        thumbnailUrl = thumb,
        mediaUrl = thumb,
        caption = match.optText("title").orEmpty(),
        mediaId = evidence.optText("media_id").orEmpty(),
        recordId = match.optText("record_id").orEmpty(),
        matchedLabels = listOf("record_candidate"),
        confidence = if (match.isNull("similarity")) null else match.optDouble("similarity"),
        simulated = match.optBoolean("simulated"),
        faceDisplayKind = "face_record_enrollment"
    )
}

/**
 * History keeps gallery items anchored to evidence, plus face matches, which
 * legitimately carry no gallery evidence id (their thumbnails live under the
 * faces arm). Unanchored gallery items are still dropped.
 */
internal fun keepHistoryThumb(thumb: GalleryThumb): Boolean = thumb.evidenceId.isNotBlank() || (thumb.thumbnailUrl.contains("/v1/profiles/") && thumb.thumbnailUrl.endsWith("/avatar")) || thumb.thumbnailUrl.contains("/v1/faces/record-enrollments/")

/** Inline chat label for one face match: name plus similarity percent. */
internal fun faceMatchLabel(caption: String, confidence: Double?): String = "$caption (${((confidence ?: 0.0) * 100).toInt()}%)"

/** Enrollment behind one `/v1/faces/search` match, for signed Display thumbnails. */
internal fun faceMatchEnrollmentId(match: JSONObject?): String = match?.optJSONObject("evidence")?.optText("enrollment_id").orEmpty()

/** Probe box behind one `/v1/faces/search` match, or null when absent or flat. */
internal fun faceMatchProbeBox(match: JSONObject?): FaceProbeBox? {
    match ?: return null
    if (match.isNull("probe_box") || match.isNull("probe_face_index")) return null
    val box = match.optJSONObject("probe_box") ?: return null
    val x = box.optDouble("x", Double.NaN)
    val y = box.optDouble("y", Double.NaN)
    val width = box.optDouble("width", Double.NaN)
    val height = box.optDouble("height", Double.NaN)
    if (!x.isFinite() || !y.isFinite() || !width.isFinite() || !height.isFinite()) return null
    if (width <= 0.0 || height <= 0.0) return null
    return FaceProbeBox(x.toFloat(), y.toFloat(), width.toFloat(), height.toFloat(), match.optInt("probe_face_index"))
}

/**
 * One numbered row per match: numbers follow distinct probe faces in match
 * order, so matches sharing a face share its number and color.
 */
internal fun faceGroupRows(thumbs: List<GalleryThumb>, palette: List<String>): List<FaceGroupRow> {
    if (palette.isEmpty()) return emptyList()
    val numbers = mutableMapOf<Int, Int>()
    return thumbs.mapNotNull { thumb ->
        val box = thumb.probeBox ?: return@mapNotNull null
        val number = numbers.getOrPut(box.faceIndex) { numbers.size + 1 }
        val colorIndex = (number - 1) % palette.size
        FaceGroupRow(number, palette[colorIndex], colorIndex, thumb)
    }
}

/** One box per distinct probe face, in row order. */
internal fun faceGroupMarks(rows: List<FaceGroupRow>): List<FaceGroupMark> {
    val seen = mutableSetOf<Int>()
    return rows.mapNotNull { row ->
        val box = row.thumb.probeBox ?: return@mapNotNull null
        if (!seen.add(box.faceIndex)) return@mapNotNull null
        FaceGroupMark(row.number, box, row.colorHex)
    }
}

internal fun faceGroupMarksJson(marks: List<FaceGroupMark>): String = marks.joinToString(",", "[", "]") { mark ->
    "{\"box\":{\"x\":${mark.box.x},\"y\":${mark.box.y},\"width\":${mark.box.width},\"height\":${mark.box.height}}," +
        "\"color\":\"${mark.colorHex}\",\"number\":${mark.number}}"
}

internal fun ChatMessage.viewerItems(): List<GalleryThumb> = buildList {
    evidenceUrl?.let { add(GalleryThumb(it, it, caption = "", imageUrl = it, mediaId = evidenceMediaId, simulated = simulated)) }
    addAll(gallery)
}.distinctBy { it.mediaId.ifBlank { it.viewerUrl } }.let(::orderedEvidence)

internal fun videoStartMs(timestampMs: Long): Long = (timestampMs - 3000L).coerceAtLeast(0L)
internal fun evidenceTime(timestampMs: Long): String {
    val seconds = timestampMs / 1000
    return "%02d:%02d:%02d".format(seconds / 3600, seconds / 60 % 60, seconds % 60)
}
