package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

@Composable
internal fun MedicationCheckForm(workspaceId: String, person: JSONObject) {
    val related = person.optJSONArray("related")
    val prescriptions = (0 until (related?.length() ?: 0)).map { related!!.getJSONObject(it) }.filter { it.optString("kind") == "prescription" }
    if (prescriptions.isEmpty()) return
    var expanded by remember(person.getString("id")) { mutableStateOf(false) }
    var selected by remember(person.getString("id")) { mutableStateOf(prescriptions.first().getString("id")) }
    var ingredient by remember { mutableStateOf("") }
    var concentration by remember { mutableStateOf("") }
    var confirmed by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var result by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    OutlinedButton(onClick = { expanded = !expanded }) { Text(stringResource(R.string.medication_compare)) }
    if (!expanded) return
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        prescriptions.forEach { rx ->
            Row {
                RadioButton(selected == rx.getString("id"), onClick = { selected = rx.getString("id"); result = "" }, enabled = !busy)
                Text(rx.getString("title"))
            }
        }
        OutlinedTextField(ingredient, { ingredient = it; result = "" }, label = { Text(stringResource(R.string.medication_ingredient)) }, enabled = !busy)
        OutlinedTextField(concentration, { concentration = it; result = "" }, label = { Text(stringResource(R.string.medication_concentration)) }, enabled = !busy)
        Row { Checkbox(confirmed, { confirmed = it; result = "" }, enabled = !busy); Text(stringResource(R.string.medication_confirmed)) }
        Button(enabled = !busy && ingredient.isNotBlank() && concentration.isNotBlank(), onClick = {
            busy = true
            scope.launch {
                try {
                    val response = withContext(Dispatchers.IO) {
                        JSONObject(SocialSession.request("workspaces/$workspaceId/records/${person.getString("id")}/medication-check", JSONObject()
                            .put("prescription_id", selected).put("observed_ingredient", ingredient).put("observed_concentration", concentration)
                            .put("patient_confirmed", confirmed).put("checked_at", java.time.Instant.now().toString())))
                    }
                    result = localizedText(when (response.optString("status")) {
                        "fields_match" -> R.string.medication_fields_match
                        "discrepancy" -> R.string.medication_discrepancy
                        else -> R.string.medication_incomplete
                    })
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (_: Exception) { result = localizedText(R.string.account_failed) }
                finally { busy = false }
            }
        }) { Text(stringResource(R.string.medication_compare)) }
        if (result.isNotBlank()) Text(result)
        Text(stringResource(R.string.medication_review), style = MaterialTheme.typography.bodySmall)
    }
}
