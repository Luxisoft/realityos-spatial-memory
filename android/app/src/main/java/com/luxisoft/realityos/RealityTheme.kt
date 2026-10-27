package com.luxisoft.realityos

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val RealityInk = Color(0xFF0B1220)
private val RealitySurface = Color(0xFF142033)
private val RealitySurfaceRaised = Color(0xFF1C2D45)
private val RealitySignal = Color(0xFF63E6BE)
private val RealitySignalInk = Color(0xFF062119)
private val RealityAttention = Color(0xFFF6BB5D)
private val RealityPaper = Color(0xFFF5F7FB)
private val RealityMuted = Color(0xFFC6D1E0)
private val RealityError = Color(0xFFFFB4AB)

private val RealityColorScheme = darkColorScheme(
    primary = RealitySignal,
    onPrimary = RealitySignalInk,
    primaryContainer = Color(0xFF124C40),
    onPrimaryContainer = Color(0xFFB9FFE8),
    secondary = RealityAttention,
    onSecondary = Color(0xFF2A1800),
    secondaryContainer = Color(0xFF573E12),
    onSecondaryContainer = Color(0xFFFFDEA7),
    background = RealityInk,
    onBackground = RealityPaper,
    surface = RealitySurface,
    onSurface = RealityPaper,
    surfaceVariant = RealitySurfaceRaised,
    onSurfaceVariant = RealityMuted,
    error = RealityError,
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    outline = Color(0xFF8E9CAF),
)

private val RealityTypography = Typography(
    headlineSmall = TextStyle(fontWeight = FontWeight.SemiBold, letterSpacing = (-0.3).sp),
    titleLarge = TextStyle(fontWeight = FontWeight.SemiBold),
    titleMedium = TextStyle(fontWeight = FontWeight.SemiBold),
    labelLarge = TextStyle(fontWeight = FontWeight.SemiBold, letterSpacing = 0.15.sp),
)

@Composable
fun RealityOsTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = RealityColorScheme,
        typography = RealityTypography,
        content = content,
    )
}
