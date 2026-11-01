package com.luxisoft.realityos.chat

import android.content.Context
import android.media.MediaPlayer
import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.luxisoft.realityos.SocialSession
import com.luxisoft.realityos.authorizedMediaUrl

/** Owns chat playback resources; the composing host releases them on disposal. */
internal class ChatAudioPlayback(private val context: Context) {
    private var audioPlayer by mutableStateOf<MediaPlayer?>(null)
    var playingId by mutableStateOf<Long?>(null)

    fun stopAudio() {
        try {
            audioPlayer?.stop()
            audioPlayer?.release()
        } catch (_: Exception) {
        }
        audioPlayer = null
        playingId = null
    }

    private fun startPlayer(player: android.media.MediaPlayer, onNext: () -> Unit) {
        player.setOnCompletionListener {
            try {
                player.release()
            } catch (_: Exception) { }
            if (audioPlayer === player) audioPlayer = null
            onNext()
        }
        player.setOnErrorListener { _, _, _ ->
            try {
                player.release()
            } catch (_: Exception) { }
            stopAudio()
            true
        }
        player.setOnPreparedListener { it.start() }
        audioPlayer = player
        try {
            player.prepareAsync()
        } catch (_: Exception) {
            stopAudio()
        }
    }

    fun playAudioSequence(paths: List<String>, index: Int) {
        if (index >= paths.size) {
            stopAudio()
            return
        }
        try {
            MediaPlayer().apply {
                setDataSource(paths[index])
                startPlayer(this) { playAudioSequence(paths, index + 1) }
            }
        } catch (_: Exception) {
            stopAudio()
        }
    }

    fun playUrlSequence(urls: List<String>, index: Int) {
        if (index >= urls.size) {
            stopAudio()
            return
        }
        try {
            MediaPlayer().apply {
                setDataSource(
                    context,
                    Uri.parse(authorizedMediaUrl(urls[index])),
                    mapOf("Authorization" to "Bearer ${SocialSession.token}")
                )
                startPlayer(this) { playUrlSequence(urls, index + 1) }
            }
        } catch (_: Exception) {
            stopAudio()
        }
    }
}
