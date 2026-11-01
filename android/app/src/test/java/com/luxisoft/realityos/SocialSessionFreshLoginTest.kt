package com.luxisoft.realityos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test

class SocialSessionFreshLoginTest {
    @Test
    fun `clear resets fresh login gate`() {
        SocialSession.freshLogin = true
        SocialSession.clear()
        assertFalse(SocialSession.freshLogin)
    }

    @Test
    fun `clear drops pending login notice`() {
        SocialSession.loginNotice = "denied"
        SocialSession.clear()
        assertNull(SocialSession.loginNotice)
    }
}
