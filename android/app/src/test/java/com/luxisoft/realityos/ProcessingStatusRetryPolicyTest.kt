package com.luxisoft.realityos

import java.io.IOException
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ProcessingStatusRetryPolicyTest {
    @Test
    fun `missing device job stops polling immediately`() {
        assertTrue(
            ProcessingStatusRetryPolicy.shouldStop(
                RealityApiException("Not Found", statusCode = 404),
                consecutiveFailures = 1,
            ),
        )
    }

    @Test
    fun `transient failures are bounded without stopping on the first one`() {
        assertFalse(
            ProcessingStatusRetryPolicy.shouldStop(
                IOException("network unavailable"),
                consecutiveFailures = 1,
            ),
        )
        assertTrue(
            ProcessingStatusRetryPolicy.shouldStop(
                IOException("network unavailable"),
                consecutiveFailures = ProcessingStatusRetryPolicy.maxConsecutiveFailures,
            ),
        )
    }
}
