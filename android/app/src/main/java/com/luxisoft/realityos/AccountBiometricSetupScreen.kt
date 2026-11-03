package com.luxisoft.realityos

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import org.json.JSONObject

/** Presentation only: consent, uploads and completion remain in the account gate. */
@Composable
internal fun AccountBiometricSetupScreen(
    status: JSONObject?,
    busy: Boolean,
    failed: Boolean,
    progress: String,
    onRetry: () -> Unit,
    onConsent: () -> Unit,
    onProfile: () -> Unit,
    onReferences: () -> Unit,
    onResetReferences: () -> Unit,
    onComplete: () -> Unit,
    onSignOut: () -> Unit
) {
    val consented = status?.optBoolean("consented") == true
    val profileReady = status?.optBoolean("profile_photo_ready") == true && status.optBoolean("avatar_ready")
    val accepted = status?.optInt("accepted_photos") ?: 0
    val ready = consented && profileReady && accepted >= 3
    val step = if (!consented) {
        1
    } else if (!profileReady) {
        2
    } else {
        3
    }
    Surface(Modifier.fillMaxSize().testTag("account-biometric-setup"), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().safeDrawingPadding().imePadding(), horizontalAlignment = Alignment.CenterHorizontally) {
            Box(Modifier.widthIn(max = 528.dp).fillMaxWidth()) {
                EntryBrandHeader {
                    if (busy && status != null) {
                        CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
                        Spacer(Modifier.width(8.dp))
                    }
                    IconButton(onClick = onSignOut, enabled = !busy, modifier = Modifier.testTag("setup-sign-out")) {
                        Icon(Icons.AutoMirrored.Outlined.Logout, localizedText(R.string.ui_sign_out), tint = AccountMuted)
                    }
                }
            }
            Column(
                Modifier.weight(1f).widthIn(max = 528.dp).fillMaxWidth()
                    .verticalScroll(rememberScrollState()).padding(horizontal = 24.dp).padding(top = 12.dp, bottom = 24.dp)
                    .testTag("setup-scroll"),
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(localizedText(R.string.biometric_setup_title), style = MaterialTheme.typography.headlineMedium, modifier = Modifier.semantics { heading() })
                    Text(localizedText(R.string.biometric_setup_intro), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
                }
                if (status == null) {
                    SetupLoadState(busy, failed, onRetry)
                } else {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(
                            localizedText(if (ready) R.string.biometric_setup_ready else R.string.biometric_setup_step, step),
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite }
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.clearAndSetSemantics {}) {
                            repeat(3) { index ->
                                Box(Modifier.weight(1f).height(4.dp).background(if (index < step) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant, CircleShape))
                            }
                        }
                    }
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        SetupSection(
                            number = 1,
                            title = R.string.biometric_consent_heading,
                            subtitle = if (consented) R.string.biometric_consent_done else R.string.biometric_consent_hint,
                            complete = consented,
                            active = !consented
                        ) {
                            if (!consented) {
                                Text(localizedText(R.string.face_consent_body), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
                                EntryPrimary(localizedText(R.string.biometric_accept_continue), Modifier.fillMaxWidth().testTag("setup-consent"), enabled = !busy, onClick = onConsent)
                            }
                        }
                        SetupSection(
                            number = 2,
                            title = R.string.biometric_profile_heading,
                            subtitle = if (profileReady) R.string.biometric_profile_ready else R.string.biometric_profile_hint,
                            complete = profileReady,
                            active = consented && !profileReady
                        ) {
                            if (consented) {
                                if (!profileReady) {
                                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                        Box(Modifier.size(56.dp).background(MaterialTheme.colorScheme.primary.copy(alpha = .10f), CircleShape), contentAlignment = Alignment.Center) {
                                            Icon(Icons.Outlined.PersonOutline, null, Modifier.size(32.dp), tint = MaterialTheme.colorScheme.primary)
                                        }
                                        Text(localizedText(R.string.biometric_profile_guidance), style = MaterialTheme.typography.bodyMedium, color = AccountMuted, modifier = Modifier.weight(1f))
                                    }
                                    EntryPrimary(localizedText(R.string.biometric_choose_profile), Modifier.fillMaxWidth().testTag("setup-profile"), enabled = !busy, onClick = onProfile)
                                } else {
                                    TextButton(onClick = onProfile, enabled = !busy, modifier = Modifier.heightIn(min = 48.dp).testTag("setup-profile")) {
                                        Icon(Icons.Outlined.Edit, null, Modifier.size(18.dp))
                                        Spacer(Modifier.width(8.dp))
                                        Text(localizedText(R.string.biometric_change_profile))
                                    }
                                }
                            }
                        }
                        SetupSection(
                            number = 3,
                            title = R.string.biometric_references_heading,
                            subtitle = R.string.biometric_references_hint,
                            complete = ready,
                            active = consented && profileReady
                        ) {
                            if (consented && profileReady) {
                                Text(localizedText(R.string.biometric_references_guidance), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
                                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Text(
                                        localizedText(R.string.biometric_reference_count, accepted),
                                        style = MaterialTheme.typography.labelLarge,
                                        modifier = Modifier.testTag("setup-reference-count").semantics { liveRegion = LiveRegionMode.Polite }
                                    )
                                    LinearProgressIndicator(
                                        progress = { (accepted / 3f).coerceIn(0f, 1f) },
                                        modifier = Modifier.fillMaxWidth().testTag("setup-reference-progress").semantics { contentDescription = localizedText(R.string.biometric_minimum_progress) },
                                        trackColor = MaterialTheme.colorScheme.outlineVariant
                                    )
                                    Text(
                                        localizedText(if (accepted >= 3) R.string.biometric_minimum_ready else R.string.biometric_minimum_remaining, (3 - accepted).coerceAtLeast(0)),
                                        style = MaterialTheme.typography.bodySmall,
                                        color = if (accepted >= 3) MaterialTheme.colorScheme.primary else AccountMuted
                                    )
                                }
                                if (accepted < 3) {
                                    EntryPrimary(localizedText(R.string.biometric_choose_references), Modifier.fillMaxWidth().testTag("setup-references"), enabled = !busy, onClick = onReferences)
                                } else {
                                    OutlinedButton(
                                        onClick = onReferences,
                                        enabled = !busy && accepted < 25,
                                        shape = MaterialTheme.shapes.medium,
                                        colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.primary),
                                        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 14.dp),
                                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("setup-references")
                                    ) {
                                        Icon(Icons.Outlined.AddPhotoAlternate, null, Modifier.size(20.dp))
                                        Spacer(Modifier.width(8.dp))
                                        Text(localizedText(if (accepted < 25) R.string.biometric_add_more else R.string.biometric_limit_reached), textAlign = TextAlign.Center, modifier = Modifier.weight(1f))
                                    }
                                }
                                if (accepted > 0) {
                                    TextButton(onClick = onResetReferences, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("setup-reset")) {
                                        Text(localizedText(R.string.biometric_reset_references), style = MaterialTheme.typography.bodySmall, textAlign = TextAlign.Center)
                                    }
                                }
                            }
                        }
                    }
                    if (busy) {
                        Column(Modifier.semantics { liveRegion = LiveRegionMode.Polite }.testTag("setup-busy"), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            LinearProgressIndicator(Modifier.fillMaxWidth())
                            Text(localizedText(if (progress.isBlank()) R.string.biometric_saving else R.string.biometric_uploading, progress), style = MaterialTheme.typography.bodySmall, color = AccountMuted)
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Icon(Icons.Outlined.Lock, null, Modifier.size(18.dp), tint = AccountMuted)
                        Text(localizedText(R.string.biometric_privacy_note), style = MaterialTheme.typography.bodySmall, color = AccountMuted)
                    }
                    if (consented && profileReady) {
                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                        EntryPrimary(localizedText(R.string.biometric_complete), Modifier.fillMaxWidth().testTag("setup-complete"), enabled = !busy && ready, onClick = onComplete)
                    }
                }
            }
        }
    }
}

