package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
class AppNoticeTest {
    @get:Rule val compose = createComposeRule()

    @Before fun reset() { AppNotices.pending.value = emptyList() }
    @After fun clear() { AppNotices.pending.value = emptyList() }

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
