<p align="center"><a href="../../en/testing/IMPLEMENTATION_CHECKLIST.md"><img src="../../assets/readme/language-en.svg" alt="English" height="32"></a> <a href="IMPLEMENTATION_CHECKLIST.md"><img src="../../assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Checklist manual RealityOS — aceptación y hackathon 2026

[← Proyecto](../README.md) · [Imágenes listas para la cámara](QA_VISUAL_FIXTURES.md) · [Acceso y escenarios](../guides/DEMO.md#access) · [Postman](../api/API.md#quick-start) · [Entrega](../project/HACKATHON.md)

**Actualizado el 3 de noviembre de 2026 para el código `0090bdf`.** Puedes empezar con las tres cuentas públicas y sus conexiones existentes. Las pruebas que cambian datos se hacen en QA.

## Empieza ahora en la app

1. Instala el APK preparado: `android/app/build/outputs/apk/debug/app-debug.apk`, versión **`0.1.6-debug-20261103-1224`**. Si ya tienes exactamente ese build, continúa. La versión corta `0.1.6` no basta para identificarlo.
2. Abre **Continuar con correo → Iniciar sesión → Usuario o correo**. Usa **`elena-marquez`** y copia su contraseña de la [tabla pública de acceso](../api/API.md#quick-start). La cuenta ya está confirmada.
3. En **Perfil**, comprueba el avatar y abre una publicación. En **Trabajo → California Valley Medical Center → Registros del espacio**, abre **Ana Solis** y su retrato. Hay 20 expedientes y siete publicaciones de grupo.
4. Abre **Perfil → Mis conexiones → Demo nursing → Comprobar acceso**. En **Destino de importación / espacio de búsqueda**, elige **California Valley Medical Center**.
5. Marca **solo** `patient-ana.png`, baja hasta **Usar para buscar persona** y pulsa. Si aparece consentimiento, léelo, acepta si corresponde y vuelve a pulsar la búsqueda. Abre el candidato Ana y su expediente. No hace falta descargar el retrato ni volver a enrolarlo.
6. Desmarca el retrato anterior y marca solo `medicine-cart.png` → **Usar para buscar objeto**. Espera el resultado y abre su evidencia. Una búsqueda por imagen puede tardar más de un minuto; el APK espera hasta **180 segundos**. No pulses repetidamente ni confundas la espera con un resultado aprobado.

Este recorrido inicia A01, A03, R02, K01, K03, K09 y K10. Marca cada ID abajo únicamente al completar **todas** sus cuentas y variantes. Continúa en el orden de las secciones: **P → A → R → M → O → B → F → G → K → V → D → U → C → S → T → H**.

Para cámara y Display, abre las [láminas](QA_VISUAL_FIXTURES.md) en la computadora y encuádralas con el teléfono. Las búsquedas desde R2 y los expedientes usan archivos que ya están disponibles dentro de la app. El alcance completo incluye **teléfono Android físico, Display con Mock Device Kit, correo real y Facebook real**; gafas físicas y Windows local quedan fuera de esta ejecución.

## Referencia preparada para esta ejecución

| Elemento | Valor verificado |
| --- | --- |
| APK de este host | `0.1.6-debug-20261103-1224` · paquete `com.luxisoft.realityos` |
| SHA-256 del APK de este host | `56b9a60ca9ec07ceb9e9338ad4b34143969fb6b42c68e3c47891851e5f872965` |
| Código app / servidor | [`0090bdf`](https://github.com/Luxisoft/realityos-spatial-memory/commit/0090bdfcb8d8f298da73ece3c8d6e57e6b5448b6) |
| API | `https://realityos.luxisoft.com/v1` |
| Disponibilidad / documentación | [Live](https://realityos.luxisoft.com/health/live) · [Ready](https://realityos.luxisoft.com/health/ready) · [Swagger](https://realityos.luxisoft.com/docs) · [OpenAPI](https://realityos.luxisoft.com/v1/openapi.json) |
| Validación técnica disponible | **492 pruebas backend/gateway, 224 Android**, builds Debug/Release y emulador en [CI aprobado](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41684656174). [Despliegue aprobado](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41684655293), Alembic `20261103_0035`. |
| Datos disponibles | 47 expedientes, 21 publicaciones de grupo y seis retratos de expediente enrolados; 426 recursos R2 y 14 conexiones privadas para 13 cuentas. |

Esta evidencia técnica no marca las pruebas manuales como aprobadas. Si usas el APK de Actions del mismo commit, registra **su** versión y hash: la fecha de compilación y el hash pueden diferir del archivo de este host. Si cambia el código del APK o servidor, registra otra ejecución y repite los casos afectados.

## Cómo marcar y guardar resultados

Todos los casos comienzan pendientes. Marca `[x]` únicamente si ejecutaste todos los pasos y guardaste evidencia del resultado. Una comprobación API anterior no aprueba automáticamente una prueba de pantalla. No uses «no aplica» para ocultar un fallo o una preparación que falta.

En una copia privada del checklist o en `.runtime/acceptance-run.csv`, registra por ID: **PENDIENTE / APROBADO / FALLIDO / BLOQUEADO**, fecha/hora, cuenta, resultado observado, evidencia, incidencia y repetición. Para casos con varias cuentas/idiomas, adjunta cada resultado antes de aprobar el ID. Guarda capturas/logs en `.runtime/acceptance-evidence/`; no publiques tokens, contraseñas, correos privados ni medios personales. Si usas una hoja de cálculo, estas son las columnas:

```csv
id,estado,fecha_hora,cuenta,resultado,evidencia,incidencia,repeticion
A01,PENDIENTE,,,,,,
```

En este host, `.runtime/acceptance-run.csv` ya tiene las **98 filas pendientes** (92 pruebas y seis pasos de cierre), en el mismo orden que esta guía.

| Identificación de esta ejecución | Completar antes de aprobar |
| --- | --- |
| Responsable y fecha / zona horaria | — |
| Teléfono y versión Android | — |
| Idioma inicial / segundo idioma | ES / EN (probar ambos) |
| APK: versión completa, fecha, SHA-256 | Referencia arriba; confirma el archivo que instalaste |
| Commit / release backend / contrato | `0090bdf` / Alembic `20261103_0035`; registra cambios |
| Display | Mock Device Kit, cámara y micrófono del teléfono |
| Antecedente aportado por el usuario | APK instalado; identidad del build por corroborar en P01 |

## Cuentas y datos listos

Las tres cuentas principales y sus contraseñas están en la [tabla pública de acceso](../api/API.md#quick-start), publicadas por autorización del propietario. Las otras seis cuentas y las cuatro QA están en la ficha privada existente `.runtime/accesos-prueba.txt`; los IDs QA están en `.runtime/acceptance-qa.json`. Entrar: **Continuar con correo → Iniciar sesión → Usuario o correo**. Las cuentas `example.test` están provisionadas y no reciben correo.

| Grupo | Cuentas, en orden | Datos iniciales |
| --- | --- | --- |
| Pacific Ridge Police Department | `alex-rivera`, `maya-johnson`, `daniel-kim` | 9 registros, 7 publicaciones; cada trabajador tiene avatar y 2/3/2 publicaciones propias. |
| California Valley Medical Center | `elena-marquez`, `mateo-rios`, `sarah-chen` | 20 registros, 7 publicaciones; Ana, Robert y Fatima con retratos adjuntos. |
| Sonoran Neurological Institute | `noah-brooks`, `lucia-vega`, `owen-patel` | 18 registros, 7 publicaciones; Luis, Grace e Hiro con retratos adjuntos. |
| QA Hackathon — disposable tests | `qa-hackathon-admin`, `qa-hackathon-member`, `qa-hackathon-reader` | Admin / registro / consulta. Dos usuarios con consentimiento y enrolamiento sintético explícito; reader sin consentimiento. |
| Fuera del grupo QA | `qa-hackathon-outsider` | Perfil privado preparado; sin acceso inicial a QA, para invitación y retirada. |
| Correo / Facebook reales | Los del evaluador | Registro y corrección usan cuentas QA nuevas con buzones reales, no las cuentas anteriores. |

Las cuatro cuentas QA tienen avatares y una publicación privada de escena sintética inicial. El grupo QA empieza sin expedientes; sus publicaciones de Trabajo se crearán en G01. En Postman usa las 39 consultas preparadas de **01 Police**, **02 Nursing** y **03 Memory**. La guía API enlazada arriba indica dónde encontrarlas en la colección vigente; el catálogo completo tiene otras operaciones con requisitos propios.

## Archivos concretos para probar desde R2

En **Perfil → Mis conexiones**, abre la conexión, elige el espacio correcto y pulsa **Vista previa** o marca una sola casilla para buscar. Los botones de búsqueda aparecen debajo de la lista. Para importar foto y video, marca ambos; para usar un CV, marca solo el PDF.

| Cuenta / conexión | Archivos ya disponibles | Resultado de búsqueda / uso |
| --- | --- | --- |
| `alex-rivera` / **Demo police** | `evidence-desk.png`, `evidence-desk-1.mp4` | Objetos del escritorio; espacio Pacific Ridge Police Department. |
| `elena-marquez` / **Demo nursing** | `patient-ana.png`, `patient-robert.png`, `patient-fatima.png`, `medicine-cart.png`, `medicine-cart-1.mp4` | Expedientes clínicos y objetos; espacio California Valley Medical Center. |
| `noah-brooks` / **Demo memory** | `patient-luis.png`, `patient-grace.png`, `patient-hiro.png`, `memory-desk.png`, `memory-desk-1.mp4` | Expedientes y memoria visual; espacio Sonoran Neurological Institute. |
| Cuentas QA / **Demo qa** | `alex-rivera.png`, `maya-johnson.png`, `evidence-desk.png`, `evidence-desk-1.mp4`, `cv-v1.pdf`, `cv-v2.pdf` | Admin/miembro QA enrolados; publicaciones de prueba y sustitución de CV. |
| QA admin / **Directorio social y taller (QA)** | Carpetas `source/`, `muse/`, `generated/`, `workshop/` | Explorar carpetas y páginas entre los 327 recursos preparados. |

Las conexiones de escenario tienen 31 archivos cada una; **Demo qa** tiene seis. Ver una foto en el bucket no concede acceso al expediente de otra organización. Seleccionar **Mi perfil privado** no selecciona automáticamente el grupo para la búsqueda.

### Antes de las pruebas que necesitan preparación adicional

- **A02, B04–B07, F, G y K con QA:** usa la ficha privada existente `.runtime/accesos-prueba.txt`. No cambies las contraseñas públicas ni las publiques en el registro.
- **K02 y K07–K08:** el responsable necesita acceso a Cloudflare y una carpeta temporal propia para esta ejecución. Entrega o introduce de forma privada las claves y prepara foto/video válidos, una imagen de un objeto ausente del conjunto, dos claves de objeto con bytes idénticos, un `.png` con bytes inválidos y un archivo multimedia que exceda el límite de descarga de la guía R2. Solo modifica esa carpeta; conserva `Demo police`, `Demo nursing`, `Demo memory` y `Demo qa`.
- **K06, K12–K15:** usan los archivos y la conexión temporal de K02. El responsable carga o corrige los archivos en R2; la app los lee/importa, no sube archivos al bucket. Sin esa preparación, marca únicamente los casos dependientes como BLOQUEADOS y continúa los recorridos ya preparados.
- **C:** necesitas tu cuenta Facebook autorizada y buzones reales para correo. Las cuentas `example.test` no sirven para recibir mensajes.

**Vigencia clínica:** el conjunto ficticio tiene prescripciones del **1 al 30 de noviembre de 2026 UTC**. Fuera de ese intervalo se espera discrepancia de vigencia: no marques coincidencia ni cambies el reloj. El responsable debe preparar un conjunto QA vigente antes de repetir positivos. La app envía la hora actual; el detalle de causas y referencias se verifica en T04.

**Límite de las láminas:** recapturar rostros sintéticos prueba integración, calidad de cámara y navegación; no mide precisión representativa ni verificación de identidad de una persona real. Para login Facebook usa tu rostro real y sus pasos normales. Si la captura de pantalla se rechaza por calidad, registra el motivo y ajusta encuadre; no desactives los controles.

## Casos de aceptación

### P — Preparación — responsable y evaluador

- [ ] **P01** — Instala o verifica el APK identificado arriba; abre la app y anota su versión completa. Esperado: build `0.1.6-debug-20261103-1224` del host, o artefacto del mismo commit identificado con su propio hash; paquete productivo, no la variante `.local`.
- [ ] **P02** — Completa responsable, teléfono, Android e idioma en la cabecera. Usa `0090bdf` como referencia de app/servidor y registra cualquier cambio. Activa No molestar. Esperado: evidencias vinculadas al build instalado.
- [ ] **P03** — Comprueba las tres cuentas públicas de escenario con avatar, publicaciones, grupo y conexión R2. Antes de probar otras cuentas, abre la ficha privada para los seis trabajadores y cuatro QA. Si falta un acceso, bloquea solo sus casos; puedes iniciar la app con las tres cuentas públicas.
- [ ] **P04** — Para B, O05 y D abre las láminas en la computadora y encuádralas con el teléfono; prepara también las tres caras juntas. Para R y K usa los retratos/archivos ya adjuntos o en Mis conexiones. Esperado: pruebas de cámara sin descargar retratos al teléfono.
- [ ] **P05** — Prepara tu Facebook autorizado y un buzón real con tres direcciones o alias que reciban correo: A para C01, B para la cuenta pendiente y C como destino corregido de C03. Guarda claves solo en tu ficha privada. Esperado: recepción en A/B/C y acceso al Facebook de prueba.

### A — Entrada y nueve cuentas preparadas

- [ ] **A01** — Abre Continuar con correo → Iniciar sesión; en Usuario o correo escribe elena-marquez y la contraseña de la tabla pública enlazada arriba. Esperado: accedes sin registrar la cuenta de nuevo.
- [ ] **A02** — Repite entrada, avatar y apertura de cada publicación con las nueve cuentas de la tabla. Esperado inicial: 2/3/2 publicaciones propias por los tres trabajadores de cada grupo; anota cambios legítimos desde el inventario. Guarda nueve resultados, no uno representativo.
- [ ] **A03** — En Trabajo selecciona el grupo asignado. Esperado inicial por grupo: siete publicaciones; Policía 9 registros, Clínica 20 y Memoria 18. Abre Registros del espacio para contarlos. Cada cuenta conserva su grupo, no los otros escenarios.
- [ ] **A04** — Cierra sesión, escribe una contraseña incorrecta una sola vez y luego la correcta. Esperado: error comprensible, sin acceso con contraseña errónea; el segundo intento permite entrar.
- [ ] **A05** — Cierra y vuelve a abrir la app, después cierra sesión y cambia de escenario. Esperado: sesión válida recuperada al reabrir; al cambiar de cuenta desaparecen datos y acciones pendientes de la anterior.

### R — Expedientes y escenarios

- [ ] **R01** — Con alex-rivera: Trabajo → Pacific Ridge Police Department → Registros del espacio → Caso de prueba 1. Abre notas, relaciones y adjuntos. Esperado: fuente/versión, evidencia y autor/contexto correctos. Este escenario no incluye personas policiales enroladas.
- [ ] **R02** — Con elena-marquez abre Ana Solis y su retrato; vuelve a atención, prescripción y notas. Repite con Robert Lane y Fatima Nasser. Esperado: tres personas distintas, cada una con sus relaciones y retrato ya adjunto.
- [ ] **R03** — Con noah-brooks abre Luis Moreno, su retrato, recordatorio y evento; revisa Grace Wilson e Hiro Tanaka. Esperado: registros relacionados correctos y fechas/fuentes visibles.
- [ ] **R04** — Abre una imagen y un MP4 de cada escenario; reproduce, pausa y vuelve al expediente. Esperado: contenido accesible y retorno correcto. Los MP4 preparados son escenas estáticas sintéticas, no movimiento real.
- [ ] **R05** — Busca por nombre y por un texto inexistente en Registros del espacio; abre dos expedientes sucesivamente y vuelve durante una carga. Esperado: filtro correcto, vacío comprensible y ninguna respuesta tardía sustituye el expediente actual.
- [ ] **R06** — Pregunta en Buscar «¿Qué información registrada hay de Ana Solis?» con Clínica seleccionada, y por el recordatorio de Luis en Memoria. Esperado: referencias del espacio autorizado y respuesta contextual sin inventar hechos ni autorizar tratamientos. Guarda el texto completo que usarás en el video.

### M — Comparador clínico — datos ficticios

- [ ] **M01** — En Ana Solis → Comparar campos de medicación, elige Prescripción ficticia 1, ingrediente DEMO MEDICINE y concentración 10 mg; confirma identidad. Esperado durante su vigencia: los campos coinciden, con revisión profesional requerida. La app envía la hora actual.
- [ ] **M02** — Cambia únicamente la concentración a 20 mg y compara. Esperado: desaparece el resultado previo al editar y la nueva comparación informa discrepancia. Responsable verifica la referencia a la prescripción en T04.
- [ ] **M03** — En Robert Lane usa Prescripción ficticia 2, DEMO MEDICINE y 10 mg. Esperado: discrepancia por alergia registrada; el detalle técnico identifica recorded_allergy.
- [ ] **M04** — En Fatima Nasser usa Prescripción ficticia 3, DEMO MEDICINE y 10 mg. Esperado: discrepancia por antecedente de administración; el detalle técnico identifica administration_history_requires_review.
- [ ] **M05** — Vacía un campo y luego prueba sin confirmar identidad. Esperado: campo vacío impide comparar; falta de confirmación nunca produce coincidencia válida. Cambiar prescripción o confirmación invalida el resultado previo.

### O — Objetos e historial

- [ ] **O01** — Con Policía busca «linterna amarilla» y «destornillador rojo»; con Clínica «carro de medicación», «bolígrafo azul», «guantes desechables»; con Memoria «carpeta roja de documentos», «llaves de latón», «cuaderno azul». Esperado: evidencia pertinente autorizada; registra cada consulta, no solo la primera.
- [ ] **O02** — Abre un resultado por escenario. Esperado: imagen/fotograma con señalización pertinente, fuente y fecha de última observación; confianza visual identificable. No se exige 1920×1280 para todos los originales ni que el objeto siga allí.
- [ ] **O03** — Pregunta «¿Dónde está el submarino violeta?» antes de añadir datos QA. Esperado: no hay evidencia suficiente; ninguna ubicación o foto inventada. Si existe evidencia real de ese objeto, el responsable elige y registra otro ausente.
- [ ] **O04** — Repite una búsqueda en español y en inglés cambiando el idioma de la app; reabre resultados e historial tras reiniciar. Esperado: idioma seleccionado coherente, adjuntos correctos y sin confundir el historial de otra cuenta.
- [ ] **O05** — Usa Buscar objeto con cámara para encuadrar una escena de las láminas. Espera la respuesta: una consulta por imagen puede superar un minuto y el límite del cliente es 180 s. Esperado: evidencia pertinente o rechazo de calidad claro; para aprobar el positivo debe existir una captura válida con coincidencia.
- [ ] **O06** — En QA registra una foto nueva desde la app, espera que termine el procesamiento y luego búscala. Esperado: aparece con fuente/fecha nuevas. Consulta por sí sola no registra esa foto; T03 comprueba la separación.

### B — Búsqueda facial — no sustituir por abrir un expediente

- [ ] **B01** — Con elena-marquez en Clínica, completa el consentimiento que solicite la app y usa Buscar persona para capturar la lámina de Ana. Esperado: candidata Ana Solis, evidencia y similitud; abrirla llega a su expediente. Ajustar el encuadre es válido; omitir la búsqueda no aprueba el caso.
- [ ] **B02** — Con noah-brooks en Memoria captura la lámina de Luis. Esperado: candidato Luis Moreno y apertura de su expediente, sin traer candidatos de Clínica.
- [ ] **B03** — En Clínica captura las tres caras juntas de Ana, Robert y Fatima. Esperado: tres rostros detectados en una captura de calidad, asociación correcta entre cajas numeradas/colores y candidatos; abre uno y vuelve al resultado grupal.
- [ ] **B04** — Con qa-hackathon-admin, selecciona el grupo QA y captura el retrato de qa-hackathon-member de las láminas. Esperado: candidato de usuario, apertura de su perfil y contenido permitido. Su enrolamiento explícito se verifica antes; no se deduce del avatar.
- [ ] **B05** — Con qa-hackathon-reader sin consentimiento, intenta buscar una persona. Esperado: explicación/solicitud de consentimiento en la app; la API rechaza la búsqueda sin él. Conserva esta cuenta sin consentimiento para el negativo.
- [ ] **B06** — Captura una lámina de objetos sin rostro y después el retrato de Ana estando en QA. Esperado: error de ausencia de rostro en el primer caso y ningún enlace al expediente clínico en el segundo. Nunca inventa una identidad.
- [ ] **B07** — Responsable, al terminar los positivos: revoca consentimiento únicamente del miembro QA, comprueba exclusión de candidatos y eliminación de sus enrolamientos; vuelve a consentir y enrolar explícitamente su retrato para restaurar el conjunto. Guarda antes/después.

### F — Perfil y documentos

- [ ] **F01** — En una cuenta QA por correo, edita nombre, ubicación, localidad, nacimiento y género; guarda y reabre. Esperado: persisten, la edad corresponde a la fecha y una fecha futura o anterior a 1900 se rechaza. Restaura los datos iniciales.
- [ ] **F02** — En Facebook verifica nombre y campos sincronizados de solo lectura; edita biografía/contacto permitidos y vuelve a entrar. Esperado: conserva las reglas de origen y refresca los datos Facebook disponibles.
- [ ] **F03** — Con QA abre **Perfil → Mis conexiones → Demo qa**, marca solo `cv-v1.pdf` → **Usar como CV** → confirma. Repite con `cv-v2.pdf` y reabre el perfil. Esperado: CV vigente actualizado, sin publicación en la galería y sin descarga permitida para otra cuenta (T02). No hace falta copiar PDFs al teléfono.
- [ ] **F04** — Abre un perfil ajeno desde un candidato autorizado y pregunta «¿Cómo se llama este perfil?». Esperado: respuesta basada en información permitida; no expone publicaciones privadas ni el archivo CV.

### G — Publicaciones, grupos y privacidad

- [ ] **G01** — Con qa-hackathon-member publica una foto y un video corto moviendo un objeto desde el teléfono, primero en Perfil y después en Trabajo → QA. Usa la nota «QA aceptación — foto/video». Esperado: cuatro publicaciones con destino correcto y apertura/reproducción.
- [ ] **G02** — Repite una foto idéntica y revisa la decisión de duplicado; cancela una sustitución y confirma otra. Esperado: la app explica la decisión, cancelar preserva el original y confirmar conserva el historial previsto.
- [ ] **G03** — Interrumpe la conexión durante una subida QA, restáurala y reintenta. Esperado: estado recuperable y ninguna publicación extra causada por repetir la misma operación.
- [ ] **G04** — En una publicación QA añade like, comentario y respuesta; reabre desde otra cuenta autorizada. Esperado: persisten y el hilo corresponde al comentario. Reporta solo contenido QA; confirma respuesta y visibilidad de moderación en la administración del grupo con qa-hackathon-admin, y su rechazo para reader, según T02.
- [ ] **G05** — Admin QA crea una invitación de un uso; el responsable entrega su código y la cuenta qa-hackathon-outsider. Introduce el código en Unirse (no el PIN compartido), intenta reutilizarlo y después retira al nuevo miembro. Esperado: primer acceso válido, reutilización rechazada y pérdida del acceso restringido al retirar. No uses ni elimines los grupos de escenario.
- [ ] **G06** — Desde otra cuenta, abre el perfil del autor QA. Esperado: solo publicaciones públicas permitidas; las privadas y las del grupo inaccesible no se exponen por compartir el enlace. Comprueba también los originales en T02.

### K — Buckets R2/S3 — cuentas y datos preparados por el responsable

Preparación R2 completada: 426 recursos remotos verificados y conexiones listas para las 13 cuentas. QA admin tiene además **Directorio social y taller (QA)**. [Comprobante de preparación](../../assets/storage/demo-verification.json). Los casos siguientes permanecen pendientes hasta ejecutarlos en la app.

- [ ] **K01** — Con las nueve cuentas de escenario y cuatro QA, abre **Perfil → Mis conexiones** y su conexión de la tabla → **Comprobar acceso**. Esperado: Conexión correcta, sin pedir claves. QA admin tiene además Directorio social y taller (QA). Registra las 13 cuentas; si falta una, bloquea esa variante y consulta la guía R2.
- [ ] **K02** — Con QA admin crea **QA aceptación** mediante Añadir bucket; el responsable introduce endpoint, bucket, región y claves válidas para su carpeta temporal. Prueba claves inválidas en esta conexión desechable y corrígelas con Editar claves. Esperado: error claro con claves malas, Comprobar acceso correcto al repararlas y claves ocultas al reabrir. No edites las conexiones demo preparadas.
- [ ] **K03** — En Demo qa abre Vista previa de `evidence-desk.png` y `evidence-desk-1.mp4`; amplía, reproduce y cambia de instante. En Directorio social y taller (QA) abre carpetas y Siguiente página cuando aparezca. Esperado: medios autorizados y retorno correcto. En Demo nursing, `hospital.json` se identifica como formato no compatible, no como una importación de expedientes.
- [ ] **K04** — Con QA admin en Demo qa, selecciona `evidence-desk.png` y `evidence-desk-1.mp4` → **Mi perfil privado → Importar selección → Confirmar**. Sigue Importaciones recientes hasta Publicado; si hay Duplicado por revisar, abre Revisar resultado y toma la decisión explícita. Abre los medios en Perfil y verifica su restricción desde otra cuenta.
- [ ] **K05** — Importa una imagen al grupo QA eligiéndolo como destino. Sus miembros pueden abrirla; outsider no ve el grupo ni el original. El responsable intenta el mismo destino por API con outsider y confirma rechazo (T02), sin crear una publicación. No retires miembros de los escenarios.
- [ ] **K06** — Repite K04 con los mismos archivos/origen/destino: no crea publicaciones adicionales mientras la copia siga publicada. En QA aceptación importa un lote con archivo válido, inválido y demasiado grande; espera el estado de cada uno. El responsable corrige el recurso fallido en R2; pulsa Reintentar fallidos. Esperado: recupera el fallo sin repetir el archivo ya publicado.
- [ ] **K07** — En QA aceptación configura **sincronización manual** de la carpeta temporal y elige Perfil privado o el grupo QA. Pulsa Actualizar ahora; recorre sus páginas y repite. El responsable añade una imagen y modifica otra: se incorpora la nueva y la sustitución conserva la revisión de duplicados. Al borrar un objeto remoto, su publicación importada sigue disponible.
- [ ] **K08** — En esa carpeta temporal activa cada 15 minutos; el responsable añade un archivo nuevo y espera un ciclo real sin pulsar actualizar. Pausa; añade otro y comprueba que no se importa automáticamente. Pulsa Actualizar ahora y comprueba que sí se procesa. Registra horas y nombre de cada archivo; no apruebes el horario solo por ver el botón activado.
- [ ] **K09** — Con Elena: Demo nursing → espacio California Valley Medical Center → marca solo `medicine-cart.png` → **Usar para buscar objeto**. Espera hasta 180 s. Si devuelve varios resultados, abre el primero y después otro: cada visor debe corresponder a la miniatura elegida, no repetir siempre la primera. Prueba además una imagen QA sin coincidencias. La búsqueda no crea publicaciones.
- [ ] **K10** — Con Elena: Demo nursing → espacio California Valley Medical Center → `patient-ana.png` → **Usar para buscar persona**. Completa consentimiento y vuelve a pulsar si se solicita; abre el candidato y expediente de Ana. En Demo qa, QA admin busca `maya-johnson.png` dentro del grupo QA y abre el perfil. QA reader rechaza otorgar consentimiento: no se ejecuta la búsqueda ni se enrolan rostros por importar archivos.
- [ ] **K11** — En Demo qa selecciona únicamente `cv-v1.pdf` → **Usar como CV** y confirma; repite con `cv-v2.pdf`. Esperado: versión vigente sustituida, sin publicaciones nuevas y sin descarga desde otra cuenta. No selecciones un PDF junto con una imagen para Importar selección.
- [ ] **K12** — En QA aceptación importa al mismo destino dos objetos con **distinta clave y bytes idénticos**, preparados por el responsable. Publica el primero; en el segundo observa Duplicado por revisar y cancela. Vuelve a seleccionarlo y pulsa Importar selección para crear una importación nueva. Esperado: puedes revisar/confirmar el duplicado otra vez; la operación cancelada anterior sigue cancelada y el original permanece hasta confirmar su sustitución.
- [ ] **K13** — Abre una publicación creada por ti en K04 → Eliminar → confirma. Reimporta ese mismo archivo desde la misma conexión y destino y resuelve la revisión de duplicado si aparece: vuelve a estar disponible, sin reutilizar como vigente la publicación retirada. Repite tras sustituir una publicación QA mediante confirmación de duplicado. Usa solo tus publicaciones de esta ejecución; no elimines escenarios ni originales de R2.
- [ ] **K14** — Importa un video nuevo de la carpeta temporal. Mientras Importaciones recientes indica Analizando, encola otro archivo y pulsa Comprobar acceso; consulta Ready desde el navegador. Esperado: acepta la nueva operación y la API responde antes de acabar el análisis anterior; el worker puede procesarlas en serie. Si todo terminó antes de probarlo, repite con otro video y guarda evidencia de la operación durante el análisis.
- [ ] **K15** — Al terminar, desconecta **QA aceptación**. Esperado: no permite listar/descargar ni iniciar nuevas sincronizaciones; las copias ya publicadas siguen abriendo. Si quedaban archivos en análisis, verifica que no se publiquen después de desconectar. Cambia de cuenta: no aparecen la conexión anterior ni sus claves. Repite textos principales en ES/EN y conserva las conexiones demo originales.

### V — Voz e idiomas

- [ ] **V01** — Con Memoria seleccionada, dicta «¿Dónde se vieron las llaves de latón?» y luego una pregunta equivalente en inglés tras cambiar idioma. Esperado: transcripción pertinente y respuesta en el idioma seleccionado.
- [ ] **V02** — Reproduce una respuesta y usa Repetir; cambia de idioma para una consulta nueva. Esperado: cada reproducción corresponde al texto y su idioma, sin reutilizar audio de otra respuesta.
- [ ] **V03** — Deniega micrófono, concede después y repite; corta la conexión durante voz y recupera. Esperado: avisos claros, recuperación y ningún audio viejo presentado como respuesta nueva.
- [ ] **V04** — Cambia cuenta ES → EN → ES conservando un borrador de prueba cuando corresponda. Esperado: UI, ejemplos, respuestas y voz respetan la cuenta/idioma sin reescribir el borrador ni mezclar historiales.

### D — Display en simulador, usando el teléfono

- [ ] **D01** — Abre Meta Ray-Ban Display → vista previa Debug e inicia Mock Device Kit. Concede cámara/audio. Esperado: conexión y pantalla inicial; registra que se usaron sensores del teléfono, no gafas físicas.
- [ ] **D02** — Buscar → Buscar objeto: apunta a una escena de la computadora. Esperado: cámara visible, resultado pertinente y apertura de la evidencia sin bloquear el regreso.
- [ ] **D03** — Buscar → Buscar persona: repite Ana, el miembro QA y las tres caras de Clínica en sus cuentas/grupos correspondientes. Esperado: candidatos, miniaturas autorizadas, cajas y apertura de expediente/perfil correctos; volver conserva el resultado grupal.
- [ ] **D04** — Comando de voz: consulta información de Ana en Clínica, un objeto en Memoria y un saludo. Esperado: personas consultan expedientes del espacio, objetos recuperan evidencia y saludo responde; voz coherente. No exigir que personas use profiles/search.
- [ ] **D05** — Con QA, captura una foto y un video nuevos en Display. Esperado: empieza el envío a **Perfil privado** al terminar la captura, sin elegir grupo ni pulsar Publicar para cada archivo nuevo. Reabre ambos en Perfil; no aparecen en Trabajo. Si surge un duplicado o fallo, usa la revisión/reintento que muestre la app.
- [ ] **D06** — Con la cámara abierta, pulsa X para cancelar, también durante una captura. Provoca un duplicado o fallo QA para probar Descartar/Reintentar cuando aparezcan; recupera la conexión y cambia de cuenta durante una operación. Esperado: cierre utilizable, ningún envío tras cancelar antes de completar la captura ni medios privados restaurados en otra sesión. No confundas una captura ya publicada automáticamente con una pendiente de revisión.

### U — Robustez del teléfono

- [ ] **U01** — Recorre Perfil / Trabajo / Buscar / Ray-Ban. Esperado: cabecera y cuenta correctas, acciones accesibles y regreso coherente.
- [ ] **U02** — Deniega por separado cámara y audio; después concédelos. Esperado: explicación del permiso faltante y continuación al conceder; no captura silenciosa.
- [ ] **U03** — Desconecta la red durante búsqueda y apertura de expediente; vuelve a conectar. Esperado: error/vacío/carga distinguibles y reintento útil, sin pantalla bloqueada.
- [ ] **U04** — En el visor pellizca, suelta el último dedo y arrastra varias veces. Esperado: imagen estable, sin saltos, desaparición ni coordenadas inválidas.
- [ ] **U05** — Con un borrador, abre teclado, rota y lleva la app al fondo; vuelve. Lee mensajes antiguos y recibe otro. Esperado: borrador conservado y scroll sin arrastrarte al final si estabas leyendo arriba.
- [ ] **U06** — Comprueba cuentas/perfil a 320 dp y texto al 200 % mediante un dispositivo/emulador configurado para ello; registra el entorno. Esperado: botones/campos utilizables y contenido accesible con scroll. Restaurar ajustes después.

### C — Correo real y Facebook

- [ ] **C01** — Con una cuenta nueva QA y tu buzón real, usa Crear cuenta. Abre el correo y confirma. Esperado: remitente RealityOS <support@luxisoft.com>, enlace funcional y acceso confirmado. No uses example.test para esta prueba.
- [ ] **C02** — Intenta registrar el usuario/correo ya ocupado. Esperado: informa qué dato está ocupado y ofrece las acciones disponibles sin crear otra cuenta.
- [ ] **C03** — Registra otra cuenta QA con el alias B y conserva su enlace sin usar. Todavía pendiente, corrige el correo al alias C usando su usuario y contraseña actuales. Esperado: cambia el destino de esa misma cuenta, llega al nuevo buzón y el enlace anterior deja de confirmar. Mantén esta cuenta pendiente hasta C04.
- [ ] **C04** — En la cuenta pendiente de C03 prueba Reenviar confirmación al alias C y confirma con el último enlace. Esperado: recepción, confirmación y acceso correctos sin crear cuentas duplicadas.
- [ ] **C05** — Recupera la contraseña de la cuenta QA confirmada. Esperado: correo real, cambio correcto, acceso con contraseña nueva y rechazo de la anterior. Reutilizar el enlace consumido se rechaza.
- [ ] **C06** — Intenta corregir como pendiente una cuenta QA ya confirmada. Esperado: rechazo y conservación de su identidad/correo actuales. Responsable puede comprobarlo por API si la app ya no ofrece la acción.
- [ ] **C07** — Entra con Facebook real desde el teléfono y completa los permisos y pasos de identidad que muestre la app. Esperado: sesión real y perfil de esa cuenta; cancelación del flujo vuelve a una pantalla utilizable. No se sustituye por un token simulado.

### S — Servidor y sesión técnica

- [ ] **S01** — Abre los enlaces Live y Ready de la referencia: ambos deben responder 200. Abre Swagger y comprueba que carga su contrato `/v1/openapi.json`. Guarda hora y respuesta; un fallo bloquea las operaciones dependientes.
- [ ] **S02** — Importa la colección pública desde la guía API, deja **No environment** y abre **Server requests → 00 Live scenarios → 01 Police / 02 Nursing / 03 Memory**. Ejecuta las 13 peticiones de cada carpeta, 39 en total. Esperado: login/refresh automáticos y datos actuales de los tres grupos. Conserva los resultados; no cambies las variables de Localhost requests.
- [ ] **S03** — Responsable: verifica la rotación con POST /v1/auth/refresh y rechazo del refresh anterior, usando una sesión QA independiente. Esperado: token nuevo válido y anterior rechazado; guarda respuestas sin tokens. Desactiva la auto-renovación en la petición negativa para probar el token consumido.

### T — Evidencia del responsable técnico

- [ ] **T01** — Revisa el CI y despliegue aprobados de `0090bdf` enlazados arriba y compara el OpenAPI público con `tests/contracts/openapi.json`. Esperado: contrato idéntico, 492 pruebas backend/gateway, 224 Android y evidencia de builds/emulador. Si cambió código, ejecuta los controles relevantes del Makefile para esa revisión. Esto no aprueba cámara física.
- [ ] **T02** — Permisos: con sesiones QA comprueba 401 sin token, 403 sin rol/consentimiento, recursos ajenos no accesibles, privacidad de medios/CV y moderación. Prueba rechazo de IDs mal formados/inexistentes según el contrato, invitación consumida y revocación. Acepta 403/404 según ruta, no un 404 universal.
- [ ] **T03** — Evidencia: usa las regresiones de BYTEA, idempotencia, Query sin captura y Register consentido; verifica hash del original antes/después de traducción/refinamiento. SAM se comprueba con un observation_id válido del flujo Register, no con el ID de una publicación social.
- [ ] **T04** — Expedientes: verifica referencias/issues del comparador, versiones e idempotencia de importaciones, relaciones clínicas y rechazo de una baja que deje registros activos huérfanos. Usa fixtures aislados de tests, no borres pacientes de los escenarios. Confirma MP4 con petición Range y respuesta parcial 206.
- [ ] **T05** — Idiomas: información ya preparada se lee de DB; si falta, el flujo separado information/prepare puede generar y guardar traducciones. Comprueba ambas ramas y ausencia de sustitución silenciosa de idioma. No afirmar que toda apertura jamás llama al proveedor.
- [ ] **T06** — Proveedores: conserva evidencia de Muse/SAM/transcripción Live y WAV ElevenLabs autenticado; sin sesión se rechaza TTS. Ante fallo, no hay caída silenciosa a mock ni audio antiguo. Mock solo en pruebas aisladas, determinista y rotulado. No cambies producción a mock para aprobar.
- [ ] **T07** — Seguridad y errores: verifica claves de proveedor/JWT/DB ausentes del APK y evidencias; regresiones de 409, 422 y 429 en entorno aislado para no bloquear cuentas demo. Guarda resultados sin secretos. Confirma aislamiento de biometría respecto al registro de objetos.

### H — Cierre y envío de hackathon

- [ ] **H01** — Abre el portal oficial y confirma allí fecha/hora límite, categoría, track, equipo y requisitos vigentes. Guarda comprobante antes de preparar el envío; no uses una fecha copiada de un checklist anterior.
- [ ] **H02** — Revisa repositorio público, licencia del proyecto, derechos de pesos InsightFace, términos DAT y procedencia de recursos. Esperado: decisiones documentadas por el responsable, sin declarar derechos pendientes como aprobados.
- [ ] **H03** — Comprueba los 92 casos de aceptación: sin pendientes, fallos ni bloqueos; evidencias correspondientes a la versión probada. Si cambió código/servidor, repite casos afectados y entrada → expediente → búsqueda → Display.
- [ ] **H04** — Graba el video real de tres minutos con los recorridos aprobados y las aportaciones del evento. Incluye búsqueda facial real con consentimiento, expediente, evidencia/SAM y Display simulado identificado como tal. Revisa las respuestas clínicas que se vean.
- [ ] **H05** — Abre el enlace del video sin sesión; revisa duración, audio, ausencia de secretos/notificaciones y enlaces de README. Esperado: el jurado puede ver la grabación; los videos conceptuales no la reemplazan.
- [ ] **H06** — Envía en el portal y guarda recibo, hora, proyecto y enlaces entregados. Esperado: confirmación de envío. Un push a GitHub o tener todas las pruebas aprobadas no es el envío.

## Resultado final

Hay **92 casos de aceptación** (todos excepto H) y **6 de cierre/envío H**. Cobertura aprobada = casos de aceptación aprobados / 92 × 100. Ejecutar un caso fallido cuenta como ejecutado, pero no como aprobado. Toda variante de un caso debe pasar; un bloqueador conserva su lugar en el denominador.

- **Pruebas aprobadas:** 92/92, con evidencia y cero fallos/bloqueos/pendientes.
- **Entrega preparada:** pruebas aprobadas y H01–H05 completos.
- **Candidatura enviada:** H06 completo con recibo del portal.

Texto de cierre, solo cuando corresponda:

> El 100 % de los 92 casos de aceptación definidos para la versión [APK/hash], servidor [release], teléfono [modelo/Android] y Display simulado fue ejecutado y aprobado el [fecha], con evidencia [registro]. No incluye gafas físicas ni Windows local.

Las comprobaciones de preparación realizadas por el responsable se documentan aparte; esta plantilla no afirma que la sesión manual ya se haya ejecutado. El recibo del portal es la evidencia de envío. [Portal oficial](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit).
