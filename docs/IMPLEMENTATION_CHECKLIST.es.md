<p align="center"><a href="IMPLEMENTATION_CHECKLIST.md"><img src="assets/readme/language-en.svg" alt="English" height="32"></a> <a href="IMPLEMENTATION_CHECKLIST.es.md"><img src="assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Checklist manual RealityOS — aceptación y hackathon 2026

[← Proyecto](../README.es.md) · [Imágenes listas para la cámara](QA_VISUAL_FIXTURES.es.md) · [Acceso y escenarios](DEMO.es.md#access) · [Postman](API.es.md#quick-start) · [Entrega](HACKATHON.es.md)

**Empieza con P01.** Sigue P → S → A → C → F → R → M → O → B → G → V → D → U → T → H. Prueba en **teléfono Android físico y Display con Mock Device Kit**, correo real y Facebook real. Cámara del teléfono apuntando a las imágenes abiertas en la computadora. Gafas físicas y Windows local quedan fuera de esta ejecución.

## Cómo marcar y guardar resultados

Todos los casos comienzan pendientes. Marca `[x]` únicamente si ejecutaste todos los pasos y guardaste evidencia del resultado. Una comprobación API anterior no aprueba automáticamente una prueba de pantalla. No uses «no aplica» para ocultar un fallo o una preparación que falta.

En una copia privada del checklist o en `.runtime/acceptance-run.csv`, registra por ID: **PENDIENTE / APROBADO / FALLIDO / BLOQUEADO**, fecha/hora, cuenta, resultado observado, evidencia, incidencia y repetición. Para casos con varias cuentas/idiomas, adjunta cada resultado antes de aprobar el ID. Guarda capturas/logs en `.runtime/acceptance-evidence/`; no publiques tokens, contraseñas, correos privados ni medios personales. Si usas una hoja de cálculo, estas son las columnas:

```csv
id,estado,fecha_hora,cuenta,resultado,evidencia,incidencia,repeticion
A01,PENDIENTE,,,,,,
```

| Identificación de esta ejecución | Completar antes de aprobar |
| --- | --- |
| Responsable y fecha / zona horaria | — |
| Teléfono y versión Android | — |
| Idioma inicial / segundo idioma | ES / EN (probar ambos) |
| APK: versión completa, fecha, SHA-256 | —; la etiqueta 0.1.6 sola no distingue builds |
| Commit / release backend / contrato | — |
| Display | Mock Device Kit, cámara y micrófono del teléfono |
| Antecedente aportado por el usuario | APK instalado; identidad del build por corroborar en P01 |

## Cuentas y datos listos

Las tres cuentas principales y sus contraseñas están en la [tabla pública de acceso](API.es.md#quick-start), publicadas por autorización del propietario. Las otras seis cuentas y las cuatro QA se entregan en la ficha privada `.runtime/accesos-prueba.txt`; los IDs QA están en `.runtime/acceptance-qa.json`. Entrar: **Continuar con correo → Iniciar sesión → Usuario o correo**. Las cuentas `example.test` están provisionadas y no reciben correo.

| Grupo | Cuentas, en orden | Datos iniciales |
| --- | --- | --- |
| Pacific Ridge Police Department | `alex-rivera`, `maya-johnson`, `daniel-kim` | 9 registros, 7 publicaciones; cada trabajador tiene avatar y 2/3/2 publicaciones propias. |
| California Valley Medical Center | `elena-marquez`, `mateo-rios`, `sarah-chen` | 20 registros, 7 publicaciones; Ana, Robert y Fatima con retratos adjuntos. |
| Sonoran Neurological Institute | `noah-brooks`, `lucia-vega`, `owen-patel` | 18 registros, 7 publicaciones; Luis, Grace e Hiro con retratos adjuntos. |
| QA Hackathon — disposable tests | `qa-hackathon-admin`, `qa-hackathon-member`, `qa-hackathon-reader` | Admin / registro / consulta. Dos usuarios con consentimiento y enrolamiento sintético explícito; reader sin consentimiento. |
| Fuera del grupo QA | `qa-hackathon-outsider` | Perfil privado preparado; sin acceso inicial a QA, para invitación y retirada. |
| Correo / Facebook reales | Los del evaluador | Registro y corrección usan cuentas QA nuevas con buzones reales, no las cuentas anteriores. |

Las cuatro cuentas QA tienen avatares y una publicación privada de escena sintética inicial. El grupo QA empieza sin expedientes; sus publicaciones de Trabajo se crearán en G01. En Postman, las 39 consultas de escenarios están en **Server requests → 00 Live scenarios**; el catálogo API completo tiene otras operaciones con requisitos propios.

**Vigencia clínica:** el conjunto ficticio tiene prescripciones del **1 al 30 de noviembre de 2026 UTC**. Fuera de ese intervalo se espera discrepancia de vigencia: no marques coincidencia ni cambies el reloj. El responsable debe preparar un conjunto QA vigente antes de repetir positivos. La app envía la hora actual; el detalle de causas y referencias se verifica en T04.

**Límite de las láminas:** recapturar rostros sintéticos prueba integración, calidad de cámara y navegación; no mide precisión representativa ni verificación de identidad de una persona real. Para login Facebook usa tu rostro real y sus pasos normales. Si la captura de pantalla se rechaza por calidad, registra el motivo y ajusta encuadre; no desactives los controles.

## Casos de aceptación

### P — Preparación — responsable y evaluador

- [ ] **P01** — Recibe el APK, abre la tabla pública de acceso y recibe la ficha privada para las demás cuentas. Conserva como antecedente la instalación que ya declaraste; comprueba ahora versión completa, fecha y SHA-256 del APK instalado. Esperado: coincide con la versión que vas a evaluar.
- [ ] **P02** — Anota teléfono, versión Android, idioma inicial, commit y release del servidor en la cabecera del registro. Activa No molestar y oculta notificaciones. Esperado: ejecución identificable y pantalla lista para grabar.
- [ ] **P03** — Responsable: entrega las nueve cuentas de escenario y las cuentas QA de la ficha. Verifica avatar, publicaciones, roles, grupo y permisos antes de empezar. Si falta algo, marca BLOQUEADO; el evaluador no importa datos.
- [ ] **P04** — Abre las láminas enlazadas arriba en la computadora. Muestra un retrato grande y luego las tres caras juntas; ajusta brillo/zoom para evitar reflejos. Esperado: el teléfono puede encuadrarlas sin descargar archivos.
- [ ] **P05** — Prepara tu Facebook autorizado y un buzón real con tres direcciones o alias que reciban correo: A para C01, B para la cuenta pendiente y C como destino corregido de C03. Guarda claves solo en tu ficha privada. Esperado: recepción en A/B/C y acceso al Facebook de prueba.

### S — Servidor y sesión técnica

- [ ] **S01** — Responsable: consulta GET /health/live y GET /health/ready. Esperado: ambos 200; guarda hora y respuesta. Un fallo bloquea las pruebas dependientes.
- [ ] **S02** — Importa la colección pública de la guía API y deja No environment. Dentro de Server requests → 00 Live scenarios, ejecuta 01 Police, 02 Nursing y 03 Memory: 13 peticiones por carpeta, 39 en total. Esperado: acceso automático, expedientes/publicaciones de los espacios existentes, imágenes legibles y respuestas pertinentes. Guarda resultado de cada petición; no uses el antiguo espacio vacío como prueba de los escenarios.
- [ ] **S03** — Responsable: verifica la rotación con POST /v1/auth/refresh y rechazo del refresh anterior, usando una sesión QA independiente. Esperado: token nuevo válido y anterior rechazado; guarda respuestas sin tokens. Desactiva la auto-renovación en la petición negativa para probar el token consumido.

### A — Entrada y nueve cuentas preparadas

- [ ] **A01** — Abre Continuar con correo → Iniciar sesión; en Usuario o correo escribe elena-marquez y la contraseña de la tabla pública enlazada arriba. Esperado: accedes sin registrar la cuenta de nuevo.
- [ ] **A02** — Repite entrada, avatar y apertura de cada publicación con las nueve cuentas de la tabla. Esperado inicial: 2/3/2 publicaciones propias por los tres trabajadores de cada grupo; anota cambios legítimos desde el inventario. Guarda nueve resultados, no uno representativo.
- [ ] **A03** — En Trabajo selecciona el grupo asignado. Esperado inicial por grupo: siete publicaciones; Policía 9 registros, Clínica 20 y Memoria 18. Abre Registros del espacio para contarlos. Cada cuenta conserva su grupo, no los otros escenarios.
- [ ] **A04** — Cierra sesión, escribe una contraseña incorrecta una sola vez y luego la correcta. Esperado: error comprensible, sin acceso con contraseña errónea; el segundo intento permite entrar.
- [ ] **A05** — Cierra y vuelve a abrir la app, después cierra sesión y cambia de escenario. Esperado: sesión válida recuperada al reabrir; al cambiar de cuenta desaparecen datos y acciones pendientes de la anterior.

### C — Correo real y Facebook

- [ ] **C01** — Con una cuenta nueva QA y tu buzón real, usa Crear cuenta. Abre el correo y confirma. Esperado: remitente RealityOS <support@luxisoft.com>, enlace funcional y acceso confirmado. No uses example.test para esta prueba.
- [ ] **C02** — Intenta registrar el usuario/correo ya ocupado. Esperado: informa qué dato está ocupado y ofrece las acciones disponibles sin crear otra cuenta.
- [ ] **C03** — Registra otra cuenta QA con el alias B y conserva su enlace sin usar. Todavía pendiente, corrige el correo al alias C usando su usuario y contraseña actuales. Esperado: cambia el destino de esa misma cuenta, llega al nuevo buzón y el enlace anterior deja de confirmar. Mantén esta cuenta pendiente hasta C04.
- [ ] **C04** — En la cuenta pendiente de C03 prueba Reenviar confirmación al alias C y confirma con el último enlace. Esperado: recepción, confirmación y acceso correctos sin crear cuentas duplicadas.
- [ ] **C05** — Recupera la contraseña de la cuenta QA confirmada. Esperado: correo real, cambio correcto, acceso con contraseña nueva y rechazo de la anterior. Reutilizar el enlace consumido se rechaza.
- [ ] **C06** — Intenta corregir como pendiente una cuenta QA ya confirmada. Esperado: rechazo y conservación de su identidad/correo actuales. Responsable puede comprobarlo por API si la app ya no ofrece la acción.
- [ ] **C07** — Entra con Facebook real desde el teléfono y completa los permisos y pasos de identidad que muestre la app. Esperado: sesión real y perfil de esa cuenta; cancelación del flujo vuelve a una pantalla utilizable. No se sustituye por un token simulado.

### F — Perfil y documentos

- [ ] **F01** — En una cuenta QA por correo, edita nombre, ubicación, localidad, nacimiento y género; guarda y reabre. Esperado: persisten, la edad corresponde a la fecha y una fecha futura o anterior a 1900 se rechaza. Restaura los datos iniciales.
- [ ] **F02** — En Facebook verifica nombre y campos sincronizados de solo lectura; edita biografía/contacto permitidos y vuelve a entrar. Esperado: conserva las reglas de origen y refresca los datos Facebook disponibles.
- [ ] **F03** — Adjunta un CV sintético PDF/DOCX desde Editar y reemplázalo por una segunda versión preparada por el responsable. Esperado: una versión vigente y contexto actualizado; otra cuenta no puede descargar el CV privado. La descarga denegada se confirma también en T02.
- [ ] **F04** — Abre un perfil ajeno desde un candidato autorizado y pregunta «¿Cómo se llama este perfil?». Esperado: respuesta basada en información permitida; no expone publicaciones privadas ni el archivo CV.

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
- [ ] **O05** — Usa Buscar objeto con cámara para encuadrar una escena de las láminas. Esperado: procesa una consulta explícita y devuelve evidencia pertinente o un rechazo de calidad comprensible; para aprobar la recuperación positiva debe existir una captura válida con coincidencia.
- [ ] **O06** — En QA registra una foto nueva desde la app, espera que termine el procesamiento y luego búscala. Esperado: aparece con fuente/fecha nuevas. Consulta por sí sola no registra esa foto; T03 comprueba la separación.

### B — Búsqueda facial — no sustituir por abrir un expediente

- [ ] **B01** — Con elena-marquez en Clínica, completa el consentimiento que solicite la app y usa Buscar persona para capturar la lámina de Ana. Esperado: candidata Ana Solis, evidencia y similitud; abrirla llega a su expediente. Ajustar el encuadre es válido; omitir la búsqueda no aprueba el caso.
- [ ] **B02** — Con noah-brooks en Memoria captura la lámina de Luis. Esperado: candidato Luis Moreno y apertura de su expediente, sin traer candidatos de Clínica.
- [ ] **B03** — En Clínica captura las tres caras juntas de Ana, Robert y Fatima. Esperado: tres rostros detectados en una captura de calidad, asociación correcta entre cajas numeradas/colores y candidatos; abre uno y vuelve al resultado grupal.
- [ ] **B04** — Con qa-hackathon-admin, selecciona el grupo QA y captura el retrato de qa-hackathon-member de las láminas. Esperado: candidato de usuario, apertura de su perfil y contenido permitido. Su enrolamiento explícito se verifica antes; no se deduce del avatar.
- [ ] **B05** — Con qa-hackathon-reader sin consentimiento, intenta buscar una persona. Esperado: explicación/solicitud de consentimiento en la app; la API rechaza la búsqueda sin él. Conserva esta cuenta sin consentimiento para el negativo.
- [ ] **B06** — Captura una lámina de objetos sin rostro y después el retrato de Ana estando en QA. Esperado: error de ausencia de rostro en el primer caso y ningún enlace al expediente clínico en el segundo. Nunca inventa una identidad.
- [ ] **B07** — Responsable, al terminar los positivos: revoca consentimiento únicamente del miembro QA, comprueba exclusión de candidatos y eliminación de sus enrolamientos; vuelve a consentir y enrolar explícitamente su retrato para restaurar el conjunto. Guarda antes/después.

### G — Publicaciones, grupos y privacidad

- [ ] **G01** — Con qa-hackathon-member publica una foto y un video corto moviendo un objeto desde el teléfono, primero en Perfil y después en Trabajo → QA. Usa la nota «QA aceptación — foto/video». Esperado: cuatro publicaciones con destino correcto y apertura/reproducción.
- [ ] **G02** — Repite una foto idéntica y revisa la decisión de duplicado; cancela una sustitución y confirma otra. Esperado: la app explica la decisión, cancelar preserva el original y confirmar conserva el historial previsto.
- [ ] **G03** — Interrumpe la conexión durante una subida QA, restáurala y reintenta. Esperado: estado recuperable y ninguna publicación extra causada por repetir la misma operación.
- [ ] **G04** — En una publicación QA añade like, comentario y respuesta; reabre desde otra cuenta autorizada. Esperado: persisten y el hilo corresponde al comentario. Reporta solo contenido QA; confirma respuesta y visibilidad de moderación en la administración del grupo con qa-hackathon-admin, y su rechazo para reader, según T02.
- [ ] **G05** — Admin QA crea una invitación de un uso; el responsable entrega su código y la cuenta qa-hackathon-outsider. Introduce el código en Unirse (no el PIN compartido), intenta reutilizarlo y después retira al nuevo miembro. Esperado: primer acceso válido, reutilización rechazada y pérdida del acceso restringido al retirar. No uses ni elimines los grupos de escenario.
- [ ] **G06** — Desde otra cuenta, abre el perfil del autor QA. Esperado: solo publicaciones públicas permitidas; las privadas y las del grupo inaccesible no se exponen por compartir el enlace. Comprueba también los originales en T02.

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
- [ ] **D05** — En QA, elige el destino disponible desde Android y captura foto/video en Display. Revisa y confirma Publicar. Esperado: destino mostrado coincide con publicación; no se asume subida automática al Perfil.
- [ ] **D06** — Cancela una captura, descarta una pendiente y prueba reintentar tras recuperar conexión. Cambia de cuenta durante una operación. Esperado: navegación recuperable, sin publicar tras descartar ni restaurar imágenes privadas de otra sesión.

### U — Robustez del teléfono

- [ ] **U01** — Recorre Perfil / Trabajo / Buscar / Ray-Ban. Esperado: cabecera y cuenta correctas, acciones accesibles y regreso coherente.
- [ ] **U02** — Deniega por separado cámara y audio; después concédelos. Esperado: explicación del permiso faltante y continuación al conceder; no captura silenciosa.
- [ ] **U03** — Desconecta la red durante búsqueda y apertura de expediente; vuelve a conectar. Esperado: error/vacío/carga distinguibles y reintento útil, sin pantalla bloqueada.
- [ ] **U04** — En el visor pellizca, suelta el último dedo y arrastra varias veces. Esperado: imagen estable, sin saltos, desaparición ni coordenadas inválidas.
- [ ] **U05** — Con un borrador, abre teclado, rota y lleva la app al fondo; vuelve. Lee mensajes antiguos y recibe otro. Esperado: borrador conservado y scroll sin arrastrarte al final si estabas leyendo arriba.
- [ ] **U06** — Comprueba cuentas/perfil a 320 dp y texto al 200 % mediante un dispositivo/emulador configurado para ello; registra el entorno. Esperado: botones/campos utilizables y contenido accesible con scroll. Restaurar ajustes después.

### T — Evidencia del responsable técnico

- [ ] **T01** — Contrato: compara el OpenAPI público con tests/contracts/openapi.json, normalizando solo el orden de claves. Ejecuta las comprobaciones relevantes del Makefile y adjunta CI del commit evaluado. Esperado: diferencias explicadas/corregidas y pruebas aprobadas; una compilación no prueba cámara física.
- [ ] **T02** — Permisos: con sesiones QA comprueba 401 sin token, 403 sin rol/consentimiento, recursos ajenos no accesibles, privacidad de medios/CV y moderación. Prueba rechazo de IDs mal formados/inexistentes según el contrato, invitación consumida y revocación. Acepta 403/404 según ruta, no un 404 universal.
- [ ] **T03** — Evidencia: usa las regresiones de BYTEA, idempotencia, Query sin captura y Register consentido; verifica hash del original antes/después de traducción/refinamiento. SAM se comprueba con un observation_id válido del flujo Register, no con el ID de una publicación social.
- [ ] **T04** — Expedientes: verifica referencias/issues del comparador, versiones e idempotencia de importaciones, relaciones clínicas y rechazo de una baja que deje registros activos huérfanos. Usa fixtures aislados de tests, no borres pacientes de los escenarios. Confirma MP4 con petición Range y respuesta parcial 206.
- [ ] **T05** — Idiomas: información ya preparada se lee de DB; si falta, el flujo separado information/prepare puede generar y guardar traducciones. Comprueba ambas ramas y ausencia de sustitución silenciosa de idioma. No afirmar que toda apertura jamás llama al proveedor.
- [ ] **T06** — Proveedores: conserva evidencia de Muse/SAM/transcripción Live y WAV ElevenLabs autenticado; sin sesión se rechaza TTS. Ante fallo, no hay caída silenciosa a mock ni audio antiguo. Mock solo en pruebas aisladas, determinista y rotulado. No cambies producción a mock para aprobar.
- [ ] **T07** — Seguridad y errores: verifica claves de proveedor/JWT/DB ausentes del APK y evidencias; regresiones de 409, 422 y 429 en entorno aislado para no bloquear cuentas demo. Guarda resultados sin secretos. Confirma aislamiento de biometría respecto al registro de objetos.

### H — Cierre y envío de hackathon

- [ ] **H01** — Confirma en el portal fecha/hora límite, categoría, track, equipo y requisitos de participación vigentes. Guarda comprobante. La referencia recibida indica 4 nov 2026, 21:00 EST/Bogotá; no sustituye la comprobación del portal.
- [ ] **H02** — Revisa repositorio público, licencia del proyecto, derechos de pesos InsightFace, términos DAT y procedencia de recursos. Esperado: decisiones documentadas por el responsable, sin declarar derechos pendientes como aprobados.
- [ ] **H03** — Comprueba todos los casos P–T: sin pendientes, fallos ni bloqueos; evidencias correspondientes a la versión probada. Si cambió código/servidor, repite casos afectados y entrada → expediente → búsqueda → Display.
- [ ] **H04** — Graba el video real de tres minutos con los recorridos aprobados y las aportaciones del evento. Incluye búsqueda facial real con consentimiento, expediente, evidencia/SAM y Display simulado identificado como tal. Revisa las respuestas clínicas que se vean.
- [ ] **H05** — Abre el enlace del video sin sesión; revisa duración, audio, ausencia de secretos/notificaciones y enlaces de README. Esperado: el jurado puede ver la grabación; los videos conceptuales no la reemplazan.
- [ ] **H06** — Envía en el portal y guarda recibo, hora, proyecto y enlaces entregados. Esperado: confirmación de envío. Un push a GitHub o tener todas las pruebas aprobadas no es el envío.

## Resultado final

Hay **77 casos de aceptación P–T** y **6 de cierre/envío H**. Cobertura aprobada = casos P–T aprobados / 77 × 100. Ejecutar un caso fallido cuenta como ejecutado, pero no como aprobado. Toda variante de un caso debe pasar; un bloqueador conserva su lugar en el denominador.

- **Pruebas aprobadas:** 77/77, con evidencia y cero fallos/bloqueos/pendientes.
- **Entrega preparada:** pruebas aprobadas y H01–H05 completos.
- **Candidatura enviada:** H06 completo con recibo del portal.

Texto de cierre, solo cuando corresponda:

> El 100 % de los 77 casos de aceptación definidos para la versión [APK/hash], servidor [release], teléfono [modelo/Android] y Display simulado fue ejecutado y aprobado el [fecha], con evidencia [registro]. No incluye gafas físicas ni Windows local.

Las comprobaciones de preparación realizadas por el responsable se documentan aparte; esta plantilla no afirma que la sesión manual ya se haya ejecutado. El recibo del portal es la evidencia de envío. [Portal oficial](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit).

## Historial

Las marcas antiguas conservan su fecha y no acreditan esta ejecución.

<details>
<summary>Secciones históricas</summary>

<a id="checklist-por-fases--realityos"></a>
[↗ checklist-por-fases--realityos](reference/IMPLEMENTATION_CHECKLIST.legacy.md#checklist-por-fases--realityos)

<a id="fase-0--fundaciones"></a>
[↗ fase-0--fundaciones](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-0--fundaciones)

<a id="fase-1--api-persistencia-y-seguridad"></a>
[↗ fase-1--api-persistencia-y-seguridad](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-1--api-persistencia-y-seguridad)

<a id="fase-2--memoria-y-consultas"></a>
[↗ fase-2--memoria-y-consultas](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-2--memoria-y-consultas)

<a id="fase-3--meta-jobs-y-vídeo"></a>
[↗ fase-3--meta-jobs-y-vídeo](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-3--meta-jobs-y-vídeo)

<a id="fase-4--panel-web"></a>
[↗ fase-4--panel-web](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-4--panel-web)

<a id="fase-5--android-y-display"></a>
[↗ fase-5--android-y-display](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-5--android-y-display)

<a id="fase-6--operación-demo-y-entrega"></a>
[↗ fase-6--operación-demo-y-entrega](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-6--operación-demo-y-entrega)

<a id="criterios-finales-de-aceptación"></a>
[↗ criterios-finales-de-aceptación](reference/IMPLEMENTATION_CHECKLIST.legacy.md#criterios-finales-de-aceptación)

</details>
