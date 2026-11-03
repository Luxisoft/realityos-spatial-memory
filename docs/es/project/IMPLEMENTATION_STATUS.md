[English](../../en/project/IMPLEMENTATION_STATUS.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Estado vigente de implementación

Actualizado el **3 de noviembre de 2026**. Un build o una comprobación HTTP no aprueba pruebas físicas. Las entregas anteriores permanecen en Git.

## Implementado

| Área | Comportamiento vigente |
| --- | --- |
| Android | Indicadores de carga/buffering, información expandida, skeleton inicial de datos, paneles/insets corregidos, administración de grupo a pantalla completa, compartir invitación y alertas inferiores con cierre. |
| Grupos | Publicar exige pertenencia. Las publicaciones propias se pueden copiar a varios grupos, con reacciones/comentarios independientes; las antiguas sin grupo quedan solo para su propietario. |
| Biometría | Se mantienen consentimiento y búsqueda facial aislada. El ingreso por email solicita foto de perfil/avatar y 3–25 referencias privadas aceptadas, con continuación y nueva selección. Los originales y URLs de referencias Meta no aparecen en galerías ni miniaturas de candidatos de cuenta. |
| Almacenamiento | R2/S3 editable, miniaturas a la derecha, destino por grupo, sincronización inmediata/cada 15 minutos, reconciliación tras recorrido completo y retiro de copias importadas/compartidas protegido por revisión. Los objetos remotos se conservan. |
| Evidencia | Originales BYTEA, proveedor real, evidencia versionada y traducciones. Consultar no inicia capturas ni inventa observaciones. |
| Expedientes y voz | Se conservan expedientes versionados y comparación clínica; transcripción Muse y síntesis ElevenLabs autenticada. |

## Entrega verificada

- Imagen local: `realityos-backend:workspace-privacy-20261103`; API, worker y scheduler usan el runtime conservado. PostgreSQL está en **`20261103_0036`**. Actualización → reversión → actualización aprobadas sobre un esquema PostgreSQL temporal; actualización productiva, salud y comparación exacta de OpenAPI público aprobadas.
- La suite backend/gateway contiene **499 pruebas**. La revisión final dirigida aprobó **13 pruebas**, incluidos contrato corregido, pérdida de membresía y privacidad de referencias. Android aprobó **226 pruebas**, formato/lint y builds Debug/Release. Documentación, estructura y Postman validados.
- APK instalable: `android/app/build/outputs/apk/debug/app-debug.apk`; SHA-256 `e835a29b0d38bc47f03266f728921980ce0355c2fa4da89db3449e3a99483395`.
- Rollback de imagen: `.runtime/workspace-privacy-20261103-rollback.json`. Diario de visibilidad demo: `.runtime/real-scenes-20261103-visibility.json`. El snapshot técnico `pre-workspace-privacy-20261103.dump` caduca mediante mantenimiento tras 24 horas, o una bajo presión de disco; no es un respaldo oficial y no se envió a R2.
- Producción conserva Meta directo con gateway de respaldo, claves privadas y la excepción aislada de ingreso Windows/Debug. El mantenimiento protege imágenes activas y rollback.
- [Comprobante de API real](../../assets/storage/workspace-privacy-verification.json): las tres cuentas de jurados accedieron, descargaron avatar y media nueva, consultaron expedientes y exploraron su bucket por autor. Las consultas a otro grupo devolvieron `403`; publicar en privado devolvió `422`.

## Datos vigentes de evaluación

El alcance se limita a los grupos **existentes**. No se recrean el taller ni otros escenarios descartados. Los tres grupos de evaluación tienen **48 escenas con licencia: 12 fotos y cuatro videos con movimiento por grupo**. Los videos duran 10–15 segundos, a 24 fps y al menos 720p, con comprobación de cambio entre fotogramas decodificados. El [catálogo y manifiesto de fuentes/licencias/hashes](../../../simulator/real-scenes/manifest.json) describe los recursos; las descargas quedan fuera de Git. El análisis real usa la cola del worker existente.

Se conservan **47 expedientes, 27 adjuntos y seis retratos de expediente enrolados**. La renovación no añadió grupos ni membresías. El inventario vigente del bucket contiene 48 escenas y seis recursos QA, verificados por lectura remota/SHA-256, con **13 conexiones activas**. Cada autor tiene un subconjunto distinto. La conexión obsoleta de exploración del directorio social quedó desactivada; sus objetos remotos se conservaron.

Postman mantiene exactamente **Server requests** y **Localhost requests**, con **403 solicitudes**, incluidos los **39 recorridos sobre datos existentes**. Los IDs de publicaciones del jurado apuntan al contenido renovado. Solo las tres contraseñas autorizadas por el propietario son públicas. Las cuentas por email, incluidas las de prueba sin configuración completa, reciben el nuevo ingreso biométrico privado; no se inventó consentimiento ni enrolamiento completado.

<a id="next-steps"></a>

## Aceptación pendiente

| Pendiente | Evidencia necesaria |
| --- | --- |
| UI en teléfono | Teclado físico, insets de navegación Android, gestos sobre cámara y checklist completo con el APK identificado. No hubo dispositivo conectado en esta sesión. |
| Integraciones externas | Login/importación Facebook Live, DAT/gafas físicas, correo real e instalación Windows completa necesitan recorridos propios registrados. Las pruebas unitarias no los aprueban. |
| Base vacía | Se detectó un problema previo del baseline histórico: `0001` carga modelos actuales y el arranque SQLite desde cero falla por una clave foránea de publicaciones sin resolver. La actualización y reversión sobre esquema PostgreSQL existente aprobaron. No se declara aprobada una instalación Windows nueva. |
| Terceros y entrega | Siguen pendientes términos DAT autenticados, constancia de derechos de `buffalo_l` y grabación/recibo final, según [Terceros](THIRD_PARTY.md) y [Hackathon](HACKATHON.md). |

Este informe excluye credenciales privadas, tokens y media personal. La aceptación manual completa requiere evidencia de todos los casos del checklist.
