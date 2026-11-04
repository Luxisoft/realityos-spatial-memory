package com.luxisoft.realityos

import android.net.Uri
import com.luxisoft.realityos.data.JsonApi
import com.luxisoft.realityos.data.SessionJsonApi
import com.luxisoft.realityos.data.get
import com.luxisoft.realityos.data.patch
import com.luxisoft.realityos.data.post
import org.json.JSONArray
import org.json.JSONObject

internal data class AuthoredText(val source: String, val translations: Map<String, String> = emptyMap()) {
    fun display(language: String = LocalizedText.languageTag): String = translations[language] ?: source

    companion object {
        fun read(row: JSONObject, field: String): AuthoredText {
            val source = row.optText(field).orEmpty()
            val translations = row.optJSONObject("display_text")?.optJSONObject(field)
            return AuthoredText(
                source,
                buildMap {
                    if (translations != null) {
                        for (language in listOf("en", "es")) {
                            translations.optText(language)?.let { put(language, it) }
                        }
                    }
                }
            )
        }
    }
}

internal data class PublicationLabel(val id: String, val name: AuthoredText)
internal data class WorkGroup(val id: String, val name: String, val role: String, val canInvite: Boolean)
internal data class GroupCreated(val id: String, val joinPin: String)
internal data class PublicationSummary(
    val id: String,
    val workspaceId: String,
    val caption: AuthoredText,
    val note: AuthoredText,
    val noteSource: String,
    val mimeType: String,
    val mediaUrl: String,
    val thumbnailUrl: String,
    val ownerName: String,
    val publishedAt: String,
    val owned: Boolean,
    val liked: Boolean,
    val category: PublicationLabel?,
    val tags: List<PublicationLabel>
) {
    val classification: PublicationClassification get() = PublicationClassification(category?.id.orEmpty(), tags.map { it.id }.toSet())
    fun classificationText(): String = buildList {
        category?.name?.display()?.takeIf(String::isNotBlank)?.let(::add)
        addAll(tags.map { "#" + it.name.display() })
    }.joinToString(" · ")

    companion object {
        fun read(row: JSONObject): PublicationSummary = PublicationSummary(
            row.optText("id").orEmpty(), row.optText("workspace_id").orEmpty(),
            AuthoredText.read(row, "caption"), AuthoredText.read(row, "note_text"),
            row.optText("note_source").orEmpty(), row.optText("mime_type").orEmpty(),
            row.optText("media_url").orEmpty(), row.optText("thumbnail_url").orEmpty(),
            row.optJSONObject("owner")?.optText("display_name").orEmpty(), row.optText("published_at").orEmpty(),
            row.optBoolean("owned"), row.optBoolean("liked"),
            row.optJSONObject("category")?.let(::label), labels(row.optJSONArray("tags"))
        )

        fun label(row: JSONObject): PublicationLabel = PublicationLabel(row.optText("id").orEmpty(), AuthoredText.read(row, "name"))
        fun labels(rows: JSONArray?): List<PublicationLabel> = List(rows?.length() ?: 0) { label(rows!!.getJSONObject(it)) }
    }
}

internal data class GalleryPage(val publications: List<PublicationSummary>, val nextCursor: String?)
internal data class CatalogTerm(val id: String, val name: AuthoredText, val active: Boolean, val workspaceName: String) {
    fun display(showWorkspace: Boolean = false): String = name.display() + if (showWorkspace && workspaceName.isNotBlank()) " · $workspaceName" else ""
}

internal data class PublicationCatalog(
    val categories: List<CatalogTerm> = emptyList(),
    val tags: List<CatalogTerm> = emptyList(),
    val owners: List<CatalogTerm> = emptyList(),
    val canManage: Boolean = false
) {
    companion object {
        fun read(row: JSONObject): PublicationCatalog {
            fun terms(key: String): List<CatalogTerm> {
                val rows = row.optJSONArray(key) ?: JSONArray()
                return List(rows.length()) {
                    val term = rows.getJSONObject(it)
                    CatalogTerm(term.getString("id"), AuthoredText.read(term, "name"), term.optBoolean("active", true), term.optText("workspace_name").orEmpty())
                }
            }
            return PublicationCatalog(terms("categories"), terms("tags"), terms("owners"), row.optBoolean("can_manage"))
        }
    }
}

