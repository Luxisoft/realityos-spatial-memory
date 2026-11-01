package com.luxisoft.realityos

/**
 * Routes a captured search probe from the backend classification without
 * asking the user: any face goes to people search (the backend prompt
 * already excludes persons from the object labels, so remaining labels are
 * background), otherwise the probe goes to object search, which also serves
 * as the automatic fallback when nothing was detected.
 */
internal object SearchTargetPolicy {
    enum class Target { PERSON, OBJECT }

    fun decide(faceCount: Int, objectLabels: List<String>): Target = when {
        faceCount > 0 -> Target.PERSON
        else -> Target.OBJECT
    }
}
