package com.luxisoft.realityos

import java.time.ZoneId
import org.junit.Assert.*
import org.junit.Test

class EvidencePresentationTest {
    private fun item(id: String, confidence: Double?, kind: String = "exact", quality: String = "sam", date: String = "2026-10-30T12:00:00Z") = GalleryThumb(id, id, evidenceId = id, confidence = confidence, matchKind = kind, localizationQuality = quality, publishedAt = date)

    @Test fun confidenceTakesPrecedenceOverRelationAndMissingValues() {
        val ordered = orderedEvidence(listOf(item("exact", 0.71), item("similar", 0.98, "similar"), item("missing", null), item("nan", Double.NaN), item("family", 0.95, "family")))
        assertEquals(listOf("similar", "family", "exact", "missing", "nan"), ordered.map { it.evidenceId })
    }

    @Test fun tiesUseRelationThenQualityThenDate() {
        val ordered = orderedEvidence(listOf(item("family", 0.9, "family"), item("approximate", 0.9, quality = "approximate_box"), item("older", 0.9, date = "2026-10-29T12:00:00Z"), item("recent", 0.9)))
        assertEquals(listOf("recent", "older", "approximate", "family"), ordered.map { it.evidenceId })
    }

    @Test fun clickedResourceIdentitySurvivesReordering() {
        val items = listOf(item("first", 0.7), item("clicked", 0.98))
        val chosen = evidenceIdentity(items[1])
        assertEquals(0, orderedEvidence(items).indexOfFirst { evidenceIdentity(it) == chosen })
    }

    @Test fun datesUseSelectedLanguageAndLocalTimezone() {
        val utc = ZoneId.of("UTC")
        assertEquals("Oct 30, 2026", evidenceDate("2026-10-30T01:00:00Z", "en", utc))
        val spanish = evidenceDate("2026-10-30T01:00:00Z", "es", utc).orEmpty()
        assertTrue(spanish.contains("oct"))
        assertFalse(spanish.contains("Oct"))
        assertTrue(evidenceDate("2026-10-30T01:00:00Z", "en", ZoneId.of("America/Bogota")).orEmpty().contains("29"))
        assertNull(evidenceDate("invalid", "es", utc))
    }

    @Test fun percentagesDoNotInventMissingConfidence() {
        assertEquals("97%", evidencePercent(0.97, "en"))
        assertTrue(evidencePercent(0.97, "es").orEmpty().contains("97"))
        assertNull(evidencePercent(null, "es"))
        assertNull(evidencePercent(1.1, "es"))
    }

    @Test fun preparedInformationUsesSelectedLanguageWithoutFallback() {
        val english = EvidenceText("Workshop", "Keep on shelf 2", listOf("crimping tool"))
        val spanish = EvidenceText("Taller", "Guardar en el estante 2", listOf("crimpadora"))
        val item = GalleryThumb("preview", "large", evidenceId = "saved", localizedInformation = mapOf("en" to english, "es" to spanish))
        assertEquals(spanish, storedEvidenceText(listOf(item), "es")["saved"])
        assertEquals(english, storedEvidenceText(listOf(item), "en")["saved"])
        assertTrue(storedEvidenceText(listOf(item.copy(localizedInformation = mapOf("en" to english))), "es").isEmpty())
    }
}
