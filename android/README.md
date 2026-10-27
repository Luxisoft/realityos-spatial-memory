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

## Hardware-free Meta validation

The instrumentation test uses Meta's official Mock Device Kit, not a custom
glasses mock. It pairs the virtual `META_RAYBAN_DISPLAY`, drives its lifecycle,
constructs the Meta Display preview renderer/test server, and sends simulated
speech partial/final results:

```bash
cd android
ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk \
  ./gradlew :app:connectedDebugAndroidTest
```

Three Mock Device Kit instrumentation tests passed in the GitHub Actions
Android 15 emulator on 2026-10-27, including the Debug controller's In-App
renderer and Chrome preview-server lifecycle. They do not validate physical
camera, microphone, Bluetooth audio, or Display behavior; those require
compatible Meta Ray-Ban hardware.

## Interactive virtual glasses on a phone

The Debug APK includes **Developer Preview**, a development-only controller for
Meta's official Mock Device Kit. It uses the same RealityOS DAT session and
Display callbacks as real glasses; only the device is simulated. It is absent
from the release APK.

1. Start RealityOS with an HTTPS API URL reachable from the phone. For a
   no-cost test use the backend's `META_MODE=mock` configuration.
2. Enroll a RealityOS device in the administrator panel, then provision the
   Debug APK with its workspace ID, device ID and device key.
3. Install the Debug APK on an Android phone:

   ```bash
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

4. Open **Developer Preview**, choose **In app**, and tap **Start virtual
   glasses**. The square viewport is Meta's renderer for `META_RAYBAN_DISPLAY`.
5. From the renderer, use Register or Find an object exactly as you would on
   glasses. The Debug controls can select a mock JPEG/PNG photo, an AVC/HEVC
   video feed, phone-camera feed, DAT permission outcome, and partial/final
   speech.

The phone camera is a mock stream source and requires Android camera
permission. It does not represent physical-glasses optics or hardware.

### Chrome preview

Choose **Chrome** in Developer Preview, connect the phone by USB with Android
debugging enabled, then run the displayed command on the computer:

```bash
adb forward tcp:<port> tcp:<port>
```

Open the displayed localhost URL in desktop Chrome with Meta Ray-Ban Display
Simulator enabled. Stop Developer Preview when done; it shuts down the local
preview server. The UI does not expose API credentials, Meta model keys or
signed media URLs as debugging values.

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

For a Debug virtual-device test, no paired physical glasses are required: use
Developer Preview instead of **Connect Display**.

Photo capture uses DAT in-stream photos. Video uses compressed HEVC frames to
create a bounded MP4 clip and stores the uploaded original in PostgreSQL BYTEA.
Speech query uses `mwdat-speech`; answer audio uses Android TTS on the active
Bluetooth audio route. Physical-device validation is still required for all
hardware capabilities.
