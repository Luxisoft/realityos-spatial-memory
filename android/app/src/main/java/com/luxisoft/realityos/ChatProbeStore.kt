package com.luxisoft.realityos

import android.content.Context
import java.io.File

/** Local-only probe photos: search probes stay ephemeral server-side by design. */
internal const val CHAT_PROBE_KEEP = 50

internal fun chatProbeDir(context: Context): File = File(context.filesDir, "chat_probes")

internal fun chatProbeFile(context: Context, serverId: Int): File =
    File(chatProbeDir(context), "probe-$serverId.jpg")

/** Oldest-first victims beyond the newest [keep] files. Pure over file metadata. */
internal fun pruneProbeFiles(files: List<File>, keep: Int): List<File> =
    if (files.size <= keep) emptyList() else files.sortedBy { it.lastModified() }.dropLast(keep)

internal fun saveChatProbe(context: Context, serverId: Int, bytes: ByteArray) {
    try {
        val dir = chatProbeDir(context).apply { mkdirs() }
        chatProbeFile(context, serverId).writeBytes(bytes)
        pruneProbeFiles(dir.listFiles()?.toList().orEmpty(), CHAT_PROBE_KEEP).forEach {
            runCatching { it.delete() }
        }
    } catch (_: Exception) {
    }
}

internal fun loadChatProbe(context: Context, serverId: Int): ByteArray? {
    return try {
        chatProbeFile(context, serverId).takeIf { it.exists() }?.readBytes()
    } catch (_: Exception) {
        null
    }
}
