package com.luxisoft.realityos

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

@Composable
internal fun FacebookAccessScreen(busy: Boolean, error: String, consentChecked: Boolean, onConsentChange: (Boolean) -> Unit, onLogin: () -> Unit, onGuest: () -> Unit, onWelcome: () -> Unit) {
    Surface(Modifier.fillMaxSize().testTag("access-screen"), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
            Column(Modifier.widthIn(max = 528.dp).fillMaxSize()) {
                EntryBrandHeader()
                BoxWithConstraints(Modifier.weight(1f)) {
                    Column(
                        Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).heightIn(min = maxHeight)
                            .padding(horizontal = 24.dp).padding(top = 8.dp, bottom = 24.dp),
                        verticalArrangement = Arrangement.Center
                    ) {
                        EntryScene(R.drawable.intro_overview, compact = true)
                        Spacer(Modifier.height(20.dp))
                        Text(stringResource(R.string.access_title), style = MaterialTheme.typography.headlineMedium)
                        Spacer(Modifier.height(8.dp))
                        Text(stringResource(R.string.access_description), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
                        Spacer(Modifier.height(20.dp))
                        NoticeEffect(error, {})
                        // Existing consent control, wording and authorization behavior are preserved.
                        Row(Modifier.fillMaxWidth().widthIn(max = 560.dp), verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = consentChecked, onCheckedChange = onConsentChange, enabled = !busy)
                            Text(
                                stringResource(R.string.facebook_consent_entry),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(start = 4.dp)
                            )
                        }
                        Spacer(Modifier.height(12.dp))
                        Button(
                            onClick = onLogin,
                            enabled = !busy && consentChecked,
                            shape = MaterialTheme.shapes.medium,
                            colors = ButtonDefaults.buttonColors(contentColor = Color(0xFF17211F)),
                            modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("access-meta"),
                            contentPadding = PaddingValues(16.dp)
                        ) {
                            if (busy) {
                                CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp, color = AccountBlue)
                            } else {
                                Icon(painterResource(R.drawable.ic_meta), null, Modifier.size(24.dp))
                            }
                            Spacer(Modifier.width(12.dp))
                            Text(stringResource(if (busy) R.string.facebook_access_connecting else R.string.facebook_access_continue), style = MaterialTheme.typography.labelLarge)
                        }
                        Spacer(Modifier.height(12.dp))
                        OutlinedButton(
                            onClick = onGuest,
                            enabled = !busy,
                            shape = MaterialTheme.shapes.medium,
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onSurface),
                            border = BorderStroke(1.dp, if (busy) MaterialTheme.colorScheme.outlineVariant else AccountBlue.copy(alpha = 0.55f)),
                            modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp).testTag("access-email"),
                            contentPadding = PaddingValues(16.dp)
                        ) {
                            Icon(Icons.Outlined.MailOutline, null, Modifier.size(22.dp), tint = if (busy) LocalContentColor.current else AccountBlue)
                            Spacer(Modifier.width(12.dp))
                            Text(stringResource(R.string.account_access), style = MaterialTheme.typography.labelLarge)
                        }
                        Spacer(Modifier.height(20.dp))
                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = onWelcome, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("access-explore")) {
                            Icon(Icons.Outlined.Explore, null, Modifier.size(20.dp))
                            Spacer(Modifier.width(10.dp))
                            Text(stringResource(R.string.explore_open), style = MaterialTheme.typography.labelLarge)
                            Spacer(Modifier.width(10.dp))
                            Icon(Icons.AutoMirrored.Outlined.ArrowForward, null, Modifier.size(18.dp))
                        }
                    }
                }
            }
        }
    }
}
