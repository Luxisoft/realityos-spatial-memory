package com.luxisoft.realityos

/** Resolve authorized workspace metadata before the first query, including cold starts. */
internal fun queryWorkspaceId(spaces: List<Pair<String, String>>, selectedWork: String?, personal: String?): String {
    selectedWork?.takeIf { selected -> spaces.any { it.first == selected } }?.let { return it }
    spaces.filter { !it.second.startsWith("home:") }.singleOrNull()?.let { return it.first }
    return personal?.takeIf { home -> spaces.any { it.first == home } } ?: spaces.firstOrNull()?.first.orEmpty()
}
