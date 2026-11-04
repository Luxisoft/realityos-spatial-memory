[English](../../en/testing/IMPLEMENTATION_CHECKLIST.md) · [Proyecto](../README.md) · [Láminas visuales](QA_VISUAL_FIXTURES.md) · [Instalación local](../guides/DEMO.md#access) · [Postman](../api/POSTMAN.md)

# Lista de aceptación local

Actualizada el 4 de noviembre de 2026 para la instalación local basada en SQL. Todos los casos manuales siguientes empiezan pendientes. Las comprobaciones automáticas y el hash del APK vigente figuran en [Estado de implementación](../project/IMPLEMENTATION_STATUS.md); no equivalen a aceptación en dispositivos físicos.

## Preparación y evidencia

Sigue la [guía local](../guides/DEMO.md). El runtime tiene cuatro servicios: PostgreSQL, Redis, API y worker. Utiliza la clave privada Meta del jurado para llamadas reales directas y las voces instaladas de Android. Conserva credenciales y registros de ejecución en privado. Usa una instalación local desechable para pruebas de edición, borrado y membresía.

Registra evaluador, fecha, versión/hash de la app, sistemas operativos, cuenta/grupo, idioma, pasos, resultado observado y captura de respaldo por caso. Marca un caso como completo únicamente cuando pasen todas sus variantes. Los dispositivos o integraciones no disponibles quedan pendientes.

| Grupo local | Cuentas de acceso | Expedientes preparados | Publicaciones del grupo |
| --- | --- | --- | --- |
| Pacific Ridge Police Department | Alex Rivera, Maya Johnson, Daniel Kim | 16 expedientes de personas ficticias | 16 retratos + 3 videos |
| Meta Social Media | Elena Marquez, Mateo Rios, Sarah Chen | Sin expedientes ordinarios del grupo | 3 presentaciones con avatar + 3 videos |

El total es de 16 expedientes y 25 publicaciones. Los trece perfiles sintéticos adicionales de Meta Social Media no son cuentas del selector; sus tres referencias privadas por perfil permanecen fuera de la galería. Fuentes y hashes originales figuran en el [manifiesto de medios](../../../simulator/media/manifest.csv).

## Instalación y acceso local

- [ ] **P01** — Obtén código y recursos Git LFS, inicia el conjunto local e instala el APK Debug canónico siguiendo el README. Registra su hash exacto y confirma que `/health/ready` responde en el PC local.
- [ ] **P02** — Completa el primer inicio en el host Windows/Linux elegido, incluida la descarga de imágenes/modelos. Confirma los cuatro servicios y la inicialización de la base antes de evaluar consultas.
- [ ] **A01** — Abre el selector local: los dos grupos comienzan contraídos. Comprueba las seis cuentas, sus nombres y avatares. Cambiar de cuenta no debe reutilizar el grupo ni la sesión de otra.
- [ ] **A02** — Confirma que cada cuenta ve únicamente grupos y recursos autorizados. Una cuenta de Policía no debe leer expedientes, originales ni referencias privadas de Meta Social Media.
- [ ] **A03** — Reinicia los servicios locales. Deben conservarse ediciones, publicaciones ocultas/eliminadas y membresías retiradas; la inicialización no debe restaurarlas.

## Expedientes y publicaciones

- [ ] **R01** — Abre los 16 expedientes policiales y sus publicaciones con retrato. Confirma cinco órdenes de captura vigentes y dos procesos activos entre esas cinco personas. Bruno Escobar y Daniel Serrano tienen orden de captura, sin procesos activos ni condenas.
- [ ] **R02** — Abre Samuel Ortega, Elena Duarte, Isabel Mora y Natalia Campos (PRP-0013–0016): deben aparecer su condición de personas desaparecidas y la orden de búsqueda vigente correspondiente, separadas de los campos de captura. Confirma ausencia de captura, antecedentes y procesos activos. Las otras siete fichas limpias conservan ausencia de antecedentes, órdenes y procesos.
- [ ] **R03** — Comprueba que cada retrato abre su original únicamente para miembros autorizados. Consultar o compartir un expediente no debe conceder autorización biométrica ni crear enrolamientos.
- [ ] **G01** — Comprueba las 25 publicaciones de los dos grupos, incluida la paginación. Revisa autores, categorías, tags, descripciones, notas y textos guardados ES/EN. Perfiles y galería deben permanecer coherentes tras las ediciones.
- [ ] **G02** — Aplica filtros de categoría, tag, autor, fecha y texto; límpialos y cambia de grupo. Abre una publicación y regresa. Verifica ámbito, orden y conservación del filtro.
- [ ] **G03** — En una instalación desechable, publica explícitamente en un grupo existente con clasificación válida. Comprueba duplicados, restricciones de autoría e interacciones independientes en copias autorizadas.

## Videos y evidencia de objetos

- [ ] **V01** — Reproduce los seis videos añadidos a Policía/Meta. Verifica originales completos, reproducción/desplazamiento y rechazo desde otro grupo.
- [ ] **V02** — Sigue [Evaluación de videos](VIDEO_EVALUATION.md) para verificar reproducción y descarga por grupo. Registra cada consulta real por separado; estos seis videos no tienen expectativas revisadas de objetos/intervalos.
- [ ] **V03** — Consulta un objeto ausente y un grupo ajeno a la cuenta. No debe inventarse evidencia ni devolverse contenido sin permiso. Una consulta no debe iniciar una captura nueva de Register.
- [ ] **V04** — Prueba la entrada explícita de cámara/imagen con las [láminas visuales](QA_VISUAL_FIXTURES.md). Registra fallos del proveedor y latencia por separado de la corrección visual; una pantalla cargando no cuenta como aprobación.

## Privacidad y consentimiento

- [ ] **B01** — Verifica que la búsqueda biométrica existente exige consentimiento y permisos. Importar los expedientes policiales o ver sus publicaciones ordinarias con retrato no debe enrolar automáticamente a esas personas.
- [ ] **B02** — Confirma que los resultados Meta usan avatares separados; las fotos privadas de referencia no deben aparecer en galería, medios genéricos ni miniaturas de resultados. Repite la comprobación tras revocar consentimiento o membresía en la instalación desechable.
- [ ] **B03** — Comprueba propiedad del perfil/CV privado y aislamiento entre grupos. Los archivos públicos no deben exponer contraseñas, claves de proveedores ni documentos privados.

## Android y Postman

- [ ] **U01** — Revisa las pantallas en ES/EN, anchos reducidos y texto al 200% en el teléfono real: selector, galería, filtros, visor y detalles de expediente. Comprueba recortes, desplazamiento, foco, etiquetas y controles con el diseño habitual de la app.
- [ ] **U02** — Verifica permisos del teléfono, recuperación de conexión local, voces instaladas sin conexión y carga real de medios. Las interacciones con gafas/DAT físicos requieren evidencia propia.
- [ ] **S01** — Importa la colección principal y abre **Localhost requests → 00 Local scenarios**. Usa la selección de cuenta local sin contraseñas. Comprueba que variables y sesiones permanezcan aisladas entre escenarios.
- [ ] **S02** — Confirma que **Server requests** está desactivado y sin URL ni credenciales activas. Ejecuta las peticiones locales preparadas, incluidas las peticiones de galería y medios del grupo; conserva los resultados HTTP por separado de la aceptación visual.
- [ ] **S03** — Aplica la actualización vigente de código/datos, reinicia y repite los escenarios afectados. Comprueba que las revisiones SQL se apliquen una sola vez y conserven contenido anterior, ediciones, eliminaciones y membresías.

## Aceptación externa separada

Facebook Live, registro/recuperación con correo real, almacenamiento del servidor, voz remota y gafas físicas requieren entornos autorizados y evidencia propios. No forman parte del runtime local de cuatro servicios. Consulta las [guías de integración](../INDEX.md) y conserva las [constancias de derechos](../project/THIRD_PARTY.md) de recursos y servicios distribuidos.
