[English](../../en/deployment/DEPLOYMENT_LOCALHOST.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Instalación local: Windows y Linux

Docker ejecuta cuatro servicios en tu computadora: PostgreSQL (base de datos), Redis (cola de tareas), API y worker. La API está disponible en `127.0.0.1:8080`.

## Requisitos

- Windows x64 con Docker Desktop, contenedores Linux y WSL2; o Linux x64 con Docker Engine y Compose. Esta instalación no admite macOS.
- Al menos 4 CPU, 8 GiB de RAM y 25 GiB libres para Docker. La primera construcción descarga dependencias y pesos de InsightFace.
- Android 12+ y Android Platform Tools (`adb`), cable USB y depuración USB. Las gafas son opcionales para capturar con el teléfono y consultar evidencia guardada.
- Conexión a internet y tu `MODEL_API_KEY` de Meta con acceso a Muse Spark, SAM y Muse Voice Transcribe.

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

Descarga **[app-debug.apk](https://github.com/Luxisoft/realityos-spatial-memory/releases/download/local-evaluation/app-debug.apk)** de la publicación pública de GitHub (sin iniciar sesión). Para instalarlo basta Platform Tools. Para compilarlo, usa **JDK 21 LTS** (la versión de CI) y Android SDK 36. [Configuración de Java en Windows](#java-windows).

Linux:

```bash
cd android
./gradlew :app:assembleDebug
```

Windows PowerShell:

```powershell
cd android
.\gradlew.bat :app:assembleDebug
```

El resultado único es `android/app/build/outputs/apk/debug/app-debug.apk`. Debug usa por defecto `com.luxisoft.realityos.local` y `http://localhost:8080/v1`.

Conecta el teléfono, acepta la depuración y ejecuta desde la raíz:

```bash
adb reverse tcp:8080 tcp:8080
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

Si descargaste el APK, indica su ruta. Repite `adb reverse` después de reconectar. Sin ese túnel, localhost en Android apunta al teléfono, no a tu computadora. No hace falta exponer un puerto a la red local.

Abre RealityOS y elige una de las nueve cuentas agrupadas por escenario. Cambiar de usuario conserva los permisos y el aislamiento entre grupos. El ingreso local no enrola un rostro ni concede consentimiento biométrico.

La respuesta hablada usa una voz ES/EN instalada sin conexión en Android. Si falta, instala el idioma en los ajustes de texto a voz; la respuesta sigue visible como texto. La entrada de audio conserva la transcripción Meta. La clave Meta nunca va en el APK.

## Archivos y datos

Los recursos públicos iniciales están en `simulator/workspaces/assets/`, `simulator/workspaces/profile-photos/` y `simulator/real-scenes/assets/`, con sus manifiestos. Se incluyen en la imagen; no se descarga contenido privado de producción. Para agregar una foto o video, selecciónalo en Android y publícalo en un grupo con categoría y etiquetas. Editar, borrar, consultar y actualizar el perfil usan las operaciones actuales sobre PostgreSQL local.

Los originales se guardan como `BYTEA` en PostgreSQL o sus fragmentos ordenados existentes. Los datos y archivos quedan juntos en el volumen `realityos-local_postgres_data`. Redis conserva la cola en su propio volumen. Agrega publicaciones desde Android.

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

<a id="java-windows"></a>

## Java en Windows: corregir `JAVA_HOME`

Usa **JDK 21 LTS**, igual que la [compilación de CI](../../../.github/workflows/ci.yml). El [proyecto Android](../../../android/app/build.gradle.kts) genera bytecode Java/Kotlin 17; eso no cambia el JDK recomendado para compilar. [AGP 8.11 requiere como mínimo JDK 17](https://developer.android.com/build/releases/agp-8-11-0-release-notes#compatibility).

El aviso `JAVA_HOME is set to 'C:\Program Files\Java\jdk-23', but it does not contain a usable Java executable` indica que el editor no puede ejecutar Java desde esa ruta.

1. Instala [Eclipse Temurin JDK 21 LTS para Windows x64](https://adoptium.net/temurin/releases/?version=21&os=windows&arch=x64&package=jdk), paquete **JDK**, instalador MSI. Comprueba la carpeta exacta de instalación: debe contener `bin\java.exe` y `bin\javac.exe`.
2. En Windows, busca **Editar las variables de entorno del sistema** y abre **Variables de entorno**. Cambia `JAVA_HOME` a esa carpeta raíz del JDK, sin comillas y sin añadir `\bin`. Revisa las variables de usuario y de sistema para que ninguna conserve la ruta obsoleta. Si existe `JDK_HOME` con esa ruta vieja, corrígelo o elimínalo.
3. En `Path`, coloca `%JAVA_HOME%\bin` antes de otras entradas de Java y retira las entradas que apunten a instalaciones eliminadas.
4. Cierra completamente el editor y las terminales. Abre una nueva PowerShell y comprueba:

```powershell
$env:JAVA_HOME
Test-Path "$env:JAVA_HOME\bin\java.exe"
Test-Path "$env:JAVA_HOME\bin\javac.exe"
& "$env:JAVA_HOME\bin\java.exe" -version
java -version
javac -version
.\android\gradlew.bat --version
```

Los dos `Test-Path` deben devolver `True`; Java, javac y la JVM de Gradle deben mostrar la versión 21. Si `java -version` muestra otra, usa `where.exe java` para localizar la entrada que tiene prioridad en `Path`.

Si el editor mantiene el aviso, abre sus ajustes JSON de usuario y del proyecto. Elimina las referencias a la instalación vieja en `java.home` o `java.jdt.ls.java.home`. La [extensión Java actual para Windows x64](https://github.com/redhat-developer/vscode-java#java-tooling-jdk) incluye su propio runtime para el servidor de lenguaje; configura `java.import.gradle.java.home` con la ruta real del JDK 21 para compilar el proyecto. Si usas Android Studio, selecciona el mismo JDK 21 en **Settings → Build, Execution, Deployment → Build Tools → Gradle → Gradle JDK**.
