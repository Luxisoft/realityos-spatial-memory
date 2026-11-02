# RealityOS en Windows con Docker: alternativa local real

Esta instalación funciona en tu computadora y conserva su propia base de datos,
usuarios, fotos, videos y modelos. Usa el proyecto Docker `realityos-local`,
archivo `.env.local` e imágenes/volúmenes independientes. No necesita acceder al
servidor RealityOS ni a FRONTEND, y sus comandos no modifican la instalación de
producción.

La IA es real: Muse Spark/SAM/transcripción se consultan en la API de Meta con tu
clave; ElevenLabs genera la voz con una clave propia e InsightFace corre localmente. No se cargan medios
sintéticos ni se ejecutan los scripts de seed. Las primeras pantallas están
vacías hasta que registres o publiques tus propios datos.

## Requisitos

- Windows x64 compatible con Docker Desktop, contenedores Linux y WSL2.
- Git y PowerShell de Windows 5.1 o PowerShell 7. Python y Node no son necesarios
  para arrancar el sistema: se construyen dentro de Docker.
- Internet para descargar imágenes/modelos y consultar la API de Meta; una clave
  propia con `muse-spark-1.3`, `sam-3.1` y `muse-voice-transcribe-1.0` habilitados.
- Una clave propia de ElevenLabs para generar audio; se introduce sin mostrarse.
- Al menos cuatro CPU, 8 GiB de RAM asignados a Docker y 25 GiB libres para
  imágenes y datos locales. No se exige GPU ni instrucciones BF16 para voz;
  no se descarga ni ejecuta un modelo local de síntesis.

