package com.luxisoft.realityos

import android.app.Application
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "en-w480dp-h1000dp")
class StorageResultsTest {
    @get:Rule val compose = createComposeRule()

    @Before fun initializeLanguage() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        RealityExperienceStore(context).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun opensResult(number: Int) {
        val items = (1..3).map { index ->
            GalleryThumb(
                thumbnailUrl = "file:///synthetic-$index.png",
                mediaUrl = "file:///synthetic-$index.png",
                caption = "Result $index",
                evidenceId = "evidence-$index",
                matchedLabels = listOf("item"),
                localizedInformation = mapOf("en" to EvidenceText("Evidence $index", "", listOf("item")))
            )
        }
        compose.setContent {
            var selected by remember { mutableStateOf<StorageEvidenceSelection?>(null) }
            MaterialTheme {
                val current = selected
                if (current == null) {
                    Column {
                        StorageResultButtons(items, onProfile = { error("Unexpected profile") }, onRecord = { error("Unexpected record") }, onEvidence = { selected = it })
                    }
                } else {
                    StorageEvidenceViewer(current) { selected = null }
                }
            }
        }
        compose.onNodeWithText("Result $number").performClick()
        compose.onAllNodesWithText("Evidence $number").onFirst().assertIsDisplayed()
    }

    @Test fun opensSecondResult() = opensResult(2)

    @Test fun opensLastResult() = opensResult(3)
}
