<p align="center">
  <a href="DEMO.md"><img src="assets/readme/language-en.svg" alt="Read in English" height="32"></a>
  <a href="DEMO.es.md"><img src="assets/readme/language-es-active.svg" alt="Español — seleccionado" height="32"></a>
</p>

# Recorridos de evaluación

Estos recorridos son ejemplos independientes de las capacidades de RealityOS. No forman una secuencia entre organizaciones ni agotan sus usos posibles. Cada prueba usa los datos y permisos de su propio espacio.

[← Proyecto](../README.es.md) · [Entrega de hackathon](HACKATHON.es.md) · [Android](../android/README.es.md)

## Preparación

Instala el APK Debug y entra con una cuenta invitada. El servidor alojado tiene los datos preparados; Windows local empieza vacío. Cada función solicita sus permisos de cámara, audio, espacio y consentimiento biométrico.

| Caso | Cuenta / espacio | Datos de prueba |
| --- | --- | --- |
| Policial | `alex-rivera` / Pacific Ridge Police Department | [Manifiesto](../simulator/workspaces/security.json) |
| Enfermería | `elena-marquez` / California Valley Medical Center | [Retrato de Ana](../simulator/workspaces/assets/patient-ana.png) · [manifiesto](../simulator/workspaces/hospital.json) |
| Memoria | `noah-brooks` / Sonoran Neurological Institute | [Retrato de Luis](../simulator/workspaces/assets/patient-luis.png) · [manifiesto](../simulator/workspaces/memory.json) |
| Social | Dos miembros autorizados y enrolados del mismo espacio | [Directorio sintético](../simulator/social-directory/README.es.md) |

Usa la contraseña demo de la invitación. El operador puede recuperarla del archivo privado `.runtime/jury-access.json`. Descarga el retrato al teléfono para **Elegir foto**. Usar la misma foto de enrolamiento prueba la integración; no mide precisión sobre personas o imágenes nuevas.

## 1. Policial: caso, persona y evidencia

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | En Trabajo, selecciona Pacific Ridge y abre el caso de prueba 1. | Fuente, versión, evento relacionado y adjuntos. |
| 2 | Lee las notas del turno y abre la imagen de evidencia. | Original y contexto del espacio seleccionado. |
| 3 | Busca la linterna amarilla o el destornillador rojo. | Evidencia señalada, fuente y fecha de última observación. |
| 4 | Para probar rostro→expediente, autoriza y enrola primero un expediente ficticio dentro del espacio policial. Busca ese retrato. | Candidato enlazado al expediente; el operador confirma la coincidencia. |

El conjunto policial incluido contiene casos, eventos y objetos, sin expedientes persona enrolados. Los seis retratos preparados están en enfermería y memoria. Las alertas policiales automáticas y la conexión con una fuente institucional real siguen pendientes. [Video conceptual](../demo-video/policial_case.mp4)

## 2. Enfermería: rostro → expediente → comparación

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | En Buscar persona, selecciona el espacio clínico y el retrato de Ana Solis. | **Expediente candidato**, retrato de evidencia y similitud. |
| 2 | Confirma al candidato y abre el expediente. | Atención, prescripción, notas y registros relacionados de Ana. |
| 3 | Introduce los campos observados del ejemplo, incluida la concentración de **20 mg**, frente a la prescripción ficticia de **10 mg**. Confirma identidad y fecha en el formulario. | Diferencia de concentración con referencia a la prescripción. |
| 4 | Revisa Robert Lane y Fatima Nasser. | Alergia relacionada de Robert y administración previa de Fatima, con fechas y fuente. |

El comparador usa campos introducidos explícitamente: no lee automáticamente el envase, calcula dosis, prescribe ni registra administraciones. El profesional conserva la verificación clínica. [Video conceptual](../demo-video/nurse_case.mp4)

