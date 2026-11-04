package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.Surface
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import java.time.LocalDate
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
class GalleryFiltersTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val requestedGroups = mutableListOf<String?>()
    private val selected = GalleryFilterSelection(categories = setOf("category"), tags = setOf("tag"), owners = setOf("owner"), from = LocalDate.parse("2026-11-01"), through = LocalDate.parse("2026-11-03"))
    private val bar = GalleryTopBarState().apply {
        selectedId = "operations"
        filters = selected
        onFilters = { filters = it }
    }

    @Before fun start() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
    }

    @After fun stop() {
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val directory = File("build/outputs/publication-classification").apply { mkdirs() }
            android.view.inspector.WindowInspector.getGlobalWindowViews().filter { it.width > 0 && it.height > 0 }.forEachIndexed { index, view ->
                val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
                view.draw(android.graphics.Canvas(bitmap))
                File(directory, "filters-$name-$index.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
                bitmap.recycle()
            }
        }
    }

    private fun applyAndClear(name: String, scale: Float) {
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    Surface {
                        GalleryFilterButton(bar) { group ->
                            requestedGroups += group
                            JSONObject("""{"categories":[{"id":"category","name":"Equipment"}],"tags":[{"id":"tag","name":"Ready"}],"owners":[{"id":"owner","name":"Alex"}]}""")
                        }
                    }
                }
            }
        }
        compose.onNodeWithText(localizedText(R.string.gallery_filters)).assertDoesNotExist()
        compose.onNodeWithTag("gallery-filter").assertContentDescriptionEquals(localizedText(R.string.gallery_filters)).performClick()
        val category = localizedText(R.string.catalog_categories) + ": Equipment"
        compose.waitUntil(10000) { compose.onAllNodesWithText(category).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText(category).assertIsDisplayed()
        capture("$name-top")
        compose.onNodeWithText(localizedText(R.string.gallery_authors) + ": Alex").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_from) + ": 2026-11-01").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextInput("100% ready & tools")
        compose.onNodeWithText(localizedText(R.string.gallery_apply)).performScrollTo().assertIsDisplayed()
        capture("$name-bottom")
        compose.onNodeWithText(localizedText(R.string.gallery_apply)).performClick()
        compose.runOnIdle { assertEquals(selected.copy(text = "100% ready & tools"), bar.filters) }
        compose.onNodeWithTag("gallery-filter").performClick()
        compose.onNodeWithText(localizedText(R.string.gallery_clear)).performScrollTo().performClick()
        compose.runOnIdle { assertEquals(GalleryFilterSelection(), bar.filters) }
        assertEquals(listOf("operations", "operations"), requestedGroups)
    }

    @Test fun spanishFiltersApplyAndClear() = applyAndClear("es-390", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun narrowSpanishFiltersAtLargeText() = applyAndClear("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun narrowEnglishFiltersAtLargeText() = applyAndClear("en-320-large", 2f)

    @Test fun loadingFailureKeepsSelectionsAndCanRetry() {
        var attempts = 0
        compose.setContent {
            RealityOsTheme {
                Surface {
                    GalleryFilterButton(bar) {
                        attempts++
                        if (attempts == 1) throw java.io.IOException("Offline")
                        JSONObject("""{"categories":[{"id":"category","name":"Equipment"}],"tags":[],"owners":[]}""")
                    }
                }
            }
        }
        compose.onNodeWithTag("gallery-filter").performClick()
        compose.onNodeWithText("Offline").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_apply)).performScrollTo().assertIsNotEnabled()
        compose.runOnIdle { assertEquals(selected, bar.filters) }
        compose.onNodeWithText(localizedText(R.string.ui_retry)).performScrollTo().performClick()
        compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": Equipment").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Offline").assertDoesNotExist()
        compose.runOnIdle { assertEquals(2, attempts) }
    }
}
