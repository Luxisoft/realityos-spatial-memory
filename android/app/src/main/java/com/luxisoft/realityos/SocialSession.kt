package com.luxisoft.realityos

import androidx.compose.runtime.*
import com.luxisoft.realityos.data.JsonHttpTransport
import com.luxisoft.realityos.data.SessionCredentials
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Human sessions are independent from the wearable's device credential. */
internal object SocialSession {
    private var preferences: android.content.SharedPreferences? = null
    private val sessionLock = Any()
    private val refreshLock = Any()
    private var sessionGeneration by mutableStateOf(0L)
    private var refreshToken: String? = null

    @Volatile
    var token: String? = null
    var active by mutableStateOf(false)
    var isGuest by mutableStateOf(false)

    // True only between a fresh Facebook login and capture/verification: it must
    // survive the login-gate -> host-shell SocialGallery instance switch.
    var freshLogin by mutableStateOf(false)
    var passwordAccount by mutableStateOf(false)
    var passwordAccountConfirmed by mutableStateOf(false)
    val accountEntryAllowed: Boolean get() = passwordAccount && passwordAccountConfirmed
    var localAccount by mutableStateOf(false)
    var localAccountConfirmed by mutableStateOf(false)
    val localEntryAllowed: Boolean get() = LocalAccessPolicy.canSkipFaceEntry(
        BuildConfig.DEBUG,
        BuildConfig.LOCAL_DEVELOPMENT,
        BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
        localAccount && localAccountConfirmed
    )