Configura Docker Desktop antes de empezar. El motor debe ser **Linux / WSL2**;
no sirve el modo Windows containers. Consulta los [requisitos oficiales de
Docker](https://docs.docker.com/desktop/setup/install/windows-install/) y
[configuración WSL2](https://docs.docker.com/desktop/features/wsl/).

## Primer arranque

Clona el repositorio o entra en una copia a la que tengas acceso. Desde PowerShell,
en la raíz del proyecto, ejecuta:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1
```

`ExecutionPolicy Bypass` aplica solo a ese proceso; no cambia la política global.
También puedes ejecutar el archivo directamente si tu política ya lo permite.

El comando crea `.env.local` desde `.env.local.example`, solicita tus claves Meta y ElevenLabs,
correo y contraseña local (mínimo 12 caracteres) y genera secretos independientes
para PostgreSQL, JWT y dispositivos. La clave y contraseña se introducen sin
mostrarse. El archivo se protege para tu usuario de Windows y SYSTEM, y no entra
en Git ni en las imágenes Docker.

Si moviste los datos de Docker a otra unidad, indícala para comprobar espacio:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1 -DockerDataDrive 'D:\'
```

El arranque verifica recursos y acceso real a Meta, construye las imágenes,
aplica migraciones, crea tu cuenta y un espacio de trabajo vacío, y espera salud
de API y voz. Comprueba audio real EN/ES sin publicar ni guardar esas muestras.
La primera descarga puede tardar; los siguientes arranques reutilizan los modelos.
Si falla una credencial, recurso o modelo, el comando muestra el problema y no
anuncia que todo está listo.

| Aplicación | Dirección por defecto |
| --- | --- |
| Panel | `http://localhost:8080` |
| Display web | `http://localhost:8080/display/` |
| Contrato API | `http://localhost:8080/v1/openapi.json` |
| Salud | `http://localhost:8080/health/ready` |

Entra con el correo y contraseña que elegiste. Son una cuenta real en tu base
local; no una identidad Facebook inventada. No se pide reconocimiento facial
para entrar con ella. No se registran consentimientos ni capturas faciales
automáticamente. Las funciones faciales mantienen sus permisos/consentimientos
cuando se solicitan expresamente.

## Configuración y reinicios

Las opciones locales están exclusivamente en `.env.local`:

```dotenv
ENVIRONMENT=local
LOCAL_LOGIN_ENABLED=true
META_MODE=live
FACE_ENGINE=insightface
META_CONNECTION_MODE=direct
META_GATEWAY_FALLBACK_ENABLED=false
ELEVENLABS_API_KEY=<clave-propia>
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
```

La generación de voz consulta ElevenLabs solo al solicitar audio. El gateway
no es una dependencia local. No copies el `.env` del servidor ni sus claves.
Las variables exportadas en PowerShell no sobrescriben las del archivo local.
Los contextos Docker remotos se rechazan para evitar actuar sobre otro equipo.

Para volver a arrancar usa el mismo comando. No se reemplazan cuentas,
contraseñas ni datos existentes. Si cambiaste la contraseña de la cuenta en la
base, actualiza su valor local; el arranque no la restablece silenciosamente.

Para revisar servicios y proveedores:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Test-RealityOS.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Test-RealityOS.ps1 -Speech
```

Para detener sin borrar datos ni modelos:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Stop-RealityOS.ps1
```

No uses `down -v` si quieres conservar los datos. Para revisar errores de voz:

```powershell
docker compose --project-name realityos-local --env-file .env.local --file infrastructure/docker-compose.local.yml logs --tail 50 api
```

Si el puerto 8080 ya está ocupado, cambia `LOCAL_HTTP_PORT` en `.env.local` y usa
ese mismo puerto en las URLs y en la conexión Android. PostgreSQL y Redis no se publican en Windows.

## Android local, sin Facebook ni reconocimiento facial al entrar

Para usar Android necesitas además un SDK Android 36, Java 21, ADB y un teléfono
con depuración USB, o un emulador para pruebas de interfaz. Android Studio puede
instalar esos componentes. El APK local se instala como otra aplicación
(`com.luxisoft.realityos.local`) y no reemplaza la habitual.

Desde la raíz:

```powershell
$env:ANDROID_HOME = 'C:\ruta\a\Android\Sdk'
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
Set-Location android
.\gradlew.bat -PlocalDevelopment=true -PrealityosApiBaseUrl=http://localhost:8080/v1 :app:assembleDebug
adb reverse tcp:8080 tcp:8080
adb install -r app\build\outputs\apk\debug\app-debug.apk
```

Ajusta la ruta SDK y el puerto si corresponde. El APK se genera siempre en la
ruta habitual; no se crean copias adicionales. `adb reverse` conecta el localhost
del teléfono/emulador con el de Windows, según la [documentación Android](https://developer.android.com/develop/ui/views/layout/webapps/access-local-server).
Vuelve a ejecutar el comando al reconectar USB. Un error de ADB normalmente
requiere confirmar depuración en el teléfono o seleccionar el dispositivo con
`adb -s <serial>`.

La app local muestra correo/contraseña y usa la cuenta que creaste. Solo ese
Debug local, confirmado por el backend local, omite la verificación facial de
entrada. Las sesiones se separan por aplicación/servidor. La app normal y Release
conservan su acceso habitual; Release nunca acepta este modo ni HTTP local.
No se inicia automáticamente un dispositivo virtual ni una sesión de simulación.
La cámara y el micrófono del teléfono procesan datos reales. Las gafas físicas
requieren hardware y configuración Meta/DAT propios; Docker no los sustituye.

La integración Facebook, si quieres probar importación y datos de Facebook,
requiere tu propia aplicación, permisos, cuenta y configuración Android real.
La cuenta local no fabrica ni sustituye esos datos externos.

## Validación y límites

Los tests automáticos emplean dobles únicamente dentro de sus pruebas. El perfil
de ejecución local exige motores reales y no tiene fallback a modo mock.
La validación de PowerShell en Windows se ejecuta en CI; probar sus scripts no
equivale a una prueba integral de Docker Desktop, cámara o gafas. El diagnóstico
anterior comprueba los proveedores reales en la máquina donde lo ejecutes.
