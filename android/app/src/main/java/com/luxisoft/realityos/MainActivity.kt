package com.luxisoft.realityos

import android.Manifest
import android.media.AudioAttributes
import android.os.Bundle
import android.speech.tts.TextToSpeech
import androidx.activity.enableEdgeToEdge
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.types.Permission
import com.meta.wearable.dat.core.types.PermissionStatus
import kotlinx.coroutines.launch
import java.util.Locale

class MainActivity : AppCompatActivity() {
    private val viewModel: RealityViewModel by viewModels()
    private var requestedDatPermission: Permission? = null
    private lateinit var speech: TextToSpeech
    private var ttsReady = false

    private val bluetoothPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { grants ->
        if (grants[Manifest.permission.BLUETOOTH_CONNECT] != true) {
            // DAT registration itself explains how to grant Bluetooth access.
        }
    }

    private val datPermissionLauncher = registerForActivityResult(
        Wearables.RequestPermissionContract(),
    ) { result ->
        val requested = requestedDatPermission ?: return@registerForActivityResult
        requestedDatPermission = null
        result.fold(
            onSuccess = { status -> viewModel.onPermissionResult(requested, status is PermissionStatus.Granted) },
            onFailure = { _, _ -> viewModel.onPermissionResult(requested, granted = false) },
        )
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        speech = TextToSpeech(this) { status ->
            ttsReady = status == TextToSpeech.SUCCESS
            if (ttsReady) {
                speech.language = if (resources.configuration.locales[0]?.language == "es") {
                    Locale.Builder().setLanguage("es").setRegion("CO").build()
                } else {
                    Locale.US
                }
                speech.setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANCE_NAVIGATION_GUIDANCE)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build(),
                )
            }
        }
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.permissionRequests.collect { permission ->
                        requestedDatPermission = permission
                        datPermissionLauncher.launch(permission)
                    }
                }
                launch {
                    viewModel.speechRequests.collect { text -> speakOnActiveAudioRoute(text) }
                }
            }
        }
        setContent {
            RealityOsApp(
                viewModel = viewModel,
                onRegisterWithMeta = { viewModel.registerWithMeta(this) },
                onConnectDisplay = viewModel::connectDisplay,
                onDisconnectDisplay = viewModel::disconnectDisplay,
            )
        }
    }

    override fun onStart() {
        super.onStart()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            bluetoothPermissionLauncher.launch(arrayOf(Manifest.permission.BLUETOOTH, Manifest.permission.BLUETOOTH_CONNECT))
        }
    }

    private fun speakOnActiveAudioRoute(text: String) {
        if (ttsReady && text.isNotBlank()) {
            speech.speak(text, TextToSpeech.QUEUE_FLUSH, null, "realityos-guidance")
        }
    }

    override fun onDestroy() {
        speech.stop()
        speech.shutdown()
        super.onDestroy()
    }
}
