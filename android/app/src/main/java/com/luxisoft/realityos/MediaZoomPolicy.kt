package com.luxisoft.realityos

internal data class MediaZoomTransform(val scale: Float = 1f, val panX: Float = 0f, val panY: Float = 0f)

/** Pan bounds for a centered image that shrinks to fit, without initial upscaling. */
internal object MediaZoomPolicy {
    fun transform(
        current: MediaZoomTransform,
        viewportWidth: Int,
        viewportHeight: Int,
        imageWidth: Int,
        imageHeight: Int,
        centroidX: Float,
        centroidY: Float,
        movementX: Float,
        movementY: Float,
        scaleChange: Float
    ): MediaZoomTransform {
        val previous = current.takeIf { it.scale.isFinite() && it.scale in 1f..8f && it.panX.isFinite() && it.panY.isFinite() }
            ?: MediaZoomTransform()
        // calculateCentroid returns Offset.Unspecified when the last pointer lifts.
        // Even with an unchanged scale, NaN * 0 would poison the graphics layer.
        if (viewportWidth <= 0 || viewportHeight <= 0 || imageWidth <= 0 || imageHeight <= 0 ||
            !centroidX.isFinite() || !centroidY.isFinite() || !movementX.isFinite() || !movementY.isFinite() ||
            !scaleChange.isFinite() || scaleChange <= 0f
        ) {
            return previous
        }
        val scale = (previous.scale * scaleChange).coerceIn(1f, 8f)
        val ratio = scale / previous.scale
        val x = previous.panX * ratio + (centroidX - viewportWidth / 2f) * (1f - ratio) + movementX
        val y = previous.panY * ratio + (centroidY - viewportHeight / 2f) * (1f - ratio) + movementY
        if (!x.isFinite() || !y.isFinite()) return previous
        val limits = panLimits(viewportWidth, viewportHeight, imageWidth, imageHeight, scale)
        return MediaZoomTransform(scale, x.coerceIn(-limits.first, limits.first), y.coerceIn(-limits.second, limits.second))
    }

    fun panLimits(
        viewportWidth: Int,
        viewportHeight: Int,
        imageWidth: Int,
        imageHeight: Int,
        zoom: Float
    ): Pair<Float, Float> {
        if (viewportWidth <= 0 || viewportHeight <= 0 || imageWidth <= 0 || imageHeight <= 0 || !zoom.isFinite() || zoom <= 0f) return 0f to 0f
        val fit = minOf(1f, viewportWidth.toFloat() / imageWidth, viewportHeight.toFloat() / imageHeight)
        return ((imageWidth * fit * zoom - viewportWidth) / 2f).coerceAtLeast(0f) to
            ((imageHeight * fit * zoom - viewportHeight) / 2f).coerceAtLeast(0f)
    }
}
