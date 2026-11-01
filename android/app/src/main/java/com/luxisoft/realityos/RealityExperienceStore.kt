package com.luxisoft.realityos

import android.content.Context
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Local cache of account preferences, also available before signing in. */
enum class RealityLanguage(val languageTag: String) {
    ENGLISH("en"),
    SPANISH("es")
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
        Context.MODE_PRIVATE
    )

    init {
        languageState.value = RealityLanguage.fromTag(preferences.getString(KEY_LANGUAGE, null))
    }

    val language = languageState.asStateFlow()

    suspend fun syncAccountLanguage(): RealityLanguage = languageMutex.withLock {
        if (SocialSession.token == null) return@withLock selectedLanguage()
        val selected = withContext(Dispatchers.IO) {
            val remote = JSONObject(SocialSession.request("me/preferences")).optText("preferred_language")
            remote ?: JSONObject(
                SocialSession.requestJson(
                    "me/preferences?initialize=true",
                    "PATCH",
                    JSONObject().put("preferred_language", selectedLanguage().languageTag)
                )
            ).getString("preferred_language")
        }
        val confirmed = RealityLanguage.fromTag(selected)
        withContext(Dispatchers.Main) { setLanguage(confirmed) }
        confirmed
    }

    suspend fun saveAccountLanguage(language: RealityLanguage) = languageMutex.withLock {
        val confirmed = if (SocialSession.token != null) {
            withContext(Dispatchers.IO) {
                RealityLanguage.fromTag(
                    JSONObject(
                        SocialSession.requestJson(
                            "me/preferences",
                            "PATCH",
                            JSONObject().put("preferred_language", language.languageTag)
                        )
                    ).getString("preferred_language")
                )
            }
        } else {
            language
        }
        withContext(Dispatchers.Main) { setLanguage(confirmed) }
    }

    fun selectedLanguage(): RealityLanguage = RealityLanguage.fromTag(
        preferences.getString(KEY_LANGUAGE, null)
    )

    fun setLanguage(language: RealityLanguage) {
        preferences.edit().putString(KEY_LANGUAGE, language.languageTag).apply()
        languageState.value = language
        AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(language.languageTag))
    }

    fun applySelectedLanguage() {
        AppCompatDelegate.setApplicationLocales(
            LocaleListCompat.forLanguageTags(selectedLanguage().languageTag)
        )
    }

    fun hasCompletedWelcome(): Boolean = preferences.getBoolean(KEY_WELCOME_COMPLETED, false)

    fun completeWelcome() {
        preferences.edit().putBoolean(KEY_WELCOME_COMPLETED, true).apply()
    }

    /** Test-only reset used by the instrumentation suite. */
    fun clearForTesting() {
        preferences.edit().clear().commit()
        languageState.value = RealityLanguage.ENGLISH
    }

    private companion object {
        val languageState = MutableStateFlow(RealityLanguage.ENGLISH)
        val languageMutex = Mutex()
        const val KEY_LANGUAGE = "language"
        const val KEY_WELCOME_COMPLETED = "welcome_completed"
    }
}
