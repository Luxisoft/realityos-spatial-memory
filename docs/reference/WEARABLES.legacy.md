> Historical source / Fuente histórica — preserved 2026-11-03. [Current guide](../WEARABLES.md) · [Guía actual](../WEARABLES.es.md). Earlier deployment instructions may be retired.

# Meta Ray-Ban Display integration

RealityOS uses the official Meta Wearables Device Access Toolkit (DAT) 1.0.1 as
the primary integration for Meta Ray-Ban Display. The Android phone hosts
Bluetooth, Meta AI registration and network transport; without glasses, the
Debug display preview uses the phone's own camera, microphone, speaker and
speech recognizer.

## Supported RealityOS flow

1. An administrator enrolls a physical RealityOS device, or the Live server
   issues a short-lived virtual-device identity for the Debug phone preview.
   The selected device ID/key is stored in encrypted Android storage. This is
   not a human login and the client never receives a Model API key.
2. The administrator completes the Meta AI registration/permission flow once.
3. DAT opens a Display-capable session and sends the RealityOS home screen to
   the glasses, or Debug opens the same screen in Mock Device Kit's renderer.
4. **Register** requires an explicit location selection and an explicit capture
   session. Phone preview uses CameraX photo/video with phone microphone audio;
   wearable mode uses DAT in-stream photos and HEVC + PCM/AAC MP4 clips. The
   Android host uploads the original media to device endpoints. Query never
   starts a capture.
5. **Query** requests phone microphone permission in preview or DAT microphone
   permission on glasses, receives final speech transcription, queries existing
   RealityOS evidence, then renders the last-seen text and signed highlighted
   image on Display.
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

### Hardware-free phone preview

The Debug variant opens the in-app **Meta Display preview** automatically with
Meta's Mock Device Kit when no physical Display is detected. It is not part of the release APK and it does not
replace the real DAT implementation: it pairs a virtual
`META_RAYBAN_DISPLAY`, then calls the same `RealityViewModel.connectDisplay`
and `DeviceSession.addDisplay` flow as a physical device. Automatic startup
does not start camera, microphone, recording, or upload.

1. A fresh Debug APK requests `POST /v1/virtual-devices/bootstrap` over HTTPS
   and fills its editable connection inputs with a real, short-lived device
   credential for the configured live workspace. The route refuses Mock mode;
   it is an actual RealityOS/Meta processing path, not simulated evidence.
2. Open **Display preview**. Debug starts the **In app** renderer once and
   presents Meta's `createPreviewView()` through a Debug-only panoramic
   Ray-Ban optical shell. The supplied frame keeps its camera on the right;
   its alpha-traced opening clips a contained square Meta renderer rather than
   stretching the renderer to the lens. This is a phone visual treatment, not
   a claim about physical-glasses optics. The fixed bottom **Stop preview**
   control stops only the virtual session.
3. Open the right-side **Display controls** panel from the Meta-specific bottom
   bar for simulator state, target selection, retry, lifecycle, media and speech
   diagnostics. It has no edge gesture, leaving the horizontal swipe exclusively
   to the left navigation drawer. Preview and physical-glasses actions share the
   **Meta Ray-Ban Display** destination; server/device identity remains in Settings.
4. From the rendered RealityOS flow, grant Android `CAMERA` for photos and
   `RECORD_AUDIO` for video/voice search. CameraX owns the phone camera while an
   action is active. Mock Device Kit's front/back controls select the CameraX
   camera for the next capture; they never open a competing SDK phone feed.
5. Search uses Android speech recognition in preview. Android TTS uses the
   phone's active audio route.

Only the glasses hardware is virtual in this workflow. Selecting a phone or
fixture camera feed and starting Register uploads media to the live server;
Live Muse/SAM processing remains server-side and no Model API key enters the
APK.

**Chrome** mode remains an explicit desktop-only diagnostic from the
right-side Display controls drawer. It starts Meta's local preview server on a
dynamic port and shows the corresponding `adb forward` command and localhost
URL; it never becomes body content in the phone host and never exposes Model
API credentials, device keys or media bearer URLs.

## Capability and testing status

The checked-in Android source uses `mwdat-core`, `mwdat-camera`,
`mwdat-display`, `mwdat-speech`, and Debug MockDeviceKit. It has a compiled
debug APK in the development environment, but no physical glasses run is
claimed.

- Camera photo/video, on-device speech and voice invocation remain DAT
  developer-preview capability areas. Request the corresponding approvals in
  Wearables Developer Center before testing them.
- Wearable video requests PCM audio with its camera stream and muxes it to AAC;
  this DAT audio path is compiled but not hardware-validated. Phone preview
  uses CameraX's MP4 recorder with microphone audio.
- The included MockDeviceKit instrumentation smoke test passed in a
  GitHub-hosted Android 15 emulator on 2026-10-27. It pairs Meta's simulated
  Display model, exercises its lifecycle, creates the official Display preview
  renderer and test server, and drives simulated speech partial/final results.
  It does not prove camera, microphone, Bluetooth-audio or Display behavior on
  physical glasses.
- The Debug-only preview opens Meta's In-App renderer automatically and keeps
  the optional Chrome renderer in the controls drawer. Its controller passed
  on the GitHub-hosted Android 15 emulator on 2026-10-27, including the
  renderer lifecycle and Chrome preview server. Interactive phone and
  desktop-Chrome extension validation remain pending and are not inferred from
  that result.
- Release does not package Mock Device Kit. CI builds Debug and Release and
  rejects a release APK containing `com/meta/wearable/dat/mockdevice`.
- Hardware QA must explicitly validate registration, camera/microphone
  permission denial, Display state, photo, video, speech partial/final result,
  evidence image, TTS route, disconnect, and recovery.

