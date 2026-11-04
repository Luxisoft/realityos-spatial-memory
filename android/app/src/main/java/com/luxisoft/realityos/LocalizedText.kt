package com.luxisoft.realityos

import android.content.Context
import android.content.res.Configuration
import androidx.annotation.PluralsRes
import androidx.annotation.StringRes
import java.util.Locale

/** Resources for callbacks and services, where a Compose resource is unavailable. */
internal object LocalizedText {
    private lateinit var application: Context
    private lateinit var experience: RealityExperienceStore
    val languageTag: String get() = if (::experience.isInitialized) experience.selectedLanguage().languageTag else "en"

    fun initialize(context: Context) {
        application = context.applicationContext
        experience = RealityExperienceStore(application)
    }

    private fun resources(): android.content.res.Resources {
        val tag = experience.selectedLanguage().languageTag
        val configuration = Configuration(application.resources.configuration).apply {
            setLocale(Locale.forLanguageTag(tag))
        }
        return application.createConfigurationContext(configuration).resources
    }

    fun get(@StringRes id: Int, vararg arguments: Any): String = resources().getString(id, *arguments)

    fun quantity(@PluralsRes id: Int, count: Int, vararg arguments: Any): String = resources().getQuantityString(id, count, *arguments)
}

internal fun localizedText(@StringRes id: Int, vararg arguments: Any): String = LocalizedText.get(id, *arguments)

internal fun localizedQuantityText(@PluralsRes id: Int, count: Int, vararg arguments: Any): String = LocalizedText.quantity(id, count, *arguments)

internal fun localizedHttpError(status: Int): String = when (status) {
    401 -> localizedText(R.string.ui_your_session_expired_sign_in_again)
    403 -> localizedText(R.string.ui_you_do_not_have_permission_for_this_action)
    else -> localizedText(R.string.ui_could_not_complete_the_request_1_d, status)
}
