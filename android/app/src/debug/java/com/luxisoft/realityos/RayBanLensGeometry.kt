package com.luxisoft.realityos

/**
 * Native geometry for the Debug-only Ray-Ban Display lens artboard.
 *
 * Coordinates use the cropped 1254 x 858 PNG. Right and bottom bounds are
 * exclusive, which keeps the dimensions stable when they are mapped to dp or
 * pixels by Compose.
 */
internal object RayBanLensGeometry {
    const val ArtboardWidth = 1254f
    const val ArtboardHeight = 858f
    const val ArtboardAspectRatio = ArtboardWidth / ArtboardHeight

    /** Complete source image used while the entrance still shows the glasses. */
    val fullArtboard = LensRect(
        left = 0f,
        top = 0f,
        right = ArtboardWidth,
        bottom = ArtboardHeight,
    )

    /** Flood-filled alpha <= 1 opening from the supplied right-lens asset. */
    val opening = LensRect(left = 176f, top = 167f, right = 1049f, bottom = 753f)

    /**
     * Final photographic crop for the physical shell. It excludes the camera
     * and temple but deliberately starts at the top of the source artboard.
     *
     * The upper brow and the rim overlap in this raster, so any rectangular
     * crop below y = 0 visibly slices an opaque part of the frame. Keeping the
     * full vertical source is the only way to reveal the complete upper rim.
     */
    val finalFrameCrop = LensRect(left = 120f, top = 0f, right = 1080f, bottom = 858f)

    /**
     * Previous fully opaque core of the aperture. It remains a useful visual
     * guardrail and reference point, but is no longer the renderer's bounds:
     * the user-facing Display preview intentionally occupies more of the lens.
     */
    val rendererSafeViewport = LensRect(left = 425f, top = 216f, right = 875f, bottom = 666f)

    /**
     * The actual square viewport for Meta's fixed 600 x 600 Debug renderer.
     *
     * It is 30% larger than [rendererSafeViewport] (585 instead of 450 px on
     * each side), horizontally centred in the aperture and anchored at its
     * upper opening. This raises its top edge by 49 source pixels, roughly
     * 10.9% of the previous rendered height, while retaining the full square
     * content surface instead of distorting it.
     */
    val rendererContentViewport = LensRect(left = 320f, top = 167f, right = 905f, bottom = 752f)

    /**
     * Raises the whole rendered app plane after it has been fitted to the
     * lens. The source viewport stays inside the aperture; only its on-screen
     * presentation moves so the lower rim cannot overlap the bottom control.
     */
    const val RendererContentLiftFraction = 0.15f

    /**
     * The phone camera is intentionally a portrait viewfinder, not a second
     * full-lens display. It sits visibly clear of the rim so the optical
     * frame and the surrounding real-world scene remain readable.
     */
    const val CameraPreviewAspectRatio = 9f / 16f
    const val CameraPreviewOpeningHeightFraction = 0.78f
    private const val CameraPreviewOpeningWidthFraction = 0.84f

    /**
     * The presentation stage includes a small transparent vertical reveal
     * around [finalFrameCrop]. At 720 px wide this produces 24 px above and
     * below the fitted frame, so the rim never touches a clipped edge.
     */
    private const val CanonicalStageWidth = 720f
    private const val CanonicalVerticalInset = 24f
    val frameStageAspectRatio: Float = CanonicalStageWidth /
        (CanonicalStageWidth / finalFrameCrop.width * finalFrameCrop.height + CanonicalVerticalInset * 2f)

    /** The fixed stage follows the full lens frame presentation, not the UI. */
    fun stageFor(availableWidth: Float, availableHeight: Float): LensStage {
        if (availableWidth <= 0f || availableHeight <= 0f) return LensStage(0f, 0f)

        val width = minOf(availableWidth, availableHeight * frameStageAspectRatio)
        return LensStage(width = width, height = width / frameStageAspectRatio)
    }

