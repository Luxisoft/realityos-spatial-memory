package com.luxisoft.realityos

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class ChatProbeStoreTest {
    @get:Rule
    val dir = TemporaryFolder()

    private fun probe(name: String, ageMs: Long): File =
        File(dir.root, name).apply {
            writeBytes(byteArrayOf(1, 2, 3))
            setLastModified(1_000_000L + ageMs)
        }

    @Test
    fun `prune drops oldest probes beyond the cap`() {
        val files = (0 until 5).map { probe("probe-$it.jpg", it * 60_000L) }
        assertEquals(files.take(3).toSet(), pruneProbeFiles(files, keep = 2).toSet())
    }

    @Test
    fun `prune keeps everything within the cap`() {
        val files = (0 until 2).map { probe("probe-$it.jpg", it * 60_000L) }
        assertTrue(pruneProbeFiles(files, keep = 5).isEmpty())
    }
}
