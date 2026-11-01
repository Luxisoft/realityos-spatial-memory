package com.luxisoft.realityos

/**
 * Routes group-join input: exactly nine digits (ignoring spaces and dashes)
 * is a shared group PIN, anything else is a legacy one-use invite code.
 */
internal object GroupJoinPolicy {
    enum class Route { PIN, CODE }

    fun route(input: String): Route {
        val digits = input.filter { it.isDigit() }
        val rest = input.filter { !it.isDigit() }
        return if (digits.length == 9 && rest.all { it.isWhitespace() || it == '-' }) Route.PIN else Route.CODE
    }
}
