package com.luxisoft.realityos

import org.junit.Assert.*
import org.junit.Test

class PhonePreviewStateTest {
    @Test fun cameraMustDeliverFramesBeforeEnablingPhotoOrVideo() {
        val opening = PhonePreviewState().open()
        assertFalse(opening.ready)
        val running = opening.streaming(opening.generation, true)
        assertTrue(running.ready)
        assertFalse(running.streaming(running.generation, false).ready)
    }

    @Test fun navigatingAwayInvalidatesLateStreamingAndErrorCallbacks() {
        val opening = PhonePreviewState().open()
        val closed = opening.close()
        assertEquals(PhonePreviewPhase.IDLE, closed.phase)
        assertEquals(closed, closed.streaming(opening.generation, true))
        assertEquals(closed, closed.fail(opening.generation, "Late permission failure"))
        assertFalse(closed.ready)
    }

    @Test fun oldSurfaceCannotDisableOrFailAReopenedCamera() {
        val old = PhonePreviewState().open()
        val new = old.close().open()
        val running = new.streaming(new.generation, true)
        assertEquals(running, running.streaming(old.generation, false))
        assertEquals(running, running.fail(old.generation, "Old timeout"))
        assertTrue(running.ready)
    }

    @Test fun timeoutStaysVisibleUntilFramesArriveOrTheCameraIsReopened() {
        val opening = PhonePreviewState().open()
        val failed = opening.fail(opening.generation, "No frames")
        assertFalse(failed.ready)
        assertEquals(failed, failed.streaming(failed.generation, false))
        assertTrue(failed.streaming(failed.generation, true).ready)
        val reopened = failed.close().open()
        assertNull(reopened.error)
        assertEquals(PhonePreviewPhase.OPENING, reopened.phase)
        assertFalse(reopened.ready)
    }

    @Test fun idleCameraCannotBeActivatedByUnsolicitedCallbacks() {
        val idle = PhonePreviewState()
        assertEquals(idle, idle.streaming(idle.generation, true))
        assertEquals(idle, idle.fail(idle.generation, "No camera request"))
    }
}
