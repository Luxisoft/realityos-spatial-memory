package com.luxisoft.realityos

import android.app.Application
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
class LanguageResourcesTest {
    private lateinit var store: RealityExperienceStore
    @Before fun initialize() {
        LocalizedText.initialize(RuntimeEnvironment.getApplication())
        store = RealityExperienceStore(RuntimeEnvironment.getApplication())
    }
    @After fun resetLocale() { store.setLanguage(RealityLanguage.ENGLISH) }

    @Test fun callbacksResolveTheSelectedLanguageOnEveryUse() {
        store.setLanguage(RealityLanguage.SPANISH)
        assertEquals("Publicar", localizedText(R.string.ui_publish))
        store.setLanguage(RealityLanguage.ENGLISH)
        assertEquals("Publish", localizedText(R.string.ui_publish))
        assertEquals("Guests cannot search for Meta people.", localizedText(R.string.ui_guests_cannot_search_for_meta_people))
        assertEquals("Published on 2026-11-01", localizedText(R.string.ui_published_on_1_s, "2026-11-01"))
        store.setLanguage(RealityLanguage.SPANISH)
        assertEquals("Publicar", localizedText(R.string.ui_publish))
    }

    @Test fun apiErrorsAndMissingVoiceMessagesUseSelectedLanguage() {
        store.setLanguage(RealityLanguage.ENGLISH)
        assertEquals("Your session expired. Sign in again.", localizedHttpError(401))
        assertTrue(localizedHttpError(403).startsWith("You do not"))
        assertTrue(localizedText(R.string.voice_language_unavailable).startsWith("The selected"))
        store.setLanguage(RealityLanguage.SPANISH)
        assertTrue(localizedHttpError(401).startsWith("Tu sesión"))
        assertTrue(localizedText(R.string.voice_language_unavailable).startsWith("La voz"))
    }

    @Test fun oldLanguageSpeechIsRejectedAfterSwitch() {
        val speech = LocalizedSpeech("Hola", "es")
        assertTrue(speech.matches("es"))
        assertFalse(speech.matches("en"))
    }
    @Test fun personCountsUseNaturalPluralsAndKeepNames() {
        store.setLanguage(RealityLanguage.ENGLISH)
        assertEquals("I found 1 person: José", localizedQuantityText(R.plurals.chat_face_found, 1, 1, "José"))
        assertEquals("I found 2 people: Ana, José", localizedQuantityText(R.plurals.chat_face_found, 2, 2, "Ana, José"))
        assertEquals("One face enrolled.", localizedQuantityText(R.plurals.face_enrolled, 1, 1))
        store.setLanguage(RealityLanguage.SPANISH)
        assertEquals("Encontré 1 persona: José", localizedQuantityText(R.plurals.chat_face_found, 1, 1, "José"))
        assertEquals("Encontré 2 personas: Ana, José", localizedQuantityText(R.plurals.chat_face_found, 2, 2, "Ana, José"))
        assertEquals("2 rostros enrolados.", localizedQuantityText(R.plurals.face_enrolled, 2, 2))
    }

}
