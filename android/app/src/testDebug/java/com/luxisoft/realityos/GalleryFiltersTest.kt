package com.luxisoft.realityos

import android.app.Application
import android.view.KeyEvent
import androidx.compose.material3.Surface
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import java.time.LocalDate
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext
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
import org.robolectric.shadows.ShadowDialog

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "es-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class GalleryFiltersTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val applied = mutableListOf<GalleryFilterSelection>()
    private val requestedGroups = mutableListOf<String?>()
    private val selected = GalleryFilterSelection(categories = setOf("category"), tags = setOf("tag"), owners = setOf("owner"), from = LocalDate.parse("2026-11-01"), through = LocalDate.parse("2026-11-03"))
    private val bar = GalleryTopBarState().apply {
        selectedId = "operations"
        filters = selected
        onFilters = {
            applied += it
            filters = it
        }
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

    private fun automaticChangesAndClear(name: String, scale: Float) {
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    Surface {
                        GalleryFilterButton(bar) { group ->
                            requestedGroups += group
                            PublicationCatalog.read(JSONObject("""{"categories":[{"id":"category","name":"Equipment"}],"tags":[{"id":"tag","name":"Ready"}],"owners":[{"id":"owner","name":"Alex"}]}"""))
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
        val title = compose.onNodeWithTag("gallery-filter-title").fetchSemanticsNode().boundsInRoot
        val clear = compose.onNodeWithTag("gallery-filter-clear").assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        assertTrue(title.right <= clear.left)
        assertEquals(title.center.y, clear.center.y, 1f)
        capture("$name-top")
        compose.onNodeWithText(localizedText(R.string.gallery_authors) + ": Alex").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_from) + ": " + evidenceDate("2026-11-01", LocalizedText.languageTag)).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextInput("100% ready & tools")
        compose.runOnIdle { assertEquals(selected.copy(text = "100% ready & tools"), bar.filters) }
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performTextReplacement("next")
        compose.runOnIdle {
            assertEquals(selected.copy(text = "next"), bar.filters)
            assertEquals(listOf("100% ready & tools", "next"), applied.map { it.text })
        }
        capture("$name-bottom")
        compose.onNodeWithTag("gallery-filter-clear").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(GalleryFilterSelection(), bar.filters) }
        compose.onNodeWithTag("gallery-filter-title").assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextInput("new filter")
        compose.runOnIdle { assertEquals(GalleryFilterSelection(text = "new filter"), bar.filters) }
        assertEquals(listOf("operations"), requestedGroups)
    }

    @Test fun spanishFiltersApplyAutomaticallyAndClear() = automaticChangesAndClear("es-390", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun narrowSpanishFiltersAtLargeText() = automaticChangesAndClear("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun narrowEnglishFiltersAtLargeText() = automaticChangesAndClear("en-320-large", 2f)

    @Test fun loadingFailureKeepsSelectionsAndCanRetry() {
        var attempts = 0
        compose.setContent {
            RealityOsTheme {
                Surface {
                    GalleryFilterButton(bar) {
                        attempts++
                        if (attempts == 1) throw java.io.IOException("Offline")
                        PublicationCatalog.read(JSONObject("""{"categories":[{"id":"category","name":"Equipment"}],"tags":[],"owners":[]}"""))
                    }
                }
            }
        }
        compose.onNodeWithTag("gallery-filter").performClick()
        compose.onNodeWithText(localizedText(R.string.account_network_error)).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": " + localizedText(R.string.catalog_select)).performScrollTo().assertIsNotEnabled()
        compose.runOnIdle { assertEquals(selected, bar.filters) }
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextInput("works offline")
        compose.runOnIdle { assertEquals(selected.copy(text = "works offline"), bar.filters) }
        compose.onNodeWithText(localizedText(R.string.ui_retry)).performScrollTo().performClick()
        compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": Equipment").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.account_network_error)).assertDoesNotExist()
        compose.runOnIdle { assertEquals(2, attempts) }
    }

    @Test
    @Config(qualifiers = "en-w480dp-h900dp-mdpi")
    fun wideEnglishFiltersApplyAutomatically() = automaticChangesAndClear("en-480", 1f)

    private fun showFilters(fetch: suspend (String?) -> PublicationCatalog = { catalog() }) {
        compose.setContent { RealityOsTheme { Surface { GalleryFilterButton(bar, fetch) } } }
        compose.onNodeWithTag("gallery-filter").performClick()
    }

    private fun catalog() = PublicationCatalog.read(JSONObject("""{"categories":[{"id":"category","name":"Equipment"},{"id":"second","name":"Vehicles"}],"tags":[{"id":"tag","name":"Ready"}],"owners":[{"id":"owner","name":"Alex"}]}"""))

    private fun closeCatalogMenu() {
        compose.runOnIdle {
            val popup = android.view.inspector.WindowInspector.getGlobalWindowViews().last()
            popup.dispatchKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BACK))
            popup.dispatchKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_BACK))
        }
    }

    @Test fun catalogChangesApplyEachSelectionWithoutClosingFilters() {
        showFilters()
        compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": Equipment").performClick()
        compose.onNodeWithText("Vehicles").performClick()
        compose.runOnIdle { assertEquals(setOf("category", "second"), bar.filters.categories) }
        compose.onNodeWithText("Equipment").performClick()
        compose.runOnIdle { assertEquals(setOf("second"), bar.filters.categories) }
        closeCatalogMenu()
        compose.onNodeWithText(localizedText(R.string.catalog_tags) + ": Ready").performScrollTo().performClick()
        compose.onNodeWithText("Ready").performClick()
        compose.runOnIdle { assertTrue(bar.filters.tags.isEmpty()) }
        closeCatalogMenu()
        compose.onNodeWithText(localizedText(R.string.gallery_authors) + ": Alex").performScrollTo().performClick()
        compose.onNodeWithText("Alex").performClick()
        compose.runOnIdle {
            assertTrue(bar.filters.owners.isEmpty())
            assertEquals(4, applied.size)
        }
        closeCatalogMenu()
        compose.onNodeWithTag("gallery-filter-title").performScrollTo().assertIsDisplayed()
    }

    private fun selectNovemberDay(day: Int) {
        val date = SemanticsMatcher("November $day, 2026") { node ->
            val labels = node.config.getOrNull(SemanticsProperties.Text).orEmpty().map { it.text } + node.config.getOrNull(SemanticsProperties.ContentDescription).orEmpty()
            labels.any { it.contains("2026") && it.contains("nov", ignoreCase = true) && Regex("\\b$day\\b").containsMatchIn(it) }
        }
        compose.onNode(date and hasClickAction()).performClick()
    }

    @Test fun invalidDatesKeepLastValidQueryUntilCorrectedAndDismissDoesNotApply() {
        showFilters()
        compose.onNodeWithText(localizedText(R.string.gallery_from) + ": " + evidenceDate("2026-11-01", LocalizedText.languageTag)).performScrollTo().performClick()
        selectNovemberDay(5)
        compose.onNodeWithText(localizedText(R.string.ui_accept)).performClick()
        compose.onNodeWithText(localizedText(R.string.gallery_dates_invalid)).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextInput("pending dates")
        compose.runOnIdle {
            assertEquals(selected, bar.filters)
            assertTrue(applied.isEmpty())
        }
        compose.onNodeWithText(localizedText(R.string.gallery_through) + ": " + evidenceDate("2026-11-03", LocalizedText.languageTag)).performScrollTo().performClick()
        selectNovemberDay(9)
        compose.onNodeWithText(localizedText(R.string.ui_accept)).performClick()
        val corrected = selected.copy(from = LocalDate.parse("2026-11-05"), through = LocalDate.parse("2026-11-09"), text = "pending dates")
        compose.runOnIdle { assertEquals(listOf(corrected), applied) }
        compose.onNodeWithText(localizedText(R.string.gallery_dates_invalid)).assertDoesNotExist()
        compose.onNodeWithText(localizedText(R.string.gallery_from) + ": " + evidenceDate("2026-11-05", LocalizedText.languageTag)).performScrollTo().performClick()
        selectNovemberDay(7)
        compose.runOnIdle { (ShadowDialog.getLatestDialog() as androidx.activity.ComponentDialog).onBackPressedDispatcher.onBackPressed() }
        compose.onNode(isDialog()).assertDoesNotExist()
        compose.runOnIdle { assertEquals(listOf(corrected), applied) }
        compose.onNodeWithText(localizedText(R.string.gallery_from) + ": " + evidenceDate("2026-11-05", LocalizedText.languageTag)).performScrollTo().performClick()
        compose.onNode(hasText(localizedText(R.string.gallery_clear)) and hasAnyAncestor(isDialog())).performClick()
        compose.runOnIdle { assertEquals(corrected.copy(from = null), bar.filters) }
        compose.onNodeWithTag("gallery-filter-clear").performScrollTo().performClick()
        compose.runOnIdle { assertEquals(GalleryFilterSelection(), bar.filters) }
        compose.onNodeWithTag("gallery-filter-title").assertIsDisplayed()
    }

    @Test fun groupChangeCancelsOldCatalogAndPickerAndSynchronizesExternalFilters() {
        val oldCatalog = CompletableDeferred<PublicationCatalog>()
        showFilters { group ->
            requestedGroups += group
            if (group == "operations") oldCatalog.await() else catalog()
        }
        compose.onNodeWithText(localizedText(R.string.gallery_from) + ": " + evidenceDate("2026-11-01", LocalizedText.languageTag)).performScrollTo().performClick()
        compose.runOnIdle {
            bar.selectedId = "second-group"
            bar.filters = GalleryFilterSelection(text = "external")
        }
        compose.onNode(isDialog()).assertDoesNotExist()
        compose.runOnIdle { oldCatalog.complete(PublicationCatalog.read(JSONObject("""{"categories":[{"id":"stale","name":"Wrong group"}]}"""))) }
        compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": " + localizedText(R.string.catalog_select)).performScrollTo().performClick()
        compose.onNodeWithText("Equipment").assertIsDisplayed()
        compose.onNodeWithText("Wrong group").assertDoesNotExist()
        closeCatalogMenu()
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextReplacement("next group")
        compose.runOnIdle {
            assertEquals(listOf("operations", "second-group"), requestedGroups)
            assertEquals(listOf(GalleryFilterSelection(text = "next group")), applied)
            bar.filters = GalleryFilterSelection(owners = setOf("owner"), text = "restored")
        }
        compose.onNodeWithText(localizedText(R.string.gallery_description)).performScrollTo().performTextReplacement("after restore")
        compose.runOnIdle { assertEquals(GalleryFilterSelection(owners = setOf("owner"), text = "after restore"), applied.last()) }
    }

    @Test fun reopeningFiltersIgnoresCancelledCatalogWithoutClearingCurrentLoading() {
        val oldCatalog = CompletableDeferred<PublicationCatalog>()
        val newCatalog = CompletableDeferred<PublicationCatalog>()
        var attempts = 0
        try {
            showFilters {
                attempts++
                if (attempts == 1) withContext(NonCancellable) { oldCatalog.await() } else newCatalog.await()
            }
            closeCatalogMenu()
            compose.onNodeWithTag("gallery-filter-title").assertDoesNotExist()
            compose.onNodeWithTag("gallery-filter").performClick()
            compose.runOnIdle {
                assertEquals(2, attempts)
                oldCatalog.complete(PublicationCatalog.read(JSONObject("""{"categories":[{"id":"stale","name":"Stale"}]}""")))
            }
            compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": " + localizedText(R.string.catalog_select)).assertIsNotEnabled()
            compose.runOnIdle { newCatalog.complete(catalog()) }
            compose.onNodeWithText(localizedText(R.string.catalog_categories) + ": Equipment").assertIsEnabled().performClick()
            compose.onNodeWithText("Vehicles").assertIsDisplayed()
            compose.onNodeWithText("Stale").assertDoesNotExist()
        } finally {
            oldCatalog.complete(catalog())
            newCatalog.complete(catalog())
        }
    }
}
