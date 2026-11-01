package com.luxisoft.realityos

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream

/** Rotation plus optional mirrors needed to display EXIF orientation upright. */
internal data class ExifTransform(val degrees: Float, val flipH: Boolean, val flipV: Boolean)

/**
 * Pure EXIF orientation mapping (constants mirror android.media.ExifInterface
 * so this stays runnable in local unit tests): 1 normal, 2 flip-H, 3 rot-180,
 * 4 flip-V, 5 transpose, 6 rot-90, 7 transverse, 8 rot-270.
 */
internal fun exifTransform(orientation: Int): ExifTransform = when (orientation) {
    6 -> ExifTransform(90f, false, false)
    3 -> ExifTransform(180f, false, false)
    8 -> ExifTransform(270f, false, false)
    2 -> ExifTransform(0f, true, false)
    4 -> ExifTransform(0f, false, true)
    5 -> ExifTransform(90f, true, false)
    7 -> ExifTransform(270f, true, false)
    else -> ExifTransform(0f, false, false)
}

/**
 * Decode phone bytes honoring EXIF orientation and re-encode an upright JPEG
 * bounded to [maxSide]. Null when the bytes are not a decodable image, so the
 * caller can keep the original bytes and mime type untouched.
 */
internal fun uprightImageBytes(raw: ByteArray, maxSide: Int = 1600, quality: Int = 90): ByteArray? {
    return try {
        val orientation = try {
            android.media.ExifInterface(ByteArrayInputStream(raw)).getAttributeInt(
                android.media.ExifInterface.TAG_ORIENTATION,
                android.media.ExifInterface.ORIENTATION_NORMAL
            )
        } catch (_: Exception) {
            android.media.ExifInterface.ORIENTATION_NORMAL
        }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(raw, 0, raw.size, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null
        var sample = 1
        while ((bounds.outWidth / sample) > maxSide || (bounds.outHeight / sample) > maxSide) sample *= 2
        val decoded = BitmapFactory.decodeByteArray(raw, 0, raw.size, BitmapFactory.Options().apply { inSampleSize = sample })
            ?: return null
        val scaled = if (decoded.width > maxSide || decoded.height > maxSide) {
            val factor = maxSide.toFloat() / maxOf(decoded.width, decoded.height)
            Bitmap.createScaledBitmap(decoded, (decoded.width * factor).toInt(), (decoded.height * factor).toInt(), true)
        } else {
            decoded
        }
        val transform = exifTransform(orientation)
        val matrix = Matrix()
        if (transform.degrees != 0f) matrix.postRotate(transform.degrees)
        if (transform.flipH || transform.flipV) {
            matrix.postScale(if (transform.flipH) -1f else 1f, if (transform.flipV) -1f else 1f)
        }
        val upright = if (matrix.isIdentity) {
            scaled
        } else {
            Bitmap.createBitmap(scaled, 0, 0, scaled.width, scaled.height, matrix, true)
        }
        val stream = ByteArrayOutputStream()
        upright.compress(Bitmap.CompressFormat.JPEG, quality, stream)
        stream.toByteArray()
    } catch (_: Exception) {
        null
    }
}
