package com.luxisoft.realityos

import android.app.Application
import android.app.LocaleManager
import android.os.Build
import androidx.appcompat.app.AppCompatDelegate
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

/** Startup must apply the locale before any AppCompat activity exists. */
@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [32, 35], qualifiers = "es-rCO")
class RealityStartupLanguageTest {
    private val application: Application get() = RuntimeEnvironment.getApplication()

    @Before
    fun clearPreferences() {
        RealityExperienceStore(application).clearForTesting()
    }

    @Test
    fun firstLaunchUsesEnglishOnASpanishPhone() {
        assertEquals("es", application.resources.configuration.locales[0].language)
        val store = RealityExperienceStore(application)

        store.applySelectedLanguage()

        assertEquals(RealityLanguage.ENGLISH, store.selectedLanguage())
        assertEquals("en", appliedLanguage())
    }

    @Test
    @Config(qualifiers = "en-rUS")
    fun restartPreservesExplicitSpanishOnAnEnglishPhone() {
        RealityExperienceStore(application).setLanguage(RealityLanguage.SPANISH)

        val restartedStore = RealityExperienceStore(application)
        restartedStore.applySelectedLanguage()

        assertEquals(RealityLanguage.SPANISH, restartedStore.selectedLanguage())
        assertEquals("es", appliedLanguage())
    }

    @Test
    fun restartPreservesExplicitEnglishOnASpanishPhone() {
        RealityExperienceStore(application).setLanguage(RealityLanguage.ENGLISH)

        RealityExperienceStore(application).applySelectedLanguage()

        assertEquals("en", appliedLanguage())
    }

    private fun appliedLanguage(): String = if (Build.VERSION.SDK_INT >= 33) {
        application.getSystemService(LocaleManager::class.java).applicationLocales.toLanguageTags()
    } else {
        AppCompatDelegate.getApplicationLocales().toLanguageTags()
    }
}
