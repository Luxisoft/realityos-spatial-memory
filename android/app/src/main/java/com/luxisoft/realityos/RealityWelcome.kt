package com.luxisoft.realityos

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

@Composable
fun AboutDestination(onReplayWelcome: () -> Unit) {
    val uriHandler = LocalUriHandler.current
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    stringResource(R.string.about_eyebrow),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.tertiary
                )
                Text(stringResource(R.string.about_title), style = MaterialTheme.typography.headlineMedium)
            }
        }
        item { AboutSection(R.string.about_problem_title, R.string.about_problem_body) }
        item { AboutSection(R.string.about_solution_title, R.string.about_solution_body, featured = true) }
        item { AboutSection(R.string.about_difference_title, R.string.about_difference_body) }
        item { AboutSection(R.string.about_meta_title, R.string.about_meta_body) }
        item { AboutSection(R.string.about_privacy_title, R.string.about_privacy_body) }
        item {
            OutlinedButton(onClick = onReplayWelcome, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(R.string.about_replay))
            }
        }
        item {
            Card(shape = MaterialTheme.shapes.large) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(stringResource(R.string.about_team_title), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.tertiary)
                    Text(stringResource(R.string.about_developed_by), style = MaterialTheme.typography.titleLarge)
                    Text(stringResource(R.string.about_creator), style = MaterialTheme.typography.bodyLarge)
                    Text("Luximus · ${stringResource(R.string.about_location)}", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    HorizontalDivider(modifier = Modifier.padding(vertical = 5.dp), color = MaterialTheme.colorScheme.outlineVariant)
                    LinkButton(stringResource(R.string.about_linkedin)) {
                        uriHandler.openUri("https://www.linkedin.com/in/jose-wilson-marin-giraldo-b1a881304/")
                    }
                    LinkButton(stringResource(R.string.about_email)) {
                        uriHandler.openUri("mailto:jmarin@luxisoft.com")
                    }
                    LinkButton(stringResource(R.string.about_github)) {
                        uriHandler.openUri("https://github.com/Luxisoft/realityos-spatial-memory")
                    }
                }
            }
        }
    }
}

@Composable
private fun AboutSection(@StringRes title: Int, @StringRes body: Int, featured: Boolean = false) {
    Card(
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = if (featured) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface,
            contentColor = if (featured) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface
        )
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(stringResource(title), style = MaterialTheme.typography.titleLarge)
            Text(
                stringResource(body),
                style = MaterialTheme.typography.bodyMedium,
                color = if (featured) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun LinkButton(label: String, onClick: () -> Unit) {
    TextButton(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Text(label, modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
        Text("↗", style = MaterialTheme.typography.titleMedium)
    }
}
