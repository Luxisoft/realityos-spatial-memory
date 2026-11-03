package com.luxisoft.realityos

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** Human sessions are independent from the wearable's device credential. */
internal object SocialSession {
    private var preferences: android.content.SharedPreferences? = null
    private var refreshToken: String? = null
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
        BuildConfig.DEBUG, BuildConfig.LOCAL_DEVELOPMENT,
        BuildConfig.DEFAULT_REALITYOS_API_BASE_URL, localAccount && localAccountConfirmed,
    )
    // One-shot notice for the login screen: denial/expiry messages are set in the
    // host-shell instance but shown in the login-gate instance after the switch.
    var loginNotice: String? = null
    var workWorkspaceId: String? = null
    var workspaceId: String? = null
    var profilePictureUrl by mutableStateOf<String?>(null)
    fun initialize(context: android.content.Context) {
        preferences = androidx.security.crypto.EncryptedSharedPreferences.create(
            context, "realityos-facebook-session",
            androidx.security.crypto.MasterKey.Builder(context).setKeyScheme(androidx.security.crypto.MasterKey.KeyScheme.AES256_GCM).build(),
            androidx.security.crypto.EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            androidx.security.crypto.EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
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
    fun remember(response: JSONObject) {
        token = response.getString("access_token")
        refreshToken = response.getString("refresh_token")
        isGuest = response.optBoolean("is_guest")
        if (response.has("password_account")) {
            passwordAccount = response.optBoolean("password_account")
            passwordAccountConfirmed = passwordAccount
        }
        if (response.has("local_access")) {
            localAccount = LocalAccessPolicy.canSkipFaceEntry(
                BuildConfig.DEBUG, BuildConfig.LOCAL_DEVELOPMENT,
                BuildConfig.DEFAULT_REALITYOS_API_BASE_URL, response.optBoolean("local_access"),
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
    fun clear() {
        active = false; token = null; refreshToken = null; workspaceId = null; isGuest = false
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
    @Synchronized
    fun request(path: String, payload: JSONObject? = null): String {
        return requestJson(path, if (payload == null) "GET" else "POST", payload)
    }
    fun searchWorkspaceRecords(workspaceId: String, payload: JSONObject): String = requestOnce(
        "workspaces/$workspaceId/records/search", "POST", payload, true, 180000,
    )

    fun chatTranslations(payload: JSONObject? = null, ids: List<Int> = emptyList()): String = requestOnce(
        if (payload != null) "chat/history/prepare" else "chat/history/translations?ids=${ids.joinToString(",")}",
        if (payload != null) "POST" else "GET", payload, true, 5000,
    )

    fun publicationInformation(payload: JSONObject, prepare: Boolean = false): String = requestOnce(
        if (prepare) "gallery/evidence/information/prepare" else "gallery/evidence/information",
        "POST", payload, true, if (prepare) 60000 else 4000
    )

    fun requestJson(path: String, method: String, payload: JSONObject? = null): String {
        return requestOnce(path, method, payload, true)
    }
    internal var openJsonConnection: (String) -> HttpURLConnection = { path ->
        URL("${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/$path").openConnection() as HttpURLConnection
    }
    private fun requestOnce(path: String, method: String, payload: JSONObject?, mayRefresh: Boolean, timeoutMillis: Int = 30000): String {
        val connection = openJsonConnection(path)
        connection.setRequestProperty("X-Client-Version", BuildConfig.VERSION_NAME)
        connection.connectTimeout = minOf(15000, timeoutMillis)
        connection.readTimeout = timeoutMillis
        token?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
        return try {
            connection.requestMethod = method
            if (payload != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.bufferedWriter().use { it.write(payload.toString()) }
            }
            val authenticatedAccountRoute = path in setOf("auth/account-session", "auth/account-capture-profile")
            if (connection.responseCode == 401 && mayRefresh && refreshToken != null && (!path.startsWith("auth/") || authenticatedAccountRoute)) {
                val refreshed = JSONObject(requestOnce("auth/refresh", "POST", JSONObject().put("refresh_token", refreshToken), false, timeoutMillis))
                remember(refreshed)
                return requestOnce(path, method, payload, false, timeoutMillis)
            }
            if (connection.responseCode == 401 && !path.startsWith("auth/facebook")) {
                val wasGuest = isGuest || passwordAccount
                clear()
                error(if (wasGuest) localizedText(R.string.ui_your_session_expired_sign_in_again) else localizedText(R.string.ui_your_session_expired_continue_with_facebook_again))
            }
            if (connection.responseCode !in 200..299) error(localizedText(R.string.ui_could_not_complete_the_request_1_d, connection.responseCode))
            connection.inputStream.bufferedReader().use { it.readText() }
        } finally { connection.disconnect() }
    }
    /** Stream captured clips from private storage; retries reuse the caller's request key. */
    @Synchronized
    fun requestMultipartFile(path: String, fields: Map<String, String>, file: File, mime: String): String =
        multipartFileOnce(path, fields, file, mime, true)

    private fun multipartFileOnce(path: String, fields: Map<String, String>, file: File, mime: String, mayRefresh: Boolean): String {
        val boundary = "RealityOS-${java.util.UUID.randomUUID()}"
        val connection = URL("${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/$path").openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        connection.connectTimeout = 15000
        connection.readTimeout = 60000
        connection.doOutput = true
        connection.setChunkedStreamingMode(64 * 1024)
        connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
        token?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
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
            if (connection.responseCode == 401 && mayRefresh && refreshToken != null) {
                val refreshed = JSONObject(requestOnce("auth/refresh", "POST", JSONObject().put("refresh_token", refreshToken), false))
                remember(refreshed)
                multipartFileOnce(path, fields, file, mime, false)
            } else {
                check(connection.responseCode in 200..299) { localizedText(R.string.ui_upload_failed_1_d, connection.responseCode) }
                connection.inputStream.bufferedReader().use { it.readText() }
            }
        } finally { connection.disconnect() }
    }

    @Synchronized
    fun requestMultipart(path: String, fields: Map<String, String>, fileBytes: ByteArray, filename: String, mimeType: String, fieldName: String? = null): String {
        return requestMultipartOnce(path, fields, fileBytes, filename, mimeType, fieldName, true)
    }
    private fun requestMultipartOnce(path: String, fields: Map<String, String>, fileBytes: ByteArray, filename: String, mimeType: String, requestedFieldName: String?, mayRefresh: Boolean): String {
        val boundary = "RealityOS-${java.util.UUID.randomUUID()}"
        val fieldName = requestedFieldName ?: if (path == "faces/search" || path == "display/face-group-links") "probe" else "file"
        val connection = URL("${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/$path").openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        connection.setRequestProperty("X-Client-Version", BuildConfig.VERSION_NAME)
        connection.connectTimeout = 15000
        connection.readTimeout = 60000
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
        token?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
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
            if (connection.responseCode == 401 && mayRefresh && refreshToken != null) {
                val refreshed = JSONObject(requestOnce("auth/refresh", "POST", JSONObject().put("refresh_token", refreshToken), false))
                remember(refreshed)
                return requestMultipartOnce(path, fields, fileBytes, filename, mimeType, requestedFieldName, false)
            }
            if (connection.responseCode == 403 && path.startsWith("faces/")) error(localizedText(R.string.ui_face_search_requires_your_biometric_consent))
            if (connection.responseCode !in 200..299) {
                error(localizedHttpError(connection.responseCode))
            }
            connection.inputStream.bufferedReader().use { it.readText() }
        } finally { connection.disconnect() }
    }
}

@Composable
@SuppressLint("LocalContextGetResourceValueCall")
fun SocialGallery(
    viewModel: RealityViewModel,
    audience: String = "home",
    onWelcome: () -> Unit = {},
    onViewerChange: (Boolean) -> Unit = {},
    galleryBar: GalleryTopBarState? = null,
    onAdminDrawerChange: (Boolean) -> Unit = {},
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var authenticated by remember { mutableStateOf(SocialSession.token != null) }
    var loginBusy by remember { mutableStateOf(false) }
    var showRecords by remember { mutableStateOf(false) }
    var groupId by remember { mutableStateOf<String?>(null) }
    var posts by remember(audience, groupId) { mutableStateOf<List<JSONObject>>(emptyList()) }
    var error by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var pageLoaded by remember(audience, groupId) { mutableStateOf(false) }
    var groupsLoading by remember { mutableStateOf(true) }
    var commentsLoading by remember { mutableStateOf(false) }
    var inviteLoading by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<JSONObject?>(null) }
    var interaction by remember { mutableStateOf<String?>(null) }
    var text by remember { mutableStateOf("") }
    var comments by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var reply by remember { mutableStateOf<String?>(null) }
    var groups by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var groupDialog by remember { mutableStateOf<String?>(null) }
    var groupPin by remember { mutableStateOf("") }
    var groupText by remember { mutableStateOf("") }
    var liked by remember { mutableStateOf(setOf<String>()) }
    var revision by remember { mutableIntStateOf(0) }
    var offset by remember(audience, groupId) { mutableIntStateOf(0) }
    var endReached by remember(audience, groupId) { mutableStateOf(false) }
    var publishing by remember { mutableStateOf(false) }
    var workPublishMenu by remember { mutableStateOf(false) }
    var workPendingPhoto by remember { mutableStateOf<PendingPublishPhoto?>(null) }
    var workNoteDialog by remember { mutableStateOf(false) }
    var workCaptureUri by remember { mutableStateOf<Uri?>(null) }
    var showAdministration by remember { mutableStateOf(false) }
    var moderator by remember { mutableStateOf(false) }
    var entryConsent by remember { mutableStateOf(false) }
    var faceConsentAsk by remember { mutableStateOf(false) }
    var faceCaptureDone by remember { mutableStateOf<Boolean?>(null) }
    var identityVerified by remember { mutableStateOf<Boolean?>(null) }
    var deniedLastTime by remember { mutableStateOf(false) }
    val resumedSession = remember { SocialSession.token != null }
    val publicationUploader = rememberPublicationUploader(onPublished = { offset = 0; endReached = false; revision++ }, onBusy = { publishing = it })
    PublicationUploadDialog(publicationUploader)
    fun uploadWorkPublication(photo: PendingPublishPhoto, noteText: String, noteSource: String) {
        val target = groupId ?: return
        publicationUploader.submit(photo, noteText, noteSource, "work", target)
    }

    fun stageWorkPhoto(bytes: ByteArray, mime: String, name: String) {
        workPendingPhoto = PendingPublishPhoto(bytes, mime, name)
        workNoteDialog = true
    }

    val pickWorkPublication = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        scope.launch {
            publishing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_image))
                val mime = context.contentResolver.getType(uri) ?: "image/jpeg"
                val name = uri.lastPathSegment?.substringAfterLast('/') ?: "publicacion"
                stageWorkPhoto(bytes, mime, name)
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                publishing = false
            }
        }
    }

    val takeWorkPhoto = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (!success) return@rememberLauncherForActivityResult
        val uri = workCaptureUri ?: return@rememberLauncherForActivityResult
        scope.launch {
            publishing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) {
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                } ?: error(localizedText(R.string.ui_could_not_read_the_photo))
                stageWorkPhoto(bytes, "image/jpeg", "camara.jpg")
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                publishing = false
            }
        }
    }

    fun launchWorkPhoneCamera() {
        val file = File(File(context.cacheDir, "captures").apply { mkdirs() }, "publicacion.jpg")
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        workCaptureUri = uri
        takeWorkPhoto.launch(uri)
    }

    val askWorkCamera = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) launchWorkPhoneCamera() else error = localizedText(R.string.ui_camera_permission_is_required)
    }

    fun launchWorkPhoneCameraChecked() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) launchWorkPhoneCamera()
        else askWorkCamera.launch(Manifest.permission.CAMERA)
    }

    fun onWorkCameraOption() {
        workPublishMenu = false
        scope.launch {
            publishing = true
            error = ""
            try {
                val bytes = withContext(Dispatchers.IO) { viewModel.captureStillForPublish() }
                if (bytes != null) stageWorkPhoto(bytes, "image/jpeg", "camara.jpg")
                else launchWorkPhoneCameraChecked()
            } catch (failure: Exception) {
                error = failure.message.orEmpty()
            } finally {
                publishing = false
            }
        }
    }

    fun requireFreshLogin() {
        SocialSession.clear(); com.facebook.login.LoginManager.getInstance().logOut()
        authenticated = false; posts = emptyList(); faceCaptureDone = null; identityVerified = null
        deniedLastTime = false
        SocialSession.loginNotice = context.getString(R.string.face_login_required)
    }
    fun runRequest(action: suspend () -> Unit) {
        scope.launch { try { action() } catch (e: Exception) {
            error = e.message ?: localizedText(R.string.ui_connection_error)
            if (SocialSession.token == null && SocialSession.loginNotice == null) SocialSession.loginNotice = error
        } }
    }
    galleryBar?.let { bar ->
        bar.loading = groupsLoading
        bar.options = if (authenticated && audience == "work") {
            groups.map { WorkspaceOption(it.optString("id"), it.optString("name"), it.optString("role")) }
        } else emptyList()
        bar.selectedId = groupId
        bar.publishEnabled = !loading && !publishing && !groupsLoading
        val currentGroup = groups.firstOrNull { it.optString("id") == groupId }
        val iCanInvite = currentGroup != null && GroupAdminPolicy.canInvite(currentGroup.optString("role"), currentGroup.optBoolean("can_invite"))
        bar.showInvite = groupId != null && iCanInvite
        bar.showAdmin = groupId != null && iCanInvite
        bar.onSelect = { groupId = it; SocialSession.workWorkspaceId = it }
        bar.onPublish = {
            if (groupId == null) error = localizedText(R.string.ui_select_a_workspace_to_publish)
            else workPublishMenu = true
        }
        bar.onInvite = {
            groupText = ""
            groupPin = ""
            error = ""
            groupDialog = "invite"
            inviteLoading = true
            runRequest {
                try {
                groupText = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("groups/$groupId/invite", JSONObject())).getString("code") }
                groupPin = if (iCanInvite) {
                    try {
                        withContext(Dispatchers.IO) { JSONObject(SocialSession.request("groups/$groupId/pin")).getString("join_pin") }
                    } catch (_: Exception) { "" }
                } else ""
                } finally { inviteLoading = false }
            }
        }
        bar.onAdmin = { showAdministration = true }
    }
    var showAccountEntry by remember { mutableStateOf(false) }
    if (!authenticated) {
        if (showAccountEntry) {
            AccountEntry(viewModel, onSuccess = { authenticated = true }, onBack = { showAccountEntry = false })
            return
        }
        if (LocalAccountEntry(viewModel, onSuccess = { authenticated = true })) return
        LaunchedEffect(Unit) {
            SocialSession.loginNotice?.let { error = it; SocialSession.loginNotice = null }
        }
        FacebookAccessScreen(loginBusy, error, entryConsent, onConsentChange = { entryConsent = it }, onLogin = {
            startFacebookAccess(context, scope, viewModel,
                onBusy = { loginBusy = it }, onError = { error = it }, onSuccess = {
                    // Set before SocialSession.active flips: the host-shell gallery
                    // instance reads it on mount.
                    SocialSession.freshLogin = true
                    runRequest {
                        withContext(Dispatchers.IO) { SocialSession.request("faces/consent", JSONObject().put("confirm", true)) }
                        authenticated = true
                    }
                })
        }, onGuest = { showAccountEntry = true
        }, onWelcome = onWelcome)
        return
    }
    if (SocialSession.passwordAccount && !SocialSession.passwordAccountConfirmed) {
        LaunchedEffect(Unit) {
            try {
                val confirmed = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("auth/account-session")).optBoolean("password_account") }
                check(confirmed)
                SocialSession.passwordAccountConfirmed = true
            } catch (_: Exception) { SocialSession.clear(); authenticated = false }
        }
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        return
    }
    if (BuildConfig.LOCAL_DEVELOPMENT && SocialSession.localAccount && !SocialSession.localAccountConfirmed) {
        LaunchedEffect(Unit) {
            try {
                val confirmed = withContext(Dispatchers.IO) {
                    // Refresh an expired access token first, then verify the server realm.
                    SocialSession.request("me/profile")
                    JSONObject(SocialSession.request("auth/local-session")).optBoolean("local_access")
                }
                check(confirmed) { "Local account unavailable" }
                SocialSession.localAccountConfirmed = true
            } catch (_: Exception) {
                SocialSession.clear()
                authenticated = false
            }
        }
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        return
    }
    LaunchedEffect(authenticated) {
        if (authenticated && !SocialSession.isGuest && !SocialSession.localEntryAllowed && !SocialSession.accountEntryAllowed && (faceCaptureDone == null || identityVerified == null)) {
            try {
                val status = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("faces/consent")) }
                if (resumedSession && !status.optBoolean("consented") && !faceConsentAsk) faceConsentAsk = true
                faceCaptureDone = status.optBoolean("face_capture_done")
                identityVerified = status.optBoolean("identity_verified")
                if (!SocialSession.freshLogin && faceCaptureDone == false) requireFreshLogin()
            } catch (e: Exception) { /* Face search stays unavailable until consent succeeds. */ }
        }
    }
    if (!SocialSession.isGuest && !SocialSession.localEntryAllowed && !SocialSession.accountEntryAllowed && (faceCaptureDone != true || identityVerified != true || deniedLastTime)) {
        if (faceCaptureDone == null || identityVerified == null) Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        else FaceCaptureScreen(hasCapture = faceCaptureDone == true && !deniedLastTime,
            onDone = { faceCaptureDone = true; identityVerified = true; deniedLastTime = false; SocialSession.freshLogin = false },
            onDenied = { message ->
                SocialSession.clear(); com.facebook.login.LoginManager.getInstance().logOut()
                authenticated = false; posts = emptyList(); faceCaptureDone = null; identityVerified = null
                deniedLastTime = true; SocialSession.loginNotice = message
            },
            allowPhoto = SocialSession.freshLogin,
            onRequireLogin = { requireFreshLogin() })
        return
    }
    LaunchedEffect(audience, authenticated, groupId, revision, offset) {
        if (!authenticated) return@LaunchedEffect
        if (offset != 0 && endReached) return@LaunchedEffect
        loading = true
        error = ""
        try {
            val result = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("gallery?audience=$audience&offset=$offset" + if (audience == "work" && groupId != null) "&workspace_id=$groupId" else "")) }
            val page = (0 until result.length()).map { result.getJSONObject(it) }
            posts = if (offset == 0) page else (posts + page).distinctBy { it.getString("id") }
            endReached = GalleryPagingPolicy.isEndOfContent(page.size)
            liked = posts.filter { it.optBoolean("liked") }.map { it.getString("id") }.toSet()
        } catch (e: Exception) { if (e is kotlinx.coroutines.CancellationException) throw e; error = e.message.orEmpty() }
        finally { loading = false; pageLoaded = true }
    }
    LaunchedEffect(authenticated, audience, revision) {
        if (!authenticated) return@LaunchedEffect
        groupsLoading = true
        try {
            moderator = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("me/social-capabilities")).optBoolean("moderator") }
            val resultGroups = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("workspaces")) }
            groups = (0 until resultGroups.length()).map { resultGroups.getJSONObject(it) }.filter { !it.getString("name").startsWith("home:") }
            if (groupId == null && groups.size == 1) {
                groupId = groups.first().getString("id")
                SocialSession.workWorkspaceId = groupId
            }
        } catch (e: Exception) { if (e is kotlinx.coroutines.CancellationException) throw e; error = e.message.orEmpty() }
        finally { groupsLoading = false }
    }
    if (showRecords && groupId != null) {
        WorkspaceRecords(groupId!!, canWrite = groups.firstOrNull { it.optString("id") == groupId }?.optString("role") in setOf("admin", "register"), onBack = { showRecords = false })
        return
    }
    Column(Modifier.fillMaxSize()) {
        if (audience == "work" && groupId != null) {
            TextButton(onClick = { showRecords = true }, modifier = Modifier.fillMaxWidth()) { Text(stringResource(R.string.records_title)) }
        }
        if (moderator && audience == "public") Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            IconButton(onClick = { showAdministration = true }) { Icon(Icons.Filled.Flag, contentDescription = localizedText(R.string.ui_review_reports)) }
        }
        if (error.isNotEmpty()) {
            Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(error, color = MaterialTheme.colorScheme.error, modifier = Modifier.weight(1f))
                IconButton(onClick = { error = "" }) { Icon(Icons.Filled.Close, contentDescription = localizedText(R.string.ui_dismiss_notice)) }
            }
        }
        if (publishing) LinearProgressIndicator(Modifier.fillMaxWidth())
        if (posts.isEmpty() && (loading || !pageLoaded) && error.isBlank()) {
            LazyVerticalGrid(columns = GridCells.Fixed(3), modifier = Modifier.weight(1f)) {
                items(9) { SkeletonBlock(Modifier.padding(1.dp).aspectRatio(0.75f)) }
            }
        } else if (authenticated && posts.isEmpty() && !loading && pageLoaded && error.isBlank()) {
            Box(Modifier.fillMaxWidth().weight(1f), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(Icons.Default.PhotoLibrary, null, modifier = Modifier.size(58.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(localizedText(R.string.ui_no_publications_in_this_workspace_yet), color = MaterialTheme.colorScheme.onSurfaceVariant)
                    if (audience == "work" && groupsLoading) SkeletonList(Modifier.padding(16.dp), rows = 2)
                    else if (audience == "work" && groups.isEmpty()) {
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(onClick = { groupText = ""; groupPin = ""; groupDialog = "create" }) { Text(localizedText(R.string.ui_create_group)) }
                            Button(onClick = { groupText = ""; groupPin = ""; groupDialog = "join" }) { Text(localizedText(R.string.ui_join)) }
                        }
                    }
                }
            }
        } else {
            LazyVerticalGrid(columns = GridCells.Fixed(3), modifier = Modifier.weight(1f)) {
                items(posts.filter { audience != "work" || groupId == null || it.optString("workspace_id") == groupId }) { post ->
                    Box(Modifier.padding(1.dp).aspectRatio(0.75f).clickable { selected = post }) {
                        DatabaseImage(
                            model = profileImageRequest(context, post.getString("thumbnail_url")),
                            contentDescription = post.optString("caption"), contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize(),
                        )
                        PublicationSourceBadge(post.optString("source"), Modifier.align(Alignment.BottomStart).padding(4.dp))
                    }
                }
                if (authenticated && posts.isNotEmpty()) item(span = { GridItemSpan(maxLineSpan) }) {
                    val loadMore = GalleryPagingPolicy.shouldLoadMore(loading, endReached)
                    Box(Modifier.fillMaxWidth().heightIn(min = 56.dp), contentAlignment = Alignment.Center) {
                        if (loading) SkeletonGrid(rows = 1)
                        else if (!loadMore) Text(
                            localizedText(R.string.ui_no_more_publications),
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        else LaunchedEffect(posts.size, audience, groupId) { offset = GalleryPagingPolicy.nextOffset(offset) }
                    }
                }
            }
        }
    }
    LaunchedEffect(selected) {
        onViewerChange(selected != null)
        comments = emptyList()
        val post = selected ?: return@LaunchedEffect
        commentsLoading = true
        try {
            val result = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("gallery/${post.getString("id")}/comments")) }
            comments = (0 until result.length()).map { result.getJSONObject(it) }
        } catch (failure: Exception) { if (failure is kotlinx.coroutines.CancellationException) throw failure; error = failure.message.orEmpty() }
        finally { commentsLoading = false }
    }
    selected?.let { post ->
        val likedNow = post.getString("id") in liked
        MediaViewerScreen(
            title = post.optString("caption"),
            mediaUrl = "${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/${post.getString("media_url")}",
            thumbnailUrl = "${BuildConfig.DEFAULT_REALITYOS_API_BASE_URL}/${post.getString("thumbnail_url")}",
            mimeType = post.optString("mime_type"),
            authToken = SocialSession.token,
            noteText = post.optString("note_text"),
            noteSource = post.optString("note_source"),
            metaLines = listOf(
                if (post.optString("source").startsWith("simulator")) localizedText(R.string.profile_simulated_media) else "",
                post.optJSONObject("owner")?.optString("display_name").orEmpty().let { if (it.isNotBlank()) localizedText(R.string.ui_by_1_s, it) else "" },
                post.optString("published_at").substringBefore("T").let { if (it.isNotBlank()) localizedText(R.string.ui_published_on_1_s, it) else "" },
            ),
            commentsLoading = commentsLoading,
            comments = comments.takeLast(5).map { ViewerComment(it.getString("id"), it.getString("text")) },
            onCommentClick = { reply = it; interaction = "comment" },
            topActions = {
                IconButton(onClick = { interaction = if (likedNow) "unlike" else "like" }) {
                    Icon(if (likedNow) Icons.Filled.Favorite else Icons.Filled.FavoriteBorder, contentDescription = if (likedNow) localizedText(R.string.ui_unlike) else "Like", tint = Color.White)
                }
                IconButton(onClick = { interaction = "comment"; reply = null }) { Icon(Icons.Filled.Comment, contentDescription = localizedText(R.string.ui_comment), tint = Color.White) }
                IconButton(onClick = { interaction = "report" }) { Icon(Icons.Filled.Flag, contentDescription = localizedText(R.string.ui_report), tint = Color.White) }
                if (post.optBoolean("owned")) {
                    IconButton(onClick = { interaction = "public" }) { Icon(Icons.Filled.Public, contentDescription = localizedText(R.string.ui_publish), tint = Color.White) }
                    IconButton(onClick = { interaction = "work" }) { Icon(Icons.Filled.Group, contentDescription = localizedText(R.string.ui_share_with_group), tint = Color.White) }
                    IconButton(onClick = { interaction = "remove" }) { Icon(Icons.Filled.Delete, contentDescription = localizedText(R.string.ui_delete), tint = Color.White) }
                }
            },
            onClose = { selected = null },
        )
        interaction?.let { action ->
            AlertDialog(onDismissRequest = { interaction = null }, title = { Text(if (reply != null) localizedText(R.string.ui_reply) else action) },
                text = {
                    if (action in listOf("comment", "report")) OutlinedTextField(value = text, onValueChange = { text = it }, label = { Text(localizedText(R.string.ui_text)) })
                    else if (action == "work") Column {
                        Text(localizedText(R.string.ui_choose_the_group_to_share_this_publication_with))
                        if (groupsLoading) SkeletonList(rows = 3)
                        else if (groups.isEmpty()) Text(localizedText(R.string.ui_create_or_join_a_group_from_work))
                        groups.forEach { group ->
                            TextButton(onClick = { groupId = group.getString("id") }) {
                                Text((if (groupId == group.getString("id")) "✓ " else "") + group.getString("name"))
                            }
                        }
                    }
                    else Text(if (action == "public") localizedText(R.string.ui_the_content_will_be_visible_to_all_users) else if (action == "remove") localizedText(R.string.ui_the_publication_will_no_longer_appear_in_the_gallery_the_original_evidence_is_preserv) else localizedText(R.string.ui_confirm_reaction))
                },
                confirmButton = { TextButton(onClick = {
                    runRequest {
                        withContext(Dispatchers.IO) {
                            if (action in listOf("public", "work")) {
                                if (action == "work" && groupId == null) error(localizedText(R.string.ui_select_a_group_in_work))
                                SocialSession.request("gallery/${post.getString("id")}/share", JSONObject().put("audience", action).apply { groupId?.let { put("workspace_id", it) } })
                            } else if (action == "remove") SocialSession.request("gallery/${post.getString("id")}/remove", JSONObject())
                            else SocialSession.request("gallery/${post.getString("id")}/interactions", JSONObject().put("action", action).put("text", text).apply { reply?.let { put("parent_id", it) } })
                        }
                        if (action == "like") liked = liked + post.getString("id")
                        if (action == "unlike") liked = liked - post.getString("id")
                        if (action == "comment") {
                            val result = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("gallery/${post.getString("id")}/comments")) }
                            comments = (0 until result.length()).map { result.getJSONObject(it) }
                        }
                        interaction = null; text = ""
                        if (action in listOf("public", "work", "remove")) { selected = null; offset = 0; endReached = false; revision++ }
                    }
                }) { Text(localizedText(R.string.ui_confirm)) } }, dismissButton = { TextButton(onClick = { interaction = null }) { Text(localizedText(R.string.ui_cancel)) } })
        }
    }
    if (workPublishMenu) {
        AlertDialog(
            onDismissRequest = { workPublishMenu = false },
            title = { Text(localizedText(R.string.ui_publish_to_workspace)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(Modifier.fillMaxWidth().clickable { onWorkCameraOption() }.padding(vertical = 12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Icon(Icons.Filled.CameraAlt, contentDescription = null)
                        Text(localizedText(R.string.ui_take_photo))
                    }
                    Row(Modifier.fillMaxWidth().clickable { workPublishMenu = false; pickWorkPublication.launch("image/*") }.padding(vertical = 12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Icon(Icons.Filled.PhotoLibrary, contentDescription = null)
                        Text(localizedText(R.string.ui_choose_image))
                    }
                }
            },
            confirmButton = {},
        )
    }
    if (workNoteDialog) {
        workPendingPhoto?.let { pending ->
            PublishNoteDialog(
                onPublish = { noteText, noteSource ->
                    workNoteDialog = false
                    workPendingPhoto = null
                    uploadWorkPublication(pending, noteText, noteSource)
                },
                onDismiss = { workNoteDialog = false; workPendingPhoto = null },
            )
        }
    }
    groupDialog?.let { action ->
        AlertDialog(onDismissRequest = { groupDialog = null }, title = { Text(if (action == "invite") localizedText(R.string.ui_invitation_code) else localizedText(R.string.ui_work_group)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (action == "invite" && error.isNotBlank()) {
                        Text(error, color = MaterialTheme.colorScheme.error)
                    } else if (action == "invite" && inviteLoading) {
                        SkeletonLines(rows = 3)
                    } else if (action == "created") {
                        Text(localizedText(R.string.ui_share_this_pin_so_others_can_join_the_group))
                        OutlinedTextField(value = groupPin, onValueChange = {}, readOnly = true, label = { Text(localizedText(R.string.ui_group_pin)) })
                    } else {
                        OutlinedTextField(value = groupText, onValueChange = { groupText = it }, readOnly = action == "invite", label = { Text(if (action == "create") localizedText(R.string.ui_name) else localizedText(R.string.ui_code_or_pin)) })
                        if (action == "invite" && groupPin.isNotBlank()) {
                            OutlinedTextField(value = groupPin, onValueChange = {}, readOnly = true, label = { Text(localizedText(R.string.ui_group_pin)) })
                        }
                    }
                }
            },
            confirmButton = { TextButton(onClick = {
                if (action == "invite" || action == "created") groupDialog = null else runRequest {
                    if (action == "create") {
                        val created = withContext(Dispatchers.IO) { JSONObject(SocialSession.request("groups", JSONObject().put("name", groupText))) }
                        groupPin = created.optString("join_pin")
                        groupText = ""
                        groupDialog = "created"
                    } else {
                        val route = GroupJoinPolicy.route(groupText)
                        withContext(Dispatchers.IO) {
                            SocialSession.request(
                                if (route == GroupJoinPolicy.Route.PIN) "groups/join-by-pin" else "groups/join",
                                JSONObject().put(if (route == GroupJoinPolicy.Route.PIN) "pin" else "code", groupText),
                            )
                        }
                        groupDialog = null; groupText = ""
                    }
                    val result = withContext(Dispatchers.IO) { JSONArray(SocialSession.request("workspaces")) }
                    groups = (0 until result.length()).map { result.getJSONObject(it) }.filter { !it.getString("name").startsWith("home:") }
                }
            }) { Text(localizedText(R.string.ui_accept)) } }, dismissButton = { TextButton(onClick = { groupDialog = null }) { Text(localizedText(R.string.ui_cancel)) } })
    }
    if (faceConsentAsk) {
        AlertDialog(onDismissRequest = { faceConsentAsk = false },
            title = { Text(stringResource(R.string.face_consent_title)) },
            text = { Text(stringResource(R.string.face_consent_body)) },
            confirmButton = { TextButton(onClick = {
                runRequest {
                    withContext(Dispatchers.IO) { SocialSession.request("faces/consent", JSONObject().put("confirm", true)) }
                    faceConsentAsk = false
                }
            }) { Text(stringResource(R.string.face_consent_accept)) } },
            dismissButton = { TextButton(onClick = { faceConsentAsk = false }) { Text(stringResource(R.string.face_consent_later)) } })
    }
    LaunchedEffect(showAdministration) { onAdminDrawerChange(showAdministration) }
    DisposableEffect(Unit) { onDispose { onAdminDrawerChange(false) } }
    if (showAdministration) SocialAdministration(
        if (audience == "work") groupId else null,
        onDismiss = { showAdministration = false; offset = 0; endReached = false; revision++ },
        onGroupDeleted = { groupId = null; showAdministration = false; offset = 0; endReached = false; revision++ },
    )
}
