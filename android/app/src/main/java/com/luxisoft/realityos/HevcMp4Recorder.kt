package com.luxisoft.realityos

import android.media.MediaCodec
import android.media.MediaFormat
import android.media.MediaMuxer
import com.meta.wearable.dat.camera.types.VideoFrame
import java.io.File
import java.nio.ByteBuffer

/**
 * Writes compressed HEVC frames received from DAT to a bounded MP4 clip.
 *
 * DAT owns camera transport; this class only persists an active, explicit
 * recording. It never starts the camera and it writes no frame while inactive.
 */
class HevcMp4Recorder(cacheDir: File) {
    private val recordingsDir = File(cacheDir, "realityos-recordings")
    private val parameterSets = linkedMapOf<Int, ByteArray>()
    private var muxer: MediaMuxer? = null
    private var output: File? = null
    private var trackIndex = -1
    private var firstPtsUs = -1L
    private var lastPtsUs = -1L
    private var framesBeforeStart = 0
    private var started = false
    private var wroteFrame = false

    fun begin(): File {
        close(deleteIncomplete = true)
        recordingsDir.mkdirs()
        output = File.createTempFile("realityos-", ".mp4", recordingsDir)
        muxer = MediaMuxer(output!!.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        trackIndex = -1
        firstPtsUs = -1L
        lastPtsUs = -1L
        framesBeforeStart = 0
        started = false
        wroteFrame = false
        return output!!
    }

    /** Returns true when this frame was accepted into the MP4 file. */
    fun append(frame: VideoFrame): Boolean {
        if (!frame.isCompressed) return false
        val bytes = frame.buffer.copyRemaining()
        if (bytes.isEmpty()) return false
        collectParameterSets(bytes)
        val activeMuxer = muxer ?: return false
        if (!started) {
            val csd = completeCsd() ?: return false
            framesBeforeStart += 1
            val keyFrame = isHevcRandomAccessPoint(bytes)
            if (!keyFrame && framesBeforeStart < MAX_FRAMES_WAITING_FOR_SYNC) return false
            val format = MediaFormat.createVideoFormat(
                MediaFormat.MIMETYPE_VIDEO_HEVC,
                frame.width,
                frame.height,
            ).apply { setByteBuffer("csd-0", ByteBuffer.wrap(csd)) }
            trackIndex = activeMuxer.addTrack(format)
            activeMuxer.start()
            started = true
            firstPtsUs = frame.presentationTimeUs
        }
        val basePts = (frame.presentationTimeUs - firstPtsUs).coerceAtLeast(0L)
        val adjustedPts = if (lastPtsUs < 0L) basePts else maxOf(basePts, lastPtsUs + MIN_FRAME_GAP_US)
        val flags = if (!wroteFrame || isHevcRandomAccessPoint(bytes)) MediaCodec.BUFFER_FLAG_KEY_FRAME else 0
        val info = MediaCodec.BufferInfo().apply { set(0, bytes.size, adjustedPts, flags) }
        return runCatching {
            activeMuxer.writeSampleData(trackIndex, ByteBuffer.wrap(bytes), info)
            lastPtsUs = adjustedPts
            wroteFrame = true
            true
        }.getOrDefault(false)
    }

    fun finish(): File? {
        val completed = output?.takeIf { wroteFrame && started }
        close(deleteIncomplete = completed == null)
        return completed
    }

    fun close(deleteIncomplete: Boolean) {
        runCatching { if (started) muxer?.stop() }
        runCatching { muxer?.release() }
        muxer = null
        val file = output
        output = null
        if (deleteIncomplete) file?.delete()
        started = false
        wroteFrame = false
        trackIndex = -1
        firstPtsUs = -1L
        lastPtsUs = -1L
    }

    /** Retain codec parameter sets while streaming so a later recording can start mid-stream. */
    fun observe(frame: VideoFrame) {
        if (!frame.isCompressed) return
        val bytes = frame.buffer.copyRemaining()
        if (bytes.isNotEmpty()) collectParameterSets(bytes)
    }

    fun clearCodecConfiguration() {
        parameterSets.clear()
    }

    private fun collectParameterSets(data: ByteArray) {
        eachNalUnit(data) { start, type, end ->
            if (type in PARAMETER_SET_TYPES) parameterSets[type] = data.copyOfRange(start, end)
        }
    }

    private fun completeCsd(): ByteArray? {
        val vps = parameterSets[VPS] ?: return null
        val sps = parameterSets[SPS] ?: return null
        val pps = parameterSets[PPS] ?: return null
        return vps + sps + pps
    }

    private fun isHevcRandomAccessPoint(data: ByteArray): Boolean {
        var key = false
        eachNalUnit(data) { _, type, _ -> if (type in 16..21) key = true }
        return key
    }

    private fun eachNalUnit(data: ByteArray, action: (Int, Int, Int) -> Unit) {
        val starts = mutableListOf<Pair<Int, Int>>()
        var index = 0
        while (index < data.size - 4) {
            val startCodeLength = when {
                data[index] == 0.toByte() && data[index + 1] == 0.toByte() && data[index + 2] == 1.toByte() -> 3
                data[index] == 0.toByte() && data[index + 1] == 0.toByte() && data[index + 2] == 0.toByte() && data[index + 3] == 1.toByte() -> 4
                else -> 0
            }
            if (startCodeLength == 0) {
                index += 1
                continue
            }
            val header = index + startCodeLength
            if (header < data.size && !hasStartCode(data, header)) {
                starts += index to ((data[header].toInt() and 0x7E) shr 1)
            }
            index = header
        }
        starts.forEachIndexed { position, (start, type) ->
            action(start, type, starts.getOrNull(position + 1)?.first ?: data.size)
        }
    }

    private fun hasStartCode(data: ByteArray, offset: Int): Boolean =
        offset + 2 < data.size && data[offset] == 0.toByte() && data[offset + 1] == 0.toByte() &&
            (data[offset + 2] == 1.toByte() || (offset + 3 < data.size && data[offset + 2] == 0.toByte() && data[offset + 3] == 1.toByte()))

    private fun ByteBuffer.copyRemaining(): ByteArray {
        val duplicate = duplicate()
        return ByteArray(duplicate.remaining()).also(duplicate::get)
    }

    private companion object {
        const val VPS = 32
        const val SPS = 33
        const val PPS = 34
        const val MAX_FRAMES_WAITING_FOR_SYNC = 60
        const val MIN_FRAME_GAP_US = 33_333L
        val PARAMETER_SET_TYPES = setOf(VPS, SPS, PPS)
    }
}
