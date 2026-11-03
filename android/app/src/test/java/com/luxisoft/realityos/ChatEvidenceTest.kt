package com.luxisoft.realityos
import org.junit.Assert.assertEquals
import org.junit.Test

class ChatEvidenceTest {
    @Test fun `video starts three seconds before the frame without negative seek`() {
        assertEquals(0L, videoStartMs(1500))
        assertEquals(9000L, videoStartMs(12000))
        assertEquals("01:02:03", evidenceTime(3723999))
    }

    @Test fun `carousel has one item for main evidence repeated in gallery`() {
        val message = ChatMessage(
            role = ChatRole.AI,
            text = "objeto",
            evidenceUrl = "marked",
            evidenceMediaId = "same",
            gallery = listOf(GalleryThumb("preview", "original", mediaId = "same", imageUrl = "marked2"), GalleryThumb("other", "other", mediaId = "different"))
        )
        assertEquals(2, message.viewerItems().size)
        assertEquals("marked", message.viewerItems().first().viewerUrl)
    }

    @Test fun `history keeps gallery items anchored to evidence`() {
        assertEquals(true, keepHistoryThumb(GalleryThumb("t", "m", evidenceId = "e1")))
    }

    @Test fun `history drops private face references and keeps only avatars`() {
        assertEquals(false, keepHistoryThumb(GalleryThumb("/v1/faces/enrollments/1/thumbnail", "/v1/faces/enrollments/1/thumbnail")))
        assertEquals(true, keepHistoryThumb(GalleryThumb("/v1/profiles/1/avatar", "/v1/profiles/1/avatar")))
    }

    @Test fun `history drops unanchored gallery items`() {
        assertEquals(false, keepHistoryThumb(GalleryThumb("/v1/gallery/media/x", "/v1/gallery/media/x")))
    }

    @Test fun `face match label shows name and similarity percent`() {
        assertEquals("Ana (92%)", faceMatchLabel("Ana", 0.92))
        assertEquals("Luis (0%)", faceMatchLabel("Luis", null))
    }

    @Test fun `group rows number distinct faces and reuse numbers on shared faces`() {
        val boxA = FaceProbeBox(0f, 0f, 0.5f, 0.5f, 0)
        val boxB = FaceProbeBox(0.5f, 0f, 0.5f, 0.5f, 1)
        val thumbs = listOf(
            GalleryThumb("t", "m", caption = "Ana", probeBox = boxA),
            GalleryThumb("t", "m", caption = "Luis", probeBox = boxB),
            GalleryThumb("t", "m", caption = "Eva", probeBox = boxA)
        )
        val rows = faceGroupRows(thumbs, listOf("#AAAAAA", "#BBBBBB"))
        assertEquals(listOf(1, 2, 1), rows.map { it.number })
        assertEquals(listOf("#AAAAAA", "#BBBBBB", "#AAAAAA"), rows.map { it.colorHex })
        assertEquals(listOf(0, 1, 0), rows.map { it.colorIndex })
        val marks = faceGroupMarks(rows)
        assertEquals(listOf(1, 2), marks.map { it.number })
        assertEquals(boxA, marks[0].box)
    }

    @Test fun `group rows skip matches without probe boxes`() {
        val rows = faceGroupRows(listOf(GalleryThumb("t", "m")), listOf("#AAAAAA"))
        assertEquals(true, rows.isEmpty())
        assertEquals(true, faceGroupMarks(rows).isEmpty())
    }

    @Test fun `group marks serialize to backend json`() {
        val marks = listOf(FaceGroupMark(1, FaceProbeBox(0.1f, 0.2f, 0.3f, 0.4f, 0), "#F0BF24"))
        assertEquals(
            "[{\"box\":{\"x\":0.1,\"y\":0.2,\"width\":0.3,\"height\":0.4},\"color\":\"#F0BF24\",\"number\":1}]",
            faceGroupMarksJson(marks)
        )
    }

    @Test fun `viewer prefers annotated full resolution image supplied by API`() {
        val thumb = GalleryThumb("small", "original", boxedUrl = "small-marked", imageUrl = "large-marked", matchKind = "family", localizationQuality = "approximate_box")
        assertEquals("large-marked", thumb.viewerUrl)
        assertEquals("family", thumb.matchKind)
    }

    @Test fun `display thumbnails default to public avatar kind`() {
        assertEquals("avatar", GalleryThumb("t", "m").faceDisplayKind)
    }
}
