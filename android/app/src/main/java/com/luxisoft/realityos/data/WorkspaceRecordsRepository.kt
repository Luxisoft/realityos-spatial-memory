package com.luxisoft.realityos

import com.luxisoft.realityos.data.JsonApi
import com.luxisoft.realityos.data.SessionJsonApi
import com.luxisoft.realityos.data.get
import com.luxisoft.realityos.data.post
import java.net.URLEncoder
import java.time.Instant
import org.json.JSONArray
import org.json.JSONObject

internal data class WorkspaceRecord(
    val id: String,
    val externalId: String,
    val title: AuthoredText,
    val kind: String,
    val version: Int,
    val occurredAt: String,
    val biometricAuthorized: Boolean
) {
    companion object {
        fun read(row: JSONObject): WorkspaceRecord = WorkspaceRecord(
            row.getString("id"),
            row.getString("external_id"),
            AuthoredText.read(row, "title"),
            row.getString("kind"),
            row.optInt("version", 1),
            row.optString("occurred_at"),
            row.optBoolean("biometric_authorized")
        )
    }
}

internal data class RecordNote(val text: String, val occurredAt: String)
internal data class RecordDetails(
    val record: WorkspaceRecord,
    val related: List<WorkspaceRecord>,
    val notes: List<RecordNote>,
    private val document: JSONObject
) {
    fun fields(language: String = LocalizedText.languageTag): List<Pair<String, String>> {
        val values = document.storedValue("data", language) as? JSONObject ?: JSONObject()
        return values.keys().asSequence().map { it to values.opt(it)?.toString().orEmpty() }.toList()
    }

    /** Compatibility input for the isolated enrollment widget. */
    fun legacyDocument(): JSONObject = document

    companion object {
        fun read(row: JSONObject): RecordDetails {
            fun <T> rows(name: String, read: (JSONObject) -> T): List<T> {
                val rows = row.optJSONArray(name) ?: JSONArray()
                return List(rows.length()) { read(rows.getJSONObject(it)) }
            }
            return RecordDetails(
                WorkspaceRecord.read(row),
                rows("related", WorkspaceRecord::read),
                rows("notes") { RecordNote(it.getString("text"), it.getString("occurred_at")) },
                row
            )
        }
    }
}

internal class WorkspaceRecordsRepository(
    workspaceId: String,
    private val api: JsonApi = SessionJsonApi()
) {
    private val base = "workspaces/$workspaceId/records"

    suspend fun list(query: String, offset: Int): List<WorkspaceRecord> {
        val rows = JSONArray(api.get("$base?q=${URLEncoder.encode(query, "UTF-8")}&offset=$offset"))
        return List(rows.length()) { WorkspaceRecord.read(rows.getJSONObject(it)) }
    }

    suspend fun detail(id: String): RecordDetails = RecordDetails.read(JSONObject(api.get("$base/$id")))

    suspend fun addNote(id: String, text: String): RecordDetails {
        api.post("$base/$id/notes", JSONObject().put("text", text).put("occurred_at", Instant.now().toString()))
        return detail(id)
    }
}
