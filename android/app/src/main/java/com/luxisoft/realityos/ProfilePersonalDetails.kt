package com.luxisoft.realityos

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import java.time.LocalDate
import java.time.ZoneOffset
import org.json.JSONObject

internal data class PersonalProfileDraft(
    val displayName: String,
    val birthday: String,
    val gender: String,
    val hometown: String,
    val location: String
) {
    fun errors(): Map<String, Int> = buildMap {
        if (displayName.trim().length !in 1..160) put("display_name", R.string.account_name_error)
        if (birthday.isNotBlank() && !validBirthday(birthday)) put("birthday", R.string.profile_birthday_error)
        if (gender.trim().length > 32) put("gender", R.string.profile_gender_error)
        if (hometown.trim().length > 160) put("hometown", R.string.profile_place_error)
        if (location.trim().length > 160) put("location", R.string.profile_place_error)
    }

    fun addTo(payload: JSONObject): JSONObject = payload
        .put("display_name", displayName.trim())
        .put("birthday", birthday.trim().ifBlank { null } ?: JSONObject.NULL)
        .put("gender", gender.trim().ifBlank { null } ?: JSONObject.NULL)
        .put("hometown", hometown.trim().ifBlank { null } ?: JSONObject.NULL)
        .put("location", location.trim().ifBlank { null } ?: JSONObject.NULL)

    companion object {
        val Saver = listSaver<PersonalProfileDraft, String>(
            save = { listOf(it.displayName, it.birthday, it.gender, it.hometown, it.location) },
            restore = { PersonalProfileDraft(it[0], it[1], it[2], it[3], it[4]) }
        )
        fun from(profile: JSONObject, language: String? = null) = PersonalProfileDraft(
            profile.optText("display_name").orEmpty(),
            profile.optText("birthday").orEmpty(),
            if (language == null) profile.optText("gender").orEmpty() else profile.storedText("gender", language),
            if (language == null) profile.optText("hometown").orEmpty() else profile.storedText("hometown", language),
            if (language == null) profile.optText("location").orEmpty() else profile.storedText("location", language)
        )
    }
}

private fun validBirthday(value: String): Boolean = runCatching {
    val date = LocalDate.parse(value.trim())
    date.year >= 1900 && !date.isAfter(LocalDate.now(ZoneOffset.UTC)) && date.toString() == value.trim()
}.getOrDefault(false)

internal fun profileBirthdayLabel(value: String, language: String = LocalizedText.languageTag): String = evidenceDate(value, language) ?: value

internal fun profileAgeLabel(value: String): String {
    if (value.isBlank()) return ""
    val age = value.toIntOrNull()
    return if (age != null) localizedQuantityText(R.plurals.profile_age, age, age) else localizedText(R.string.ui_1_s_years_old, value)
}

internal fun LazyListScope.personalProfileFields(
    draft: PersonalProfileDraft,
    onChange: (PersonalProfileDraft) -> Unit,
    editable: Boolean,
    facebook: Boolean,
    busy: Boolean,
    errors: Map<String, Int>
) {
    if (!editable && !facebook) return
    item {
        Surface(color = MaterialTheme.colorScheme.surfaceVariant, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("profile-personal-source")) {
            Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Icon(if (facebook) Icons.Outlined.Sync else Icons.Outlined.Badge, null, tint = MaterialTheme.colorScheme.primary)
                Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(stringResource(if (facebook) R.string.profile_facebook_details else R.string.profile_personal_details), style = MaterialTheme.typography.titleSmall)
                    Text(stringResource(if (facebook) R.string.profile_facebook_details_hint else R.string.profile_personal_details_hint), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
    val fields = listOf(
        Triple("display_name", R.string.account_name, draft.displayName),
        Triple("location", R.string.ui_location, draft.location),
        Triple("hometown", R.string.ui_hometown, draft.hometown),
        Triple("birthday", R.string.ui_birthday, draft.birthday),
        Triple("gender", R.string.ui_gender, draft.gender)
    )
    fields.forEach { (key, label, value) ->
        item(key = "personal-$key") {
            val icon = when (key) {
                "location" -> Icons.Outlined.LocationOn
                "hometown" -> Icons.Outlined.Home
                "birthday" -> Icons.Outlined.Cake
                else -> Icons.Outlined.PersonOutline
            }
            if (editable) {
                if (key == "birthday") {
                    BirthdayField(value, { onChange(draft.copy(birthday = it)) }, busy, errors[key])
                } else {
                    OutlinedTextField(
                        value = value,
                        onValueChange = {
                            onChange(
                                when (key) {
                                    "display_name" -> draft.copy(displayName = it)
                                    "location" -> draft.copy(location = it)
                                    "hometown" -> draft.copy(hometown = it)
                                    else -> draft.copy(gender = it)
                                }
                            )
                        },
                        label = { Text(stringResource(label)) },
                        leadingIcon = { Icon(icon, null) },
                        enabled = !busy, singleLine = true,
                        isError = key in errors,
                        supportingText = errors[key]?.let { resource -> { Text(stringResource(resource)) } },
                        keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Words),
                        modifier = Modifier.fillMaxWidth().testTag("profile-$key")
                    )
                }
            } else {
                Row(Modifier.fillMaxWidth().padding(horizontal = 4.dp, vertical = 6.dp).testTag("profile-readonly-$key"), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(icon, null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    Column(Modifier.weight(1f)) {
                        Text(stringResource(label), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text((if (key == "birthday") profileBirthdayLabel(value) else value).ifBlank { stringResource(R.string.profile_not_shared) }, style = MaterialTheme.typography.bodyMedium)
                    }
                    Icon(Icons.Outlined.Lock, null, Modifier.size(16.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
    item { HorizontalDivider(Modifier.padding(vertical = 8.dp)) }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BirthdayField(value: String, onChange: (String) -> Unit, busy: Boolean, error: Int?) {
    var showCalendar by remember { mutableStateOf(false) }
    OutlinedTextField(
        value = value, onValueChange = onChange,
        label = { Text(stringResource(R.string.ui_birthday)) },
        leadingIcon = { Icon(Icons.Outlined.Cake, null) },
        trailingIcon = {
            IconButton(onClick = { showCalendar = true }, enabled = !busy, modifier = Modifier.testTag("profile-birthday-calendar")) {
                Icon(Icons.Outlined.CalendarMonth, stringResource(R.string.profile_choose_birthday))
            }
        },
        supportingText = { Text(stringResource(error ?: R.string.profile_birthday_hint)) },
        enabled = !busy, isError = error != null, singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Ascii),
        modifier = Modifier.fillMaxWidth().testTag("profile-birthday")
    )
    if (showCalendar) {
        val today = LocalDate.now(ZoneOffset.UTC)
        val calendar = rememberDatePickerState(
            initialSelectedDateMillis = if (validBirthday(value)) LocalDate.parse(value.trim()).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli() else null,
            yearRange = 1900..today.year,
            selectableDates = object : SelectableDates {
                override fun isSelectableDate(utcTimeMillis: Long) = utcTimeMillis <= today.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()
            }
        )
        DatePickerDialog(
            onDismissRequest = { showCalendar = false },
            confirmButton = {
                TextButton(onClick = {
                    calendar.selectedDateMillis?.let { onChange(java.time.Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate().toString()) }
                    showCalendar = false
                }, enabled = calendar.selectedDateMillis != null) { Text(stringResource(R.string.ui_save)) }
            },
            dismissButton = {
                TextButton(onClick = {
                    onChange("")
                    showCalendar = false
                }) { Text(stringResource(R.string.profile_clear_birthday)) }
            }
        ) { DatePicker(state = calendar) }
    }
}
