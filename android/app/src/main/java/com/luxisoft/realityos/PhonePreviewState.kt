package com.luxisoft.realityos

enum class PhonePreviewPhase { IDLE, OPENING, STREAMING, ERROR }

/** Each camera entry gets a generation so a disposed surface cannot affect its replacement. */
data class PhonePreviewState(
    val generation: Long = 0,
    val phase: PhonePreviewPhase = PhonePreviewPhase.IDLE,
    val error: String? = null
) {
    val ready: Boolean get() = phase == PhonePreviewPhase.STREAMING

    fun open(): PhonePreviewState = PhonePreviewState(generation + 1, PhonePreviewPhase.OPENING)
    fun close(): PhonePreviewState = PhonePreviewState(generation + 1)

    fun streaming(expected: Long, streaming: Boolean): PhonePreviewState = if (expected != generation || phase == PhonePreviewPhase.IDLE || (!streaming && phase == PhonePreviewPhase.ERROR)) {
        this
    } else {
        copy(phase = if (streaming) PhonePreviewPhase.STREAMING else PhonePreviewPhase.OPENING, error = null)
    }

    fun fail(expected: Long, message: String): PhonePreviewState = if (expected != generation || phase == PhonePreviewPhase.IDLE) {
        this
    } else {
        copy(phase = PhonePreviewPhase.ERROR, error = message)
    }
}

/** Compare the viewport's value, not freshly allocated ViewPort object identities. */
internal data class PhonePreviewGeometry(
    val numerator: Int,
    val denominator: Int,
    val rotation: Int,
    val scaleType: Int,
    val layoutDirection: Int
)
