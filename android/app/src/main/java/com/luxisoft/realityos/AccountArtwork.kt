package com.luxisoft.realityos

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Login
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.unit.dp

internal val AccountBlue = Color(0xFF62A9F8)
internal val AccountMuted = Color(0xFFAAB4AF)
internal val AccountFieldSurface = Color(0xFF2D3034)

/** A local vector composition, echoing the observation trail in the welcome screen. */
@Composable
internal fun AccountArtwork(step: AccountStep, sent: Boolean, compact: Boolean) {
    Box(Modifier.fillMaxWidth().height(if (compact) 80.dp else 144.dp).clearAndSetSemantics {}, contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height
            // A restrained coordinate field and an observation trail, not a repeating image.
            for (x in 0..12) {
                for (y in 0..4) {
                    drawCircle(AccountBlue.copy(alpha = .12f), 1.dp.toPx(), Offset(w * (.08f + x * .07f), h * (.14f + y * .18f)))
                }
            }
            val trace = Path().apply {
                moveTo(w * .04f, h * .68f)
                cubicTo(w * .22f, h * .90f, w * .28f, h * .06f, w * .51f, h * .38f)
                cubicTo(w * .73f, h * .78f, w * .79f, h * .14f, w * .96f, h * .27f)
            }
            drawPath(trace, AccountBlue.copy(alpha = .22f), style = Stroke(1.5.dp.toPx()))
            listOf(Offset(w * .13f, h * .65f), Offset(w * .83f, h * .34f)).forEach {
                drawCircle(AccountBlue.copy(alpha = .08f), 13.dp.toPx(), it)
                drawCircle(AccountBlue.copy(alpha = .7f), 3.dp.toPx(), it)
            }
        }
        val cardSize = if (compact) 66.dp else 102.dp
        Box(Modifier.size(cardSize).rotate(-9f).background(Color(0xFF293440), RoundedCornerShape(24.dp)).border(1.dp, AccountBlue.copy(alpha = .36f), RoundedCornerShape(24.dp)), contentAlignment = Alignment.Center) {
            Icon(
                if (step == AccountStep.Register && !sent) {
                    Icons.Outlined.PersonOutline
                } else if (step == AccountStep.Recover && !sent) {
                    Icons.Outlined.Key
                } else {
                    Icons.Outlined.MailOutline
                },
                null,
                tint = AccountBlue,
                modifier = Modifier.size(if (compact) 34.dp else 52.dp)
            )
        }
        Box(Modifier.offset(x = if (compact) 31.dp else 47.dp, y = if (compact) 19.dp else 33.dp).size(if (compact) 28.dp else 38.dp).background(AccountBlue, CircleShape).border(3.dp, Color(0xFF262729), CircleShape), contentAlignment = Alignment.Center) {
            Icon(
                when {
                    sent -> Icons.Outlined.Check
                    step == AccountStep.Register -> Icons.Outlined.Add
                    step == AccountStep.Recover -> Icons.Outlined.LockReset
                    step == AccountStep.Resend -> Icons.Outlined.Refresh
                    else -> Icons.AutoMirrored.Outlined.Login
                },
                null,
                Modifier.size(if (compact) 16.dp else 20.dp),
                tint = Color(0xFF17211F)
            )
        }
    }
}
