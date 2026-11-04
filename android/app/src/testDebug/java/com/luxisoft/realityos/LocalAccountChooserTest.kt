package com.luxisoft.realityos

import android.app.Application
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import java.io.File
import java.util.concurrent.TimeUnit
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okio.Buffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "en-w390dp-h844dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class LocalAccountChooserTest {
    @get:Rule val compose = createAndroidComposeRule<androidx.activity.ComponentActivity>()

    private fun chooser(scale: Float) {
        val groups = listOf("Pacific Ridge Police Department", "Meta Social Media", "Sonoran Neurological Institute")
        val names = listOf("Alex Rivera", "Maya Johnson", "Daniel Kim", "Elena Marquez", "Mateo Rios", "Sarah Chen", "Noah Brooks", "Lucia Vega", "Owen Patel")
        val accounts = names.mapIndexed { index, name -> LocalAccount(index.toString(), "person-$index", name, "group-${index / 3}", groups[index / 3]) }
        var selected = ""
        compose.setContent {
            CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, scale)) {
                RealityOsTheme { LocalAccountChooser(accounts, false, false, {}, { selected = it.id }) }
            }
        }
        names.forEach { compose.onNodeWithText(it).assertDoesNotExist() }
        capture("collapsed-$scale")
        groups.forEachIndexed { index, group ->
            compose.onNodeWithTag("local-group-$group").performScrollTo().performClick()
            for (member in index * 3 until index * 3 + 3) {
                compose.onNodeWithTag("local-account-person-$member").performScrollTo().assertIsDisplayed().performClick()
                assertEquals(member.toString(), selected)
            }
            capture("expanded-$index-$scale")
            compose.onNodeWithTag("local-group-$group").performScrollTo().performClick()
            names.slice(index * 3 until index * 3 + 3).forEach { compose.onNodeWithText(it).assertDoesNotExist() }
        }
        assertEquals("8", selected)
    }

    private fun capture(name: String) {
        compose.waitForIdle()
        compose.runOnIdle {
            val view = compose.activity.window.decorView
            val bitmap = android.graphics.Bitmap.createBitmap(view.width, view.height, android.graphics.Bitmap.Config.ARGB_8888)
            view.draw(android.graphics.Canvas(bitmap))
            val language = compose.activity.resources.configuration.locales[0].language
            val directory = File("build/outputs/local-access").apply { mkdirs() }
            File(directory, "$language-$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        }
    }

    @Test fun allNineAccountsCanBeReachedAndSelected() = chooser(1f)

    @Test
    @Config(qualifiers = "es-w320dp-h640dp-mdpi")
    fun spanishNarrowScreenAtTwoHundredPercentText() = chooser(2f)

    @Test fun connectionErrorOffersRetry() {
        var retries = 0
        compose.setContent { RealityOsTheme { LocalAccountChooser(emptyList(), false, true, { retries++ }, {}) } }
        compose.onNodeWithText("Retry").performClick()
        assertEquals(1, retries)
        capture("error")
    }

    @Test fun profilePhotoLoadsWithoutLoginCredentials() {
        val server = MockWebServer().apply { start() }
        val imageError = java.util.concurrent.atomic.AtomicReference("")
        val imageLoaded = java.util.concurrent.atomic.AtomicBoolean(false)
        coil.Coil.setImageLoader(
            coil.ImageLoader.Builder(compose.activity)
                .networkObserverEnabled(false)
                .eventListener(object : coil.EventListener {
                    override fun onError(request: coil.request.ImageRequest, result: coil.request.ErrorResult) {
                        imageError.set(result.throwable.toString())
                    }
                    override fun onSuccess(request: coil.request.ImageRequest, result: coil.request.SuccessResult) {
                        imageLoaded.set(true)
                    }
                })
                .build()
        )
        try {
            val photo = android.graphics.Bitmap.createBitmap(16, 16, android.graphics.Bitmap.Config.ARGB_8888)
            photo.eraseColor(android.graphics.Color.RED)
            val bytes = java.io.ByteArrayOutputStream()
            photo.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, bytes)
            photo.recycle()
            server.enqueue(MockResponse().setHeader("Content-Type", "image/png").setBody(Buffer().write(bytes.toByteArray())))
            val account = LocalAccount("photo", "photo", "Photo", "group", "Group", server.url("/avatar").toString())
            compose.setContent { RealityOsTheme { LocalAccountAvatar(account) } }
            compose.onNodeWithTag("local-avatar-photo").assertIsDisplayed()
            compose.waitUntil(10_000) {
                compose.waitForIdle()
                check(imageError.get().isEmpty()) { imageError.get() }
                imageLoaded.get()
            }
            compose.onNodeWithTag("local-avatar-photo").assertIsDisplayed()
            capture("loaded-photo")
            val request = server.takeRequest(1, TimeUnit.SECONDS)
            assertNotNull(request)
            assertEquals(null, request!!.getHeader("Authorization"))
        } finally {
            coil.Coil.reset()
            server.shutdown()
        }
    }

    @Test fun missingPhotoUsesTheIllustratedAvatar() {
        val account = LocalAccount("missing", "missing", "Missing", "group", "Group")
        compose.setContent { RealityOsTheme { LocalAccountAvatar(account) } }
        compose.onNodeWithTag("local-avatar-missing").assertIsDisplayed()
        capture("default-avatar")
    }

    @Test fun failedPhotoKeepsTheIllustratedAvatar() {
        val server = MockWebServer().apply { start() }
        val failed = java.util.concurrent.atomic.AtomicBoolean(false)
        coil.Coil.setImageLoader(
            coil.ImageLoader.Builder(compose.activity)
                .networkObserverEnabled(false)
                .eventListener(object : coil.EventListener {
                    override fun onError(request: coil.request.ImageRequest, result: coil.request.ErrorResult) {
                        failed.set(true)
                    }
                })
                .build()
        )
        try {
            server.enqueue(MockResponse().setResponseCode(404))
            val account = LocalAccount("failed", "failed", "Failed", "group", "Group", server.url("/missing-avatar").toString())
            compose.setContent { RealityOsTheme { LocalAccountAvatar(account) } }
            compose.onNodeWithTag("local-avatar-failed").assertIsDisplayed()
            compose.waitUntil(10_000) {
                compose.waitForIdle()
                failed.get()
            }
            compose.onNodeWithTag("local-avatar-failed").assertIsDisplayed()
            capture("failed-avatar")
        } finally {
            coil.Coil.reset()
            server.shutdown()
        }
    }
}
