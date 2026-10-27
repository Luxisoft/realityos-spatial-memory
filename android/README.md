# RealityOS DAT host

This Android app is the required host for the official Meta Wearables Device
Access Toolkit. It is not the field-worker UI: after one-time administrator
provisioning and Meta registration, Register and Query are controlled from
Meta Ray-Ban Display.

## Build

```bash
cd android
ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk ./gradlew :app:assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

For local DAT Developer Mode, create an ignored `android/local.properties`:

```properties
sdk.dir=/opt/android-sdk
mwdat_application_id=0
mwdat_client_token=0
```

For a Meta release channel, replace the two DAT values with the Wearables
Developer Center values. Never commit those values, RealityOS device keys, or
Meta Model API keys.

## Device workflow

1. Enroll a device in the RealityOS admin panel and copy the one-time device
   ID/key into the administrator provisioning screen.
2. Pair Meta Ray-Ban Display with the phone, enable Meta AI Developer Mode,
   then use **Register with Meta AI** and grant required DAT permissions.
3. Use **Connect Display** once. The home, location, capture, voice-query, and
   evidence screens are subsequently delivered to the glasses.

Photo capture uses DAT in-stream photos. Video uses compressed HEVC frames to
create a bounded MP4 clip and stores the uploaded original in PostgreSQL BYTEA.
Speech query uses `mwdat-speech`; answer audio uses Android TTS on the active
Bluetooth audio route. Physical-device validation is still required for all
hardware capabilities.
