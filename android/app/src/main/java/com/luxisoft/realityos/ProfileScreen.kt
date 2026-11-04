package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** A person's information, separate from the group's publication gallery. */
@Composable
internal fun ProfileScreen(userId: String, onBack: () -> Unit) {
    val context = LocalContext.current
    val state = rememberProfileState(userId)
    val scope = rememberCoroutineScope()
    var question by rememberSaveable(userId) { mutableStateOf("") }
    var answer by remember(userId) { mutableStateOf("") }
    var loading by remember(userId) { mutableStateOf(false) }
    var error by remember(userId) { mutableStateOf("") }
    Column(Modifier.fillMaxSize()) {
        ProfileHeader(state = state, onBack = onBack, initiallyExpanded = true)
        Column(
            Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            NoticeEffect(error, { error = "" })
            if (state.profile != null) {
                Text(localizedText(R.string.ui_ask_about_this_profile), style = MaterialTheme.typography.titleMedium)
                OutlinedTextField(
                    question,
                    { question = it },
                    label = { Text(localizedText(R.string.ui_e_g_how_much_do_they_know_about_architecture)) },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = {
                    scope.launch {
                        loading = true
                        error = ""
                        try {
                            val language = RealityExperienceStore(context).syncAccountLanguage().languageTag
                            val response = withContext(Dispatchers.IO) {
                                JSONObject(SocialSession.request("profiles/search", JSONObject().put("question", question).put("user_id", userId).put("language", language)))
                            }
                            if (language == RealityExperienceStore(context).selectedLanguage().languageTag) {
                                answer = response.optString("answer") + if (response.optBoolean("simulated")) localizedText(R.string.ui_simulated) else ""
                            }
                        } catch (cancelled: CancellationException) {
                            throw cancelled
                        } catch (failure: Exception) {
                            error = localizedFailure(failure)
                        } finally {
                            loading = false
                        }
                    }
                }, enabled = question.length >= 2 && !loading) { Text(localizedText(R.string.ui_ask)) }
                if (loading) {
                    SkeletonLines()
                } else if (answer.isNotBlank()) {
                    Text(answer)
                }
            }
        }
    }
}
