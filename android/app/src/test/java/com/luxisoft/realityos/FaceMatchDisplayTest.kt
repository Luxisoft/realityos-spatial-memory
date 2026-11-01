package com.luxisoft.realityos

import android.app.Application
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/** Face-match JSON parsing needs the Android framework (Robolectric provides org.json). */
@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35])
class FaceMatchDisplayTest {
    @Test fun `face match exposes its enrollment for signed display thumbnails`() {
        val match = JSONObject()
            .put("display_name", "Ana")
            .put("evidence", JSONObject().put("enrollment_id", "e-1").put("thumbnail_url", "/v1/faces/enrollments/e-1/thumbnail"))
        assertEquals("e-1", faceMatchEnrollmentId(match))
        assertEquals("", faceMatchEnrollmentId(JSONObject().put("display_name", "Ana")))
        assertEquals("", faceMatchEnrollmentId(null))
    }

    @Test fun `face match exposes its probe box`() {
        val match = JSONObject()
            .put("probe_face_index", 2)
            .put("probe_box", JSONObject().put("x", 0.1).put("y", 0.2).put("width", 0.3).put("height", 0.4))
        assertEquals(FaceProbeBox(0.1f, 0.2f, 0.3f, 0.4f, 2), faceMatchProbeBox(match))
        assertEquals(null, faceMatchProbeBox(JSONObject()))
        assertEquals(null, faceMatchProbeBox(null))
        val flat = JSONObject()
            .put("probe_face_index", 0)
            .put("probe_box", JSONObject().put("x", 0.1).put("y", 0.2).put("width", 0.0).put("height", 0.4))
        assertEquals(null, faceMatchProbeBox(flat))
    }
}
