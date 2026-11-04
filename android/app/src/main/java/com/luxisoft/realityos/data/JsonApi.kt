package com.luxisoft.realityos.data

import com.luxisoft.realityos.SocialSession
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Feature repositories own wire formats; screens consume their typed results. */
internal fun interface JsonApi {
    suspend fun exchange(path: String, method: String, payload: JSONObject?): String
}

/** Bind every operation in a screen to the account that opened that screen. */
internal class SessionJsonApi(private val identity: Long = SocialSession.identity) : JsonApi {
    override suspend fun exchange(path: String, method: String, payload: JSONObject?): String = withContext(Dispatchers.IO) {
        SocialSession.requestJson(path, method, payload, identity)
    }
}

internal suspend fun JsonApi.get(path: String): String = exchange(path, "GET", null)
internal suspend fun JsonApi.post(path: String, payload: JSONObject = JSONObject()): String = exchange(path, "POST", payload)
internal suspend fun JsonApi.patch(path: String, payload: JSONObject): String = exchange(path, "PATCH", payload)
