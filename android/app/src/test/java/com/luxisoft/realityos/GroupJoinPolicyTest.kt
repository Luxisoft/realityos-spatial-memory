package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class GroupJoinPolicyTest {
    @Test
    fun `nine digits route to pin join`() {
        assertEquals(GroupJoinPolicy.Route.PIN, GroupJoinPolicy.route("123456789"))
    }

    @Test
    fun `pin ignores spaces and dashes`() {
        assertEquals(GroupJoinPolicy.Route.PIN, GroupJoinPolicy.route("123 456 789"))
        assertEquals(GroupJoinPolicy.Route.PIN, GroupJoinPolicy.route("123-456-789"))
    }

    @Test
    fun `other input routes to legacy code join`() {
        assertEquals(GroupJoinPolicy.Route.CODE, GroupJoinPolicy.route("aB3x9Q2"))
        assertEquals(GroupJoinPolicy.Route.CODE, GroupJoinPolicy.route("12345678"))
        assertEquals(GroupJoinPolicy.Route.CODE, GroupJoinPolicy.route("1234567890"))
        assertEquals(GroupJoinPolicy.Route.CODE, GroupJoinPolicy.route(""))
    }
}
