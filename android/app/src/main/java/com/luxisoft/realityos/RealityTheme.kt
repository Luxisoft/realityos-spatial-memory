package com.luxisoft.realityos

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// The palette is a spatial field rather than a generic dark dashboard:
// deep blue-black for depth, LUXISOFT mint for active memory, and amber only
// for evidence or attention that needs a human decision.
private val OrbitInk = Color(0xFF08121F)
private val OrbitSurface = Color(0xFF101F31)
private val OrbitRaised = Color(0xFF172A40)
private val OrbitTrace = Color(0xFF203A54)
private val MemoryMint = Color(0xFF62E7BE)
private val MemoryMintInk = Color(0xFF06231B)
private val EvidenceAmber = Color(0xFFFFC56A)
private val Paper = Color(0xFFF5F8FC)
private val Mist = Color(0xFFBBC9D9)
private val ErrorRose = Color(0xFFFFB4AB)

private val RealityColorScheme = darkColorScheme(
    primary = MemoryMint,
    onPrimary = MemoryMintInk,
    primaryContainer = Color(0xFF0E4E40),
    onPrimaryContainer = Color(0xFFB9FFE8),
    secondary = EvidenceAmber,
    onSecondary = Color(0xFF2C1900),
    secondaryContainer = Color(0xFF5A4010),
    onSecondaryContainer = Color(0xFFFFDEA7),
    tertiary = Color(0xFFB9C8FF),
    onTertiary = Color(0xFF14214D),
    background = OrbitInk,
    onBackground = Paper,
    surface = OrbitSurface,
    onSurface = Paper,
    surfaceVariant = OrbitRaised,
    onSurfaceVariant = Mist,
    surfaceContainerHigh = OrbitRaised,
    surfaceContainerHighest = OrbitTrace,
    outline = Color(0xFF8297AD),
    outlineVariant = Color(0xFF30465D),
    error = ErrorRose,
    onError = Color(0xFF690005),
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
)

private val RealityTypography = Typography(
    displaySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 36.sp,
        lineHeight = 42.sp,
        letterSpacing = (-1.2).sp,
    ),
    headlineMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 27.sp,
        lineHeight = 33.sp,
        letterSpacing = (-0.6).sp,
    ),
    headlineSmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 23.sp,
        lineHeight = 29.sp,
        letterSpacing = (-0.35).sp,
    ),
    titleLarge = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 20.sp, lineHeight = 26.sp),
    titleMedium = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 22.sp),
    bodyLarge = TextStyle(fontSize = 17.sp, lineHeight = 25.sp),
    bodyMedium = TextStyle(fontSize = 14.sp, lineHeight = 21.sp),
    bodySmall = TextStyle(fontSize = 12.sp, lineHeight = 17.sp),
    labelLarge = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 14.sp,
        letterSpacing = 0.2.sp,
    ),
    labelMedium = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 12.sp,
        letterSpacing = 0.85.sp,
    ),
)

private val RealityShapes = Shapes(
    extraSmall = androidx.compose.foundation.shape.RoundedCornerShape(8.dp),
    small = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
    medium = androidx.compose.foundation.shape.RoundedCornerShape(18.dp),
    large = androidx.compose.foundation.shape.RoundedCornerShape(24.dp),
    extraLarge = androidx.compose.foundation.shape.RoundedCornerShape(32.dp),
)

@Composable
fun RealityOsTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = RealityColorScheme,
        typography = RealityTypography,
        shapes = RealityShapes,
        content = content,
    )
}
