package com.luxisoft.realityos

import android.net.Uri
import java.time.LocalDate
import java.time.ZoneId
import org.json.JSONArray
import org.json.JSONObject

internal data class PublicationClassification(val categoryId: String = "", val tagIds: Set<String> = emptySet()) {
    val complete: Boolean get() = categoryId.isNotBlank() && tagIds.isNotEmpty()
    fun json(): JSONObject = JSONObject().put("category_id", categoryId).put("tag_ids", JSONArray(tagIds.toList()))
}

internal data class GalleryFilterSelection(
    val categories: Set<String> = emptySet(),
    val tags: Set<String> = emptySet(),
    val owners: Set<String> = emptySet(),
    val from: LocalDate? = null,
    val through: LocalDate? = null,
    val text: String = ""
) {
    val active: Boolean get() = categories.isNotEmpty() || tags.isNotEmpty() || owners.isNotEmpty() || from != null || through != null || text.isNotBlank()
    val valid: Boolean get() = from == null || through == null || !through.isBefore(from)
    fun query(zone: ZoneId = ZoneId.systemDefault()): String = buildList {
        categories.sorted().forEach { add("category_ids=" + Uri.encode(it)) }
        tags.sorted().forEach { add("tag_ids=" + Uri.encode(it)) }
        owners.sorted().forEach { add("owner_ids=" + Uri.encode(it)) }
        from?.let { add("published_from=" + Uri.encode(it.atStartOfDay(zone).toInstant().toString())) }
        through?.let { add("published_before=" + Uri.encode(it.plusDays(1).atStartOfDay(zone).toInstant().toString())) }
        if (text.isNotBlank()) add("description_q=" + Uri.encode(text.trim()))
    }.joinToString("&")
}
