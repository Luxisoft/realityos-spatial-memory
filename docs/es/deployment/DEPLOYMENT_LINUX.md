[English](../../en/deployment/DEPLOYMENT_LINUX.md) · [Windows](../README.md)

<a id="linux-server"></a>

# Evaluación privada en un servidor Linux

Ejecuta los mismos **cuatro servicios y escenarios preparados** en un servidor Linux x64. La API permanece en `127.0.0.1:8080` del servidor; tu computadora se conecta mediante SSH. No necesitas dominio ni un endpoint HTTPS público. Mantén privado el puerto 8080: el selector de cuentas de evaluación no utiliza contraseñas.

**1. Prepara el servidor.** Usa al menos 4 CPU, 8 GiB de RAM y 25 GiB libres para Docker. Instala Git, [Git LFS](https://git-lfs.com/), curl, [Docker Engine y el plugin de Compose](https://docs.docker.com/engine/install/ubuntu/), e inicia Docker. Conéctate con tu propia cuenta SSH; sustituye `deploy@YOUR_SERVER` en toda esta sección:

```bash
ssh deploy@YOUR_SERVER
uname -m
docker info
docker compose version
```

Debes obtener `x86_64`, un motor Linux que responda y Compose. Los comandos Docker deben funcionar desde esa cuenta. Ejecuta los siguientes comandos del servidor **dentro de esa sesión SSH**.

**2. Descarga e inicia RealityOS.** Usa un checkout separado para esta evaluación:

```bash
git lfs install &&
git clone https://github.com/Luxisoft/realityos-spatial-memory.git &&
cd realityos-spatial-memory &&
bash scripts/local/start.sh
```

Introduce tu clave Meta cuando se solicite. El instalador crea un `.env.local` privado en el servidor, genera los secretos internos y prepara una sola vez los tres grupos y nueve cuentas. Reiniciar conserva la configuración local existente y los datos. PostgreSQL y Redis permanecen internos; Android usa sus voces instaladas sin conexión.

**3. Verifica en el servidor.** Espera a que termine la instalación y ejecuta:

```bash
curl --fail --silent --show-error http://127.0.0.1:8080/health/ready
curl --fail --silent --show-error http://127.0.0.1:8080/v1/openapi.json -o /dev/null
bash scripts/local/test.sh
```

El diagnóstico comprueba servicios, disponibilidad de modelos y cuentas locales. La indexación puede continuar después del arranque; espera a que termine antes de buscar la evidencia preparada.

**4. Conecta desde tu computadora.** Abre otra terminal **en tu computadora**, asegúrate de que su puerto 8080 esté libre y mantén activo este [túnel SSH](https://man.openbsd.org/ssh#L):

```bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8080:127.0.0.1:8080 deploy@YOUR_SERVER
```

Abre [http://localhost:8080/docs](http://localhost:8080/docs) en tu computadora. Postman usa **Localhost requests** a través del túnel; deja **Server requests** desactivado. Si tu computadora ya ejecuta RealityOS localmente, detén primero esa instancia para liberar su puerto 8080.

**5. Conecta Android.** Con el túnel abierto y el teléfono conectado por USB a tu computadora, instala el [APK Debug local](../README.md#android) y ejecuta en Git Bash en tu computadora Windows:

```bash
/c/platform-tools/adb.exe reverse tcp:8080 tcp:8080
```

La app conserva `http://localhost:8080/v1` y llega al servidor a través de tu computadora. Elige una de las nueve cuentas. Repite `adb reverse` después de reconectar el teléfono. Cerrar el túnel desconecta los clientes, pero deja el servidor funcionando.

**6. Detén o reanuda.** Dentro del checkout del servidor, usa `bash scripts/local/stop.sh` para detener y `bash scripts/local/start.sh` para reanudar. Detener conserva los datos. No elimines volúmenes ni uses `down -v` salvo que quieras borrar los datos de evaluación.

Estos pasos reutilizan el instalador Linux existente. El recorrido SSH/USB debe comprobarse en tu servidor y teléfono; este cambio de documentación no despliega un servidor.

## Actualizaciones y salida de consola

Desde el checkout del servidor:

```bash
git pull --ff-only &&
git lfs pull &&
bash scripts/local/start.sh
```

Los comandos de inicio, diagnóstico y parada muestran progreso por etapas en inglés, resúmenes, advertencias, errores y confirmaciones. La primera ejecución descarga dependencias; una etapa larga puede mantener el porcentaje mientras trabaja. El 100 % indica que terminó el comando; la indexación puede continuar en segundo plano. Reiniciar conserva cambios y eliminaciones. Mantén privado `.env.local`.

Para actualizar el teléfono, repite la actualización e instalación del [README Windows](../README.md#android), manteniendo abierto el túnel.

**Postman:** importa la [colección](../../postman/RealityOS.postman_collection.json) y usa **No environment → Localhost requests → 00 Quick start**. Para escribir, activa `enable_write_requests=true`; deja **Server requests** desactivado.

## Uso en una computadora Linux

Si ejecutas el backend en tu propia computadora Linux, realiza los pasos 1–3 en su terminal local y omite SSH. Inicia Docker Engine antes de `bash scripts/local/start.sh`; usa `bash scripts/local/test.sh` para diagnosticar y `bash scripts/local/stop.sh` para detener conservando los datos.

## Compilar Android en Linux

Para desarrollo, instala JDK 21 y Android SDK 36 con Build-Tools 36.0.0. Configura `JAVA_HOME` y `ANDROID_HOME`. Desde la raíz del repositorio:

```bash
REALITYOS_API_BASE_URL=http://localhost:8080/v1 ./android/gradlew -p android -PlocalDevelopment=true :app:assembleDebug
```

Espera a `BUILD SUCCESSFUL`. El APK reemplaza `android/app/build/outputs/apk/debug/app-debug.apk`. Usa la misma clave de firma del servidor para publicar actualizaciones mediante Git LFS.
