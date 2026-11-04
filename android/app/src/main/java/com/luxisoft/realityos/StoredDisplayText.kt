package com.luxisoft.realityos

import org.json.JSONArray
import org.json.JSONObject

/** Select already-authored database copy. Never translate or request a provider. */
internal fun JSONObject.storedValue(field: String, language: String = LocalizedText.languageTag): Any? = optJSONObject("display_text")?.optJSONObject(field)?.opt(language) ?: opt(field)

internal fun JSONObject.storedText(field: String, language: String = LocalizedText.languageTag): String = storedValue(field, language)?.takeUnless { it == JSONObject.NULL }?.toString().orEmpty()

internal fun JSONObject.storedObject(field: String): JSONObject = storedValue(field) as? JSONObject ?: JSONObject()

internal fun JSONObject.storedArray(field: String): JSONArray = storedValue(field) as? JSONArray ?: JSONArray()

internal fun recordFieldLabel(key: String): String = when (key) {
    "description" -> localizedText(R.string.record_label_description)
    "reference" -> localizedText(R.string.record_label_reference)
    "status" -> localizedText(R.string.record_label_status)
    "note" -> localizedText(R.string.record_label_note)
    "last_seen_location" -> localizedText(R.string.record_label_last_seen_location)
    "identifier" -> localizedText(R.string.record_label_identifier)
    "birth_date" -> localizedText(R.string.record_label_birth_date)
    "allergies_reviewed_at" -> localizedText(R.string.record_label_allergies_reviewed_at)
    "ingredient" -> localizedText(R.string.record_label_ingredient)
    "concentration" -> localizedText(R.string.record_label_concentration)
    "state" -> localizedText(R.string.record_label_state)
    "valid_from" -> localizedText(R.string.record_label_valid_from)
    "valid_until" -> localizedText(R.string.record_label_valid_until)
    "substance" -> localizedText(R.string.record_label_substance)
    "person" -> localizedText(R.string.record_label_person)
    "case" -> localizedText(R.string.record_label_case)
    "encounter" -> localizedText(R.string.record_label_encounter)
    "event" -> localizedText(R.string.record_label_event)
    "object" -> localizedText(R.string.record_label_object)
    "prescription" -> localizedText(R.string.record_label_prescription)
    "allergy" -> localizedText(R.string.record_label_allergy)
    "administration" -> localizedText(R.string.record_label_administration)
    else -> key
}
