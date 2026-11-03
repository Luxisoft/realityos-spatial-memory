package com.luxisoft.realityos

import org.json.JSONObject
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

@org.junit.runner.RunWith(org.robolectric.RobolectricTestRunner::class)
@org.robolectric.annotation.Config(sdk = [35], application = android.app.Application::class)
class PasswordAccountSessionTest {
    @Test
    fun `confirmed password session is independent from local debug access`() {
        SocialSession.clear()
        SocialSession.remember(JSONObject().put("access_token", "a").put("refresh_token", "b").put("password_account", true))
        assertTrue(SocialSession.accountEntryAllowed)
        assertFalse(SocialSession.localAccount)
        SocialSession.clear()
        assertFalse(SocialSession.accountEntryAllowed)
    }

    @Test
    fun `unconfirmed restored flag cannot admit account`() {
        SocialSession.clear()
        SocialSession.passwordAccount = true
        assertFalse(SocialSession.accountEntryAllowed)
        SocialSession.clear()
    }
}
