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

    @Test fun `record face match decodes to expediente thumbnail`() {
        val match = JSONObject()
            .put("record_id", "record-1")
            .put("title", "Ana Solis")
            .put("similarity", 0.93)
            .put("simulated", true)
            .put(
                "evidence",
                JSONObject()
                    .put("thumbnail_url", "/v1/faces/record-enrollments/e1/thumbnail")
                    .put("media_id", "media-1")
            )
        val thumb = decodeRecordFaceThumb(match)!!
        assertEquals("Ana Solis", thumb.caption)
        assertEquals("record-1", thumb.recordId)
        assertEquals("media-1", thumb.mediaId)
        assertEquals(true, thumb.simulated)
        assertEquals(listOf("record_candidate"), thumb.matchedLabels)
        assertEquals("face_record_enrollment", thumb.faceDisplayKind)
        assertEquals(true, keepHistoryThumb(thumb))
    }

    @Test fun `record face match without evidence is dropped`() {
        assertEquals(null, decodeRecordFaceThumb(JSONObject().put("title", "Ana")))
        assertEquals(null, decodeRecordFaceThumb(null))
    }
}
