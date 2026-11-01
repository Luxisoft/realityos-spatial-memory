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
// renderer is the focal point; Meta blue carries actions and live state.
private val LuxCanvas = Color(0xFF262729)
private val LuxSurface = Color(0xFF262729)
private val LuxRaised = Color(0xFF262729)
private val LuxInput = Color(0xFF262729)
private val LuxSecondaryContainer = Color(0xFF333333)
private val LuxBorder = Color(0xFF363D45)
private val LuxPaper = Color(0xFFF4F7F5)
private val LuxMist = Color(0xFFAAB4AF)
private val LuxMint = Color(0xFF62A9F8)
private val LuxActionEmerald = Color(0xFF62A9F8)
private val EvidenceAmber = Color(0xFFFFC56A)
private val ErrorRose = Color(0xFFFFB4AB)
internal val RealityIconDefault = Color(0xFF7C7D80)
internal val RealityIconSelected = Color(0xFF747578)

private val RealityColorScheme = darkColorScheme(
    primary = LuxActionEmerald,
    onPrimary = Color.White,
    primaryContainer = LuxSurface,
    onPrimaryContainer = LuxMint,
    secondary = EvidenceAmber,
    onSecondary = Color(0xFF2C1900),
    secondaryContainer = LuxSecondaryContainer,
    onSecondaryContainer = EvidenceAmber,
    tertiary = LuxMint,
    onTertiary = Color(0xFF07140E),
    background = LuxCanvas,
    onBackground = LuxPaper,
    surface = LuxSurface,
    onSurface = LuxPaper,
    surfaceTint = LuxSurface,
    surfaceVariant = LuxRaised,
    onSurfaceVariant = RealityIconDefault,
    surfaceDim = LuxSurface,
    surfaceBright = LuxSurface,
    surfaceContainerLowest = LuxSurface,
    surfaceContainerLow = LuxSurface,
    surfaceContainer = LuxSurface,
    surfaceContainerHigh = LuxRaised,
    surfaceContainerHighest = LuxInput,
    inverseSurface = LuxSurface,
    inverseOnSurface = LuxPaper,
    outline = LuxMist,
    outlineVariant = LuxBorder,
    error = ErrorRose,
    onError = Color(0xFF690005),
    errorContainer = LuxSecondaryContainer,
    onErrorContainer = ErrorRose,
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
