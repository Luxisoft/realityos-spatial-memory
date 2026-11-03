package com.luxisoft.realityos

import android.app.Application
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.media.ExifInterface
import java.io.File
import java.net.HttpURLConnection
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okio.ByteString.Companion.toByteString
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class RecognitionPhotoUploadTest {
    private val originalConnection = SocialSession.openJsonConnection
    private val colors = listOf(Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW)

    @Before fun initialize() {
        LocalizedText.initialize(RuntimeEnvironment.getApplication())
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.SPANISH)
        SocialSession.clear()
    }

    @After fun reset() {
        SocialSession.openJsonConnection = originalConnection
        SocialSession.clear()
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
    }

    private fun photo(orientation: Int, width: Int = 96, height: Int = 64): ByteArray {
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val canvas = android.graphics.Canvas(bitmap)
        val paint = android.graphics.Paint()
        colors.forEachIndexed { index, color ->
            paint.color = color
            val left = if (index % 2 == 0) 0f else width / 2f
            val top = if (index < 2) 0f else height / 2f
            canvas.drawRect(left, top, left + width / 2f, top + height / 2f, paint)
        }
        val file = File.createTempFile("orientation-", ".jpg", RuntimeEnvironment.getApplication().cacheDir)
        try {
            file.outputStream().use { bitmap.compress(Bitmap.CompressFormat.JPEG, 98, it) }
            ExifInterface(file).apply {
                setAttribute(ExifInterface.TAG_ORIENTATION, orientation.toString())
                saveAttributes()
            }
            return file.readBytes()
        } finally {
            bitmap.recycle()
            file.delete()
        }
    }

    @Test fun allEightExifOrientationsProduceUprightPixelsAndNoSecondRotation() {
        val expected = listOf(
            listOf(0, 1, 2, 3),
            listOf(1, 0, 3, 2),
            listOf(3, 2, 1, 0),
            listOf(2, 3, 0, 1),
            listOf(0, 2, 1, 3),
            listOf(2, 0, 3, 1),
            listOf(3, 1, 2, 0),
            listOf(1, 3, 0, 2)
        )
        for (orientation in 1..8) {
            val bytes = prepareRecognitionPhoto(photo(orientation))
            val decoded = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
            assertEquals(if (orientation >= 5) 64 else 96, decoded.width)
            assertEquals(if (orientation >= 5) 96 else 64, decoded.height)
            expected[orientation - 1].forEachIndexed { corner, colorIndex ->
                val actual = decoded.getPixel(decoded.width * (if (corner % 2 == 0) 1 else 3) / 4, decoded.height * (if (corner < 2) 1 else 3) / 4)
                val correct = colors[colorIndex]
                assertTrue("orientation=$orientation corner=$corner", listOf(Color.red(actual) - Color.red(correct), Color.green(actual) - Color.green(correct), Color.blue(actual) - Color.blue(correct)).all { kotlin.math.abs(it) < 20 })
            }
            assertTrue(ExifInterface(bytes.inputStream()).getAttributeInt(ExifInterface.TAG_ORIENTATION, 1) in setOf(0, 1))
            decoded.recycle()
        }
    }

    @Test fun largePhonePhotoIsBoundedAndInvalidInputIsNotUploaded() {
        val bytes = prepareRecognitionPhoto(photo(6, width = 3600, height = 2400))
        val decoded = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        assertTrue(decoded.height > decoded.width)
        assertTrue(maxOf(decoded.width, decoded.height) <= 1600)
        assertTrue(bytes.size < 5 * 1024 * 1024)
        decoded.recycle()
        val failure = assertThrows(IllegalStateException::class.java) { prepareRecognitionPhoto(byteArrayOf(1, 2, 3)) }
        assertEquals(localizedText(R.string.face_unreadable), failure.message)
    }

    @Test fun profileAndAvatarReceiveExactlyTheSameUprightJpeg() {
        val server = MockWebServer().apply { start() }
        try {
            SocialSession.token = "synthetic-profile-session"
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setResponseCode(201).setBody("""{"faces_enrolled":1}"""))
            server.enqueue(MockResponse().setBody("{}"))
            val bytes = prepareRecognitionPhoto(photo(6))
            uploadRecognitionProfile(bytes)
            listOf("/faces/profile-photo", "/me/profile/avatar").forEach { path ->
                val request = server.takeRequest()
                assertEquals(path, request.path)
                assertEquals("Bearer synthetic-profile-session", request.getHeader("Authorization"))
                val body = request.body.readByteString()
                assertTrue(body.utf8().contains("name=\"file\""))
                assertTrue(body.utf8().contains("Content-Type: image/jpeg"))
                assertTrue(body.indexOf(bytes.toByteString()) >= 0)
            }
        } finally {
            server.shutdown()
        }
    }

    @Test fun rejectedProfileExplainsTheReasonAndNeverUploadsAnAvatar() {
        val server = MockWebServer().apply { start() }
        try {
            SocialSession.token = "synthetic-profile-session"
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setResponseCode(422).setBody(JSONObject().put("detail", "Profile photos must show exactly one face.").toString()))
            val failure = assertThrows(IllegalStateException::class.java) { uploadRecognitionProfile(prepareRecognitionPhoto(photo(1))) }
            assertEquals(localizedText(R.string.biometric_photo_one_face), failure.message)
            assertEquals(1, server.requestCount)
            assertEquals("synthetic-profile-session", SocialSession.token)
            server.enqueue(MockResponse().setResponseCode(201).setBody("""{"faces_enrolled":0}"""))
            assertThrows(IllegalStateException::class.java) { uploadRecognitionProfile(prepareRecognitionPhoto(photo(1))) }
            assertEquals(2, server.requestCount)
        } finally {
            server.shutdown()
        }
    }

    @Test fun rejectionMessagesAreLocalizedAndNeverExposeUnknownServerDetails() {
        val body = JSONObject().put("detail", "No live face could be verified in this image. Take the photo directly with the camera in good light.").toString()
        assertEquals(localizedText(R.string.biometric_photo_quality), recognitionPhotoFailure("faces/profile-photo", 422, body))
        RealityExperienceStore(RuntimeEnvironment.getApplication()).setLanguage(RealityLanguage.ENGLISH)
        assertEquals(localizedText(R.string.biometric_photo_quality), recognitionPhotoFailure("faces/profile-photo", 422, body))
        assertEquals(localizedText(R.string.biometric_photo_rejected), recognitionPhotoFailure("faces/profile-photo", 422, "private server details"))
        assertNull(recognitionPhotoFailure("me/publication-uploads", 422, body))
        assertNull(recognitionPhotoFailure("faces/profile-photo", 500, body))
    }
}
