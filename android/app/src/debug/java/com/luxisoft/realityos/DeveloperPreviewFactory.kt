package com.luxisoft.realityos

import android.app.Application

internal fun createDeveloperPreviewController(application: Application): DeveloperPreviewController =
    MockDeveloperPreviewController(application)
