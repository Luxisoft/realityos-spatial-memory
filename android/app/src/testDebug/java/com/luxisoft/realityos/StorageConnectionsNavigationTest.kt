package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import com.luxisoft.realityos.host.RealityDrawer
import java.io.File
import java.net.HttpURLConnection
import java.util.concurrent.atomic.AtomicInteger
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
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
@Config(application = Application::class, sdk = [35], qualifiers = "en-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class StorageConnectionsNavigationTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val server = MockWebServer()
    private val original = SocialSession.openJsonConnection

    @Before fun start() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
        server.start()
        SocialSession.clear()
        SocialSession.remember(JSONObject().put("access_token", "expired").put("refresh_token", "refresh-first").put("password_account", true))
        SocialSession.active = true
        SocialSession.workWorkspaceId = "california"
        SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
    }

    @After fun stop() {
        SocialSession.openJsonConnection = original
        SocialSession.clear()
        server.shutdown()
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun openConnections(scale: Float = 1f, unavailable: Boolean = false) {
        val refreshes = AtomicInteger()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse = when {
                request.path == "/auth/refresh" -> {
                    refreshes.incrementAndGet()
                    MockResponse().setBody("""{"access_token":"renewed","refresh_token":"refresh-next"}""")
                }
                request.getHeader("Authorization") == "Bearer expired" -> MockResponse().setResponseCode(401)
                request.path == "/$STORAGE_BASE" -> if (unavailable) MockResponse().setResponseCode(503) else MockResponse().setBody("""[{"id":"source","name":"Clinical resources","bucket":"california","workspace_id":"california"}]""")
                request.path == "/workspaces" -> MockResponse().setBody("""[{"id":"california","name":"California Valley Medical Center"}]""")
                else -> MockResponse().setResponseCode(404)
            }
        }
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            var showConnections by remember { mutableStateOf(false) }
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    NoticeLayer {
                        if (showConnections) {
                            RootPanel(onClose = { showConnections = false }) {
                                StorageConnectionsScreen { showConnections = false }
                            }
                        } else {
                            RealityDrawer(RealityExperienceStore(RuntimeEnvironment.getApplication()), onAbout = {}, onConnections = { showConnections = true }, connectionsEnabled = true, onLogout = { error("Connections must not log out") })
                        }
                    }
                }
            }
        }
        compose.onNodeWithTag("drawer-connections").performClick()
        val expected = if (unavailable) localizedText(R.string.storage_error) else "Clinical resources · california"
        compose.waitUntil(15000) { compose.onAllNodesWithText(expected, substring = unavailable).fetchSemanticsNodes().isNotEmpty() }
        compose.waitUntil(15000) { compose.onAllNodes(hasText(localizedText(R.string.storage_back)) and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(localizedText(R.string.storage_title)).assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.storage_add)).assertIsDisplayed()
        if (!unavailable) compose.onNodeWithText(expected).assertIsDisplayed()
        compose.runOnIdle {
            assertTrue(SocialSession.active)
            assertEquals("renewed", SocialSession.token)
            assertEquals(1, refreshes.get())
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/connections-navigation").apply { mkdirs() }
            val language = RuntimeEnvironment.getApplication().resources.configuration.locales[0].language
            File(directory, "$language-$scale-$unavailable.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
        compose.onNodeWithText(localizedText(R.string.storage_back)).performClick()
        compose.onNodeWithTag("drawer-connections").assertIsDisplayed()
        assertTrue(SocialSession.active)
    }

    @Test fun drawerOpensConnectionsAndRefreshesExpiredAccess() = openConnections()

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun spanishConnectionsOpenWithLargeText() = openConnections(2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun connectionFailureKeepsSessionAndBackNavigation() = openConnections(2f, unavailable = true)
}
