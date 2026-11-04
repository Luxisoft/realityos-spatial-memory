[EN](../../en/testing/VIDEO_EVALUATION.md) · [RealityOS](../README.md) · [Postman](../api/POSTMAN.md)

# Evaluación local de videos

Policía y Meta Social Media contienen tres publicaciones ordinarias de video cada uno. Sus seis originales MP4 se instalan mediante el cargador SQL compartido y se guardan en PostgreSQL BYTEA. Fuentes, licencias y hashes SHA-256 figuran en el [manifiesto de medios](../../../simulator/media/manifest.csv); la [guía local](../guides/DEMO.md#video) enumera las grabaciones.

Usa una cuenta autorizada del grupo seleccionado. Abre su galería, reproduce cada video, desplázate dentro del original y descarga sus bytes. Repite la descarga con una petición de rango de bytes y confirma intervalo y longitud recibidos. Una cuenta ajena al grupo no debe obtener el medio. La cobertura automática está en [las pruebas de video](../../../tests/test_local_videos.py).

Postman ofrece peticiones de galería, medios y consultas derivadas de la BD en **Localhost requests → 00 Local scenarios → Police / Meta Social Media**. Inicia primero los cuatro servicios locales. La selección usa cuentas locales sin contraseñas publicadas; Server requests permanece desactivado.

Las seis grabaciones no tienen una matriz revisada de objetos e intervalos. Se retiraron los videos de Memory y sus peticiones QA específicas. No declares detecciones, calidad de localización ni intervalos esperados sin revisar la fuente y la evidencia devuelta. Las consultas reales a Meta requieren la clave local privada y la indexación terminada; sus resultados necesitan una validación registrada aparte.

Las consultas no crean capturas de Register. «Última vez visto» describe evidencia registrada, no ubicación actual. Cada coincidencia de galería debe respetar el grupo seleccionado; las referencias sociales privadas nunca deben convertirse en evidencia de galería.

Regenera las peticiones públicas desde la base canónica con `.venv/bin/python scripts/build_api_docs.py` y ejecuta `make docs-check`. La generación utiliza SQLite aislado en memoria; no lee una instalación activa ni llama proveedores. Las pruebas de reproducción y documentación no sustituyen la aceptación en Android/gafas reales o con modelos reales.
