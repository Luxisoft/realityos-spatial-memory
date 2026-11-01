package com.luxisoft.realityos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatScrollPolicyTest {
    @Test
    fun sendAndReplyResumeFollowingWhileReadingHistory() {
        val policy = ChatScrollPolicy()
        policy.manualDrag()
        assertFalse(policy.follow)
        policy.newTurn() // Local send, irrespective of current history position.
        assertTrue(policy.follow)
        policy.manualDrag()
        policy.newTurn() // Received reply must also bring its bubble into view.
        assertTrue(policy.follow)
    }

    @Test
    fun historyLoadingAndResizingDoNotStealManualPosition() {
        val policy = ChatScrollPolicy()
        policy.manualDrag()
        repeat(3) { policy.settledAtBottom(false) }
        assertFalse(policy.follow)
        policy.settledAtBottom(true)
        assertTrue(policy.follow)
    }
}