The standalone `display-webapp/` remains a browser-based query demo for
Meta Ray-Ban Display. It is not used for camera or microphone capture because
those capabilities are provided by DAT.


## Quick actions aligned with the app (2026-11-01)

The native Display home offers Search and Capture photo or video. Search opens
**Search object / Search person / Voice command**. Both photo buttons open the
same camera with a still-photo action and never open a Register session or
create a publication; only the sense differs. Object uses the existing
ephemeral `/queries/image` service; person runs the existing consent-gated
1:N `faces/search` arm over the same probe bytes. Every match carries its
probe box, so group photos open a marked card (`display/face-group-links`,
numbered color boxes, ephemeral signed URL) with a numbered list (name,
similarity, color name) and each candidate keeps its enrolled match thumbnail
(signed `face_enrollment` URL) behind See match photos. Voice
classifies the request with the existing `search/route` service: person
descriptions run `profiles/search` and show the answer with matched names,
objects and ambiguous text run the gallery query, and greetings stay in chat;
guests remain blocked from people search, as in the app. Its source remains
configurable on the phone (**In the app** or **By location**), with app
gallery as the default.
Gallery results use confidence ordering, short-lived authorized images,
last-seen date, visual confidence and an explicit partial/simulated label.

Face numbers sit outside all face regions; crowded images use a reserved label
band and thin outlines. Open profile in app opens the matched internal profile
on the phone, or a selector when several profiles match. Back preserves the
Display result. Profile access uses the existing authenticated server routes;
Facebook URLs are not used for this navigation.
Previous/next actions share one compact row; title, notes, replay and another
query live on the result actions screen.

The Android host downloads and validates signed result images before sending
bitmaps to DAT, so image decoding failures produce a retry action rather than
an empty result card. Each candidate visit requests a fresh authorized link.
The marked group image remains in memory only for the current search and up
to its link expiry; returning from match photos restores those pixels. Home,
a new search, disconnect and account changes discard the group image. Expired
group links offer a new person search. Image requests are cancelled on leaving
the result flow, and late responses cannot replace a newer screen. The native
profile overlay keeps the existing Display result mounted.

Capture opens the camera directly with **Take photo / Record video**. Taking
the photo or stopping the video (up to 120 seconds) sends it through the
existing publication-upload flow to the signed-in account's private Profile
(`audience=home`, no Work workspace). A previous group selection cannot redirect
a new capture. Group assignment and additional information belong in the app.
Physical glasses and Debug phone preview share this flow. Duplicate replacement
still requires confirmation, and failed uploads retain the original for retry.
Previously pending uploads retain their original destination for recovery.
The location Register implementation remains available independently of this
glasses capture entry point.

### Phone camera, navigation and device selection

The host selects an eligible physical Display first, excluding all mock IDs
created by its controller, including IDs from previous renderer generations.
It pins the source to the selected session: physical glasses use DAT sensors;
Mock Device Kit uses CameraX and Android speech recognition, even when the
virtual device was selected automatically. A supplied device identifier alone
does not determine the sensor route. Disconnect resets the local route; no
camera, microphone or upload restarts automatically.

Opening the phone camera keeps the top bar, bottom navigation and menus
available. Search by photo has only a close X at the upper right and a photo
button at the bottom center. Publication capture retains a video/stop control
above that photo button. The close X stays at the upper right. There are no
Retry/Back buttons over the viewfinder. A bounded opening indicator or error
message explains a missing image, and taking a photo/video requires actual
preview frames. Users can close with X and reopen to retry.

The native viewfinder has one stable surface and compares viewport geometry
by value, avoiding CameraX rebinds on equivalent layouts. Each camera entry
has a generation that invalidates late surface, stream and error callbacks.
Its native controls have explicit priority over the SDK renderer in Compose's
draw and touch order; hiding an Android view's pixels is insufficient to
guarantee touch delivery. X remains enabled during capture so cancellation
cannot leave the user trapped. A late CameraX completion deletes a photo that
was cancelled while it was being saved.

Search and Capture callbacks run on the Android main thread. A pending permission
or active operation produces visible feedback, and a retained publication opens
its review without discarding the original. Camera startup is bounded; its owner
releases the busy state even when the response generation changes. Instrumented
CI tests send pointer events through the official WebView bridge, exercise
permission/cancellation recovery and check CameraX frames using an emulated
camera. They do not establish physical phone or glasses validation.
The official Display renderer remains mounted, hidden and non-interactive
behind the camera; returning to results does not recreate it. Navigating away
or recreating the phone host releases local sensors without deleting an
already staged publication or cancelling its upload.

The Debug touch regression runs on Robolectric with Compose pointer injection
against the production viewfinder, including a consuming transparent Android
renderer above it in composition order. It covers photo, video/stop, X during
opening and busy capture, and touch return to the SDK after closing. These
JVM UI tests do not validate camera hardware, microphone or the actual DAT WebView.

The Android host shows a local capture preview, processing, duplicate review
and retry controls. Private pending originals and stable request keys survive
restarts and network failures; reconnect never starts another capture.
Responses from disconnected sessions or previous accounts are invalidated.
Logging out releases sensors and clears visible results, while pending files
remain scoped to their account for recovery. Debug preview still simulates
only hardware, and Release excludes Mock Device Kit.

Validation: backend and Android unit tests plus Debug/Release APK builds run
on this host. Hardware-free browser inspection uses fixture content in the
SDK's official web renderer; this does not validate the APK or touch input.
No Android emulator/system image is installed on this host. Touch interaction,
Bluetooth audio, camera/microphone and physical Display QA remain pending.
