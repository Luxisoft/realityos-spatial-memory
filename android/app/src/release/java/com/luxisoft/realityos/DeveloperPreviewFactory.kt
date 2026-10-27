package com.luxisoft.realityos

import android.app.Application
import android.content.Context
import android.net.Uri
import android.view.View
import com.meta.wearable.dat.core.types.DeviceIdentifier
import com.meta.wearable.dat.core.types.Permission
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/** Release builds intentionally have no Mock Device Kit dependency or controls. */
internal fun createDeveloperPreviewController(application: Application): DeveloperPreviewController =
    object : DeveloperPreviewController {
        private val unsupported = MutableStateFlow(
            DeveloperPreviewState(message = "Developer preview is available only in Debug builds."),
        )

        override val state: StateFlow<DeveloperPreviewState> = unsupported

        override suspend fun start(mode: DeveloperPreviewMode): DeviceIdentifier? = null
        override suspend fun stop() = Unit
        override fun powerOn() = Unit
        override fun powerOff() = Unit
        override fun unfold() = Unit
        override fun fold() = Unit
        override fun don() = Unit
        override fun doff() = Unit
        override fun setDatPermission(permission: Permission, granted: Boolean) = Unit
        override fun setCapturedPhoto(uri: Uri?) = Unit
        override fun setVideoFeed(uri: Uri?) = Unit
        override fun setPhoneCamera(camera: PreviewPhoneCamera) = Unit
        override fun simulateTranscription(text: String, isFinal: Boolean) = Unit
        override fun clearError() = Unit
        override fun createInAppPreviewView(context: Context): View? = null
    }
