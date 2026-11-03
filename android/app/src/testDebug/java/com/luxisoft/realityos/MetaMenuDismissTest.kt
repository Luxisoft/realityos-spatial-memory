package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.luxisoft.realityos.host.PreviewControlsOverlay
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "w390dp-h844dp-mdpi")
class MetaMenuDismissTest {
    @get:Rule val compose = createComposeRule()

    @Test fun outsideTouchAndRightSwipeBothCloseControls() {
        val visible = mutableStateOf(true)
        compose.setContent {
            MaterialTheme {
                PreviewControlsOverlay(visible.value, { visible.value = false }) { Text("Controls") }
            }
        }
        compose.onNodeWithTag("meta-controls-scrim").performTouchInput { click(Offset(4f, centerY)) }
        compose.onNodeWithTag("preview-controls-drawer").assertDoesNotExist()
        compose.runOnIdle { visible.value = true }
        compose.onNodeWithTag("preview-controls-drawer").performTouchInput { swipeRight() }
        compose.onNodeWithTag("preview-controls-drawer").assertDoesNotExist()
    }
}
