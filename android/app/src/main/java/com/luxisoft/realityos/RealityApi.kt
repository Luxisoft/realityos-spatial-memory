package com.luxisoft.realityos

import java.io.BufferedOutputStream
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL
import java.time.Instant
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject

class RealityApiException(message: String) : IOException(message)

data class RemoteSession(val id: String, val status: String)
data class RemoteCapture(val id: String, val mimeType: String)
data class RemoteZone(val id: String, val name: String, val kind: String, val parentId: String?)
data class QueryEvidence(
    val found: Boolean,
    val ambiguous: Boolean,
    val message: String,
    val ttsText: String,
    val highlightedPath: String?,
    val displayMediaPath: String?,
)

data class VirtualDeviceProfile(
    val apiBaseUrl: String,
    val workspaceId: String,
    val workspaceName: String,
    val deviceId: String,
    val deviceKey: String,
    val expiresAt: Instant,
    val processingMode: String,
) {
    fun toProvisioning() = DeviceProvisioning(
        apiBaseUrl = apiBaseUrl,
        workspaceId = workspaceId,
        deviceId = deviceId,
        deviceKey = deviceKey,
        workspaceName = workspaceName,
        expiresAt = expiresAt,
        processingMode = processingMode,
        source = ProvisioningSource.VIRTUAL_LIVE,
    )
}

/**
 * Acquires a real, short-lived device credential for Meta's virtual glasses.
 * It carries no administrator or Meta-model key and is HTTPS-only by design.
 */
object VirtualDeviceBootstrapApi {
    fun fetch(apiBaseUrl: String, installationId: String): VirtualDeviceProfile {
        val normalizedBaseUrl = apiBaseUrl.trim().trimEnd('/')
        val url = URL("$normalizedBaseUrl/virtual-devices/bootstrap")
        require(url.protocol == "https") { "Virtual glasses require an HTTPS RealityOS URL." }
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 20_000
            readTimeout = 30_000
            doInput = true
            setRequestProperty("Accept", "application/json")
            setRequestProperty("X-RealityOS-Installation-ID", installationId)
        }
        return try {
            val payload = responseBody(connection)
            val result = JSONObject(payload)
            VirtualDeviceProfile(
                apiBaseUrl = result.getString("api_base_url"),
                workspaceId = result.getString("workspace_id"),
                workspaceName = result.getString("workspace_name"),
                deviceId = result.getString("device_id"),
                deviceKey = result.getString("device_key"),
                expiresAt = Instant.parse(result.getString("expires_at")),
                processingMode = result.getString("processing_mode"),
            )
        } finally {
            connection.disconnect()
        }
    }
}

/**
 * HTTPS-only client for an enrolled glasses host. It carries an independent
 * device credential and never receives a Meta model key or an administrator token.
 */
class RealityApi(private val provisioning: DeviceProvisioning) {
    private fun endpoint(path: String): URL {
        if (path.startsWith("http://") || path.startsWith("https://")) return URL(path)
        if (path.startsWith('/')) {
            val base = URL(provisioning.apiBaseUrl)
            val port = if (base.port == -1) "" else ":${base.port}"
            return URL("${base.protocol}://${base.host}$port$path")
        }
        return URL("${provisioning.apiBaseUrl.trimEnd('/')}/${path.trimStart('/')}")
    }

    fun absoluteUrl(path: String): String = endpoint(path).toExternalForm()

