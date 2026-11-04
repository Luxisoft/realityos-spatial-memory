package com.luxisoft.realityos

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.viewModelScope
import java.lang.reflect.Proxy
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.Implementation
import org.robolectric.annotation.Implements
import org.robolectric.shadows.ShadowApplication

/** Exercises the real stage, including the localhost build that formerly skipped startup. */
@RunWith(RobolectricTestRunner::class)
@Config(
    application = RealityOsApplication::class,
    sdk = [35],
    qualifiers = "w320dp-h640dp",
    shadows = [PreviewApplicationShadow::class, GalleryDeviceProvisioningShadow::class]
)
class DeveloperPreviewStartupTest {
    @get:Rule val compose = createComposeRule()
    private lateinit var app: RealityOsApplication
    private lateinit var vm: RealityViewModel
    private val modes = mutableListOf<DeveloperPreviewMode>()
    private val enabled = mutableStateOf(true)

    @Before fun prepare() {
        app = RuntimeEnvironment.getApplication() as RealityOsApplication
        LocalizedText.initialize(app)
        val state = MutableStateFlow(DeveloperPreviewState(available = true))
        // Observe startup without creating hardware, capturing media or authenticating.
        val controller = Proxy.newProxyInstance(
            DeveloperPreviewController::class.java.classLoader,
            arrayOf(DeveloperPreviewController::class.java)
        ) { proxy, method, args ->
            when (method.name) {
                "equals" -> proxy === args[0]
                "hashCode" -> System.identityHashCode(proxy)
                "toString" -> "Preview startup test controller"
                "getState" -> state
                "start" -> {
                    modes += args[0] as DeveloperPreviewMode
                    null
                }
                "isSimulatedDevice" -> false
                else -> null
            }
        } as DeveloperPreviewController
        setController(controller)
        vm = RealityViewModel(app)
        compose.mainClock.autoAdvance = false
    }

    @After fun restore() {
        if (::vm.isInitialized) vm.viewModelScope.cancel()
    }

    @Test fun opensInAppPreviewWhenTransportIsReady() {
        transportReady(true)
        showStage()
        advanceStartup()
        assertEquals(listOf(DeveloperPreviewMode.IN_APP), modes)
        assertEquals(false, vm.state.value.wearable.cameraActive)
        assertEquals(false, vm.state.value.wearable.speechActive)
        assertEquals(null, vm.state.value.captureSessionId)
    }

    @Test fun waitsForBluetoothInitializationThenStarts() {
        showStage()
        advanceStartup()
        assertEquals(emptyList<DeveloperPreviewMode>(), modes)
        compose.runOnIdle { transportReady(true) }
        advanceStartup()
        assertEquals(listOf(DeveloperPreviewMode.IN_APP), modes)
    }

    @Test fun disabledStageDoesNotStartHardware() {
        enabled.value = false
        transportReady(true)
        showStage()
        advanceStartup()
        assertEquals(emptyList<DeveloperPreviewMode>(), modes)
    }

    @Test fun disablingBeforeBluetoothIsReadyPreventsLateStartup() {
        showStage()
        advanceStartup()
        compose.runOnIdle {
            enabled.value = false
            transportReady(true)
        }
        advanceStartup()
        assertEquals(emptyList<DeveloperPreviewMode>(), modes)
    }

    private fun showStage() {
        compose.setContent { MaterialTheme { DeveloperPreviewStage(vm, enabled.value) } }
    }

    private fun advanceStartup() {
        compose.mainClock.advanceTimeBy(1_000)
        compose.waitForIdle()
    }

    private fun transportReady(ready: Boolean) {
        vm.mutableUiState.value = vm.state.value.copy(wearable = vm.state.value.wearable.copy(transportReady = ready))
    }

    private fun setController(controller: DeveloperPreviewController) {
        RealityOsApplication::class.java.getDeclaredField("developerPreviewController").apply { isAccessible = true }
            .set(app, controller)
    }
}

/** Keep Android's keystore and DAT singletons outside this startup orchestration test. */
@Implements(value = RealityOsApplication::class, isInAndroidSdk = false)
class PreviewApplicationShadow : ShadowApplication() {
    @Implementation
    fun onCreate() = Unit
}