    // One-shot notice for the login screen: denial/expiry messages are set in the
    // host-shell instance but shown in the login-gate instance after the switch.
    var loginNotice: String? = null
    var workWorkspaceId: String? = null
    var workspaceId: String? = null
    var profilePictureUrl by mutableStateOf<String?>(null)
    fun initialize(context: android.content.Context) {
        preferences = androidx.security.crypto.EncryptedSharedPreferences.create(
            context,
            "realityos-facebook-session",
            androidx.security.crypto.MasterKey.Builder(context).setKeyScheme(androidx.security.crypto.MasterKey.KeyScheme.AES256_GCM).build(),
            androidx.security.crypto.EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            androidx.security.crypto.EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        // Facebook user IDs and grants belong to a particular Meta app.
        // Never resume a session created for a different App ID.
        if (preferences?.getString("facebook_app_id", null) != BuildConfig.FACEBOOK_APP_ID) {
            clear()
            return
        }
        val savedBase = preferences?.getString("session_api_base", null)
        if (savedBase != null && savedBase != BuildConfig.DEFAULT_REALITYOS_API_BASE_URL) {
            clear()
            return
        }
        localAccount = BuildConfig.LOCAL_DEVELOPMENT && preferences?.getBoolean("local_account", false) == true
        localAccountConfirmed = false
        passwordAccount = preferences?.getBoolean("password_account", false) == true
        passwordAccountConfirmed = false
        token = preferences?.getString("access", null)
        refreshToken = preferences?.getString("refresh", null)
        workspaceId = preferences?.getString("workspace", null)
        isGuest = preferences?.getBoolean("guest", false) == true && token != null
        active = token != null && refreshToken != null && workspaceId != null
    }
    fun remember(credentials: SessionCredentials) = remember(credentials.toJson())

    fun remember(response: JSONObject) = synchronized(sessionLock) {
        sessionGeneration++
        rememberTokens(response)
    }
    private fun rememberTokens(response: JSONObject) {
        token = response.getString("access_token")
        refreshToken = response.getString("refresh_token")
        isGuest = response.optBoolean("is_guest")
        if (response.has("password_account")) {
            passwordAccount = response.optBoolean("password_account")
            passwordAccountConfirmed = passwordAccount
        }
        if (response.has("local_access")) {
            localAccount = LocalAccessPolicy.canSkipFaceEntry(
                BuildConfig.DEBUG,
                BuildConfig.LOCAL_DEVELOPMENT,
                BuildConfig.DEFAULT_REALITYOS_API_BASE_URL,
                response.optBoolean("local_access")
            )
            localAccountConfirmed = localAccount
        }
        preferences?.edit()?.putString("access", token)?.putString("refresh", refreshToken)
            ?.putBoolean("password_account", passwordAccount)
            ?.putBoolean("local_account", localAccount)
            ?.putString("session_api_base", BuildConfig.DEFAULT_REALITYOS_API_BASE_URL)
            ?.putString("facebook_app_id", BuildConfig.FACEBOOK_APP_ID)
            ?.putString("workspace", workspaceId)?.putBoolean("guest", isGuest)?.apply()
    }
    fun clear(): Unit = synchronized(sessionLock) {
        sessionGeneration++
        AppNotices.pending.value = emptyList()
        active = false
        token = null
        refreshToken = null
        workspaceId = null
        isGuest = false
        workWorkspaceId = null
        profilePictureUrl = null
        freshLogin = false
        localAccount = false
        localAccountConfirmed = false
        passwordAccount = false
        passwordAccountConfirmed = false
        loginNotice = null
        preferences?.edit()?.clear()?.apply()
    }
    val identity: Long get() = synchronized(sessionLock) { sessionGeneration }
    fun isCurrent(identity: Long): Boolean = synchronized(sessionLock) { identity == sessionGeneration }
    fun requireCurrent(identity: Long) {
        sessionSnapshot(identity)
    }
    fun clearIfCurrent(identity: Long): Unit = synchronized(sessionLock) {
        if (identity == sessionGeneration) clear()
    }
    suspend fun signOut() {
        val session = sessionSnapshot()
        try {
            withContext(Dispatchers.IO) {
                runCatching { requestOnce("auth/logout", "POST", JSONObject(), false, 5000, session) }
            }
        } finally {
            if (isCurrent(session.generation)) {
                clearIfCurrent(session.generation)
                // Local Debug deliberately never initializes the Facebook SDK.
                if (!BuildConfig.LOCAL_DEVELOPMENT && com.facebook.FacebookSdk.isInitialized()) {
                    runCatching { com.facebook.login.LoginManager.getInstance().logOut() }
                }
            }
        }
    }
    fun refreshAccess(identity: Long, rejectedAccess: String): String {
        val session = sessionSnapshot(identity)
        return requireNotNull(refreshSession(session.copy(access = rejectedAccess)).access)
    }
    private data class RequestSession(val generation: Long, val access: String?, val refresh: String?)
    private fun sessionSnapshot(generation: Long? = null): RequestSession = synchronized(sessionLock) {
        check(generation == null || generation == sessionGeneration) { localizedText(R.string.storage_session_changed) }
        RequestSession(sessionGeneration, token, refreshToken)
    }
    private fun expireSession(session: RequestSession): Nothing = synchronized(sessionLock) {
        sessionSnapshot(session.generation)
        // A late rejection must not erase credentials renewed by another request.
        check(token == session.access && refreshToken == session.refresh) { localizedText(R.string.storage_session_changed) }
        val wasGuest = isGuest || passwordAccount
        val message = if (wasGuest) localizedText(R.string.ui_your_session_expired_sign_in_again) else localizedText(R.string.ui_your_session_expired_continue_with_facebook_again)
        clear()
        loginNotice = message
        error(message)
    }
    private fun refreshSession(session: RequestSession, timeoutMillis: Int = 30000): RequestSession = synchronized(refreshLock) {
        val current = sessionSnapshot(session.generation)
        // Profile, connections, chat and uploads share one rotating refresh token.
        // Reuse a completed renewal; never submit that one-use token twice.
        if (current.access != session.access || current.refresh != session.refresh) return@synchronized current
        if (current.refresh == null) expireSession(current)
        val refreshed = JSONObject(requestOnce("auth/refresh", "POST", JSONObject().put("refresh_token", current.refresh), false, timeoutMillis, current))
        synchronized(sessionLock) {
            sessionSnapshot(session.generation)
            rememberTokens(refreshed)
            sessionSnapshot(session.generation)
        }
    }
    fun request(path: String, payload: JSONObject? = null, identity: Long = this.identity): String = requestJson(path, if (payload == null) "GET" else "POST", payload, identity)
    fun searchWorkspaceRecords(workspaceId: String, payload: JSONObject): String = requestOnce(
        "workspaces/$workspaceId/records/search",
        "POST",
        payload,
        true,
        180000
    )

    fun chatTranslations(payload: JSONObject? = null, ids: List<Int> = emptyList()): String = requestOnce(
        if (payload != null) "chat/history/prepare" else "chat/history/translations?ids=${ids.joinToString(",")}",
        if (payload != null) "POST" else "GET",
        payload,
        true,
        5000
    )

    fun publicationInformation(payload: JSONObject, prepare: Boolean = false): String = requestOnce(
        if (prepare) "gallery/evidence/information/prepare" else "gallery/evidence/information",
        "POST",
        payload,
        true,
        if (prepare) 60000 else 4000
    )

    fun requestJson(path: String, method: String, payload: JSONObject? = null, identity: Long = this.identity): String = requestOnce(path, method, payload, true, session = sessionSnapshot(identity))
    internal var openJsonConnection: (String) -> HttpURLConnection = { path ->
        URL("${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/$path").openConnection() as HttpURLConnection
    }
    private fun requestOnce(path: String, method: String, payload: JSONObject?, mayRefresh: Boolean, timeoutMillis: Int = 30000, session: RequestSession = sessionSnapshot()): String {
        sessionSnapshot(session.generation)
        val headers = buildMap {
            put("X-Client-Version", BuildConfig.VERSION_NAME)
            if (path in setOf("auth/register", "auth/resend-confirmation", "auth/forgot-password", "auth/change-pending-email")) put("Accept-Language", AccountRequestLanguage.value)
            session.access?.let { put("Authorization", "Bearer $it") }
        }
        val result = JsonHttpTransport.exchange(openJsonConnection(path), method, payload, headers, timeoutMillis)
        sessionSnapshot(session.generation)
        val authenticatedAccountRoute = path in setOf("auth/me", "auth/local-session", "auth/account-session", "auth/account-capture-profile", "auth/logout")
        if (result.status == 409 && path in setOf("auth/register", "auth/change-pending-email")) {
            accountConflict(path, 409, result.body)?.let { throw it }
        }
        if (result.status !in 200..299) accountFailure(path, result.status)?.let { throw it }
        if (result.status == 401 && mayRefresh && session.refresh != null && (!path.startsWith("auth/") || authenticatedAccountRoute)) {
            val renewed = refreshSession(session, timeoutMillis)
            return requestOnce(path, method, payload, false, timeoutMillis, renewed)
        }
        if (result.status == 401 && path != "auth/logout" && (path == "auth/refresh" || session.refresh == null && (!path.startsWith("auth/") || authenticatedAccountRoute))) expireSession(session)
        if (result.status !in 200..299) error(localizedText(R.string.ui_could_not_complete_the_request_1_d, result.status))
        return result.body
    }

    /** Stream captured clips from private storage; retries reuse the caller's request key. */
    fun requestMultipartFile(path: String, fields: Map<String, String>, file: File, mime: String): String = multipartFileOnce(path, fields, file, mime, true)

    private fun multipartFileOnce(path: String, fields: Map<String, String>, file: File, mime: String, mayRefresh: Boolean, session: RequestSession = sessionSnapshot()): String {
        sessionSnapshot(session.generation)
        val boundary = "RealityOS-${java.util.UUID.randomUUID()}"
        val connection = openJsonConnection(path)
        connection.requestMethod = "POST"
        connection.connectTimeout = 15000
        connection.readTimeout = 60000
        connection.doOutput = true
        connection.setChunkedStreamingMode(64 * 1024)
        connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
        session.access?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
        return try {
            connection.outputStream.buffered().use { output ->
                fun text(value: String) = output.write(value.toByteArray(Charsets.UTF_8))
                fields.forEach { (name, value) ->
                    text("--$boundary\r\nContent-Disposition: form-data; name=\"$name\"\r\n\r\n$value\r\n")
                }
                text("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"${file.name}\"\r\nContent-Type: $mime\r\n\r\n")
                file.inputStream().use { it.copyTo(output) }
                text("\r\n--$boundary--\r\n")
            }
            val status = connection.responseCode
            sessionSnapshot(session.generation)
            if (status == 401 && mayRefresh && session.refresh != null) {
                val renewed = refreshSession(session)
                multipartFileOnce(path, fields, file, mime, false, renewed)
            } else {
                if (status == 401 && session.refresh == null) expireSession(session)
                check(connection.responseCode in 200..299) { localizedText(R.string.ui_upload_failed_1_d, connection.responseCode) }
                connection.inputStream.bufferedReader().use { it.readText() }.also { sessionSnapshot(session.generation) }
            }
        } finally {
            connection.disconnect()
        }
    }

    fun requestMultipart(path: String, fields: Map<String, String>, fileBytes: ByteArray, filename: String, mimeType: String, fieldName: String? = null): String = requestMultipartOnce(path, fields, fileBytes, filename, mimeType, fieldName, true)
    private fun requestMultipartOnce(path: String, fields: Map<String, String>, fileBytes: ByteArray, filename: String, mimeType: String, requestedFieldName: String?, mayRefresh: Boolean, session: RequestSession = sessionSnapshot()): String {
        sessionSnapshot(session.generation)
        val boundary = "RealityOS-${java.util.UUID.randomUUID()}"
        val fieldName = requestedFieldName ?: if (path == "faces/search" || path == "display/face-group-links") "probe" else "file"
        val connection = openJsonConnection(path)
        connection.requestMethod = "POST"
        connection.setRequestProperty("X-Client-Version", BuildConfig.VERSION_NAME)
        connection.connectTimeout = 15000
        // Image identification and evidence matching can require several provider calls.
        connection.readTimeout = if (path == "queries/image") 180000 else 60000
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
        session.access?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
        return try {
            val output = java.io.DataOutputStream(connection.outputStream)
            fun text(value: String) = output.write(value.toByteArray(Charsets.UTF_8))
            fields.forEach { (name, value) ->
                text("--$boundary\r\nContent-Disposition: form-data; name=\"$name\"\r\n\r\n")
                text(value)
                text("\r\n")
            }
            text("--$boundary\r\nContent-Disposition: form-data; name=\"$fieldName\"; filename=\"$filename\"\r\nContent-Type: $mimeType\r\n\r\n")
            output.write(fileBytes)
            text("\r\n--$boundary--\r\n")
            output.flush()
            val status = connection.responseCode
            sessionSnapshot(session.generation)
            if (status == 401 && mayRefresh && session.refresh != null) {
                val renewed = refreshSession(session)
                return requestMultipartOnce(path, fields, fileBytes, filename, mimeType, requestedFieldName, false, renewed)
            }
            if (status == 401 && session.refresh == null) expireSession(session)
            if (connection.responseCode == 403 && path.startsWith("faces/")) error(localizedText(R.string.ui_face_search_requires_your_biometric_consent))
            if (connection.responseCode !in 200..299) {
                val detail = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                recognitionPhotoFailure(path, connection.responseCode, detail)?.let { error(it) }
                publicationUploadFailure(path, connection.responseCode, detail)?.let { error(it) }
                error(localizedHttpError(connection.responseCode))
            }
            connection.inputStream.bufferedReader().use { it.readText() }.also { sessionSnapshot(session.generation) }
        } finally {
            connection.disconnect()
        }
    }

    fun download(path: String, identity: Long, maximum: Int): ByteArray = downloadOnce(path, maximum, sessionSnapshot(identity), true)

    private fun downloadOnce(path: String, maximum: Int, session: RequestSession, mayRefresh: Boolean): ByteArray {
        sessionSnapshot(session.generation)
        val connection = openJsonConnection(path)
        connection.instanceFollowRedirects = false
        connection.connectTimeout = 15000
        connection.readTimeout = 90000
        session.access?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
        return try {
            val status = connection.responseCode
            sessionSnapshot(session.generation)
            if (status == 401 && mayRefresh && session.refresh != null) {
                return downloadOnce(path, maximum, refreshSession(session), false)
            }
            if (status == 401 && session.refresh == null) expireSession(session)
            check(status == 200) { localizedHttpError(status) }
            check(connection.contentLengthLong <= maximum) { "Resource exceeds download limit" }
            connection.inputStream.use { input ->
                val output = java.io.ByteArrayOutputStream()
                val buffer = ByteArray(32768)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    sessionSnapshot(session.generation)
                    check(output.size() + count <= maximum) { "Resource exceeds download limit" }
                    output.write(buffer, 0, count)
                }
                output.toByteArray().also { sessionSnapshot(session.generation) }
            }
        } finally {
            connection.disconnect()
        }
    }
}