    private fun connection(path: String, method: String): HttpURLConnection =
        (endpoint(path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 20_000
            readTimeout = 120_000
            doInput = true
            setRequestProperty("X-RealityOS-Device-ID", provisioning.deviceId)
            setRequestProperty("X-RealityOS-Device-Key", provisioning.deviceKey)
            setRequestProperty("Accept", "application/json")
        }

    private fun body(connection: HttpURLConnection): String {
        return responseBody(connection)
    }

    private fun postJson(path: String, json: JSONObject): JSONObject {
        val connection = connection(path, "POST")
        return try {
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            connection.outputStream.bufferedWriter().use { it.write(json.toString()) }
            JSONObject(body(connection))
        } finally {
            connection.disconnect()
        }
    }

    fun listZones(): List<RemoteZone> {
        val connection = connection("device/zones", "GET")
        return try {
            val payload = JSONArray(body(connection))
            buildList {
                for (index in 0 until payload.length()) {
                    val zone = payload.getJSONObject(index)
                    add(
                        RemoteZone(
                            id = zone.getString("id"),
                            name = zone.getString("name"),
                            kind = zone.optString("kind", "zone"),
                            parentId = zone.optString("parent_id").takeIf { it.isNotBlank() },
                        ),
                    )
                }
            }
        } finally {
            connection.disconnect()
        }
    }

    fun openCaptureSession(zoneId: String?): RemoteSession {
        val payload = JSONObject()
        if (!zoneId.isNullOrBlank()) payload.put("zone_id", zoneId.trim())
        val result = postJson("device/sessions", payload)
        return RemoteSession(result.getString("id"), result.getString("status"))
    }

    fun closeCaptureSession(sessionId: String) {
        postJson("device/sessions/$sessionId/close", JSONObject())
    }

    fun uploadCapture(
        sessionId: String,
        bytes: ByteArray,
        filename: String,
        mimeType: String,
        capturedAt: Instant = Instant.now(),
    ): RemoteCapture = uploadCapture(sessionId, filename, mimeType, capturedAt) { output -> output.write(bytes) }

    fun uploadCaptureFile(
        sessionId: String,
        file: File,
        mimeType: String,
        capturedAt: Instant = Instant.now(),
    ): RemoteCapture = uploadCapture(sessionId, file.name, mimeType, capturedAt) { output ->
        file.inputStream().buffered().use { input -> input.copyTo(output, 64 * 1024) }
    }

    private fun uploadCapture(
        sessionId: String,
        filename: String,
        mimeType: String,
        capturedAt: Instant,
        writeContent: (BufferedOutputStream) -> Unit,
    ): RemoteCapture {
        val boundary = "RealityOS-${UUID.randomUUID()}"
        val connection = connection("device/captures", "POST")
        return try {
            connection.doOutput = true
            connection.setChunkedStreamingMode(64 * 1024)
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
            BufferedOutputStream(connection.outputStream).use { output ->
                output.writeFormField(boundary, "session_id", sessionId)
                output.writeFormField(boundary, "captured_at", capturedAt.toString())
                output.writeFileHeader(boundary, "file", filename, mimeType)
                writeContent(output)
                output.write("\r\n--$boundary--\r\n".toByteArray())
            }
            val result = JSONObject(body(connection))
            RemoteCapture(result.getString("id"), result.getString("mime_type"))
        } finally {
            connection.disconnect()
        }
    }

    fun requestProcessing(captureId: String, detailed: Boolean, priorityTerms: List<String> = emptyList()) {
        val terms = JSONArray()
        priorityTerms.filter { it.isNotBlank() }.take(16).forEach { terms.put(it.trim()) }
        postJson(
            "device/captures/$captureId/process",
            JSONObject()
                .put("profile", if (detailed) "detailed" else "basic")
                .put("priority_terms", terms),
        )
    }

    fun query(question: String): QueryEvidence {
        val result = postJson(
            "device/queries",
            JSONObject().put("workspace_id", provisioning.workspaceId).put("question", question.trim()),
        )
        return QueryEvidence(
            found = result.optBoolean("found"),
            ambiguous = result.optBoolean("ambiguous"),
            message = result.optString("message"),
            ttsText = result.optString("tts_text", result.optString("message")),
            highlightedPath = result.optString("highlighted_media_url").takeIf { it.isNotBlank() },
            displayMediaPath = result.optString("display_media_url").takeIf { it.isNotBlank() },
        )
    }

    fun download(path: String): ByteArray {
        val connection = connection(path, "GET")
        return try {
            if (connection.responseCode !in 200..299) body(connection)
            connection.inputStream.use(InputStream::readBytes)
        } finally {
            connection.disconnect()
        }
    }
}

private fun responseBody(connection: HttpURLConnection): String {
    val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
    val payload = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
    if (connection.responseCode !in 200..299) {
        val detail = runCatching { JSONObject(payload).optString("detail") }.getOrNull()
        throw RealityApiException(detail?.takeIf { it.isNotBlank() } ?: "Server returned ${connection.responseCode}.")
    }
    return payload
}

private fun BufferedOutputStream.writeFormField(boundary: String, name: String, value: String) {
    write("--$boundary\r\n".toByteArray())
    write("Content-Disposition: form-data; name=\"$name\"\r\n\r\n".toByteArray())
    write(value.toByteArray())
    write("\r\n".toByteArray())
}

private fun BufferedOutputStream.writeFileHeader(
    boundary: String,
    field: String,
    filename: String,
    mimeType: String,
) {
    write("--$boundary\r\n".toByteArray())
    write("Content-Disposition: form-data; name=\"$field\"; filename=\"${filename.replace("\"", "_")}\"\r\n".toByteArray())
    write("Content-Type: $mimeType\r\n\r\n".toByteArray())
}
