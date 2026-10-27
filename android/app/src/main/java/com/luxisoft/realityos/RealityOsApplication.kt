package com.luxisoft.realityos

import android.app.Application
import android.util.Log
import com.meta.wearable.dat.core.Wearables

/** Initializes DAT once, before any device registration or session work. */
class RealityOsApplication : Application() {
    lateinit var developerPreviewController: DeveloperPreviewController
        private set

    override fun onCreate() {
        super.onCreate()
        // The demo always begins in English unless the user explicitly chose
        // Spanish from the in-app menu. Apply it before composing any UI.
        RealityExperienceStore(this).applySelectedLanguage()
        developerPreviewController = createDeveloperPreviewController(this)
        Wearables.initialize(this).onFailure { error, _ ->
            Log.e("RealityOS", "DAT initialization failed: ${error.description}")
        }
    }
}
