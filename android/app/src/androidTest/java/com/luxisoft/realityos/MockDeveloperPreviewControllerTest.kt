package com.luxisoft.realityos

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.meta.wearable.dat.core.types.Permission
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Exercises the Debug-only controller that powers the manual phone preview.
 * It deliberately covers Meta's renderer rather than reproducing Display UI.
 */
@RunWith(AndroidJUnit4::class)
class MockDeveloperPreviewControllerTest {
    private lateinit var controller: MockDeveloperPreviewController

    @Before
    fun set_up() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        controller = MockDeveloperPreviewController(context)
    }

    @After
    fun tear_down() = runBlocking {
        if (::controller.isInitialized) controller.stop()
    }

    @Test
    fun starts_an_in_app_display_preview_and_releases_it() = runBlocking {
        val identifier = controller.start(DeveloperPreviewMode.IN_APP)

        assertNotNull(identifier)
        assertTrue(controller.state.value.active)
        assertEquals(DeveloperPreviewMode.IN_APP, controller.state.value.mode)
        assertTrue(controller.state.value.poweredOn)
        assertTrue(controller.state.value.unfolded)
        assertTrue(controller.state.value.worn)

        var preview: android.view.View? = null
        InstrumentationRegistry.getInstrumentation().runOnMainSync {
            preview = controller.createInAppPreviewView(
                InstrumentationRegistry.getInstrumentation().targetContext,
            )
        }
        assertNotNull(preview)

        controller.setDatPermission(Permission.CAMERA, granted = false)
        controller.simulateTranscription("Where is the yellow drill?", isFinal = false)
        controller.simulateTranscription("Where is the yellow drill?", isFinal = true)
        controller.stop()

        assertFalse(controller.state.value.active)
    }

    @Test
    fun starts_a_chrome_preview_server_with_a_forwardable_url() = runBlocking {
        val identifier = controller.start(DeveloperPreviewMode.CHROME)

        assertNotNull(identifier)
        val chrome = controller.state.value.chrome
        assertNotNull(chrome)
        assertTrue(chrome!!.port > 0)
        assertTrue(chrome.adbForwardCommand.contains("tcp:${chrome.port}"))
        assertEquals("http://127.0.0.1:${chrome.port}/", chrome.url)
    }
}
