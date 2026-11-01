package com.luxisoft.realityos

import android.Manifest
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.util.Log
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
    val facebookCallbacks = com.facebook.CallbackManager.Factory.create()

    @Deprecated("Facebook callback bridge")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: android.content.Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        facebookCallbacks.onActivityResult(requestCode, resultCode, data)
    }
    private val viewModel: RealityViewModel by viewModels()
    private var requestedDatPermission: RealityPermissionRequest.Dat? = null
    private var requestedPhonePermission: RealityPermissionRequest.Android? = null
    private var lastLaunchedPermissionRequestId = -1L
    private var wearablesInitialized = false
    private lateinit var speech: TextToSpeech
    private var ttsReady = false
    private var speechRevision = 0L
    private val agentSpeech by lazy {
        AgentSpeechPlayer(
            this, lifecycleScope, { viewModel.state.value.provisioning },
            viewModel::onSpeechStarted, viewModel::onSpeechDone,
            ::speakWithDeviceVoice,
            { android.widget.Toast.makeText(this, getString(R.string.voice_device_fallback), android.widget.Toast.LENGTH_SHORT).show() },
        )
    }
    private val phoneCaptureSource by lazy { CameraXPhoneCaptureSource(this, this) }
    private val phoneSpeechSource by lazy { AndroidPhoneSpeechSource(this) }

    private val bluetoothPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { grants ->
        if (grants[Manifest.permission.BLUETOOTH_CONNECT] != true) {
            viewModel.onWearablesInitializationFailure(getString(R.string.status_bluetooth_permission))
        } else {
            initializeWearables()
        }
    }

    private val datPermissionLauncher = registerForActivityResult(
        Wearables.RequestPermissionContract(),
    ) { result ->
        val requested = requestedDatPermission ?: return@registerForActivityResult
        requestedDatPermission = null
        result.fold(
            onSuccess = { status ->
                viewModel.onDatPermissionResult(
                    requested.id,
                    requested.permission,
                    status is PermissionStatus.Granted,
                )
            },
            onFailure = { error, _ ->
                viewModel.onDatPermissionResult(
                    requested.id,
                    requested.permission,
                    granted = false,
                    failureMessage = error.description,
                )
            },
        )
    }

    private val phonePermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        val requested = requestedPhonePermission ?: return@registerForActivityResult
        requestedPhonePermission = null
        viewModel.onPhonePermissionResult(requested.id, requested.permission, granted)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        val pendingPermission = viewModel.permissionRequest.value
        if (pendingPermission != null && savedInstanceState?.getLong("active-permission-request", -1L) == pendingPermission.id) {
            lastLaunchedPermissionRequestId = pendingPermission.id
            requestedDatPermission = pendingPermission as? RealityPermissionRequest.Dat
            requestedPhonePermission = pendingPermission as? RealityPermissionRequest.Android
        }
        enableEdgeToEdge()
        window.isNavigationBarContrastEnforced = false
        viewModel.setPhoneInputSources(phoneCaptureSource, phoneSpeechSource)
        speech = TextToSpeech(this) { status ->
            ttsReady = status == TextToSpeech.SUCCESS
            if (ttsReady) {
                speech.language = Locale.forLanguageTag(RealityExperienceStore(this).selectedLanguage().languageTag)
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
                    viewModel.permissionRequest.collect { request ->
                        if (request == null || request.id == lastLaunchedPermissionRequestId) return@collect
                        lastLaunchedPermissionRequestId = request.id
                        when (request) {
                            is RealityPermissionRequest.Dat -> {
                                requestedDatPermission = request
                                datPermissionLauncher.launch(request.permission)
                            }
                            is RealityPermissionRequest.Android -> {
                                requestedPhonePermission = request
                                try {
                                    phonePermissionLauncher.launch(
                                        if (request.permission == PhonePermission.CAMERA) {
                                            Manifest.permission.CAMERA
                                        } else {
                                            Manifest.permission.RECORD_AUDIO
                                        },
                                    )
                                } catch (error: IllegalStateException) {
                                    requestedPhonePermission = null
                                    viewModel.onPhonePermissionResult(request.id, request.permission, granted = false)
                                }
                            }
                        }
                    }
                }
                launch {
                    viewModel.speechRequests.collect { text -> speakOnActiveAudioRoute(text) }
                }
                launch {
                    RealityExperienceStore(this@MainActivity).language.collect {
                        speechRevision++
                        agentSpeech.stop()
                        speech.stop()
                        viewModel.onSpeechDone()
                    }
                }
                launch {
                    viewModel.speechStopRequests.collect {
                        speechRevision++
                        agentSpeech.stop()
                        try { speech.stop() } catch (_: Exception) { }
                        viewModel.onSpeechDone()
                    }
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
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
            bluetoothPermissionLauncher.launch(arrayOf(Manifest.permission.BLUETOOTH, Manifest.permission.BLUETOOTH_CONNECT))
        } else {
            initializeWearables()
        }
    }

    private fun initializeWearables() {
        if (wearablesInitialized) return
        val realityApplication = application as RealityOsApplication
        if (realityApplication.wearablesInitialized) {
            wearablesInitialized = true
            viewModel.onWearablesInitialized()
            return
        }
        Wearables.initialize(this).fold(
            onSuccess = {
                wearablesInitialized = true
                realityApplication.markWearablesInitialized()
                viewModel.onWearablesInitialized()
            },
            onFailure = { error, _ ->
                Log.e("RealityOS", "DAT initialization failed: ${error.description}")
                viewModel.onWearablesInitializationFailure(error.description)
            },
        )
    }

    private fun speakOnActiveAudioRoute(request: LocalizedSpeech) {
        speechRevision++
        speech.stop()
        agentSpeech.speak(request)
    }

    private fun speakWithDeviceVoice(request: LocalizedSpeech) {
        val revision = speechRevision
        val selected = RealityExperienceStore(this).selectedLanguage().languageTag
        if (!ttsReady || request.text.isBlank() || !request.matches(selected)) {
            viewModel.onSpeechDone()
            return
        }
        val locale = Locale.forLanguageTag(selected)
        if (speech.isLanguageAvailable(locale) < TextToSpeech.LANG_AVAILABLE) {
            android.widget.Toast.makeText(this, localizedText(R.string.voice_language_unavailable), android.widget.Toast.LENGTH_LONG).show()
            viewModel.onSpeechDone()
            return
        }
        speech.language = locale
        speech.setOnUtteranceProgressListener(object : android.speech.tts.UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                if (revision == speechRevision) viewModel.onSpeechStarted()
            }

            override fun onDone(utteranceId: String?) {
                if (revision == speechRevision) viewModel.onSpeechDone()
            }

            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String?) {
                if (revision == speechRevision) viewModel.onSpeechDone()
            }

            override fun onError(utteranceId: String?, errorCode: Int) {
                if (revision == speechRevision) viewModel.onSpeechDone()
            }

            override fun onStop(utteranceId: String?, interrupted: Boolean) {
                if (revision == speechRevision) viewModel.onSpeechDone()
            }
        })
        speech.speak(request.text, TextToSpeech.QUEUE_FLUSH, null, "realityos-guidance")
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putLong("active-permission-request", lastLaunchedPermissionRequestId)
        super.onSaveInstanceState(outState)
    }

    override fun onDestroy() {
        agentSpeech.stop()
        speech.stop()
        speech.shutdown()
        super.onDestroy()
    }

    override fun onStop() {
        speechRevision++
        agentSpeech.stop()
        speech.stop()
        viewModel.onSpeechDone()
        super.onStop()
    }
}
