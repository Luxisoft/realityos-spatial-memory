package com.luxisoft.realityos

import android.app.Application
import android.view.MotionEvent
import android.view.View
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.click
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTouchInput
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/** Send pointer events through Compose/Android interop; semantic clicks bypass the reported bug. */
@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "w480dp-h800dp")
class PhoneCaptureTouchTest {
    @get:Rule val compose = createComposeRule()

    @Test fun photoAndCloseReceiveTouchesAboveTheTransparentSdkRenderer() {
        var photos = 0
        var closes = 0
        compose.setContent {
            Fixture(onPhoto = { photos++ }, onClose = { closes++ })
        }
        compose.onNodeWithTag("rayban-camera-photo").assertIsEnabled().performTouchInput { click() }
        compose.onNodeWithTag("rayban-camera-cancel").assertIsEnabled().performTouchInput { click() }
        compose.runOnIdle {
            assertEquals("The touch must reach photo, even with an Android renderer layered after it", 1, photos)
            assertEquals("The touch must reach the close X", 1, closes)
        }
        compose.onNodeWithTag("rayban-camera-record-video").assertDoesNotExist()
    }

    @Test fun captureKeepsPhotoAndVideoTouchable() {
        var photos = 0
        var videos = 0
        compose.setContent {
            Fixture(photoSearch = false, onPhoto = { photos++ }, onVideo = { videos++ })
        }
        compose.onNodeWithTag("rayban-camera-photo").performTouchInput { click() }
        compose.onNodeWithTag("rayban-camera-record-video").performTouchInput { click() }
        compose.runOnIdle {
            assertEquals(1, photos)
            assertEquals(1, videos)
        }
    }

    @Test fun closeRemainsTouchableWhileCaptureIsBusy() {
        var closes = 0
        compose.setContent { Fixture(busy = true, onClose = { closes++ }) }
        compose.onNodeWithTag("rayban-camera-photo").assertIsNotEnabled()
        compose.onNodeWithTag("rayban-camera-cancel").assertIsEnabled().performTouchInput { click() }
        compose.runOnIdle { assertEquals(1, closes) }
    }

    @Test fun openingCameraCanBeClosedBeforeAnyFramesArrive() {
        var closes = 0
        compose.setContent {
            Fixture(preview = PhonePreviewState().open(), onClose = { closes++ })
        }
        compose.onNodeWithTag("rayban-camera-photo").assertIsNotEnabled()
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        compose.runOnIdle { assertEquals(1, closes) }
    }

    @Test fun closingTheCameraReturnsTouchControlToTheSdkRenderer() {
        var sdkTouches = 0
        compose.setContent {
            var cameraOpen by remember { mutableStateOf(true) }
            Fixture(cameraVisible = cameraOpen, onClose = { cameraOpen = false }, onSdkTouch = { sdkTouches++ })
        }
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        compose.onNodeWithTag("rayban-camera-cancel").assertDoesNotExist()
        compose.onNodeWithTag("sdk-renderer").performTouchInput { click() }
        compose.runOnIdle { assertEquals(1, sdkTouches) }
    }

    @Test fun recordingCanBeStoppedOrClosedUsingTouches() {
        var stopped = 0
        var closed = 0
        compose.setContent {
            Fixture(recording = true, photoSearch = false, onVideo = { stopped++ }, onClose = { closed++ })
        }
        compose.onNodeWithTag("rayban-camera-photo").assertDoesNotExist()
        compose.onNodeWithTag("rayban-camera-stop-video").performTouchInput { click() }
        compose.onNodeWithTag("rayban-camera-cancel").performTouchInput { click() }
        compose.runOnIdle {
            assertEquals(1, stopped)
            assertEquals(1, closed)
        }
    }

    @Composable
    private fun Fixture(
        preview: PhonePreviewState = PhonePreviewState(1, PhonePreviewPhase.STREAMING),
        busy: Boolean = false,
        photoSearch: Boolean = true,
        recording: Boolean = false,
        cameraVisible: Boolean = true,
        onPhoto: () -> Unit = {},
        onVideo: () -> Unit = {},
        onClose: () -> Unit = {},
        onSdkTouch: () -> Unit = {}
    ) {
        MaterialTheme {
            Box(Modifier.size(108.dp, 192.dp)) {
                if (cameraVisible) {
                    PhoneCaptureViewfinder(
                        preview = preview,
                        recording = recording,
                        recordingSeconds = 0,
                        busy = busy,
                        photoSearch = photoSearch,
                        onPhoto = onPhoto,
                        onVideo = onVideo,
                        onClose = onClose,
                        modifier = Modifier.fillMaxSize()
                    ) {
                        AndroidView(
                            factory = { context -> View(context).apply { setOnTouchListener { _, _ -> true } } },
                            modifier = Modifier.fillMaxSize().testTag("camera-preview-surface")
                        )
                    }
                }
                // Keep a consuming Android renderer in the hit-test path:
                // alpha hides its pixels, including during visibility updates.
                AndroidView(
                    factory = { context ->
                        View(context).apply {
                            setOnTouchListener { _, event ->
                                if (event.action == MotionEvent.ACTION_UP) onSdkTouch()
                                true
                            }
                        }
                    },
                    modifier = Modifier.fillMaxSize().graphicsLayer { alpha = if (cameraVisible) 0f else 1f }.testTag("sdk-renderer")
                )
            }
        }
    }
}
