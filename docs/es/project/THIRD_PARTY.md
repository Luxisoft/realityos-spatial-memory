[English](../../en/project/THIRD_PARTY.md) · [Índice](../INDEX.md) · [Entrega](HACKATHON.md#rights)

# Terceros, recursos y derechos de uso

Revisión del **3 de noviembre de 2026**. El código propio conserva [Apache 2.0](../../../LICENSE). Esa licencia no cambia las condiciones de SDK, modelos, servicios o recursos de terceros. Esta revisión identifica las condiciones y la evidencia disponible; no acredita acuerdos privados que no se hayan aportado.

## Inventario verificable

El [inventario de dependencias](../../assets/legal/dependency-inventory.json) registra **93 paquetes Python** y **210 dependencias Android**, con versiones, metadatos de licencia y hashes de sus fuentes locales. Python corresponde al cierre de dependencias de ejecución y `faces` instalado en el entorno del host; Android corresponde a `debugRuntimeClasspath`, incluidos componentes transitivos y Mock Device Kit. Se resolvieron también las licencias heredadas de los POM padre.

El inventario es una fotografía del entorno identificado, no un archivo de bloqueo de versiones. No certifica por sí solo el contenido de todas las imágenes desplegadas, las bibliotecas del sistema ni futuras compilaciones. Al publicar el APK aprobado y otros binarios se deben conservar sus avisos y textos de licencia; el inventario enlaza sus fuentes y no los sustituye.

## Componentes y condiciones

| Componente | Uso y condición comprobada | Resultado de la revisión |
| --- | --- | --- |
| InsightFace 0.7.3, código | Detector y comparación facial en servidor; metadatos MIT. [Proveedor](https://github.com/deepinsight/insightface#license). | Identificado; conservar avisos MIT. |
| Pesos `buffalo_l` | El [Dockerfile](../../../backend/Dockerfile) descarga estos pesos. El proveedor los distingue del código y limita los modelos descargados a investigación no comercial; publica un contacto específico para licencias de reconocimiento. | **Autorización para este uso sin acreditar.** No se presupone que participar en una hackathon, publicar el código o no cobrar satisfaga esa condición. Registrar una autorización aplicable o una evaluación del uso concreto. |
| Meta DAT 1.0.1 | Core, Camera, Display y Speech; Mock Device Kit solo en Debug. La [licencia del SDK](https://github.com/meta/meta-wearables-dat-android/blob/main/LICENSE) remite a los [términos](https://wearables.developer.meta.com/terms) y la [política de uso](https://wearables.developer.meta.com/acceptable-use-policy). | **Texto autenticado y aceptación pendientes de evidencia.** Ambas páginas devolvieron una solicitud de inicio de sesión. No se deduce aprobación de biometría por disponer del SDK. |
| `meta-sam-parser` 0.1.0 | Parser del protocolo SAM; sus metadatos incluyen [SAM License](https://github.com/meta-models/meta-sam/blob/main/LICENSE). | Identificado. Mantener el acuerdo al redistribuir los materiales y reconocer su uso al publicar resultados; revisar sus restricciones de uso. El acceso a la API Meta tiene condiciones adicionales propias de la cuenta. |
| Facebook Android SDK 18.1.3 | Login y flujos autorizados de Facebook. [Facebook Platform License](https://github.com/meta/facebook-android-sdk/blob/main/LICENSE.txt). | Identificado. Uso ligado a servicios/API de Facebook, conservación del aviso y sujeción a políticas de plataforma. No se presenta como biblioteca MIT/Apache. |
| ONNX Runtime y bibliotecas Python/Android | Inferencia, HTTP, procesamiento y UI. El inventario distingue MIT, Apache, BSD, LGPL, MPL y licencias compuestas. | Metadatos inventariados. Las obligaciones dependen del componente y del artefacto distribuido; no se declara que todo sea Apache. |
| Muse, SAM y Transcribe por API | Servicios Meta usados desde el servidor. | Clave y acceso técnico no prueban una autorización de cualquier uso. Conservar las condiciones del acceso proporcionado para el evento. |
| ElevenLabs | Síntesis desde la cuenta del proyecto. [Términos del servicio](https://elevenlabs.io/terms-of-use). | El uso de salidas depende de las condiciones y plan de esa cuenta. Al grabar, utilizar una voz autorizada y conservar la evidencia de sus derechos. |

## Procedencia de los recursos

| Recursos | Evidencia y alcance |
| --- | --- |
| Portadas, miniaturas e ilustraciones Android | [Gráficos y prompts](GRAPHICS.md). Generación sintética documentada; no representan expedientes o pacientes reales. |
| Escenarios y medios de prueba | [Datos de espacios](../guides/WORKSPACE_DATA.md), [directorio social](../testing/SOCIAL_DIRECTORY.md) y [manifiesto organizado de medios](../../../simulator/media/manifest.csv). Conserva fuente, licencia, hash y ruta del recurso. El SQL versionado inicializa las filas locales; la preparación no carga archivos a almacenamiento remoto. |
| Copias históricas de evaluación en R2 | Los recibos privados anteriores conservan verificaciones de fuentes y hashes. Son evidencia histórica, no el conjunto local activo ni autorización para cargas nuevas. |
| Videos conceptuales de `demo-video/` | Se mantienen identificados como conceptuales. No se encontró un manifiesto de generación/licencia junto a esos cuatro archivos; su procedencia y los derechos de sus pistas deben quedar confirmados por quien los aportó si se incluyen en el envío. La grabación final es una entrega independiente. |
| Capturas finales de la app | Usar los datos sintéticos preparados y medios autorizados. La revisión de salidas clínicas y de datos visibles se realiza al ejecutar el checklist y grabar la demo. |

## Evidencia que falta para cerrar derechos

1. **InsightFace:** referencia de la autorización o evaluación aplicable a `buffalo_l`, titular, uso permitido y fecha. El proveedor indica `recognition-oss-pack@insightface.ai` para estos modelos. No se ha enviado ninguna comunicación en nombre del propietario.
2. **DAT:** versión o copia de los términos y política visibles con la cuenta Meta del proyecto, y constancia de aceptación/aplicabilidad al uso presentado.
3. **Material final:** confirmar procedencia de videos conceptuales si se reutilizan, condiciones de la voz y permisos de cualquier recurso ajeno incluido en la grabación. Se registra al cerrar el video.

Guardar contratos, correos y constancias privados en `.runtime/rights-evidence/`; publicar solo una conclusión y referencia no sensible. La revisión documental está realizada. El cierre de autorizaciones permanece pendiente de esa evidencia; no se ha modificado ni desactivado la función biométrica.
