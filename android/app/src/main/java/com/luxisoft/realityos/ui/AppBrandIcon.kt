package com.luxisoft.realityos

import androidx.compose.foundation.Image
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource

@Composable
internal fun AppBrandIcon(modifier: Modifier = Modifier) {
    Image(
        painter = painterResource(R.drawable.icon_app),
        contentDescription = null,
        contentScale = ContentScale.Crop,
        modifier = modifier.clip(CircleShape)
    )
}
