package com.luxisoft.realityos.data

import java.net.HttpURLConnection
import org.json.JSONObject

internal data class HttpResult(val status: Int, val body: String)

/** Executes one attempt. Authentication, session renewal and retries stay with the caller. */
internal object JsonHttpTransport {
    fun exchange(
        connection: HttpURLConnection,
        method: String,
        payload: JSONObject?,
        headers: Map<String, String>,
        timeoutMillis: Int
    ): HttpResult = try {
        connection.requestMethod = method
        connection.connectTimeout = minOf(15000, timeoutMillis)
        connection.readTimeout = timeoutMillis
        headers.forEach(connection::setRequestProperty)
        if (payload != null) {
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.bufferedWriter().use { it.write(payload.toString()) }
        }
        val status = connection.responseCode
        val stream = if (status in 200..299) connection.inputStream else connection.errorStream
        HttpResult(status, stream?.bufferedReader()?.use { it.readText() }.orEmpty())
    } finally {
        connection.disconnect()
    }
}
