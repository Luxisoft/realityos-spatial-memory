package com.luxisoft.realityos

import android.app.Application
import android.content.Context
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import java.net.HttpURLConnection
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.json.JSONArray
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
import org.robolectric.annotation.Implementation
import org.robolectric.annotation.Implements

/** Real gallery composition and HTTP requests, with controlled response ordering. */
@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "en-w390dp-h844dp-mdpi", shadows = [GalleryDeviceProvisioningShadow::class])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class GalleryLiveFilteringTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val bar = GalleryTopBarState()
    private val server = MockWebServer()
    private val originalConnection = SocialSession.openJsonConnection
    private val requests = ConcurrentLinkedQueue<RecordedRequest>()
    private val opened = ConcurrentLinkedQueue<String>()
    private val completed = ConcurrentLinkedQueue<String>()
    private val gates = mutableListOf<CountDownLatch>()

    @Before fun start() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(RealityLanguage.ENGLISH)
        SocialSession.clear()
        SocialSession.remember(JSONObject().put("access_token", "gallery-test").put("refresh_token", "gallery-refresh").put("local_access", true))
        SocialSession.active = true
        SocialSession.workWorkspaceId = "police"
        server.start()
        SocialSession.openJsonConnection = { path ->
            opened += path
            val delegate = server.url("/$path").toUrl().openConnection() as HttpURLConnection
            // Observe actual consumption, not just the server receiving a request.
            object : HttpURLConnection(delegate.url) {
                override fun connect() = delegate.connect()
                override fun usingProxy() = delegate.usingProxy()
                override fun setRequestProperty(key: String, value: String) = delegate.setRequestProperty(key, value)
                override fun setRequestMethod(method: String) {
                    delegate.requestMethod = method
                }
                override fun getResponseCode() = delegate.responseCode
                override fun getInputStream() = delegate.inputStream
                override fun getErrorStream() = delegate.errorStream
                override fun disconnect() {
                    delegate.disconnect()
                    completed += path
                }
            }
        }
    }

    @After fun stop() {
        gates.forEach { it.countDown() }
        compose.runOnIdle { compose.activity.viewModelStore.clear() }
        SocialSession.openJsonConnection = originalConnection
        SocialSession.clear()
        server.shutdown()
    }

    private fun gate() = CountDownLatch(1).also { gates += it }

    private fun respondAfter(gate: CountDownLatch, body: String): MockResponse {
        check(gate.await(20, TimeUnit.SECONDS)) { "The test did not release its pending HTTP response" }
        return MockResponse().setBody(body)
    }

    private fun showGallery(page: (RecordedRequest) -> MockResponse) {
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                requests += request
                return when (request.requestUrl!!.encodedPath) {
                    "/workspaces" -> MockResponse().setBody("""[{"id":"police","name":"Police","role":"admin"},{"id":"meta","name":"Meta","role":"admin"}]""")
                    "/gallery/page" -> page(request)
                    else -> MockResponse().setResponseCode(404)
                }
            }
        }
        compose.setContent {
            RealityOsTheme {
                Surface(Modifier.fillMaxSize()) {
                    SocialGallery(ViewModelProvider(compose.activity)[RealityViewModel::class.java], galleryBar = bar)
                }
            }
        }
    }

    private fun page(label: String, workspace: String = "police", next: String? = null): String = JSONObject()
        .put(
            "items",
            JSONArray().put(
                JSONObject()
                    .put("id", label)
                    .put("workspace_id", workspace)
                    .put("caption", label)
                    .put("mime_type", "image/png")
                    .put("thumbnail_url", server.url("/thumbnail/$label").toString())
                    .put("category", JSONObject().put("id", label).put("name", label))
            )
        )
        .put("next_cursor", next ?: JSONObject.NULL)
        .toString()

    private fun awaitLabel(label: String) {
        compose.waitUntil(10_000) { compose.onAllNodesWithText(label).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(label).assertIsDisplayed()
    }

    private fun pageRequests() = requests.filter { it.requestUrl!!.encodedPath == "/gallery/page" }

    private fun awaitPage(description: String, predicate: (RecordedRequest) -> Boolean) {
        try {
            compose.waitUntil(10_000) { pageRequests().any(predicate) }
        } catch (failure: ComposeTimeoutException) {
            throw AssertionError("Missing $description. Opened=$opened; received=${requests.map { it.path }}; completed=$completed; group=${bar.selectedId}; filters=${bar.filters}; publishEnabled=${bar.publishEnabled}; UI=${compose.onRoot().printToString()}", failure)
        }
    }

    @Test fun identicalSelectionsKeepResultsAndTypingOnlyReloadsPublications() {
        showGallery { request ->
            val query = request.requestUrl!!.queryParameter("description_q").orEmpty()
            MockResponse().setBody(page(if (query.isEmpty()) "Initial publication" else "Result $query"))
        }
        awaitLabel("Initial publication")
        compose.waitUntil(10_000) { !bar.loading }
        compose.runOnIdle {
            bar.onFilters(GalleryFilterSelection())
            bar.onSelect("police")
        }
        compose.onNodeWithText("Initial publication").assertIsDisplayed()
        assertEquals(1, pageRequests().size)
        listOf("first", "second").forEach { text ->
            compose.runOnIdle { bar.onFilters(GalleryFilterSelection(text = text)) }
            awaitLabel("Result $text")
        }
        assertEquals(listOf("", "first", "second"), pageRequests().map { it.requestUrl!!.queryParameter("description_q").orEmpty() })
        assertTrue(pageRequests().all { it.requestUrl!!.queryParameter("cursor") == null })
        assertEquals(1, requests.count { it.requestUrl!!.encodedPath == "/workspaces" })
    }

    @Test fun cancelledPagesCannotReplaceNewFiltersOrStopAnotherGroupsLoadingState() {
        val oldPage = gate()
        val oldFilter = gate()
        val newGroup = gate()
        showGallery { request ->
            val url = request.requestUrl!!
            when {
                url.queryParameter("cursor") == "police-next" -> respondAfter(oldPage, page("Stale second page", next = "obsolete-cursor"))
                url.queryParameter("workspace_id") == "meta" -> respondAfter(newGroup, page("Current Meta publication", workspace = "meta"))
                url.queryParameter("description_q") == "late" -> respondAfter(oldFilter, page("Stale Police filter"))
                url.queryParameter("description_q") == "filtered" -> MockResponse().setBody(page("Current filtered publication"))
                else -> MockResponse().setBody(page("First Police page", next = "police-next"))
            }
        }
        awaitLabel("First Police page")
        compose.waitUntil(10_000) { pageRequests().any { it.requestUrl!!.queryParameter("cursor") == "police-next" } }
        compose.runOnIdle { bar.onFilters(GalleryFilterSelection(text = "filtered")) }
        awaitLabel("Current filtered publication")
        oldPage.countDown()
        compose.waitUntil(10_000) { completed.any { it.contains("cursor=police-next") } }
        compose.waitForIdle()
        compose.onNodeWithText("Current filtered publication").assertIsDisplayed()
        compose.onNodeWithText("Stale second page").assertDoesNotExist()

        compose.runOnIdle { bar.onFilters(GalleryFilterSelection(text = "late")) }
        compose.waitForIdle()
        awaitPage("late filter request") { it.requestUrl!!.queryParameter("description_q") == "late" }
        compose.runOnIdle { bar.onSelect("meta") }
        compose.waitForIdle()
        compose.waitUntil(10_000) { pageRequests().any { it.requestUrl!!.queryParameter("workspace_id") == "meta" } }
        oldFilter.countDown()
        compose.waitUntil(10_000) { completed.any { it.contains("description_q=late") } }
        compose.waitForIdle()
        compose.runOnIdle { assertFalse("The current group is still loading", bar.publishEnabled) }
        compose.onNodeWithText("Stale Police filter").assertDoesNotExist()
        newGroup.countDown()
        awaitLabel("Current Meta publication")
        compose.onNodeWithText("Current filtered publication").assertDoesNotExist()
        compose.onNodeWithText("Stale Police filter").assertDoesNotExist()
        compose.runOnIdle {
            assertEquals("meta", bar.selectedId)
            assertEquals(GalleryFilterSelection(), bar.filters)
            assertTrue(bar.publishEnabled)
        }
        val groupRequest = pageRequests().single { it.requestUrl!!.queryParameter("workspace_id") == "meta" }
        assertNull(groupRequest.requestUrl!!.queryParameter("cursor"))
        assertTrue(groupRequest.requestUrl!!.queryParameter("description_q").isNullOrEmpty())
        assertEquals(1, requests.count { it.requestUrl!!.encodedPath == "/workspaces" })
    }
}

/** Device ingestion credentials are unrelated to the human gallery session. */
@Implements(value = DeviceProvisioningStore::class, isInAndroidSdk = false)
class GalleryDeviceProvisioningShadow {
    @Implementation
    @Suppress("UNUSED_PARAMETER", "FunctionName")
    fun __constructor__(context: Context) = Unit

    @Implementation
    fun read(): DeviceProvisioning? = null
}
