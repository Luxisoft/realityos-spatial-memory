package com.luxisoft.realityos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RayBanLensGeometryTest {
    @Test
    fun stage_is_empty_for_pre_layout_zero_constraints() {
        assertEquals(LensStage(0f, 0f), RayBanLensGeometry.stageFor(0f, 720f))
        assertEquals(LensStage(0f, 0f), RayBanLensGeometry.stageFor(360f, 0f))
    }

    @Test
    fun stage_uses_the_largest_full_frame_presentation_that_fits_each_available_size() {
        val portrait = RayBanLensGeometry.stageFor(360f, 720f)
        val landscape = RayBanLensGeometry.stageFor(720f, 360f)
        val square = RayBanLensGeometry.stageFor(600f, 600f)

        assertEquals(360f, portrait.width, 0.001f)
        assertEquals(360f / RayBanLensGeometry.frameStageAspectRatio, portrait.height, 0.001f)
        assertEquals(360f * RayBanLensGeometry.frameStageAspectRatio, landscape.width, 0.001f)
        assertEquals(360f, landscape.height, 0.001f)
        assertEquals(600f, square.width, 0.001f)
        assertEquals(600f / RayBanLensGeometry.frameStageAspectRatio, square.height, 0.001f)

        listOf(portrait, landscape, square).forEach { stage ->
            assertEquals(RayBanLensGeometry.frameStageAspectRatio, stage.width / stage.height, 0.001f)
        }
    }

    @Test
    fun source_crop_has_exact_full_frame_and_complete_rim_endpoints() {
        assertEquals(RayBanLensGeometry.fullArtboard, RayBanLensGeometry.sourceCrop(0f))
        assertEquals(RayBanLensGeometry.fullArtboard, RayBanLensGeometry.sourceCrop(-1f))
        assertEquals(RayBanLensGeometry.finalFrameCrop, RayBanLensGeometry.sourceCrop(1f))
        assertEquals(RayBanLensGeometry.finalFrameCrop, RayBanLensGeometry.sourceCrop(2f))
        assertEquals(0f, RayBanLensGeometry.finalFrameCrop.top, 0f)
    }

    @Test
    fun source_crop_shrinks_monotonically_without_leaving_the_original_artboard() {
        val early = RayBanLensGeometry.sourceCrop(0.25f)
        val middle = RayBanLensGeometry.sourceCrop(0.5f)
        val late = RayBanLensGeometry.sourceCrop(0.75f)

        assertTrue(RayBanLensGeometry.fullArtboard.contains(early))
        assertTrue(early.contains(middle))
        assertTrue(middle.contains(late))
        assertTrue(late.contains(RayBanLensGeometry.finalFrameCrop))
        assertTrue(early.width > middle.width)
        assertTrue(middle.width > late.width)
        // The corrected final crop preserves the complete source height so
        // the upper rim is never sliced; this entrance zoom is horizontal.
        assertEquals(RayBanLensGeometry.fullArtboard.height, early.height, 0.001f)
        assertEquals(early.height, middle.height, 0.001f)
        assertEquals(middle.height, late.height, 0.001f)
    }

    @Test
    fun final_frame_is_fitted_with_vertical_reveal_instead_of_being_edge_clipped() {
        val stage = RayBanLensGeometry.stageFor(720f, 900f)
        val destination = RayBanLensGeometry.finalFrameDestination(stage)

        assertEquals(720f, stage.width, 0.001f)
        assertEquals(0f, destination.left, 0.001f)
        assertEquals(stage.width, destination.right, 0.001f)
        assertEquals(24f, destination.top, 0.001f)
        assertEquals(stage.height - 24f, destination.bottom, 0.001f)
        assertTrue(stage.height > destination.height)
    }

    @Test
    fun renderer_content_viewport_is_thirty_percent_larger_and_lifted_clear_of_the_lower_rim() {
        val stage = RayBanLensGeometry.stageFor(720f, 900f)
        val frame = RayBanLensGeometry.finalFrameDestination(stage)
        val renderer = RayBanLensGeometry.rendererBounds(stage)
        val mappedBeforeLift = RayBanLensGeometry.mapIntoFrame(
            source = RayBanLensGeometry.rendererContentViewport,
            frameSource = RayBanLensGeometry.finalFrameCrop,
            frameDestination = frame,
        )
        val visibleStage = LensRect(0f, 0f, stage.width, stage.height)
        val safe = RayBanLensGeometry.rendererSafeViewport
        val content = RayBanLensGeometry.rendererContentViewport

        assertTrue(RayBanLensGeometry.finalFrameCrop.contains(content))
        assertTrue(RayBanLensGeometry.opening.contains(content))
        assertTrue(content.contains(safe))
        assertEquals(1.30f, content.width / safe.width, 0.001f)
        assertEquals(1.30f, content.height / safe.height, 0.001f)
        assertEquals(RayBanLensGeometry.opening.top, content.top, 0.001f)
        assertEquals(49f, safe.top - content.top, 0.001f)
        assertEquals(0.108_888_89f, (safe.top - content.top) / safe.height, 0.001f)
        assertEquals(0.15f, RayBanLensGeometry.RendererContentLiftFraction, 0f)
        assertEquals(
            mappedBeforeLift.height * RayBanLensGeometry.RendererContentLiftFraction,
            mappedBeforeLift.top - renderer.top,
            0.001f,
        )
        assertTrue(frame.contains(renderer, epsilon = 0.001f))
        assertTrue(visibleStage.contains(renderer, epsilon = 0.001f))
        assertEquals(150f, renderer.left, 0.001f)
        assertEquals(83.4375f, renderer.top, 0.001f)
        assertEquals(438.75f, renderer.width, 0.001f)
        assertEquals(438.75f, renderer.height, 0.001f)
        assertEquals(522.1875f, renderer.bottom, 0.001f)
    }

    @Test
    fun camera_preview_is_a_centered_inset_portrait_viewfinder() {
        val stage = RayBanLensGeometry.stageFor(720f, 900f)
        val frame = RayBanLensGeometry.finalFrameDestination(stage)
        val opening = RayBanLensGeometry.mapIntoFrame(
            source = RayBanLensGeometry.opening,
            frameSource = RayBanLensGeometry.finalFrameCrop,
            frameDestination = frame,
        )
        val preview = RayBanLensGeometry.cameraPreviewBounds(stage)

        assertTrue(opening.contains(preview, epsilon = 0.001f))
        assertEquals(
            RayBanLensGeometry.CameraPreviewAspectRatio,
            preview.width / preview.height,
            0.001f,
        )
        assertEquals(opening.left + opening.width / 2f, preview.left + preview.width / 2f, 0.001f)
        assertEquals(opening.top + opening.height / 2f, preview.top + preview.height / 2f, 0.001f)
        assertTrue(preview.left > opening.left)
        assertTrue(preview.top > opening.top)
        assertTrue(preview.right < opening.right)
        assertTrue(preview.bottom < opening.bottom)
        assertEquals(
            opening.height * RayBanLensGeometry.CameraPreviewOpeningHeightFraction,
            preview.height,
            0.001f,
        )
    }
}
