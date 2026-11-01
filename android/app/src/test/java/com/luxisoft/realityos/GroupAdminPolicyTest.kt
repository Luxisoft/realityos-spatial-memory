package com.luxisoft.realityos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class GroupAdminPolicyTest {
    @Test
    fun adminAlwaysInvites() {
        assertTrue(GroupAdminPolicy.canInvite("admin", false))
    }

    @Test
    fun grantedMemberInvitesButPlainMemberDoesNot() {
        assertTrue(GroupAdminPolicy.canInvite("query", true))
        assertFalse(GroupAdminPolicy.canInvite("query", false))
        assertFalse(GroupAdminPolicy.canInvite("register", false))
    }

    @Test
    fun nobodyRemovesAdmins() {
        assertFalse(GroupAdminPolicy.canRemoveMember("admin", false, "admin"))
        assertFalse(GroupAdminPolicy.canRemoveMember("query", true, "admin"))
    }

    @Test
    fun invitersRemovePlainMembers() {
        assertTrue(GroupAdminPolicy.canRemoveMember("admin", false, "query"))
        assertTrue(GroupAdminPolicy.canRemoveMember("query", true, "query"))
        assertFalse(GroupAdminPolicy.canRemoveMember("query", false, "query"))
    }

    @Test
    fun onlyAdminGrantsInvite() {
        assertTrue(GroupAdminPolicy.canGrantInvite("admin"))
        assertFalse(GroupAdminPolicy.canGrantInvite("query"))
    }

    @Test
    fun onlyCreatorDeletes() {
        assertTrue(GroupAdminPolicy.showDeleteGroup(true))
        assertFalse(GroupAdminPolicy.showDeleteGroup(false))
    }
}
