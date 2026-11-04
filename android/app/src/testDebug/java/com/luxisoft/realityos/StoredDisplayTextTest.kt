package com.luxisoft.realityos

import android.app.Application
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
class StoredDisplayTextTest {
    @Test fun existingPayloadChangesDisplayLanguageWithoutChangingIdsOrFetchingCopy() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        val experience = RealityExperienceStore(context)
        val term = JSONObject("""{"id":"same-id","name":"Llaves","display_text":{"name":{"source":"Llaves","es":"Llaves","en":"Keys"}}}""")
        val post = JSONObject().put("category", term)
        try {
            experience.setLanguage(RealityLanguage.ENGLISH)
            assertEquals("Keys", PublicationSummary.read(post).classificationText())
            experience.setLanguage(RealityLanguage.SPANISH)
            assertEquals("Llaves", PublicationSummary.read(post).classificationText())
            assertEquals("same-id", term.getString("id"))
            assertEquals("Llaves", term.getString("name"))
            assertEquals("User wording", JSONObject().put("name", "User wording").storedText("name"))
        } finally {
            experience.setLanguage(RealityLanguage.ENGLISH)
        }
    }
}
