package com.luxisoft.realityos

import android.Manifest
import android.app.Application
import android.os.Looper
import android.os.SystemClock
import android.util.Base64
import android.view.InputDevice
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import androidx.activity.ComponentActivity
import androidx.camera.core.Preview
import androidx.camera.core.ViewPort
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Actual pointer events cross Meta's WebView bridge into the production camera flow. */
@RunWith(AndroidJUnit4::class)
class DisplaySearchCameraTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private lateinit var vm: RealityViewModel
    private lateinit var source: CameraSource
    private lateinit var controller: DeveloperPreviewController
    private var retainedFile: File? = null

    @Before fun startDisplay() = runBlocking {
        val app = instrumentation.targetContext.applicationContext as RealityOsApplication
        for (permission in listOf(Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.CAMERA)) {
            instrumentation.uiAutomation.grantRuntimePermission(app.packageName, permission)
        }
        // This fixture never contacts a server or authenticates a real account.
        // A CUSTOM device profile prevents automatic Live bootstrap in the test.
        DeviceProvisioningStore(app).save(DeviceProvisioning("https://example.invalid/v1", "camera-test", "camera-test", "test-only"))
        val payload = Base64.encodeToString("""{"sub":"display-camera-test"}""".toByteArray(), Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)
        SocialSession.token = "e30.$payload.test-only"
        SocialSession.workspaceId = "camera-test"
        controller = app.developerPreviewController
        val identifier = checkNotNull(controller.start(DeveloperPreviewMode.IN_APP))
        compose.activityRule.scenario.onActivity { activity ->
            vm = ViewModelProvider(activity)[RealityViewModel::class.java]
            // Set only the account identity normally established by refresh();
            // the fixture avoids network requests and changes no login gates.
            MetaDisplayController::class.java.getDeclaredField("owner").apply { isAccessible = true }
                .set(vm.metaController, "display-camera-test")
            source = CameraSource()
            vm.setPhoneInputSources(source, AndroidPhoneSpeechSource(activity))
            vm.mutableUiState.update { current ->
                current.copy(
                    wearable = current.wearable.copy(transportReady = true),
                    meta = current.meta.copy(destinations = listOf(MetaDestination("home", "Profile", "home")))
                )
            }
            vm.connectDisplay(identifier)
        }
        compose.setContent {
            RealityOsTheme { DeveloperPreviewStage(vm, enabled = false, modifier = Modifier.fillMaxSize()) }
        }
        await { vm.state.value.wearable.displayReady }
        main { vm.renderSearchMenu() }
        awaitButton(vm.copy(R.string.meta_search_object))
    }

    @After fun stopDisplay() = runBlocking {
        if (::vm.isInitialized) {
            main {
                vm.cancelPendingActionAndRenderHome()
                vm.disconnectDisplay()
            }
        }
        retainedFile?.delete()
        if (::controller.isInitialized) controller.stop()
        SocialSession.token = null
        SocialSession.workspaceId = null
    }

    @Test fun objectAndPersonButtonsOpenCameraAndCanBeReopened() {
        for (kind in MetaPhotoSearchKind.entries) {
            showSearch()
            tapButton(vm.copy(if (kind == MetaPhotoSearchKind.OBJECT) R.string.meta_search_object else R.string.meta_search_person))
            grantCamera()
            await { vm.state.value.wearable.cameraActive && !vm.state.value.busy }
            assertEquals(kind, vm.state.value.meta.photoSearchKind)
            assertNull("Search must not open a Register session", vm.state.value.captureSessionId)
            assertEquals(PhonePreviewPhase.OPENING, vm.state.value.phonePreview.phase)
            main { vm.onPhonePreviewStreaming(vm.state.value.phonePreview.generation, true) }
            compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
            await { !vm.state.value.wearable.cameraActive && !vm.state.value.meta.captureForSearch }
        }
        assertEquals(2, source.starts)
    }

    @Test fun activeOperationShowsFeedbackInsteadOfIgnoringSearchButton() {
        main { vm.mutableUiState.update { it.copy(busy = true, message = "before tap") } }
        tapButton(vm.copy(R.string.meta_search_object))
        regression("DISPLAY_SEARCH_BUSY_NO_FEEDBACK") { vm.state.value.message == vm.copy(R.string.meta_action_busy) }
        awaitButtonText(vm.copy(R.string.meta_action_busy))
        assertTrue("A camera tap must not release another operation's busy state", vm.state.value.busy)
        assertEquals(0, source.starts)
        main { vm.setBusy(false) }
    }

    @Test fun permissionDenialAndCancelledCallbacksDoNotBlockNextSearch() {
        tapButton(vm.copy(R.string.meta_search_person))
        val denied = cameraRequest()
        main { vm.onPhonePermissionResult(denied.id, denied.permission, false) }
        await { vm.permissionRequest.value == null && !vm.state.value.meta.captureForSearch }
        assertEquals(0, source.starts)
        showSearch()
        tapButton(vm.copy(R.string.meta_search_object))
        val cancelled = cameraRequest()
        main { vm.cancelPendingActionAndRenderHome() }
        main { vm.onPhonePermissionResult(cancelled.id, cancelled.permission, true) }
        assertEquals(0, source.starts)
        showSearch()
        tapButton(vm.copy(R.string.meta_search_person))
        grantCamera()
        await { source.starts == 1 && !vm.state.value.busy }
    }

    @Test fun pendingPublicationOpensReviewAndKeepsOriginal() {
        val app = instrumentation.targetContext.applicationContext as Application
        val original = File.createTempFile("pending-camera-test", ".jpg", app.cacheDir).apply { writeText("retained original") }
        retainedFile = original
        main {
            MetaDisplayController::class.java.getDeclaredField("pending").apply { isAccessible = true }.set(vm.metaController, original)
            vm.mutableUiState.update { it.copy(meta = it.meta.copy(pendingMime = "image/jpeg", pendingDestination = "Profile")) }
        }
        tapButton(vm.copy(R.string.meta_search_person))
        awaitButton(vm.copy(R.string.meta_publish))
        assertTrue(original.isFile)
        assertEquals("retained original", original.readText())
        assertNull(vm.permissionRequest.value)
        assertEquals(0, source.starts)
    }

    @Test fun generationChangeWhileCameraStartsDoesNotLeaveBusyLatched() {
        val started = CompletableDeferred<Unit>()
        source.waitForStart = started
        tapButton(vm.copy(R.string.meta_search_object))
        grantCamera()
        await { vm.state.value.busy && source.starts == 1 }
        // The previous implementation released busy only for the old response
        // generation; a language refresh or newer screen could strand it.
        main { vm.metaController.generation.invalidate() }
        started.complete(Unit)
        regression("DISPLAY_CAMERA_BUSY_NOT_RELEASED") { !vm.state.value.busy }
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        await { !vm.state.value.wearable.cameraActive }
    }

    @Test fun aDifferentAccountCannotOpenThePreviousAccountsPendingPublication() {
        val app = instrumentation.targetContext.applicationContext as Application
        retainedFile = File.createTempFile("other-account-camera-test", ".jpg", app.cacheDir)
        main {
            MetaDisplayController::class.java.getDeclaredField("pending").apply { isAccessible = true }.set(vm.metaController, retainedFile)
            vm.mutableUiState.update { it.copy(meta = it.meta.copy(pendingMime = "image/jpeg")) }
            val payload = Base64.encodeToString("""{"sub":"another-account"}""".toByteArray(), Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)
            SocialSession.token = "e30.$payload.test-only"
        }
        tapButton(vm.copy(R.string.meta_search_person))
        awaitButtonText(vm.copy(R.string.meta_login_required))
        assertEquals("false", javascript("document.body.textContent.includes(${JSONObject.quote(vm.copy(R.string.meta_publish))})"))
        assertNull(vm.permissionRequest.value)
        assertEquals(0, source.starts)
    }

    @Test fun cameraStartupFailureCanBeClosedAndRetried() {
        source.failStart = true
        tapButton(vm.copy(R.string.meta_search_object))
        grantCamera()
        await { vm.state.value.phonePreview.phase == PhonePreviewPhase.ERROR && !vm.state.value.busy }
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        source.failStart = false
        showSearch()
        tapButton(vm.copy(R.string.meta_search_person))
        grantCamera()
        await { source.starts == 2 && !vm.state.value.busy }
    }

    @Test fun closingWhileCameraStartsRejectsLateCompletionAndAllowsAnotherSearch() {
        val started = CompletableDeferred<Unit>()
        source.waitForStart = started
        tapButton(vm.copy(R.string.meta_search_object))
        grantCamera()
        await { vm.state.value.busy && source.starts == 1 }
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        started.complete(Unit)
        await { !vm.state.value.wearable.cameraActive && !vm.state.value.busy }
        showSearch()
        tapButton(vm.copy(R.string.meta_search_person))
        grantCamera()
        await { source.starts == 2 && !vm.state.value.busy }
    }

    @Test fun actualCameraXReceivesFramesAfterDisplayButtonTap() {
        main { vm.phoneCapture = CameraXPhoneCaptureSource(compose.activity, compose.activity) }
        tapButton(vm.copy(R.string.meta_search_object))
        grantCamera()
        await { vm.state.value.phonePreview.ready && !vm.state.value.busy }
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        await { !vm.state.value.wearable.cameraActive }
        assertEquals("This case must use CameraX rather than the controlled source", 0, source.starts)
    }

    @Test fun aCallbackFromADisconnectedDisplayCannotOpenCamera() {
        main {
            vm.disconnectDisplay()
            vm.beginMetaObjectSearch()
        }
        await { vm.state.value.message == vm.copy(R.string.status_display_not_connected) }
        assertNull(vm.permissionRequest.value)
        assertEquals(0, source.starts)
    }

    private fun grantCamera() {
        val request = cameraRequest()
        main { vm.onPhonePermissionResult(request.id, request.permission, true) }
    }

    private fun cameraRequest(): RealityPermissionRequest.Android {
        await { vm.permissionRequest.value is RealityPermissionRequest.Android }
        return (vm.permissionRequest.value as RealityPermissionRequest.Android).also { assertEquals(PhonePermission.CAMERA, it.permission) }
    }

    private fun showSearch() {
        main { vm.renderSearchMenu() }
        awaitButton(vm.copy(R.string.meta_search_object))
    }

    private fun await(condition: () -> Boolean) = compose.waitUntil(20_000, condition)
    private fun regression(reason: String, condition: () -> Boolean) {
        try {
            await(condition)
        } catch (error: androidx.compose.ui.test.ComposeTimeoutException) {
            throw AssertionError(reason, error)
        }
    }
    private fun main(block: () -> Unit) {
        if (Looper.myLooper() == Looper.getMainLooper()) block() else instrumentation.runOnMainSync(block)
    }

    private fun webView(): WebView {
        fun find(view: View): WebView? = if (view is WebView) {
            view
        } else {
            (view as? ViewGroup)?.let { group ->
                (0 until group.childCount).firstNotNullOfOrNull { find(group.getChildAt(it)) }
            }
        }
        var result: WebView? = null
        main { result = find(compose.activity.window.decorView) }
        return checkNotNull(result)
    }

    private fun javascript(expression: String): String {
        val result = arrayOf("")
        val done = CountDownLatch(1)
        main {
            webView().evaluateJavascript(expression) {
                result[0] = it
                done.countDown()
            }
        }
        assertTrue("The SDK WebView must answer", done.await(5, TimeUnit.SECONDS))
        return result[0]
    }

    private fun awaitButton(label: String) {
        await { javascript("Array.from(document.querySelectorAll('button,[role=button]')).some(b => b.textContent.includes(${JSONObject.quote(label)}))") == "true" }
    }

    private fun awaitButtonText(text: String) {
        await { javascript("document.body.textContent.includes(${JSONObject.quote(text)})") == "true" }
    }

    private fun tapButton(label: String) {
        awaitButton(label)
        val rectangle = JSONObject(
            javascript(
                """
            (() => {
                const b = Array.from(document.querySelectorAll('button,[role=button]')).find(b => b.textContent.includes(${JSONObject.quote(label)}));
                const r = b.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2, viewport: window.innerWidth};
            })()
                """.trimIndent()
            )
        )
        val location = IntArray(2)
        var factor = 1f
        main {
            val view = webView()
            view.getLocationOnScreen(location)
            factor = (view.width / rectangle.getDouble("viewport")).toFloat()
        }
        val x = location[0] + rectangle.getDouble("x").toFloat() * factor
        val y = location[1] + rectangle.getDouble("y").toFloat() * factor
        val now = SystemClock.uptimeMillis()
        for (action in listOf(MotionEvent.ACTION_DOWN, MotionEvent.ACTION_UP)) {
            val event = MotionEvent.obtain(now, now + if (action == MotionEvent.ACTION_UP) 80 else 0, action, x, y, 0)
            event.source = InputDevice.SOURCE_TOUCHSCREEN
            instrumentation.sendPointerSync(event)
            event.recycle()
        }
    }

    private class CameraSource : PhoneCaptureSource {
        @Volatile var starts = 0
        var waitForStart: CompletableDeferred<Unit>? = null
        var failStart = false
        override suspend fun setPreviewSurface(surfaceProvider: Preview.SurfaceProvider?, viewPort: ViewPort?) = Unit
        override suspend fun startPreview() {
            starts++
            waitForStart?.await()
            check(!failStart) { "Camera startup failed" }
        }
        override suspend fun stopPreview() = Unit
        override suspend fun takePhoto(): PhoneMedia = error("No test photo may be uploaded")
        override suspend fun startVideo() = error("No test recording may start")
        override suspend fun stopVideo(): PhoneMedia = error("No test recording may be uploaded")
        override fun cancelVideo() = Unit
        override fun close() = Unit
    }
}
