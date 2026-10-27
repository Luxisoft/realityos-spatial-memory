package com.luxisoft.realityos

import android.content.Context
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat

/** Phone-local experience preferences; this intentionally contains no credential material. */
enum class RealityLanguage(val languageTag: String) {
    ENGLISH("en"),
    SPANISH("es"),
    ;

    companion object {
        fun fromTag(value: String?): RealityLanguage = entries.firstOrNull {
            it.languageTag == value
        } ?: ENGLISH
    }
}

class RealityExperienceStore(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences(
        "realityos-experience",
        Context.MODE_PRIVATE,
    )

    fun selectedLanguage(): RealityLanguage = RealityLanguage.fromTag(
        preferences.getString(KEY_LANGUAGE, null),
    )

    fun setLanguage(language: RealityLanguage) {
        preferences.edit().putString(KEY_LANGUAGE, language.languageTag).apply()
        AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(language.languageTag))
    }

    fun applySelectedLanguage() {
        AppCompatDelegate.setApplicationLocales(
            LocaleListCompat.forLanguageTags(selectedLanguage().languageTag),
        )
    }

    fun hasCompletedWelcome(): Boolean = preferences.getBoolean(KEY_WELCOME_COMPLETED, false)

    fun completeWelcome() {
        preferences.edit().putBoolean(KEY_WELCOME_COMPLETED, true).apply()
    }

    /** Test-only reset used by the instrumentation suite. */
    fun clearForTesting() {
        preferences.edit().clear().commit()
    }

    private companion object {
        const val KEY_LANGUAGE = "language"
        const val KEY_WELCOME_COMPLETED = "welcome_completed"
    }
}
