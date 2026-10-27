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
        developerPreviewController = createDeveloperPreviewController(this)
        Wearables.initialize(this).onFailure { error, _ ->
            Log.e("RealityOS", "DAT initialization failed: ${error.description}")
        }
    }
}
