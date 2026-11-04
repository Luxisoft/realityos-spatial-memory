[English](../../en/api/API.md) · [RealityOS](../README.md)

# API / Postman

La API existente se ejecuta dentro de Docker local. La colección refleja las rutas habilitadas de localhost y conserva el catálogo histórico de servidor desactivado.

<a id="quick-start"></a>

## Import → Send

1. Inicia la [instalación local](../deployment/DEPLOYMENT_LOCALHOST.md).
2. Importa la [colección](../../postman/RealityOS.postman_collection.json) y selecciona **No environment**.
3. Abre **Localhost requests → 00 Quick start** o **00 Local scenarios → Police / Meta Social Media**.
4. Pulsa **Send**. El selector de cuenta obtiene tokens reales; la renovación es automática. No necesitas contraseñas.

`localhost_user_id` elige la cuenta del inicio rápido. Los escenarios tienen sus propios prefijos `security_` y `meta_social_`, IDs y sesiones. Los seis usuarios disponibles se consultan en `GET /v1/auth/local-accounts`; `POST /v1/auth/local-select` recibe `{"user_id":"..."}`. Estas rutas no existen en producción. No conceden permisos entre grupos ni consentimiento biométrico.

La primera preparación carga recursos locales y el worker los indexa con tu clave Meta. Los 48 controles bilingües de video requieren que la indexación termine. No contienen resultados IA precalculados.

**Server requests está desactivado** por un script que evita enviar peticiones. No incluye endpoint ni contraseñas. Localhost excluye buckets, Facebook, integraciones remotas, SMTP y TTS remoto. El [contrato local](../../../tests/contracts/openapi.local.json) se comprueba contra las rutas reales; el [contrato histórico](../../../tests/contracts/openapi.json) permanece separado.

Las escrituras requieren `enable_write_requests=true` con el prefijo correspondiente. Usa los IDs de recursos autorizados y selecciona archivos para multipart. Crear publicaciones requiere grupo, categoría y etiquetas. Consulta los ejemplos del catálogo para editar perfiles, publicar, borrar y consultar. Un error de autenticación detiene la petición: no se registra como éxito.

El [entorno local opcional](../../postman/RealityOS.local.postman_environment.json) no contiene secretos. Mantén la clave Meta solo en `.env.local`, nunca en Postman ni en el APK. Los tokens se obtienen al ejecutar y no se exportan.

Swagger: `http://localhost:8080/docs`. OpenAPI: `http://localhost:8080/v1/openapi.json`. [Referencia generada](API_REFERENCE.md) · [Datos y expedientes](../guides/WORKSPACE_DATA.md) · [Escenarios](../guides/DEMO.md#access).
