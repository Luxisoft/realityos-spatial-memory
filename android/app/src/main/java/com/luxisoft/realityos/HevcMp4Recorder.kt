package com.luxisoft.realityos

import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import com.meta.wearable.dat.camera.types.AudioFrame
import com.meta.wearable.dat.camera.types.VideoFrame
import java.io.File
import java.nio.ByteBuffer

/**
 * Writes a short, explicit HEVC + AAC MP4 from the compressed video and PCM
 * streams supplied by DAT. A clip is rejected when either track is absent so
 * evidence video never silently loses its audio.
 */
class HevcMp4Recorder(cacheDir: File) {
    private val recordingsDir = File(cacheDir, "realityos-recordings")
    private val parameterSets = linkedMapOf<Int, ByteArray>()
    private val pendingSamples = ArrayDeque<PendingSample>()

    private var muxer: MediaMuxer? = null
    private var output: File? = null
    private var videoTrackIndex = -1
    private var audioTrackIndex = -1
    private var muxerStarted = false
    private var firstPtsUs = -1L
    private var lastVideoPtsUs = -1L
    private var lastAudioPtsUs = -1L
    private var lastAudioInputPtsUs = 0L
    private var wroteVideoFrame = false
    private var wroteAudioFrame = false

    private var audioEncoder: MediaCodec? = null
    private var audioEncoderStarted = false
    private var audioInputClosed = false

