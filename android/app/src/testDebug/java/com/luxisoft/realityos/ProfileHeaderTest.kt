package com.luxisoft.realityos

import android.app.Application
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertHeightIsEqualTo
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToNode
import androidx.compose.ui.unit.dp
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "w320dp-h800dp")
class ProfileHeaderTest {
    @get:Rule val compose = createComposeRule()

    private fun profile(userId: String? = null) = ProfileState(userId).apply {
        apply(
            JSONObject().put("display_name", "Sample person").put("email", "sample@example.test")
                .put("facebook_link", "https://facebook.invalid/sample").put("location", "Madrid")
                .put("hometown", "Lima").put("cv", JSONObject().put("present", false))
        )
    }

    @Test fun compactHeaderKeepsEmailActionsAndCollapsibleLocation() {
        val state = profile()
        var glasses = 0
        var menus = 0
        compose.setContent {
            MaterialTheme { Box(Modifier.width(320.dp)) { ProfileHeader(state, onMenu = { menus++ }, onGlasses = { glasses++ }) } }
        }
        compose.onNodeWithTag("global-profile-header").assertHeightIsEqualTo(96.dp)
        compose.onNodeWithText("sample@example.test").assertIsDisplayed()
        compose.onNodeWithText("Madrid").assertDoesNotExist()
        compose.onNodeWithTag("profile-facebook").assertIsDisplayed()
        compose.onNodeWithTag("profile-glasses").performClick()
        compose.onNodeWithTag("host-menu-button").performClick()
        compose.runOnIdle {
            assertEquals(1, glasses)
            assertEquals(1, menus)
        }
        compose.onNodeWithTag("profile-expand").performClick()
        compose.onNodeWithText("Madrid").assertIsDisplayed()
        compose.onNodeWithText("Lima").assertIsDisplayed()
        compose.onNodeWithTag("profile-expand").performClick()
        compose.onNodeWithTag("profile-details").assertDoesNotExist()
    }

    @Test fun visitedProfileHasBackWithoutPersonalControls() {
        val state = profile("other")
        var backs = 0
        compose.setContent { MaterialTheme { ProfileHeader(state, onBack = { backs++ }) } }
        compose.onNodeWithText("Sample person").assertIsDisplayed()
        compose.onNodeWithTag("profile-edit").assertDoesNotExist()
        compose.onNodeWithTag("profile-glasses").assertDoesNotExist()
        compose.onNodeWithTag("host-menu-button").performClick()
        compose.runOnIdle { assertEquals(1, backs) }
    }

    @Test fun sharedProfileChangesRefreshTheVisibleHeader() {
        val state = profile()
        compose.setContent { MaterialTheme { ProfileHeader(state) } }
        compose.runOnIdle { state.apply(JSONObject().put("display_name", "Updated name").put("email", "updated@example.test")) }
        compose.onNodeWithText("Updated name").assertIsDisplayed()
        compose.onNodeWithText("updated@example.test").assertIsDisplayed()
        compose.onNodeWithText("sample@example.test").assertDoesNotExist()
    }

    @Test fun editActionOpensTheProfileEditor() {
        val state = profile()
        compose.setContent { MaterialTheme { ProfileHeader(state) } }
        compose.onNodeWithText("Upload resume").assertDoesNotExist()
        compose.onNodeWithTag("profile-edit").performClick()
        compose.onNodeWithTag("profile-edit-fields").performScrollToNode(hasTestTag("profile-cv-upload"))
        compose.onNodeWithTag("profile-cv-upload").assertIsDisplayed()
    }

    @Test fun languageSelectorSavesWithoutOpeningAnotherScreen() {
        val store = RealityExperienceStore(androidx.test.core.app.ApplicationProvider.getApplicationContext())
        store.clearForTesting()
        var chosen: RealityLanguage? = null
        compose.setContent {
            MaterialTheme {
                com.luxisoft.realityos.host.DrawerLanguageSelector(store) {
                    chosen = it
                    store.setLanguage(it)
                }
            }
        }
        compose.onNodeWithText("ES").performClick()
        compose.runOnIdle {
            assertEquals(RealityLanguage.SPANISH, chosen)
            assertEquals(RealityLanguage.SPANISH, store.selectedLanguage())
            store.clearForTesting()
        }
        compose.onNodeWithTag("language-save-error").assertDoesNotExist()
    }

    @Test fun languageSaveFailureKeepsThePreviousPreference() {
        val store = RealityExperienceStore(androidx.test.core.app.ApplicationProvider.getApplicationContext())
        store.clearForTesting()
        compose.setContent {
            MaterialTheme { com.luxisoft.realityos.host.DrawerLanguageSelector(store) { throw java.io.IOException("offline") } }
        }
        compose.onNodeWithText("ES").performClick()
        compose.onNodeWithTag("language-save-error").assertIsDisplayed()
        compose.runOnIdle { assertEquals(RealityLanguage.ENGLISH, store.selectedLanguage()) }
    }

    @Test fun retainedWorkDemoHasAnExplicitSimulationLabel() {
        val source = androidx.compose.runtime.mutableStateOf("local")
        compose.setContent { MaterialTheme { PublicationSourceBadge(source.value) } }
        compose.onNodeWithTag("publication-simulated").assertDoesNotExist()
        compose.runOnIdle { source.value = "simulator-work" }
        compose.onNodeWithTag("publication-simulated").assertIsDisplayed()
    }
}
