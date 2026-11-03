package com.luxisoft.realityos

import android.app.Application
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CompletableDeferred
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "en-w480dp-h1000dp")
class WorkspaceRecordsTest {
    @get:Rule val compose = createComposeRule()

    private fun record(id: String) = JSONObject().put("id", id).put("title", "Patient $id")
        .put("external_id", "external-$id").put("version", 1).put("kind", "person")
        .put("occurred_at", "2026-11-02T12:00:00Z").put("data", JSONObject())
        .put("notes", JSONArray()).put("related", JSONArray()).put("media", JSONArray())

    private fun waitText(text: String) = compose.waitUntil(10000) {
        compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty()
    }

    @Test fun backCancelsPendingDetailAndKeepsRecordList() {
        val held = CompletableDeferred<String>()
        val started = AtomicInteger()
        var exits = 0
        compose.setContent {
            MaterialTheme {
                WorkspaceRecords("work", true, { exits++ }) { path, _ ->
                    if (path.endsWith("/a")) {
                        started.incrementAndGet()
                        held.await()
                    } else if (path.endsWith("/b")) {
                        record("b").toString()
                    } else {
                        JSONArray().put(record("a")).put(record("b")).toString()
                    }
                }
            }
        }
        waitText("Patient a")
        compose.onNodeWithText("Patient a").performClick()
        compose.waitUntil(10000) { started.get() == 1 }
        compose.onNodeWithText("Back").performClick()
        compose.runOnIdle { assertEquals(0, exits) }
        compose.onNodeWithText("Patient b").assertIsEnabled().performClick()
        waitText("external-b · v1")
        compose.runOnIdle { held.complete(record("a").toString()) }
        compose.waitForIdle()
        compose.onNodeWithText("external-b · v1").assertIsDisplayed()
        compose.onNodeWithText("external-a · v1").assertDoesNotExist()
    }

    @Test fun leavingPendingNoteDoesNotRestorePreviousPatient() {
        val held = CompletableDeferred<String>()
        val saving = AtomicInteger()
        compose.setContent {
            MaterialTheme {
                WorkspaceRecords("work", true, {}) { path, _ ->
                    when {
                        path.endsWith("/notes") -> {
                            saving.incrementAndGet()
                            held.await()
                        }
                        path.endsWith("/a") -> record("a").toString()
                        path.endsWith("/b") -> record("b").toString()
                        else -> JSONArray().put(record("a")).put(record("b")).toString()
                    }
                }
            }
        }
        waitText("Patient a")
        compose.onNodeWithText("Patient a").performClick()
        waitText("external-a · v1")
        compose.onNodeWithText("Add note").performTextInput("Note for patient a")
        compose.onNodeWithText("Save note").performScrollTo().performClick()
        compose.waitUntil(10000) { saving.get() == 1 }
        compose.onNodeWithText("Back").performScrollTo().performClick()
        compose.onNodeWithText("Patient b").assertIsEnabled().performClick()
        waitText("external-b · v1")
        compose.onNodeWithText("Add note").performTextInput("Draft for patient b")
        compose.runOnIdle { held.complete("{}") }
        compose.waitForIdle()
        compose.onNodeWithText("external-b · v1").assertIsDisplayed()
        compose.onNodeWithText("Draft for patient b").assertIsDisplayed()
    }
}
