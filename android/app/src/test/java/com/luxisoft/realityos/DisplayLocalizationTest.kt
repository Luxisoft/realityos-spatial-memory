package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DisplayLocalizationTest {
    @Test fun missingEnglishInformationNeverFallsBackToSpanishDescriptions() {
        val item = GalleryThumb("small", "full", caption = "Taladro amarillo", noteText = "Junto a la caja")
        assertNull(displayEvidenceInformation(item, "en"))
        assertEquals("Taladro amarillo", item.caption)
        assertEquals("Junto a la caja", item.noteText)
    }

    @Test fun savedInformationUsesOnlyTheSelectedLanguage() {
        val english = EvidenceText("Yellow drill", "Next to the box", listOf("drill"))
        val spanish = EvidenceText("Taladro amarillo", "Junto a la caja", listOf("taladro"))
        val item = GalleryThumb("small", "full", localizedInformation = mapOf("en" to english, "es" to spanish))
        assertEquals(english, displayEvidenceInformation(item, "en"))
        assertEquals(spanish, displayEvidenceInformation(item, "es"))
        assertNull(displayEvidenceInformation(item, "fr"))
        assertNull(displayEvidenceInformation(null, "en"))
    }

    @Test fun personalNamesRetainTheirOriginalSpelling() {
        val item = GalleryThumb("small", "full", caption = "José Muñoz", faceEnrollmentId = "consented-match")
        assertEquals("José Muñoz", displayEvidenceInformation(item, "en")?.title)
        assertEquals("José Muñoz", displayEvidenceInformation(item, "es")?.title)
    }
}
