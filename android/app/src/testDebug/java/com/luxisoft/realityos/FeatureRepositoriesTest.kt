package com.luxisoft.realityos

import android.app.Application
import com.luxisoft.realityos.data.JsonApi
import com.luxisoft.realityos.data.SessionJsonApi
import com.luxisoft.realityos.data.get
import java.net.HttpURLConnection
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], application = Application::class)
class FeatureRepositoriesTest {
    @Test fun localListKeepsDistinctWorkspaceIdsAndNullAvatars() = runBlocking {
        val repository = LocalAccountRepository(
            JsonApi { path, method, body ->
                assertEquals("auth/local-accounts", path)
                assertEquals("GET", method)
                assertNull(body)
                """{"local_access":true,"accounts":[
                {"id":"a","username":"alex","display_name":"Alex","workspace_id":"one","workspace_name":"Operations","picture_url":null},
                {"id":"b","username":"elena","display_name":"Elena","workspace_id":"two","workspace_name":"Operations","picture_url":"/v1/avatar/b"}
            ]}"""
            }
        )
        val accounts = repository.accounts()
        assertEquals(listOf("one", "two"), accounts.map { it.workspaceId })
        assertNull(accounts.first().pictureUrl)
        assertEquals("/v1/avatar/b", accounts.last().pictureUrl)
    }

    @Test fun localSelectionRejectsAResponseForAnotherWorkspace() {
        val repository = LocalAccountRepository(
            JsonApi { _, _, _ ->
                """{"local_access":true,"access_token":"access","refresh_token":"refresh","capture_profile":{"workspace_id":"other"}}"""
            }
        )
        assertThrows(IllegalStateException::class.java) {
            runBlocking { repository.select(LocalAccount("a", "alex", "Alex", "one", "Operations")) }
        }
    }

    @Test fun nonLocalResponseCannotPopulateLocalChooser() {
        val repository = LocalAccountRepository(JsonApi { _, _, _ -> """{"local_access":false,"accounts":[]}""" })
        assertThrows(IllegalStateException::class.java) { runBlocking { repository.accounts() } }
    }

    @Test fun galleryPreservesDatabaseCopyAndEncodesPagingContext() = runBlocking {
        val repository = GalleryRepository(
            JsonApi { path, method, _ ->
                assertEquals("GET", method)
                assertTrue(path.contains("workspace_id=work"))
                assertTrue(path.contains("cursor=next%2Bpage%3D"))
                assertTrue(path.contains("description_q=keys"))
                """{"items":[{"id":"post","workspace_id":"work","caption":"Keys","display_text":{"caption":{"source":"Keys","en":"Keys","es":"Llaves"}},"liked":true,"owned":false,"category":{"id":"category","name":"Objects"},"tags":[{"id":"tag","name":"Keys"}],"owner":{"display_name":"Alex"}}],"next_cursor":null}"""
            }
        )
        val page = repository.page("work", "next+page=", GalleryFilterSelection(text = "keys"))
        assertNull(page.nextCursor)
        val post = page.publications.single()
        assertEquals("Llaves", post.caption.display("es"))
        assertEquals("Keys", post.caption.display("en"))
        assertTrue(post.liked)
        assertFalse(post.owned)
        assertEquals(setOf("tag"), post.classification.tagIds)
    }

    @Test fun recordNoteRefreshUsesTheSameWorkspaceAndDocument() = runBlocking {
        val requests = mutableListOf<String>()
        val repository = WorkspaceRecordsRepository(
            "work",
            JsonApi { path, method, body ->
                requests += "$method $path"
                if (method == "POST") {
                    assertEquals("Reviewed", body!!.getString("text"))
                    "{}"
                } else {
                    """{"id":"record","external_id":"external","title":"Record","kind":"case","version":2,"notes":[{"text":"Reviewed","occurred_at":"2026-11-04T12:00:00Z"}]}"""
                }
            }
        )
        val details = repository.addNote("record", "Reviewed")
        assertEquals(listOf("POST workspaces/work/records/record/notes", "GET workspaces/work/records/record"), requests)
        assertEquals("Reviewed", details.notes.single().text)
        assertEquals(2, details.record.version)
    }

    @Test fun catalogKeepsArchivedTermsAndScopesManagementRequestsToTheGroup() = runBlocking {
        val requests = mutableListOf<String>()
        val repository = GalleryRepository(
            JsonApi { path, method, body ->
                requests += "$method $path"
                if (method == "GET") {
                    """{"can_manage":true,"categories":[{"id":"category","name":"Tools","workspace_name":"Operations","active":false,"display_text":{"name":{"es":"Herramientas"}}}],"tags":[]}"""
                } else {
                    assertEquals("Supplies", body!!.getString("name"))
                    assertTrue(body.getBoolean("active"))
                    "{}"
                }
            }
        )
        val catalog = repository.catalog("work")
        assertTrue(catalog.canManage)
        val term = catalog.categories.single()
        assertFalse(term.active)
        assertEquals("Herramientas", term.name.display("es"))
        assertEquals("Operations", term.workspaceName)
        repository.saveCatalogTerm("work", term, "category", "Supplies", true)
        repository.saveCatalogTerm("work", null, "tag", "Supplies", true)
        assertEquals(listOf("GET groups/work/publication-catalog", "PATCH groups/work/publication-catalog/category", "POST groups/work/publication-catalog/tag"), requests)
    }

    @Test fun aRepositoryFromAnOldSessionCannotIssueARequestAsTheNewAccount() {
        LocalizedText.initialize(RuntimeEnvironment.getApplication())
        val original = SocialSession.openJsonConnection
        try {
            SocialSession.clear()
            SocialSession.remember(JSONObject().put("access_token", "old").put("refresh_token", "old-refresh"))
            val api = SessionJsonApi()
            SocialSession.remember(JSONObject().put("access_token", "new").put("refresh_token", "new-refresh"))
            var opened = false
            SocialSession.openJsonConnection = {
                opened = true
                throw AssertionError("A stale screen must not open a connection")
            }
            assertThrows(IllegalStateException::class.java) { runBlocking { api.get("gallery/page") } }
            assertFalse(opened)
            assertEquals("new", SocialSession.token)
        } finally {
            SocialSession.openJsonConnection = original
            SocialSession.clear()
        }
    }

    @Test fun chatPersistenceKeepsEvidenceAndLanguageWithoutLeakingUiState() = runBlocking {
        val repository = ChatRepository(
            api = JsonApi { path, method, body ->
                assertEquals("POST", method)
                assertEquals("chat/append", path)
                assertEquals("es", body!!.getString("response_language"))
                assertEquals("/v1/evidence", body.getString("evidence_url"))
                assertEquals("Hola", body.getString("text"))
                assertFalse(body.has("imagePreview"))
                """{"id":12}"""
            }
        )
        val id = repository.append(ChatTurn("ai", "text", "Hola", "/v1/evidence", emptyList(), false, emptyList(), false, "es"))
        assertEquals(12, id)
    }
}
