package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.Surface
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import com.luxisoft.realityos.host.GalleryActions
import java.io.File
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
class WorkGroupActionsTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val actions = mutableListOf<String>()
    private val bar = GalleryTopBarState().apply {
        loading = false
        options = listOf(WorkspaceOption("group-a", "Grupo de trabajo", "admin"))
        selectedId = "group-a"
        showInvite = true
        showAdmin = true
        onCreate = { actions += "create-group" }
        onInvite = { actions += "invite-person" }
        onPublish = { actions += "publish-photo" }
        onAdmin = { actions += "admin" }
        onRecords = { actions += "records" }
    }

    @Before fun initialize() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(if (context.resources.configuration.locales[0].language == "es") RealityLanguage.SPANISH else RealityLanguage.ENGLISH)
    }

    @After fun reset() {
        RuntimeEnvironment.setFontScale(1f)
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun show(scale: Float = 1f) {
        RuntimeEnvironment.setFontScale(scale)
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme {
                    Surface { GalleryActions(bar) }
                }
            }
        }
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val views = android.view.inspector.WindowInspector.getGlobalWindowViews().filter { it.width > 0 && it.height > 0 }
            assertTrue(views.isNotEmpty())
            val directory = File("build/outputs/work-group-actions").apply { mkdirs() }
            views.forEachIndexed { index, view ->
                val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
                view.draw(android.graphics.Canvas(bitmap))
                File(directory, "$name-$index.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
                bitmap.recycle()
            }
        }
    }

    private fun checkDistinctActions(name: String, scale: Float) {
        show(scale)
        val create = compose.onNodeWithTag("work-create-group")
        val publish = compose.onNodeWithTag("work-publish")
        create.assertContentDescriptionEquals(localizedText(R.string.ui_create_group)).assertIsDisplayed()
        publish.assertContentDescriptionEquals(localizedText(R.string.ui_publish)).assertIsDisplayed()
        compose.onNodeWithTag("work-history").assertDoesNotExist()
        compose.onNodeWithContentDescription(localizedText(R.string.ui_select_workspace)).assertIsDisplayed()
        assertTrue(create.fetchSemanticsNode().boundsInRoot.right <= publish.fetchSemanticsNode().boundsInRoot.left)
        capture("toolbar-$name")
        create.performTouchInput { click() }
        compose.runOnIdle { assertEquals(listOf("create-group"), actions) }
        publish.performTouchInput { click() }
        compose.runOnIdle { assertEquals(listOf("create-group", "publish-photo"), actions) }
        compose.onNodeWithContentDescription(localizedText(R.string.ui_manage)).performTouchInput { click() }
        val invite = compose.onNodeWithTag("work-invite-person")
        invite.assertTextEquals(localizedText(R.string.ui_invite_person)).assertIsDisplayed()
        capture("menu-$name")
        invite.performTouchInput { click() }
        compose.runOnIdle { assertEquals(listOf("create-group", "publish-photo", "invite-person"), actions) }
        invite.assertDoesNotExist()
        compose.onNodeWithContentDescription(localizedText(R.string.ui_manage)).performTouchInput { click() }
        compose.onNodeWithTag("work-history").assertTextEquals(localizedText(R.string.ui_history)).assertIsDisplayed().performTouchInput { click() }
        compose.runOnIdle { assertEquals(listOf("create-group", "publish-photo", "invite-person", "records"), actions) }
        compose.onNodeWithTag("work-history").assertDoesNotExist()
    }

    @Test fun groupCreationPersonInvitationAndPublicationUseSeparateButtons() = checkDistinctActions("es-390", 1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun narrowSpanishToolbarKeepsCorrectTouchTargetsAtLargeText() = checkDistinctActions("es-320-large", 2f)

    @Test
    @Config(qualifiers = "en-w320dp-h640dp-mdpi")
    fun narrowEnglishToolbarKeepsCorrectTouchTargetsAtLargeText() = checkDistinctActions("en-320-large", 2f)

    @Test fun creatingGroupDoesNotRequireInvitationPermissionOrAnExistingGroup() {
        bar.selectedId = null
        bar.options = emptyList()
        bar.showInvite = false
        bar.showAdmin = false
        bar.publishEnabled = false
        show()
        compose.onNodeWithTag("work-create-group").assertIsEnabled().performTouchInput { click() }
        compose.runOnIdle { assertEquals(listOf("create-group"), actions) }
        compose.onNodeWithTag("work-publish").assertIsNotEnabled()
        compose.onNodeWithContentDescription(localizedText(R.string.ui_manage)).performTouchInput { click() }
        compose.onNodeWithTag("work-history").assertIsNotEnabled()
        compose.onNodeWithTag("work-invite-person").assertDoesNotExist()
    }
}
