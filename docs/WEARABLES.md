# Wearables and Display

display-webapp is a separate React application with a 600×600-oriented layout,
keyboard-compatible native controls, high contrast, concise last-seen copy and
browser speech synthesis when available. It makes query requests only.

The Android Kotlin/Compose project and Meta Wearables DAT wiring are not
implemented yet. This is intentional: toolkit dependency, Display API and Mock
Device Kit sample must first be verified against official Wearables
documentation and a compatible Android SDK. Ray-Ban variants without a display
must use audio and phone presentation instead.

No physical glasses or official Display simulator was available here, so neither
is claimed tested.
