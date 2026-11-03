package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class ProfilePersonalDetailsTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    private var originalConnection = SocialSession.openJsonConnection

    @Before fun initializeLocalization() {
        originalConnection = SocialSession.openJsonConnection
        SocialSession.openJsonConnection = { error("Unexpected network request in profile UI test") }
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
    }

    @After fun resetLocalization() {
        RuntimeEnvironment.setFontScale(1f)
        SocialSession.openJsonConnection = originalConnection
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    // Android supports PATCH; the JVM's default HttpURLConnection does not.
    // Keep a real HTTP exchange with MockWebServer using the existing OkHttp test client.
    private class PatchConnection(url: URL) : HttpURLConnection(url) {
        private val output = ByteArrayOutputStream()
        private var response: okhttp3.Response? = null
        override fun setRequestMethod(value: String) {
            method = value
        }
        override fun getOutputStream() = output
        override fun connect() {
            if (response != null) return
            val request = Request.Builder().url(url).method(method, output.toByteArray().toRequestBody("application/json".toMediaType()))
            requestProperties.forEach { (key, values) -> values.forEach { request.addHeader(key, it) } }
            response = OkHttpClient().newCall(request.build()).execute()
        }
        override fun getResponseCode(): Int {
            connect()
            return response!!.code
        }
        override fun getInputStream(): java.io.InputStream {
            connect()
            return response!!.body!!.byteStream()
        }
        override fun disconnect() {
            response?.close()
        }
        override fun usingProxy() = false
    }

    private fun data(facebook: Boolean = false) = JSONObject()
        .put("user_id", "synthetic-owner").put("display_name", "Ana Solis").put("email", "ana@example.test")
        .put("location", "Madrid").put("hometown", "Lima").put("birthday", "1990-01-02").put("gender", "female")
        .put("profile_source", if (facebook) "facebook" else "email").put("personal_details_editable", !facebook)
        .put("headline", "Architect").put("biography", "Original biography").put("phone", "").put("website", "")
        .put("cv", JSONObject().put("present", false))

    private fun field(tag: String): SemanticsNodeInteraction {
        compose.onNodeWithTag("profile-edit-fields").performScrollToNode(hasTestTag(tag))
        return compose.onNodeWithTag(tag)
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val view = org.robolectric.shadows.ShadowDialog.getLatestDialog().window!!.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/profile-design").apply { mkdirs() }
            File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        }
    }

    private fun show(value: JSONObject, scale: Float = 1f): ProfileState {
        RuntimeEnvironment.setFontScale(scale)
        val state = ProfileState().apply { apply(value) }
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme { ProfileHeader(state) }
            }
        }
        compose.onNodeWithTag("profile-edit").performClick()
        return state
    }

    @Test fun emailProfileEditsPersistAndRefreshHeader() {
        val original = SocialSession.openJsonConnection
        val server = MockWebServer().apply { start() }
        try {
            SocialSession.openJsonConnection = { path -> PatchConnection(server.url("/$path").toUrl()) }
            val response = data().put("display_name", "Ana Updated").put("location", "Bogotá").put("birthday", JSONObject.NULL)
            server.enqueue(MockResponse().setBody(response.toString()))
            val state = show(data())
            capture("email-en-390")
            field("profile-display_name").performTextReplacement("Ana Updated")
            field("profile-location").performTextReplacement("Bogotá")
            field("profile-birthday").performTextClearance()
            field("profile-save").performClick()
            compose.waitUntil(10000) { state.profile?.optString("display_name") == "Ana Updated" }
            compose.onNodeWithText("Ana Updated").assertIsDisplayed()
            val request = server.takeRequest()
            assertEquals("PATCH", request.method)
            assertEquals("/me/profile", request.path)
            val payload = JSONObject(request.body.readUtf8())
            assertEquals("Bogotá", payload.getString("location"))
            assertEquals("Lima", payload.getString("hometown"))
            assertEquals("female", payload.getString("gender"))
            assertTrue(payload.isNull("birthday"))
            assertFalse(payload.has("email"))
        } finally {
            SocialSession.openJsonConnection = original
            server.shutdown()
        }
    }

    @Test fun facebookFieldsAreReadOnlyAndNeverSentInProfilePatch() {
        val original = SocialSession.openJsonConnection
        val server = MockWebServer().apply { start() }
        try {
            SocialSession.openJsonConnection = { path -> PatchConnection(server.url("/$path").toUrl()) }
            server.enqueue(MockResponse().setBody(data(true).toString()))
            show(data(true))
            capture("facebook-en-390")
            field("profile-readonly-location").assertExists()
            compose.onNodeWithTag("profile-location").assertDoesNotExist()
            compose.onNodeWithTag("profile-birthday-calendar").assertDoesNotExist()
            field("profile-save").performClick()
            compose.waitUntil(10000) { server.requestCount == 1 }
            val payload = JSONObject(server.takeRequest().body.readUtf8())
            listOf("display_name", "birthday", "gender", "hometown", "location").forEach { assertFalse(payload.has(it)) }
            assertEquals("Original biography", payload.getString("biography"))
        } finally {
            SocialSession.openJsonConnection = original
            server.shutdown()
        }
    }

    @Test fun invalidBirthdayBlocksSaveAndShowsTheFieldError() {
        show(data())
        field("profile-birthday").performTextReplacement("2999-01-01")
        field("profile-save").performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.profile_birthday_error)).assertIsDisplayed()
        field("profile-birthday-calendar").performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.profile_clear_birthday)).performClick()
        field("profile-birthday").assert(SemanticsMatcher.expectValue(androidx.compose.ui.semantics.SemanticsProperties.EditableText, androidx.compose.ui.text.AnnotatedString("")))
    }

    @Test
    @Config(qualifiers = "es-w320dp-h720dp-mdpi")
    fun spanishLargeTextKeepsFieldsAndSaveReachable() {
        show(data(), 2f)
        capture("email-es-320-text200")
        listOf("profile-location", "profile-hometown", "profile-birthday", "profile-gender", "profile-save").forEach { field(it).assertIsDisplayed() }
    }
}
