package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class AppNoticeTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    @Before fun reset() {
        AppNotices.pending.value = emptyList()
    }

    @After fun clear() {
        AppNotices.pending.value = emptyList()
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun referenceMismatchFitsNarrowSpanishNoticeWithLargeText() = referenceMismatchNotice(RealityLanguage.SPANISH, "es")

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun referenceMismatchFitsNarrowEnglishNoticeWithLargeText() = referenceMismatchNotice(RealityLanguage.ENGLISH, "en")

    private fun referenceMismatchNotice(language: RealityLanguage, name: String) {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(language)
        RuntimeEnvironment.setFontScale(2f)
        val message = "3: " + checkNotNull(recognitionPhotoFailure("faces/reference-photos", 422, """{"detail":"This photo does not match the registered face."}"""))
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, 2f)) {
                RealityOsTheme { NoticeLayer {} }
            }
        }
        compose.runOnIdle { AppNotices.show(message, NoticeKind.ERROR) }
        compose.onNodeWithText(message).assertIsDisplayed()
        val layouts = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
        compose.onNodeWithText(message).performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult) { it(layouts) }
        assertTrue(layouts.isNotEmpty() && layouts.none { it.hasVisualOverflow })
        val notice = compose.onNodeWithTag("app-notice").fetchSemanticsNode().boundsInRoot
        val root = compose.onRoot().fetchSemanticsNode().boundsInRoot
        assertTrue(notice.top >= root.top && notice.bottom <= root.bottom)
        compose.runOnIdle {
            val view = compose.activity.findViewById<android.view.View>(android.R.id.content)
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val directory = File("build/outputs/recognition-design").apply { mkdirs() }
            File(directory, "reference-mismatch-$name-320-large.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
        compose.onNodeWithTag("notice-dismiss").assertIsDisplayed().performClick()
        compose.onNodeWithTag("app-notice").assertDoesNotExist()
    }

    @Test fun foregroundPanelShowsOneDismissibleNoticeAndThenTheNext() {
        compose.setContent {
            MaterialTheme { NoticeLayer { NoticeLayer {} } }
        }
        compose.runOnIdle {
            AppNotices.show("First error", NoticeKind.ERROR)
            AppNotices.show("Saved", NoticeKind.SUCCESS)
        }
        compose.onAllNodesWithTag("app-notice").assertCountEquals(1)
        compose.onNodeWithText("First error").assertIsDisplayed()
        compose.onNodeWithTag("notice-dismiss").performClick()
        compose.onNodeWithText("First error").assertDoesNotExist()
        compose.onNodeWithText("Saved").assertIsDisplayed()
        compose.onNodeWithTag("notice-dismiss").performClick()
        compose.onNodeWithTag("app-notice").assertDoesNotExist()
    }
}