## 3. Social: rostro → perfil → contexto compartido

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | Utiliza dos miembros del mismo espacio con consentimiento y enrolamiento completados. | Autorización y perfil visible de cada miembro. |
| 2 | Busca al otro miembro con una foto o video autorizado. | **Usuario candidato**, evidencia facial y enlace a su perfil. |
| 3 | Abre el perfil y pregunta sobre información que haya puesto a disposición. | Contexto y medios autorizados; el archivo privado de CV no se expone como adjunto público. |
| 4 | Comprueba desde una cuenta sin permiso el acceso a medios restringidos. | El recurso restringido permanece inaccesible. |

El directorio sintético es independiente; no implica que todas sus cuentas estén disponibles para cada jurado. Las referencias Facebook son internas a sus flujos autorizados; no es una búsqueda facial global de Facebook. [Video conceptual](../demo-video/profile_found.mp4)

## 4. Memoria: persona, recordatorio y última observación

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | Selecciona el espacio de memoria y busca el retrato de Luis Moreno. | Candidato que enlaza a su expediente autorizado. |
| 2 | Abre su recordatorio y evento relacionados. | Contexto guardado, fechas, notas y fuente. |
| 3 | Pregunta dónde se vieron los documentos, las llaves de latón o el cuaderno azul. | Foto/fotograma señalado, ubicación y fecha de última observación. |
| 4 | Pregunta por un objeto sin evidencia. | Sin coincidencia o evidencia suficiente; ninguna ubicación inventada. |

La función recupera información registrada; no diagnostica ni trata condiciones de memoria. «Visto por última vez» no significa «sigue allí». [Video conceptual](../demo-video/memory.mp4)

<a id="video"></a>

## Grabar la demo de tres minutos

**Enlace a la grabación final: pendiente.** La guía exige un video accesible de tres minutos que destaque únicamente las funciones construidas durante la hackathon. Identifica la [base previa y las aportaciones nuevas](HACKATHON.es.md#contributions); los videos conceptuales son material auxiliar.

| Tiempo | Qué mostrar en el producto | Evidencia |
| --- | --- | --- |
| 0:00–0:15 | Problema, alcance y qué se añadió durante el evento. | Distinguir la base existente de las funciones que se van a demostrar. |
| 0:15–1:15 | Espacio autorizado, retrato de prueba, candidato facial y apertura del expediente. | Consentimiento, evidencia y similitud; confirmación humana del candidato. |
| 1:15–1:50 | Notas, relaciones y adjuntos del expediente. | Fuente, versión y contexto consultable. |
| 1:50–2:25 | Refinamiento SAM y evidencia de video añadidos durante el evento. | Fotograma, geometría y fecha de última observación; la consulta de objetos original es parte de la base. |
| 2:25–2:45 | Interacción Android/DAT que pueda ejecutarse realmente. | Indicar teléfono, gafas físicas o simulador; rotular cualquier simulación. |
| 2:45–3:00 | Un límite de permisos y el desglose de aportaciones. | Recurso restringido, enlace público al código y commits. |

Ensaya el recorrido antes de grabar. Elige un espacio con datos preparados y oculta secretos, notificaciones y datos ajenos a la demo. No presentes una escena conceptual como ejecución real ni afirmes una prueba con gafas físicas si solo se usó el teléfono. Comprueba que el enlace final abra sin solicitar acceso y añádelo al README y a la candidatura.

| Evidencia documentada | Pendiente |
| --- | --- |
| Seis retratos enrolados por API; consulta de Ana Solis con InsightFace vivo. | Evaluación con retratos independientes y datos representativos. |
| Importaciones HTTP, consultas contextuales, búsquedas de objetos y pruebas de permisos. | Fuente institucional real y recorridos completos con teléfono/gafas físicos. |
| Imágenes sintéticas y MP4 de escenas estáticas. | Grabación final del producto accesible al jurado. |

[Estado de implementación](IMPLEMENTATION_STATUS.md) contiene las verificaciones fechadas. Este documento describe el guion; no declara una ejecución nueva de esos recorridos.

[← Proyecto](../README.es.md) · [English](DEMO.md)