@Composable
private fun SetupSection(number: Int, title: Int, subtitle: Int, complete: Boolean, active: Boolean, content: @Composable ColumnScope.() -> Unit) {
    Surface(
        color = if (active) AccountFieldSurface else MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.medium,
        border = BorderStroke(1.dp, if (active) MaterialTheme.colorScheme.primary.copy(alpha = .45f) else MaterialTheme.colorScheme.outlineVariant),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(
                    Modifier.size(32.dp).background(if (active || complete) MaterialTheme.colorScheme.primary.copy(alpha = .12f) else MaterialTheme.colorScheme.outlineVariant, CircleShape).clearAndSetSemantics {},
                    contentAlignment = Alignment.Center
                ) {
                    if (complete) {
                        Icon(Icons.Outlined.Check, null, Modifier.size(18.dp), tint = MaterialTheme.colorScheme.primary)
                    } else {
                        Text(number.toString(), style = MaterialTheme.typography.labelLarge, color = if (active) MaterialTheme.colorScheme.primary else AccountMuted)
                    }
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text(localizedText(title), style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                    Text(localizedText(subtitle), style = MaterialTheme.typography.bodySmall, color = AccountMuted)
                }
            }
            content()
        }
    }
}

@Composable
private fun SetupLoadState(busy: Boolean, failed: Boolean, onRetry: () -> Unit) {
    Surface(color = AccountFieldSurface, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(24.dp).semantics { liveRegion = LiveRegionMode.Polite }, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            if (failed && !busy) {
                Icon(Icons.Outlined.CloudOff, null, tint = AccountMuted)
                Text(localizedText(R.string.biometric_load_failed), style = MaterialTheme.typography.bodyMedium)
                OutlinedButton(onClick = onRetry, shape = MaterialTheme.shapes.medium, colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.primary), modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("setup-retry")) {
                    Text(localizedText(R.string.ui_retry))
                }
            } else {
                LinearProgressIndicator(Modifier.fillMaxWidth().testTag("setup-loading"))
                Text(localizedText(R.string.biometric_loading), style = MaterialTheme.typography.bodyMedium, color = AccountMuted)
            }
        }
    }
}
