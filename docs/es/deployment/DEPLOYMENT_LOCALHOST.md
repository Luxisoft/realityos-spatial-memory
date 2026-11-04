[English](../../en/deployment/DEPLOYMENT_LOCALHOST.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Instalación local: Windows y Linux

Esta es la instalación principal para evaluar el proyecto. Docker ejecuta cuatro servicios en tu computadora: PostgreSQL (una sola base de datos de la aplicación), Redis (cola de tareas), la API existente y el worker existente. Solo se publica la API en `127.0.0.1:8080`. No requiere gateway, proxy, scheduler, buckets, login Facebook, SMTP ni ElevenLabs. La IA sigue usando internet y tu propia `MODEL_API_KEY` de Meta.

## Requisitos

- Windows x64 con Docker Desktop, contenedores Linux y WSL2; o Linux x64 con Docker Engine y Compose. Esta instalación no admite macOS.
- Al menos 4 CPU, 8 GiB de RAM y 25 GiB libres para Docker. La primera construcción descarga dependencias y pesos de InsightFace.
- Android 12+ y Android Platform Tools (`adb`), cable USB y depuración USB. Las gafas son opcionales para capturar con el teléfono y consultar evidencia guardada.
- Tu clave Meta con acceso a los modelos actuales de RealityOS: Muse Spark, SAM y Muse Voice Transcribe. No necesitas cuentas de otros proveedores para el recorrido local.

Clona o descarga el repositorio público. Ejecuta los comandos desde la raíz. No copies un `.env` de producción.

## 1. Descargar y preparar

1. Descarga el [ZIP del repositorio](https://github.com/Luxisoft/realityos-spatial-memory/archive/refs/heads/main.zip) y extráelo, o ejecuta `git clone https://github.com/Luxisoft/realityos-spatial-memory.git`. No necesitas iniciar sesión en GitHub.
2. Windows: instala [Docker Desktop x64](https://docs.docker.com/desktop/setup/install/windows-install/), activa WSL2/contenedores Linux y abre Docker Desktop. Linux: sigue la [instalación de Docker Engine](https://docs.docker.com/engine/install/) para tu distribución, incluyendo Compose. Comprueba que `docker info` y `docker compose version` funcionen en tu terminal.
3. Descarga [Android Platform Tools para tu sistema](https://developer.android.com/tools/releases/platform-tools), extráelo y añade su carpeta al PATH. Comprueba `adb version`.
4. Abre PowerShell o Bash dentro de la carpeta extraída `realityos-spatial-memory`. El resto se ejecuta en Docker: no instales Python, PostgreSQL ni Redis manualmente en el equipo.

## 2. Iniciar

Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1
```

Linux:

```bash
bash scripts/local/start.sh
```

El instalador crea `.env.local` desde `.env.local.example`, genera los secretos internos y pide tu clave Meta sin mostrarla. También puedes completar `MODEL_API_KEY` directamente en ese archivo privado. No publiques `.env.local`. Las contraseñas internas se generan en tu equipo; no se entregan credenciales por el README.

En el primer inicio se prepara el esquema y los escenarios. Las instalaciones existentes se actualizan conservando su base de datos. Una base no vacía sin versión se rechaza, sin sobrescribirla. La preparación inicial utiliza el esquema ORM vigente, los índices de búsqueda PostgreSQL y una versión Alembic fijada: la migración inicial histórica no reconstruye de forma fiable una base vacía. El instalador no modifica migraciones aplicadas ni archivos de ejecución de producción.

Se cargan **3 grupos, 9 usuarios, 47 expedientes, 27 adjuntos y 48 escenas de galería con licencia**, desde archivos existentes del repositorio. Los expedientes ficticios mantienen su marca de simulación; las escenas conservan fuente y licencia. No se inventan detecciones IA, consentimientos ni enrolamientos biométricos. El worker indexa con el procesamiento real existente de Meta. Las búsquedas se habilitan a medida que termina; los errores quedan visibles y se pueden reintentar mediante la acción habitual de indexación.

Reiniciar no vuelve a cargar los escenarios ni restaura lo eliminado. No ejecutes `down -v` salvo que quieras borrar expresamente la instalación local.

<a id="android"></a>

## 3. Android

Descarga **[app-debug.apk](https://github.com/Luxisoft/realityos-spatial-memory/releases/download/local-evaluation/app-debug.apk)** de la publicación pública de GitHub (sin iniciar sesión). Para instalarlo no necesitas Android Studio, Java ni el SDK completo; basta Platform Tools. Compilarlo es opcional y requiere Java 21 y Android SDK 36:

```bash
cd android
./gradlew :app:assembleDebug
```

En Windows usa `gradlew.bat`. El resultado único es `android/app/build/outputs/apk/debug/app-debug.apk`. Debug usa por defecto `com.luxisoft.realityos.local` y `http://localhost:8080/v1`.

Conecta el teléfono, acepta la depuración y ejecuta desde la raíz:

```bash
adb reverse tcp:8080 tcp:8080
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

Si descargaste el APK, indica su ruta. Repite `adb reverse` después de reconectar. Sin ese túnel, localhost en Android apunta al teléfono, no a tu computadora. No hace falta exponer un puerto a la red local.

Abre RealityOS y elige una de las nueve cuentas agrupadas por escenario. No hay contraseña ni login de Facebook. Cambiar de usuario conserva los permisos y el aislamiento entre grupos. El ingreso local no enrola un rostro ni concede consentimiento biométrico.

La respuesta hablada usa una voz ES/EN instalada sin conexión en Android. Si falta, instala el idioma en los ajustes de texto a voz; la respuesta sigue visible como texto. La entrada de audio conserva la transcripción Meta. La clave Meta nunca va en el APK.

## Archivos y datos

Los recursos públicos iniciales están en `simulator/workspaces/assets/`, `simulator/workspaces/profile-photos/` y `simulator/real-scenes/assets/`, con sus manifiestos. Se incluyen en la imagen; no se descarga contenido privado de producción. Para agregar una foto o video, selecciónalo en Android y publícalo en un grupo con categoría y etiquetas. Editar, borrar, consultar y actualizar el perfil usan las operaciones actuales sobre PostgreSQL local.

Los originales se guardan como `BYTEA` en PostgreSQL o sus fragmentos ordenados existentes. Los datos y archivos quedan juntos en el volumen `realityos-local_postgres_data`. Redis conserva la cola en su propio volumen. No hay observadores de carpetas, adaptadores, conexiones a buckets ni sincronización. Copiar un archivo nuevo a una carpeta de fixtures no lo publica automáticamente.

## Postman y diagnóstico

Importa [RealityOS.postman_collection.json](../../postman/RealityOS.postman_collection.json), selecciona **No environment** y abre **Localhost requests → 00 Quick start** o **00 Local scenarios**. La sesión se obtiene y renueva automáticamente mediante el selector local. **Server requests** conserva el catálogo histórico desactivado, sin endpoint ni contraseñas. Las escrituras requieren `enable_write_requests=true` del destino.

Windows:

```powershell
.\scripts\local\Test-RealityOS.ps1
.\scripts\local\Stop-RealityOS.ps1
```

Linux:

```bash
bash scripts/local/test.sh
bash scripts/local/stop.sh
```

Comprueba `http://localhost:8080/health/ready` y `http://localhost:8080/docs`. El diagnóstico consulta Meta con tu clave real. Detener conserva los datos. Si la clave falla, corrígela en el archivo privado y reinicia; no hay sustitución por modelos simulados. Consulta los logs de API/worker con el Compose local y evita publicar secretos o archivos personales en reportes.

La instalación Windows completa, el teléfono físico, las voces instaladas y el recorrido Meta real requieren su propia comprobación. Las pruebas automáticas no certifican esos resultados. Consulta el [estado verificado](../project/IMPLEMENTATION_STATUS.md).
