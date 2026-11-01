package com.luxisoft.realityos

/**
 * Decides when a device-job polling failure is no longer safe to retry in the
 * background. A missing job is terminal immediately; transient failures get a
 * small bounded retry window so the display never loops raw transport errors.
 */
internal object ProcessingStatusRetryPolicy {
    const val maxConsecutiveFailures = 3

    fun shouldStop(error: Throwable, consecutiveFailures: Int): Boolean =
        (error as? RealityApiException)?.statusCode == 404 ||
            consecutiveFailures >= maxConsecutiveFailures
}
