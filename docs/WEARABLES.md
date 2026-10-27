# Meta Ray-Ban Display integration

RealityOS uses the official Meta Wearables Device Access Toolkit (DAT) 1.0.1 as
the primary integration for Meta Ray-Ban Display. The Android phone is the
required technical host for Bluetooth, Meta AI registration, and network
transport; field operation is rendered on the glasses, not in a phone UI.

## Supported RealityOS flow

1. An administrator enrolls a RealityOS device and stores its device ID/key in
   encrypted Android storage. This is not a human login and the client never
   receives a Model API key.
2. The administrator completes the Meta AI registration/permission flow once.
3. DAT opens a Display-capable session and sends the RealityOS home screen to
   the glasses.
4. **Register** requires an explicit location selection and an explicit capture
   session. DAT camera streaming supplies in-stream photos and bounded HEVC MP4
   clips; the Android host uploads them to the device endpoints. Query never
   starts the camera.
5. **Query** requests DAT microphone permission from a glasses-side action,
   receives final speech transcription, queries existing RealityOS evidence,
   then renders the last-seen text and signed highlighted image on Display.
6. Android system TTS speaks the response through the currently active audio
   route. On a paired glasses route this should be the glasses audio device,
   but it must be confirmed on actual hardware before it is claimed as tested.

The API returns a short-lived `display_media_url` for Display images. A DAT
Display image request cannot attach custom device headers, so this is an
observation-scoped bearer URL issued for an active enrolled device. It expires
quickly and is not an API token.

## Development setup

- Install the Meta AI app on a supported Android phone and enable Developer
  Mode for the paired Meta Ray-Ban Display glasses.
- For Developer Mode, DAT accepts `mwdat_application_id=0` and
  `mwdat_client_token=0`. Production/release-channel testing instead requires
  credentials and approved capabilities from Wearables Developer Center. Keep
  them in `android/local.properties`, never Git.
- Provision the RealityOS device ID/key once through the administrator host
  screen. The end user then works from the Display UI.
- Build with `ANDROID_HOME=/opt/android-sdk ./gradlew :app:assembleDebug` from
  `android/`.

## Capability and testing status

The checked-in Android source uses `mwdat-core`, `mwdat-camera`,
`mwdat-display`, `mwdat-speech`, and Debug MockDeviceKit. It has a compiled
debug APK in the development environment, but no physical glasses run is
claimed.

- Camera photo/video, on-device speech and voice invocation remain DAT
  developer-preview capability areas. Request the corresponding approvals in
  Wearables Developer Center before testing them.
- Standalone high-quality photo and PCM audio streaming are experimental and
  are not used as the baseline RealityOS flow. Video clips are recorded from
  compressed HEVC camera frames; microphone-based query uses DAT Speech.
- The included MockDeviceKit instrumentation smoke test passed in a
  GitHub-hosted Android 15 emulator on 2026-10-27. It pairs Meta's simulated
  Display model, exercises its lifecycle, creates the official Display preview
  renderer and test server, and drives simulated speech partial/final results.
  It does not prove camera, microphone, Bluetooth-audio or Display behavior on
  physical glasses.
- Hardware QA must explicitly validate registration, camera/microphone
  permission denial, Display state, photo, video, speech partial/final result,
  evidence image, TTS route, disconnect, and recovery.

The standalone `display-webapp/` remains a browser-based query demo for
Meta Ray-Ban Display. It is not used for camera or microphone capture because
those capabilities are provided by DAT.
