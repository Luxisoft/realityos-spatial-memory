package com.luxisoft.realityos

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/** Verifies first-run onboarding and the English-first language preference. */
@RunWith(AndroidJUnit4::class)
class RealityExperienceStoreTest {
    private lateinit var store: RealityExperienceStore

    @Before
    fun set_up() {
        store = RealityExperienceStore(InstrumentationRegistry.getInstrumentation().targetContext)
        store.clearForTesting()
        store.setLanguage(RealityLanguage.ENGLISH)
    }

    @After
    fun tear_down() {
        store.clearForTesting()
        store.setLanguage(RealityLanguage.ENGLISH)
    }

    @Test
    fun defaults_to_english_and_remembers_the_completed_welcome() {
        assertEquals(RealityLanguage.ENGLISH, store.selectedLanguage())
        assertFalse(store.hasCompletedWelcome())

        store.completeWelcome()
        store.setLanguage(RealityLanguage.SPANISH)

        assertTrue(store.hasCompletedWelcome())
        assertEquals(RealityLanguage.SPANISH, store.selectedLanguage())
    }
}