/** All publication and group wire contracts live here; no fixture catalog is consulted. */
internal class GalleryRepository(private val api: JsonApi = SessionJsonApi()) {
    suspend fun catalog(workspaceId: String): PublicationCatalog = PublicationCatalog.read(JSONObject(api.get("groups/$workspaceId/publication-catalog")))

    suspend fun filterOptions(workspaceId: String?): PublicationCatalog = PublicationCatalog.read(
        JSONObject(api.get("gallery/filter-options" + (workspaceId?.let { "?workspace_id=${Uri.encode(it)}" } ?: "")))
    )

    suspend fun saveCatalogTerm(workspaceId: String, editing: CatalogTerm?, kind: String, name: String, active: Boolean) {
        val path = "groups/$workspaceId/publication-catalog/" + (editing?.id ?: kind)
        api.exchange(path, if (editing == null) "POST" else "PATCH", JSONObject().put("name", name).put("active", active))
    }

    suspend fun page(workspaceId: String?, cursor: String?, filters: GalleryFilterSelection): GalleryPage {
        val path = "gallery/page?limit=30" +
            (workspaceId?.let { "&workspace_id=${Uri.encode(it)}" } ?: "") +
            (cursor?.let { "&cursor=${Uri.encode(it)}" } ?: "") + "&" + filters.query()
        val result = JSONObject(api.get(path))
        val rows = result.getJSONArray("items")
        return GalleryPage(List(rows.length()) { PublicationSummary.read(rows.getJSONObject(it)) }, result.optText("next_cursor"))
    }

    suspend fun groups(): List<WorkGroup> {
        val rows = JSONArray(api.get("workspaces"))
        return List(rows.length()) {
            val row = rows.getJSONObject(it)
            WorkGroup(row.getString("id"), row.getString("name"), row.optString("role"), row.optBoolean("can_invite"))
        }.filterNot { it.name.startsWith("home:") }
    }

    suspend fun comments(publicationId: String): List<ViewerComment> {
        val rows = JSONArray(api.get("gallery/$publicationId/comments"))
        return List(rows.length()) {
            val row = rows.getJSONObject(it)
            ViewerComment(row.getString("id"), row.getString("text"))
        }
    }

    suspend fun interact(publicationId: String, action: String, text: String, parentId: String?) {
        api.post(
            "gallery/$publicationId/interactions",
            JSONObject().put("action", action).put("text", text).apply {
                parentId?.let { put("parent_id", it) }
            }
        )
    }

    suspend fun share(publicationId: String, workspaceId: String, classification: PublicationClassification) {
        api.post("gallery/$publicationId/share", classification.json().put("workspace_id", workspaceId))
    }

    suspend fun remove(publicationId: String) {
        api.post("gallery/$publicationId/remove")
    }

    suspend fun classify(publication: PublicationSummary, value: PublicationClassification): PublicationSummary {
        val result = JSONObject(api.patch("gallery/${publication.id}/classification", value.json()))
        return publication.copy(category = result.optJSONObject("category")?.let(PublicationSummary::label), tags = PublicationSummary.labels(result.optJSONArray("tags")))
    }

    suspend fun invite(workspaceId: String): String = JSONObject(api.post("groups/$workspaceId/invite")).getString("code")
    suspend fun pin(workspaceId: String): String = JSONObject(api.get("groups/$workspaceId/pin")).getString("join_pin")

    suspend fun createGroup(name: String, categories: List<String>, tags: List<String>): GroupCreated {
        val row = JSONObject(api.post("groups", JSONObject().put("name", name).put("categories", JSONArray(categories)).put("tags", JSONArray(tags))))
        return GroupCreated(row.getString("id"), row.optString("join_pin"))
    }

    suspend fun joinGroup(code: String): String {
        val pin = GroupJoinPolicy.route(code) == GroupJoinPolicy.Route.PIN
        val row = JSONObject(api.post(if (pin) "groups/join-by-pin" else "groups/join", JSONObject().put(if (pin) "pin" else "code", code)))
        return row.optText("workspace_id") ?: row.getString("id")
    }
}
