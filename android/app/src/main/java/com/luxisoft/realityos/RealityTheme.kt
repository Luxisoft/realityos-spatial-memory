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

// LUXISOFT Platform dark tokens. The preview stays quiet so the Display
// renderer is the focal point; the brighter mint is reserved for live state
// and memory traces while the darker emerald carries white action labels.
private val LuxCanvas = Color(0xFF181B20)
private val LuxSurface = Color(0xFF22272E)
private val LuxRaised = Color(0xFF2A3037)
private val LuxInput = Color(0xFF1A1E23)
private val LuxBorder = Color(0xFF363D45)
private val LuxPaper = Color(0xFFF4F7F5)
private val LuxMist = Color(0xFFAAB4AF)
private val LuxMint = Color(0xFF63E6AE)
private val LuxActionEmerald = Color(0xFF047857)
private val LuxMintContainer = Color(0xFF173729)
private val LuxMintContainerText = Color(0xFFC2F7D5)
private val EvidenceAmber = Color(0xFFFFC56A)
private val ErrorRose = Color(0xFFFFB4AB)

private val RealityColorScheme = darkColorScheme(
    primary = LuxActionEmerald,
    onPrimary = Color.White,
    primaryContainer = LuxMintContainer,
    onPrimaryContainer = LuxMintContainerText,
    secondary = EvidenceAmber,
    onSecondary = Color(0xFF2C1900),
    secondaryContainer = Color(0xFF5A4010),
    onSecondaryContainer = Color(0xFFFFDEA7),
    tertiary = LuxMint,
    onTertiary = Color(0xFF07140E),
    background = LuxCanvas,
    onBackground = LuxPaper,
    surface = LuxSurface,
    onSurface = LuxPaper,
    surfaceVariant = LuxRaised,
    onSurfaceVariant = LuxMist,
    surfaceContainerHigh = LuxRaised,
    surfaceContainerHighest = LuxInput,
    outline = LuxMist,
    outlineVariant = LuxBorder,
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
    medium = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
    large = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
    extraLarge = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
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
