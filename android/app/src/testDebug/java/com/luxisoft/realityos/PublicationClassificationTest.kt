package com.luxisoft.realityos

import android.app.Application
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Surface
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import java.io.File
import java.time.LocalDate
import java.time.ZoneId
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

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "es-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class PublicationClassificationTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @Before fun initialize() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
    }

    @After fun reset() {
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun post(video: Boolean): JSONObject = JSONObject()
        .put("thumbnail_url", "").put("source", "simulator-work")
        .put("caption", "Medical instruments")
        .put("mime_type", if (video) "video/mp4" else "image/jpeg")
        .put("category", JSONObject().put("name", "Instrumental clínico"))
        .put("tags", JSONArray().put(JSONObject().put("name", "Pinzas")).put(JSONObject().put("name", "Tijeras")).put(JSONObject().put("name", "Bandejas")))

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val directory = File("build/outputs/publication-classification").apply { mkdirs() }
            android.view.inspector.WindowInspector.getGlobalWindowViews().filter { it.width > 0 && it.height > 0 }.forEachIndexed { index, view ->
                val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
                view.draw(android.graphics.Canvas(bitmap))
                File(directory, "$name-$index.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
                bitmap.recycle()
            }
        }
    }

    private fun thumbnails(name: String, scale: Float) {
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    Surface(Modifier.fillMaxSize()) {
                        Row(Modifier.fillMaxWidth().padding(8.dp)) {
                            PublicationThumbnail(PublicationSummary.read(post(false)), Modifier.weight(1f).aspectRatio(.75f)) {}
                            PublicationThumbnail(PublicationSummary.read(post(true)), Modifier.weight(1f).aspectRatio(.75f)) {}
                        }
                    }
                }
            }
        }
        capture(name)
        compose.onAllNodesWithTag("publication-classification", useUnmergedTree = true).assertCountEquals(2)
        compose.onNodeWithTag("publication-video", useUnmergedTree = true).assertIsDisplayed()
        compose.onAllNodesWithText(" +1", useUnmergedTree = true).assertCountEquals(2)
        compose.onNodeWithTag("publication-simulated").assertDoesNotExist()
    }

    @Test fun spanishThumbnails() = thumbnails("es-390", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun narrowSpanishThumbnailsAtLargeText() = thumbnails("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun narrowEnglishThumbnailsAtLargeText() = thumbnails("en-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w480dp-h900dp-mdpi")
    fun wideEnglishThumbnails() = thumbnails("en-480", 1f)

    @Test fun filterDatesUseLocalDaysAndEscapeDescription() {
        val selection = GalleryFilterSelection(categories = setOf("category"), tags = setOf("tag"), owners = setOf("owner"), from = LocalDate.parse("2026-03-08"), through = LocalDate.parse("2026-03-08"), text = "100% ready & tools")
        val query = android.net.Uri.parse("https://example.invalid/?" + selection.query(ZoneId.of("America/New_York")))
        assertEquals("2026-03-08T05:00:00Z", query.getQueryParameter("published_from"))
        assertEquals("2026-03-09T04:00:00Z", query.getQueryParameter("published_before"))
        assertEquals("100% ready & tools", query.getQueryParameter("description_q"))
        assertTrue(selection.active)
        assertFalse(selection.copy(through = LocalDate.parse("2026-03-07")).valid)
        assertFalse(GalleryFilterSelection().active)
    }
}