    @Synchronized
    fun begin(): File {
        close(deleteIncomplete = true)
        recordingsDir.mkdirs()
        output = File.createTempFile("realityos-", ".mp4", recordingsDir)
        muxer = MediaMuxer(output!!.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        resetClipState()
        audioEncoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_AAC).also { encoder ->
            val format = MediaFormat.createAudioFormat(
                MediaFormat.MIMETYPE_AUDIO_AAC,
                AUDIO_SAMPLE_RATE,
                AUDIO_CHANNEL_COUNT,
            ).apply {
                setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
                setInteger(MediaFormat.KEY_BIT_RATE, AUDIO_BIT_RATE)
                setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, AUDIO_MAX_INPUT_BYTES)
            }
            encoder.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            encoder.start()
            audioEncoderStarted = true
        }
        return output!!
    }

    /** Returns true when this compressed HEVC frame was accepted. */
    @Synchronized
    fun append(frame: VideoFrame): Boolean {
        if (!frame.isCompressed) return false
        val bytes = frame.buffer.copyRemaining()
        if (bytes.isEmpty()) return false
        collectParameterSets(bytes)
        // DAT emits codec configuration separately from playable samples.
        // Keep its VPS/SPS/PPS, but never put it in the MP4 timeline.
        if (frame.isCodecConfig) return true
        val activeMuxer = muxer ?: return false
        if (videoTrackIndex == -1) {
            val csd = completeCsd() ?: return false
            // A clip that begins on an inter frame can be accepted by the
            // muxer but cannot be decoded reliably. Wait for a real HEVC
            // random-access point instead of forcing an invalid start.
            if (!isHevcRandomAccessPoint(bytes)) return false
            val format = MediaFormat.createVideoFormat(
                MediaFormat.MIMETYPE_VIDEO_HEVC,
                frame.width,
                frame.height,
            ).apply { setByteBuffer("csd-0", ByteBuffer.wrap(csd)) }
            videoTrackIndex = activeMuxer.addTrack(format)
            tryStartMuxer()
        }
        writeOrQueue(
            PendingSample(
                Track.VIDEO,
                bytes,
                frame.presentationTimeUs,
                if (isHevcRandomAccessPoint(bytes)) MediaCodec.BUFFER_FLAG_KEY_FRAME else 0,
            ),
        )
        return true
    }

    /** Encodes a 44.1 kHz mono 16-bit PCM AudioFrame as AAC. */
    @Synchronized
    fun appendAudio(frame: AudioFrame): Boolean {
        val encoder = audioEncoder ?: return false
        if (audioInputClosed) return false
        val source = frame.buffer.duplicate()
        var presentationTimeUs = frame.presentationTimeUs
        var wroteInput = false
        while (source.hasRemaining()) {
            val inputIndex = encoder.dequeueInputBuffer(CODEC_TIMEOUT_US)
            if (inputIndex < 0) break
            val input = encoder.getInputBuffer(inputIndex) ?: break
            input.clear()
            val size = minOf(input.remaining(), source.remaining())
            val chunk = ByteArray(size)
            source.get(chunk)
            input.put(chunk)
            encoder.queueInputBuffer(inputIndex, 0, size, presentationTimeUs, 0)
            wroteInput = true
            lastAudioInputPtsUs = presentationTimeUs
            presentationTimeUs += size.toLong() * MICROS_PER_SECOND / AUDIO_BYTES_PER_SECOND
        }
        drainAudioEncoder(untilEndOfStream = false)
        return wroteInput
    }

    @Synchronized
    fun finish(): File? {
        signalAudioEndOfStream()
        val completed = output?.takeIf { wroteVideoFrame && wroteAudioFrame && muxerStarted }
        val muxerStopped = close(deleteIncomplete = completed == null)
        return completed?.takeIf { muxerStopped }
    }

    @Synchronized
    fun close(deleteIncomplete: Boolean): Boolean {
        releaseAudioEncoder()
        val activeMuxer = muxer
        val muxerStopped = !muxerStarted ||
            (activeMuxer != null && runCatching { activeMuxer.stop() }.isSuccess)
        runCatching { muxer?.release() }
        muxer = null
        val file = output
        output = null
        if (deleteIncomplete || !muxerStopped) file?.delete()
        resetClipState()
        return muxerStopped
    }

    /** Retain HEVC parameter sets while streaming so recording can start mid-stream. */
    @Synchronized
    fun observe(frame: VideoFrame) {
        if (!frame.isCompressed) return
        val bytes = frame.buffer.copyRemaining()
        if (bytes.isNotEmpty()) collectParameterSets(bytes)
    }

    @Synchronized
    fun clearCodecConfiguration() {
        parameterSets.clear()
    }

    private fun signalAudioEndOfStream() {
        val encoder = audioEncoder ?: return
        if (audioInputClosed) return
        repeat(MAX_EOS_INPUT_ATTEMPTS) {
            val inputIndex = encoder.dequeueInputBuffer(CODEC_TIMEOUT_US)
            if (inputIndex >= 0) {
                encoder.queueInputBuffer(
                    inputIndex,
                    0,
                    0,
                    lastAudioInputPtsUs + 1,
                    MediaCodec.BUFFER_FLAG_END_OF_STREAM,
                )
                audioInputClosed = true
                drainAudioEncoder(untilEndOfStream = true)
                return
            }
        }
    }

    private fun drainAudioEncoder(untilEndOfStream: Boolean) {
        val encoder = audioEncoder ?: return
        val info = MediaCodec.BufferInfo()
        var keepDraining = true
        var emptyPolls = 0
        while (keepDraining) {
            when (val outputIndex = encoder.dequeueOutputBuffer(info, CODEC_TIMEOUT_US)) {
                MediaCodec.INFO_TRY_AGAIN_LATER -> {
                    emptyPolls += 1
                    keepDraining = untilEndOfStream && emptyPolls < MAX_EMPTY_OUTPUT_POLLS
                }
                MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                    emptyPolls = 0
                    if (audioTrackIndex == -1) {
                        audioTrackIndex = muxer?.addTrack(encoder.outputFormat) ?: -1
                        tryStartMuxer()
                    }
                }
                else -> if (outputIndex >= 0) {
                    emptyPolls = 0
                    val outputBuffer = encoder.getOutputBuffer(outputIndex)
                    if (outputBuffer != null && info.size > 0 &&
                        info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG == 0
                    ) {
                        val payload = outputBuffer.copyRange(info.offset, info.size)
                        writeOrQueue(PendingSample(Track.AUDIO, payload, info.presentationTimeUs, info.flags))
                    }
                    val endOfStream = info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                    encoder.releaseOutputBuffer(outputIndex, false)
                    if (endOfStream) keepDraining = false
                }
            }
        }
    }

    private fun tryStartMuxer() {
        if (muxerStarted || videoTrackIndex < 0 || audioTrackIndex < 0) return
        val activeMuxer = muxer ?: return
        activeMuxer.start()
        muxerStarted = true
        pendingSamples.sortedBy { it.presentationTimeUs }.forEach(::writeSample)
        pendingSamples.clear()
    }

    private fun writeOrQueue(sample: PendingSample) {
        if (muxerStarted) {
            writeSample(sample)
        } else {
            if (pendingSamples.size == MAX_PENDING_SAMPLES) pendingSamples.removeFirst()
            pendingSamples.addLast(sample)
        }
    }

    private fun writeSample(sample: PendingSample) {
        val activeMuxer = muxer ?: return
        val track = when (sample.track) {
            Track.VIDEO -> videoTrackIndex
            Track.AUDIO -> audioTrackIndex
        }
        if (track < 0) return
        if (firstPtsUs < 0L) firstPtsUs = sample.presentationTimeUs
        val basePts = (sample.presentationTimeUs - firstPtsUs).coerceAtLeast(0L)
        val adjustedPts = when (sample.track) {
            Track.VIDEO -> {
                val next = if (lastVideoPtsUs < 0L) basePts else maxOf(basePts, lastVideoPtsUs + MIN_VIDEO_FRAME_GAP_US)
                lastVideoPtsUs = next
                next
            }
            Track.AUDIO -> {
                val next = if (lastAudioPtsUs < 0L) basePts else maxOf(basePts, lastAudioPtsUs + 1L)
                lastAudioPtsUs = next
                next
            }
        }
        val info = MediaCodec.BufferInfo().apply { set(0, sample.data.size, adjustedPts, sample.flags) }
        runCatching {
            activeMuxer.writeSampleData(track, ByteBuffer.wrap(sample.data), info)
            if (sample.track == Track.VIDEO) wroteVideoFrame = true else wroteAudioFrame = true
        }
    }

    private fun releaseAudioEncoder() {
        val encoder = audioEncoder
        if (encoder != null) {
            runCatching { if (audioEncoderStarted) encoder.stop() }
            runCatching { encoder.release() }
        }
        audioEncoder = null
        audioEncoderStarted = false
        audioInputClosed = false
    }

    private fun resetClipState() {
        pendingSamples.clear()
        videoTrackIndex = -1
        audioTrackIndex = -1
        muxerStarted = false
        firstPtsUs = -1L
        lastVideoPtsUs = -1L
        lastAudioPtsUs = -1L
        lastAudioInputPtsUs = 0L
        wroteVideoFrame = false
        wroteAudioFrame = false
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

    private fun ByteBuffer.copyRange(offset: Int, size: Int): ByteArray {
        val duplicate = duplicate()
        duplicate.position(offset)
        duplicate.limit(offset + size)
        return ByteArray(size).also(duplicate::get)
    }

    private enum class Track { VIDEO, AUDIO }

    private data class PendingSample(
        val track: Track,
        val data: ByteArray,
        val presentationTimeUs: Long,
        val flags: Int,
    )

    private companion object {
        const val VPS = 32
        const val SPS = 33
        const val PPS = 34
        const val MAX_PENDING_SAMPLES = 240
        const val MIN_VIDEO_FRAME_GAP_US = 33_333L
        const val CODEC_TIMEOUT_US = 10_000L
        // AAC encoders can retain a small tail after EOS. Give the muxer up to
        // one second off the UI thread before deciding that no audible track
        // was produced.
        const val MAX_EOS_INPUT_ATTEMPTS = 100
        const val MAX_EMPTY_OUTPUT_POLLS = 100
        const val MICROS_PER_SECOND = 1_000_000L
        const val AUDIO_SAMPLE_RATE = 44_100
        const val AUDIO_CHANNEL_COUNT = 1
        const val AUDIO_BIT_RATE = 64_000
        const val AUDIO_MAX_INPUT_BYTES = 16_384
        const val AUDIO_BYTES_PER_SECOND = AUDIO_SAMPLE_RATE * AUDIO_CHANNEL_COUNT * 2L
        val PARAMETER_SET_TYPES = setOf(VPS, SPS, PPS)
    }
}
