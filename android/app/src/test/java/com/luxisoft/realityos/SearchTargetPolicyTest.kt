package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class SearchTargetPolicyTest {
    @Test
    fun `faces without object labels route to people search`() {
        assertEquals(
            SearchTargetPolicy.Target.PERSON,
            SearchTargetPolicy.decide(faceCount = 2, objectLabels = emptyList()),
        )
    }

    @Test
    fun `labels without faces route to object search`() {
        assertEquals(
            SearchTargetPolicy.Target.OBJECT,
            SearchTargetPolicy.decide(faceCount = 0, objectLabels = listOf("hammer")),
        )
    }

    @Test
    fun `faces take precedence over object labels`() {
        assertEquals(
            SearchTargetPolicy.Target.PERSON,
            SearchTargetPolicy.decide(faceCount = 1, objectLabels = listOf("hammer")),
        )
    }

    @Test
    fun `empty classification falls back to object search`() {
        assertEquals(
            SearchTargetPolicy.Target.OBJECT,
            SearchTargetPolicy.decide(faceCount = 0, objectLabels = emptyList()),
        )
    }
}
