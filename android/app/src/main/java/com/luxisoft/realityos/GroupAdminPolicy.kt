package com.luxisoft.realityos

/** Client-side visibility for group administration. The server re-checks every action. */
internal object GroupAdminPolicy {
    fun canInvite(role: String, canInvite: Boolean): Boolean = role == "admin" || canInvite

    fun canRemoveMember(myRole: String, myCanInvite: Boolean, targetRole: String): Boolean =
        canInvite(myRole, myCanInvite) && targetRole != "admin"

    fun canGrantInvite(myRole: String): Boolean = myRole == "admin"

    fun showDeleteGroup(myIsCreator: Boolean): Boolean = myIsCreator
}