    /**
     * Source rectangle for the photographic frame at [progress]. The
     * destination stage never changes size; shrinking this rectangle creates
     * the optical zoom without moving or clipping the renderer beneath it.
     */
    fun sourceCrop(progress: Float): LensRect {
        val fraction = progress.coerceIn(0f, 1f)
        return LensRect(
            left = interpolate(fullArtboard.left, finalFrameCrop.left, fraction),
            top = interpolate(fullArtboard.top, finalFrameCrop.top, fraction),
            right = interpolate(fullArtboard.right, finalFrameCrop.right, fraction),
            bottom = interpolate(fullArtboard.bottom, finalFrameCrop.bottom, fraction),
        )
    }

    /** Fits a source crop into the stable stage without distortion or clipping. */
    fun frameDestination(stage: LensStage, sourceCrop: LensRect): LensRect {
        if (stage.width <= 0f || stage.height <= 0f || sourceCrop.width <= 0f || sourceCrop.height <= 0f) {
            return LensRect(0f, 0f, 0f, 0f)
        }
        val scale = minOf(stage.width / sourceCrop.width, stage.height / sourceCrop.height)
        val width = sourceCrop.width * scale
        val height = sourceCrop.height * scale
        val left = (stage.width - width) / 2f
        val top = (stage.height - height) / 2f
        return LensRect(left = left, top = top, right = left + width, bottom = top + height)
    }

    /** Maps a source-space rectangle into the fitted [frameDestination]. */
    fun mapIntoFrame(
        source: LensRect,
        frameSource: LensRect,
        frameDestination: LensRect,
    ): LensRect {
        if (frameSource.width <= 0f || frameSource.height <= 0f) {
            return LensRect(0f, 0f, 0f, 0f)
        }
        val scaleX = frameDestination.width / frameSource.width
        val scaleY = frameDestination.height / frameSource.height
        return LensRect(
            left = frameDestination.left + (source.left - frameSource.left) * scaleX,
            top = frameDestination.top + (source.top - frameSource.top) * scaleY,
            right = frameDestination.left + (source.right - frameSource.left) * scaleX,
            bottom = frameDestination.top + (source.bottom - frameSource.top) * scaleY,
        )
    }

    fun finalFrameDestination(stage: LensStage): LensRect = frameDestination(stage, finalFrameCrop)

    /**
     * Maps the centered, inset 9:16 phone viewfinder into the final lens
     * stage. The width guard keeps its rounded card safely inside unusually
     * narrow layouts while preserving the requested portrait aspect ratio.
     */
    fun cameraPreviewBounds(stage: LensStage): LensRect {
        val frame = finalFrameDestination(stage)
        val aperture = mapIntoFrame(opening, finalFrameCrop, frame)
        if (aperture.width <= 0f || aperture.height <= 0f) return LensRect(0f, 0f, 0f, 0f)

        val height = minOf(
            aperture.height * CameraPreviewOpeningHeightFraction,
            aperture.width * CameraPreviewOpeningWidthFraction / CameraPreviewAspectRatio,
        )
        val width = height * CameraPreviewAspectRatio
        val left = aperture.left + (aperture.width - width) / 2f
        val top = aperture.top + (aperture.height - height) / 2f
        return LensRect(left = left, top = top, right = left + width, bottom = top + height)
    }

    fun rendererBounds(stage: LensStage): LensRect {
        val mapped = mapIntoFrame(
            source = rendererContentViewport,
            frameSource = finalFrameCrop,
            frameDestination = finalFrameDestination(stage),
        )
        val lift = mapped.height * RendererContentLiftFraction
        return mapped.copy(top = mapped.top - lift, bottom = mapped.bottom - lift)
    }

    private fun interpolate(start: Float, end: Float, fraction: Float): Float =
        start + (end - start) * fraction
}

internal data class LensStage(
    val width: Float,
    val height: Float,
)

/** A source-space or stage-space rectangle with exclusive right/bottom edges. */
internal data class LensRect(
    val left: Float,
    val top: Float,
    val right: Float,
    val bottom: Float,
) {
    val width: Float get() = right - left
    val height: Float get() = bottom - top

    fun contains(other: LensRect, epsilon: Float = 0f): Boolean =
        other.left >= left - epsilon &&
            other.top >= top - epsilon &&
            other.right <= right + epsilon &&
            other.bottom <= bottom + epsilon
}
