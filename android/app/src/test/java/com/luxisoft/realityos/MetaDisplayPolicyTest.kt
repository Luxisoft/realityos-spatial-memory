package com.luxisoft.realityos

import org.junit.Assert.*
import org.junit.Test

class MetaDisplayPolicyTest {
    private val profile = MetaDestination("home", "Profile")
    private val work = MetaDestination("group-a", "Care team")

    @Test fun captureAndPendingUploadFreezeDestination() {
        assertTrue(MetaDisplayPolicy.canChangeDestination(false, false, false))
        assertFalse(MetaDisplayPolicy.canChangeDestination(true, false, false))
        assertFalse(MetaDisplayPolicy.canChangeDestination(false, true, false))
        assertFalse(MetaDisplayPolicy.canChangeDestination(false, false, true))
    }

    @Test fun captureRequiresAnExistingGroup() {
        assertEquals(work, MetaDisplayPolicy.publicationDestination(listOf(work, profile), null))
        assertNull(MetaDisplayPolicy.publicationDestination(listOf(profile), null))
        assertNull(MetaDisplayPolicy.publicationDestination(emptyList(), null))
    }

    @Test fun multipleGroupsRequireASelection() {
        val other = work.copy(id = "group-b")
        assertNull(MetaDisplayPolicy.publicationDestination(listOf(work, other), null))
        assertEquals(other, MetaDisplayPolicy.publicationDestination(listOf(work, other), other.id))
    }

    @Test fun galleryIsDefaultAndSourcesHaveDifferentWireValues() {
        assertEquals(MetaSearchScope.GALLERY, MetaDisplayState().searchScope)
        assertEquals("gallery", MetaSearchScope.GALLERY.wire)
        assertEquals("registry", MetaSearchScope.REGISTRY.wire)
    }

    @Test fun photoSearchDefaultsToObject() {
        assertEquals(MetaPhotoSearchKind.OBJECT, MetaDisplayState().photoSearchKind)
    }

    @Test fun photoSearchKindsUseDifferentBackends() {
        assertEquals("queries/image", MetaDisplayPolicy.photoSearchPath(MetaPhotoSearchKind.OBJECT))
        assertEquals("faces/search", MetaDisplayPolicy.photoSearchPath(MetaPhotoSearchKind.PERSON))
    }

    @Test fun photoSearchKindsShowDifferentCaptureTitles() {
        assertEquals(R.string.meta_search_photo_object, MetaDisplayPolicy.photoSearchCaptureTitle(MetaPhotoSearchKind.OBJECT))
        assertEquals(R.string.meta_search_photo_person, MetaDisplayPolicy.photoSearchCaptureTitle(MetaPhotoSearchKind.PERSON))
    }

    @Test fun voiceRoutesPersonDescriptionsToPeopleSearch() {
        assertEquals(MetaVoiceSearch.PERSON_TEXT, MetaDisplayPolicy.voiceSearchRoute("person", false))
    }

    @Test fun voiceBlocksPeopleSearchForGuests() {
        assertEquals(MetaVoiceSearch.PERSON_BLOCKED, MetaDisplayPolicy.voiceSearchRoute("person", true))
    }

    @Test fun voiceRoutesObjectsAndAmbiguousTextToObjectSearch() {
        assertEquals(MetaVoiceSearch.OBJECT_QUERY, MetaDisplayPolicy.voiceSearchRoute("object", false))
        assertEquals(MetaVoiceSearch.OBJECT_QUERY, MetaDisplayPolicy.voiceSearchRoute("ask", false))
        assertEquals(MetaVoiceSearch.OBJECT_QUERY, MetaDisplayPolicy.voiceSearchRoute("unknown", false))
    }

    @Test fun voiceKeepsGreetingsAsChat() {
        assertEquals(MetaVoiceSearch.CHAT, MetaDisplayPolicy.voiceSearchRoute("chat", false))
    }

    @Test fun faceMatchesRenderOnlyAvatars() {
        assertEquals("avatar", MetaDisplayPolicy.faceDisplayKind())
    }

    @Test fun faceGroupPaletteHasEightDistinctHexColors() {
        val palette = MetaDisplayPolicy.faceGroupPalette()
        assertEquals(8, palette.size)
        assertEquals(8, palette.toSet().size)
        palette.forEach { assertTrue(it.matches(Regex("#[0-9A-Fa-f]{6}"))) }
    }

    @Test fun faceMarkColorNamesCycleWithPalette() {
        assertEquals(R.string.meta_face_color_1, MetaDisplayPolicy.faceMarkColorName(0))
        assertEquals(R.string.meta_face_color_8, MetaDisplayPolicy.faceMarkColorName(7))
        assertEquals(R.string.meta_face_color_1, MetaDisplayPolicy.faceMarkColorName(8))
    }

    @Test fun oldResponsesCannotCrossReconnectOrAccountSwitch() {
        val generation = MetaDisplayGeneration()
        val first = generation.revision
        assertTrue(generation.accepts(first))
        generation.invalidate()
        assertFalse(generation.accepts(first))
        val reconnected = generation.revision
        assertTrue(generation.accepts(reconnected))
        generation.invalidate()
        assertFalse(generation.accepts(reconnected))
    }
}
