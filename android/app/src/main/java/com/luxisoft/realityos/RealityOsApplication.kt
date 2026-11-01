package com.luxisoft.realityos

import android.app.Application

/** Owns process-wide configuration. DAT initializes after Bluetooth consent. */
class RealityOsApplication : Application() {
    lateinit var developerPreviewController: DeveloperPreviewController
        private set

    /** DAT may only initialize once per process, after runtime consent. */
    var wearablesInitialized: Boolean = false
        private set

    fun markWearablesInitialized() {
        wearablesInitialized = true
    }

    override fun onCreate() {
        super.onCreate()
        LocalizedText.initialize(this)
        SocialSession.initialize(this)
        // The demo always begins in English unless the user explicitly chose
        // Spanish from the in-app menu. Apply it before composing any UI.
        RealityExperienceStore(this).applySelectedLanguage()
        developerPreviewController = createDeveloperPreviewController(this)
    }
}
