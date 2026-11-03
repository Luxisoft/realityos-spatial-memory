package com.luxisoft.realityos

import org.json.JSONObject

/** Match camera uploads: apply all EXIF rotations/mirrors and send a bounded JPEG. */
internal fun prepareRecognitionPhoto(raw: ByteArray): ByteArray = uprightImageBytes(raw) ?: error(localizedText(R.string.face_unreadable))

internal fun uploadRecognitionProfile(photo: ByteArray) {
    val result = JSONObject(SocialSession.requestMultipart("faces/profile-photo", emptyMap(), photo, "profile-photo.jpg", "image/jpeg"))
    check(result.optInt("faces_enrolled") == 1) { localizedText(R.string.biometric_photo_one_face) }
    SocialSession.requestMultipart("me/profile/avatar", emptyMap(), photo, "avatar.jpg", "image/jpeg")
}

/** Translate known validation reasons; never expose arbitrary server internals. */
internal fun recognitionPhotoFailure(path: String, status: Int, body: String): String? {
    if (path !in setOf("faces/profile-photo", "faces/reference-photos", "me/profile/avatar")) return null
    if (status !in setOf(409, 413, 415, 422)) return null
    val detail = runCatching { JSONObject(body).optString("detail") }.getOrDefault("")
    val message = when {
        status == 413 -> R.string.biometric_photo_too_large
        status == 415 || detail in setOf("Invalid image data.", "Invalid image.") -> R.string.face_unreadable
        detail in setOf("Profile photos must show exactly one face.", "Each reference photo must show exactly one face.") -> R.string.biometric_photo_one_face
        detail.startsWith("No live face could be verified") -> R.string.biometric_photo_quality
        detail == "The face is too small or unclear. Choose a sharper photo." -> R.string.biometric_photo_quality
        detail == "This photo does not match the registered face." -> R.string.biometric_photo_identity
        detail == "Choose another photo; the profile photo does not count as a reference." -> R.string.biometric_photo_different
        detail == "At most 25 reference photos are allowed." -> R.string.biometric_limit_reached
        status == 409 && detail == "Upload the profile photo first." -> R.string.biometric_profile_needed
        status == 422 -> R.string.biometric_photo_rejected
        else -> return null
    }
    return localizedText(message)
}
