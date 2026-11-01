# RealityOS DAT host

This Android app is the secure host for the official Meta Wearables Device
Access Toolkit. With compatible Meta Ray-Ban Display glasses, Register and
Query are rendered on the glasses. In the Debug optical preview, those same
Display actions use the phone camera, microphone, speaker and speech service.

The phone experience is English-first and has a short first-run RealityOS
introduction. **About RealityOS** replays that introduction directly. One
shared host shell now owns navigation:

- The social bottom bar has exactly **Profile**, **Work** and **Search**.
  Profile is the default home and includes the account's newest-first media;
  voice and photo input live inside Search rather than in navigation.
- The left swipe drawer contains Profile, Meta Ray-Ban Display, Idooma, About
  and Settings, with a bottom-pinned sign out action. Gallery is not duplicated.
- **Meta Ray-Ban Display** combines preview and physical-glasses controls with
  its own Preview / Glasses / Controls bottom bar. The left drawer owns the
  horizontal edge gesture; the right diagnostic panel opens only from Controls.
- **Settings** automatically obtains and encrypts the project Live device
  profile and permits an administrator-supplied HTTPS device profile.
- **Profile** exposes the authenticated public profile while keeping the one
  current CV private; uploading a new PDF/DOCX replaces the old CV and its AI
  context. No Model API key is ever stored in the app.

## Build

```bash
cd android
ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk ./gradlew :app:assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

Every successful GitHub Actions **CI** run also retains that installable Debug
APK for 14 days as `realityos-android-debug-apk`. This is the artifact to use
for phone and virtual-glasses validation; the Release artifact is unsigned
until a production signing key is configured outside the repository.

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

1. Start the Live RealityOS deployment at `https://realityos.luxisoft.com/v1`.
   The virtual-glasses route refuses to issue a profile unless the server is in
   `META_MODE=live`; captured media is therefore processed by the real Meta
   integration, not a synthetic provider.
2. On a fresh Debug APK install, complete or skip the short RealityOS
   introduction. The host requests and securely saves a short-lived,
   workspace-scoped virtual-device identity automatically. Use **Settings →
   Use a custom server** only when an administrator issues different values.
3. Install the Debug APK on an Android phone:

   ```bash
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```

4. Keep **Display preview** open, choose **In app**, and tap **Start virtual
   glasses**. Meta's square renderer for `META_RAYBAN_DISPLAY` is contained
   inside a Debug-only panoramic Ray-Ban shell; the supplied artwork keeps its
   camera on the right and does not mirror or stretch the renderer. This
   phone-only visual treatment is not a physical-glasses optics validation.
5. From the renderer, use **Register** or **Find an object**. The preview asks
   Android for `CAMERA` when opening capture and `RECORD_AUDIO` for video or
   voice search. Photo/video use CameraX; video includes real phone microphone
   audio, search uses Android speech recognition, and answers use TTS on the
   active phone/Bluetooth audio route.

The Debug visual shell is still not physical-glasses validation. Its phone
photos and video are nevertheless uploaded to the real RealityOS API only
after an explicit Register action.

### Chrome preview

Choose **Chrome** in **Display preview**, connect the phone by USB with Android
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

The API base URL is not editable in the app. It resolves at build time from
the `REALITYOS_API_BASE_URL` environment variable, then the
`realityosApiBaseUrl` Gradle property, defaulting to the production host.

## Device workflow

1. For virtual glasses, the host automatically saves its short-lived live
   profile. For a physical device, an administrator enrolls the device key
   out of band; the app no longer exposes connection settings.
2. Pair Meta Ray-Ban Display with the phone, enable Meta AI Developer Mode,
   then use **Register with Meta AI** and grant required DAT permissions.
3. Use **Connect Display** once. The home, location, capture, voice-query, and
   evidence screens are subsequently delivered to the glasses.

For a Debug virtual-device test, no paired physical glasses are required: use
Developer Preview instead of **Connect Display**.

Phone preview uses CameraX photo/video and Android speech recognition. Physical
glasses use DAT in-stream photos, HEVC + PCM/AAC MP4 and `mwdat-speech`; answer
audio uses Android TTS on the active Bluetooth route. Physical-device
validation is still required for all wearable hardware capabilities.


## Información del recurso en Buscar

Al abrir un resultado del chat, el panel de información aparece desplegado.
La flecha permite plegarlo; tocar el texto o desplazarse no cambia ese estado.
Las miniaturas quedan encima de la fila de fecha de publicación y confianza
visual. El título y las notas se muestran debajo. El panel ocupa como máximo
el 45 % de la altura, con desplazamiento para contenido largo, y reserva su
espacio para mantener la imagen completa y señalizada visible.

Los textos, incluidas las notas, se presentan en el idioma elegido en Idioma
(español o inglés). Ambos idiomas quedan preparados y guardados al publicar y
viajan con los resultados y el historial. Abrir el visor utiliza ese mapa de
textos directamente. Para mensajes antiguos, una consulta corta recupera de
la base de datos lo ya preparado; no llama al modelo ni inicia traducciones.
La carga tiene un límite y ofrece información pendiente/error con reintento,
sin sustituir silenciosamente español por inglés. Las imágenes y las etiquetas
canónicas que generan los recuadros permanecen iguales. Los resultados del chat,
miniaturas y carrusel siguen ordenados por confianza visual descendente.


El historial se refresca al volver a Buscar y al cambiar de idioma, incluso si
la lista ya está cargada. Se actualizan los recursos existentes conservando los
identificadores y mensajes pendientes. Los registros de imágenes antiguos se
recuperan desde evidencia señalizada existente. Si falta una traducción, el
visor inicia su preparación explícita, la guarda y muestra el resultado en la
misma apertura; un estado visible y un límite de espera evitan carga indefinida.


## Meta Display quick actions (2026-11-01)

The glasses home offers Search and Capture photo or video. Search opens
Photo / Voice command; photo queries use the existing ephemeral image service,
while voice keeps its configured search source. Capture opens the camera
directly. Taking a photo or stopping a video sends it to the signed-in account's
private Profile without a group or metadata form. Organize it later in the app.
Processing, duplicate confirmation and safe retries use the existing upload
service. Original pending files remain account-scoped across reconnect/restart,
and older pending uploads keep their saved destinations. The Debug optical
preview uses the same flow; only its sensors and Display transport are virtual.
See `docs/WEARABLES.md` for operation and remaining hardware QA.

The simulator uses the phone's real CameraX camera and Android speech service.
Only an eligible physical Display selects glasses sensors; automatic selection
of a virtual Display still uses the phone. Camera screens retain the host's
navigation and menus. Search shows X at the upper right and photo at the bottom;
Capture also retains video/stop above photo. Retry/Back overlays are removed.
Closing or navigating away releases sensors, and late callbacks cannot reopen
or fail a newer camera entry. The Debug APK still requires handset camera/audio
QA; compiling it is not proof of sensor or physical-glasses operation.

The phone viewfinder explicitly wins touch dispatch over transparent SDK layers,
and X remains enabled during capture. The Compose/Robolectric regression injects
pointer events (not semantic clicks) into the production photo/video/X controls:

```bash
ANDROID_HOME=/opt/android-sdk ANDROID_SDK_ROOT=/opt/android-sdk \
  ./gradlew :app:testDebugUnitTest --tests com.luxisoft.realityos.PhoneCaptureTouchTest
```

These local UI tests use substitute Android views for the sensors and renderer;
phone camera/audio and physical-glasses QA remain separate.
