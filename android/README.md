# Android status

This directory is reserved for the Kotlin/Jetpack Compose client. It is not yet
implemented because the Meta Wearables DAT SDK version, required repository
configuration and Mock Device Kit compatibility must be verified before adding
an integration that could not compile or run.

The API is ready for Android flows: explicit capture sessions, multipart image
upload, jobs, text/WAV query, binary media and highlighted evidence. Android
must keep MODEL_API_KEY out of the client, use native TTS only where available,
and distinguish phone rendering from Display hardware.
