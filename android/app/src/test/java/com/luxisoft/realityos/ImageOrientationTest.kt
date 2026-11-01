package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Test

class ImageOrientationTest {
    @Test
    fun `normal and unknown orientations keep identity`() {
        assertEquals(ExifTransform(0f, false, false), exifTransform(1))
        assertEquals(ExifTransform(0f, false, false), exifTransform(0))
        assertEquals(ExifTransform(0f, false, false), exifTransform(99))
    }

    @Test
    fun `rotations map to degrees`() {
        assertEquals(ExifTransform(90f, false, false), exifTransform(6))
        assertEquals(ExifTransform(180f, false, false), exifTransform(3))
        assertEquals(ExifTransform(270f, false, false), exifTransform(8))
    }

    @Test
    fun `mirrors map to flips`() {
        assertEquals(ExifTransform(0f, true, false), exifTransform(2))
        assertEquals(ExifTransform(0f, false, true), exifTransform(4))
        assertEquals(ExifTransform(90f, true, false), exifTransform(5))
        assertEquals(ExifTransform(270f, true, false), exifTransform(7))
    }
}
