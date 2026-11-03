<p align="center">
  <a href="DEMO.md"><img src="assets/readme/language-en.svg" alt="Read in English" height="32"></a>
  <a href="DEMO.es.md"><img src="assets/readme/language-es-active.svg" alt="Español — seleccionado" height="32"></a>
</p>

# Recorridos de evaluación

**[Checklist operativo de aceptación](IMPLEMENTATION_CHECKLIST.es.md)** · [Láminas listas para cámara](QA_VISUAL_FIXTURES.es.md). Registra pruebas manuales y evidencia técnica por versión antes de cerrar la entrega.

Estos recorridos son ejemplos independientes de las capacidades de RealityOS. No forman una secuencia entre organizaciones ni agotan sus usos posibles. Cada prueba usa los datos y permisos de su propio espacio.

[← Proyecto](../README.es.md) · [Entrega de hackathon](HACKATHON.es.md) · [Android](../android/README.es.md)

<a id="access"></a>

## Entrar y ver los datos preparados

**Las nueve cuentas tienen foto de perfil, publicaciones y un grupo de trabajo asignado.** Los retratos de Ana, Luis y las demás personas forman parte de sus expedientes. El evaluador no tiene que descargar imágenes, importar JSON, subir fotos ni crear grupos para empezar.

1. Descarga **app-debug.apk** y usa una de las tres [cuentas públicas incluidas](API.es.md#quick-start). Para Postman basta con importar la colección y pulsar **Send**.
2. Instala el APK habitual del servidor ([descarga e instalación](../README.es.md#evaluate)). Abre **Continuar con correo → Iniciar sesión**. Escribe el usuario en **Usuario o correo** y su contraseña de la tabla pública. Estas cuentas ya están confirmadas.
3. En **Perfil**, comprueba tu foto y abre una de tus publicaciones.
4. En **Trabajo**, selecciona el grupo indicado abajo y pulsa **Registros del espacio**. Abre el expediente inicial para ver su contenido y adjuntos dentro de la app.

| Escenario / grupo | Cuentas ya preparadas | Primer contenido |
| --- | --- | --- |
| Enfermería / California Valley Medical Center | `elena-marquez`, `mateo-rios`, `sarah-chen` | Ana Solis: expediente, retrato y registros relacionados. |
| Policial / Pacific Ridge Police Department | `alex-rivera`, `maya-johnson`, `daniel-kim` | Caso de prueba 1, notas y evidencia del turno. |
| Memoria / Sonoran Neurological Institute | `noah-brooks`, `lucia-vega`, `owen-patel` | Luis Moreno: expediente, retrato y recordatorio. |

Cada cuenta pertenece a su grupo de trabajo y tiene su espacio personal. El servidor contiene **47 registros, 27 adjuntos y seis retratos enrolados**. Las tres cuentas principales y sus contraseñas están [publicadas para el jurado](API.es.md#quick-start), por autorización del propietario. Postman las utiliza automáticamente sobre estos mismos datos.

Comprobación HTTP del 3 de noviembre de 2026: las nueve cuentas acceden, sus avatares responden correctamente, cada una tiene dos o tres publicaciones propias y cada grupo tiene siete publicaciones. Se verificaron los seis retratos adjuntos y el rechazo de acceso entre grupos. Esta comprobación no sustituye una prueba física de Android o gafas.

### Si no ves lo esperado

| Situación | Qué hacer |
| --- | --- |
| No sé dónde entrar | Usa la app Android y **Continuar con correo → Iniciar sesión**. La dirección del servidor en el navegador no abre una app web. |
| El acceso no funciona | Usa usuario y contraseña de la misma fila de la tabla pública. Estas cuentas ya están confirmadas y sus direcciones `example.test` no reciben correos de recuperación. |
| Solo veo Postman Demo o un espacio vacío | Importa la colección pública actual y abre Police, Nursing o Memory; las tres cuentas y espacios ya están configurados. |
| No aparece mi foto, publicaciones o grupo | El responsable debe completar la cuenta antes de la prueba; el evaluador no tiene que preparar los datos. |

<a id="handoff"></a>

## Acceso público del jurado

Las [tres cuentas y contraseñas](API.es.md#quick-start) están incluidas en la colección pública. El propietario autorizó su publicación el 3 de noviembre de 2026. Se conservan sus roles y espacios actuales; no se crea otro servidor ni se duplican los datos.

Para Postman, importa la colección y pulsa Send. Para Android, instala el APK y usa una de esas cuentas. Las otras seis cuentas de trabajadores y las claves de proveedores, integraciones e infraestructura no se publican con esta entrega.

Los manifiestos [policial](../simulator/workspaces/security.json), [enfermería](../simulator/workspaces/hospital.json) y [memoria](../simulator/workspaces/memory.json) son material de mantenimiento. Los escenarios del servidor ya están importados. Para preparar otra instalación, el responsable sigue [datos e importaciones](WORKSPACE_DATA.es.md).

## 1. Policial: caso, persona y evidencia

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | En Trabajo, selecciona Pacific Ridge → Registros del espacio → caso de prueba 1. | Fuente, versión, evento relacionado y adjuntos. |
| 2 | Lee las notas del turno y abre la imagen de evidencia. | Original y contexto del espacio seleccionado. |
| 3 | Busca la linterna amarilla o el destornillador rojo. | Evidencia señalada, fuente y fecha de última observación. |
| 4 | Abre una publicación del turno y revisa su autor y grupo. | Publicación ya cargada y vinculada al espacio policial. |

El conjunto policial incluido contiene casos, eventos y objetos, sin expedientes persona enrolados. Los seis retratos preparados están en enfermería y memoria. Las alertas policiales automáticas y la conexión con una fuente institucional real siguen pendientes. [Video conceptual](../demo-video/policial_case.mp4)

## 2. Enfermería: expediente preparado → comparación

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | En Trabajo, selecciona California Valley Medical Center → Registros del espacio → Ana Solis. | Expediente ya cargado con su retrato; se abre dentro de la app. |
| 2 | Abre el retrato y vuelve a los registros relacionados. | Atención, prescripción y notas de Ana, con fuente y fechas. |
| 3 | Introduce los campos observados del ejemplo, incluida la concentración de **20 mg**, frente a la prescripción ficticia de **10 mg**. Confirma identidad y fecha en el formulario. | Diferencia de concentración con referencia a la prescripción. |
| 4 | Revisa Robert Lane y Fatima Nasser. | Alergia relacionada de Robert y administración previa de Fatima, con fechas y fuente. |

El comparador usa campos introducidos explícitamente: no lee automáticamente el envase, calcula dosis, prescribe ni registra administraciones. El profesional conserva la verificación clínica. [Video conceptual](../demo-video/nurse_case.mp4)

## 3. Perfil y publicaciones preparadas

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | En Perfil, comprueba el nombre y la foto de tu cuenta de prueba. | Perfil ya preparado con un avatar propio. |
| 2 | Abre una de tus publicaciones. | Foto o video del escenario con su autor y grupo. |
| 3 | Vuelve a Trabajo y revisa las publicaciones del grupo. | Contenido compartido por los tres trabajadores del escenario. |
| 4 | Para comparar los escenarios, cierra sesión y entra con otra cuenta entregada por el responsable. | Cada cuenta abre su propio grupo y mantiene sus permisos. |

El directorio sintético es independiente; no implica que todas sus cuentas estén disponibles para cada jurado. Las referencias Facebook son internas a sus flujos autorizados; no es una búsqueda facial global de Facebook. [Video conceptual](../demo-video/profile_found.mp4)

## 4. Memoria: persona, recordatorio y última observación

| Paso | Acción | Resultado esperado |
| --- | --- | --- |
| 1 | En Trabajo, selecciona Sonoran Neurological Institute → Registros del espacio → Luis Moreno. | Expediente autorizado con su retrato ya adjunto. |
| 2 | Abre su recordatorio y evento relacionados. | Contexto guardado, fechas, notas y fuente. |
| 3 | Pregunta dónde se vieron los documentos, las llaves de latón o el cuaderno azul. | Foto/fotograma señalado, ubicación y fecha de última observación. |
| 4 | Pregunta por un objeto sin evidencia. | Sin coincidencia o evidencia suficiente; ninguna ubicación inventada. |

La función recupera información registrada; no diagnostica ni trata condiciones de memoria. «Visto por última vez» no significa «sigue allí». [Video conceptual](../demo-video/memory.mp4)

La búsqueda facial es una prueba adicional con captura explícita y sus propios permisos y consentimientos. Tener un avatar o abrir un expediente no enrola automáticamente una cuenta. El responsable prepara por separado cualquier demostración facial.

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

[Estado de implementación](IMPLEMENTATION_STATUS.es.md) contiene las verificaciones fechadas. Este documento describe el guion; no declara una ejecución nueva de esos recorridos.

[← Proyecto](../README.es.md) · [English](DEMO.md)
