package com.luxisoft.realityos.host

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.luxisoft.realityos.*
import com.luxisoft.realityos.R

/** Keeps the Display result mounted so Back returns to the same matches. */
@Composable
internal fun DisplayProfileOverlay(
    viewModel: RealityViewModel,
    profileContent: @Composable (String, () -> Unit) -> Unit = { id, back -> ProfileScreen(userId = id, onBack = back) }
) {
    val request by viewModel.displayProfileRequest.collectAsStateWithLifecycle()
    val current = request ?: return
    if (!viewModel.canShowMatchedProfile(current)) {
        LaunchedEffect(current) { viewModel.closeMatchedProfiles() }
        return
    }
    var selected by remember(current) { mutableStateOf(current.targets.singleOrNull()?.userId) }
    fun back() {
        if (selected != null && current.targets.size > 1) selected = null else viewModel.closeMatchedProfiles()
    }
    Dialog(onDismissRequest = ::back, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.fillMaxSize().testTag("display-profile-overlay")) {
            val userId = selected
            if (userId != null) {
                key(userId) { profileContent(userId, ::back) }
            } else {
                Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    TextButton(onClick = ::back) { Text(stringResource(R.string.display_back)) }
                    Text(stringResource(R.string.meta_open_profiles), style = MaterialTheme.typography.titleLarge)
                    LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        items(current.targets, key = { it.userId }) { target ->
                            OutlinedButton(
                                onClick = { selected = target.userId },
                                modifier = Modifier.fillMaxWidth().testTag("matched-profile-${target.userId}")
                            ) { Text(target.name.ifBlank { stringResource(R.string.meta_profile) }) }
                        }
                    }
                }
            }
        }
    }
}
