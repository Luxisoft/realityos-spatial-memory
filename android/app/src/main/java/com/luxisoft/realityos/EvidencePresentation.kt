package com.luxisoft.realityos

import java.text.NumberFormat
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale

internal fun evidenceIdentity(item: GalleryThumb): String = item.evidenceId.ifBlank { item.mediaId.ifBlank { item.viewerUrl } }

internal fun visualConfidence(value: Double?): Double? = value?.takeIf { it.isFinite() && it in 0.0..1.0 }

internal fun orderedEvidence(items: List<GalleryThumb>): List<GalleryThumb> = items.sortedWith(
    compareByDescending<GalleryThumb> { visualConfidence(it.confidence) ?: -1.0 }
        .thenBy {
            when (it.matchKind) {
                "exact" -> 0
                "family" -> 1
                "similar" -> 2
                else -> 3
            }
        }
        .thenBy { if (it.localizationQuality == "sam") 0 else 1 }
        .thenByDescending { it.publishedAt }
)

internal fun evidencePercent(value: Double?, language: String): String? = visualConfidence(value)?.let {
    NumberFormat.getPercentInstance(Locale.forLanguageTag(language)).apply { maximumFractionDigits = 0 }.format(it)
}

internal fun evidenceDate(raw: String, language: String, zone: ZoneId = ZoneId.systemDefault()): String? {
    val date = runCatching { OffsetDateTime.parse(raw).atZoneSameInstant(zone).toLocalDate() }.getOrElse {
        runCatching { LocalDate.parse(raw.substringBefore('T')) }.getOrNull()
    } ?: return null
    return date.format(DateTimeFormatter.ofLocalizedDate(FormatStyle.MEDIUM).withLocale(Locale.forLanguageTag(language)))
}

/** Event times retain their clock time while using the app language and viewer time zone. */
internal fun presentationDateTime(raw: String, language: String = LocalizedText.languageTag, zone: ZoneId = ZoneId.systemDefault()): String = runCatching {
    OffsetDateTime.parse(raw).atZoneSameInstant(zone)
        .format(DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM, FormatStyle.SHORT).withLocale(Locale.forLanguageTag(language)))
}.getOrElse { evidenceDate(raw, language, zone) ?: raw }
