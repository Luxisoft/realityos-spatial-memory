<p align="center">
  <a href="HACKATHON.md"><img src="assets/readme/language-en.svg" alt="Read in English" height="32"></a>
  <a href="HACKATHON.es.md"><img src="assets/readme/language-es-active.svg" alt="Español — seleccionado" height="32"></a>
</p>

# RealityOS — entrega de hackathon

[← Proyecto](../README.es.md) · [Guion de demo](DEMO.es.md) · [Estado técnico](IMPLEMENTATION_STATUS.md)

## Propuesta para el jurado

RealityOS conecta lo que una persona ve con información que puede consultar: reconocimiento facial hacia perfiles y expedientes autorizados, búsqueda contextual y memoria visual trazable. Android y el Display nativo de gafas Meta dan acceso por imagen, video, texto y voz. Los casos policial, enfermería, social y memoria muestran distintas aplicaciones de esos componentes.

**Tema propuesto:** *Build for Your World*. Es una propuesta de encaje, no una afirmación de la categoría registrada. El track y los integrantes deben coincidir con la inscripción del equipo. [Evento oficial](https://cerebralvalley.ai/e/meta-ai-developer-hackathon)

## Evidencia por criterio

Los pesos proceden de las [bases oficiales de Meta y Cerebral Valley](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), consultadas el **3 de noviembre de 2026**.

| Criterio | Qué muestra el proyecto | Dónde comprobarlo |
| --- | --- | --- |
| Impacto · 30 % | Resolver la separación entre persona, contexto y evidencia en cuatro recorridos concretos. | [Casos](../README.es.md#cases) y [pasos de evaluación](DEMO.es.md). No se presentan métricas de impacto no medidas. |
| Uso de Meta AI · 25 % | Muse Spark interpreta imagen/contexto, SAM señala evidencia y Muse Voice Transcribe procesa voz; DAT conecta la experiencia con gafas. | [Contratos Meta](META_INTEGRATION.md), [proveedores](../backend/app/providers/) y [Android](../android/README.es.md). InsightFace y ElevenLabs se identifican por separado. |
| Profundidad técnica · 20 % | BYTEA, permisos por espacio, enrolamiento explícito, importaciones versionadas, worker idempotente y evidencia persistida. | [Arquitectura](ARCHITECTURE.md), [API](API.md), [pruebas](../tests/) y [ejecuciones automáticas](https://github.com/Luxisoft/realityos-spatial-memory/actions/workflows/ci.yml). |
| Demo · 25 % | APK instalable, cuentas, datos sintéticos y recorrido con resultados comprobables. | [Guion](DEMO.es.md). Los videos conceptuales existentes no sustituyen la grabación final del software funcionando. |

## Material de entrega y estado

| Elemento | Estado del repositorio |
| --- | --- |
| Explicación y acceso al código | README EN/ES, diagramas y repositorio público con licencia Apache 2.0. |
| Qué se construyó | [Historial público](https://github.com/Luxisoft/realityos-spatial-memory/commits/main/), iniciado el 26 de octubre de 2026, y [registro de implementación](IMPLEMENTATION_STATUS.md). No se atribuyen al equipo los modelos, SDK o dependencias de terceros. |
| Instalación y acceso de evaluación | [APK/compilación](../android/README.es.md#build), cuentas demo y guías de servidor/Windows. Las contraseñas demo se entregan con la invitación; las claves de servicios son privadas. |
| Demo funcional y video | Guion preparado; falta añadir el enlace público de la grabación final del producto. La portada es una simulación gráfica. |
| Equipo y track | Confirmar representante, integrantes y selección registrada. Las bases contemplan una entrega por equipo en un único track. |
| Fuentes y derechos | Código bajo [Apache 2.0](../LICENSE), fixtures sintéticos y [procedencia de gráficos](assets/readme/PROMPTS.md). La licencia del proyecto no sustituye las licencias de modelos/SDK/otros componentes. |
| Registro de entrega | No hay comprobante de envío al portal dentro del repositorio. Publicar en GitHub no realiza esa entrega. |

La página pública fija el cierre en **4 de noviembre de 2026, 21:00 ET** (21:00 en Bogotá). El [portal de entrega](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit) es independiente de GitHub. [Calendario oficial](https://cerebralvalley.ai/e/meta-ai-developer-hackathon)

## Alcance de esta revisión

Se verificaron la página pública y las bases. La [guía detallada de participantes](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details) redirige al inicio de sesión; sus requisitos adicionales, campos del formulario y formato/duración exacta del video **aún no están verificados**. Completar esa revisión con la cuenta participante antes de enviar. Esta matriz no declara elegibilidad ni cumplimiento integral.

Las pruebas técnicas documentadas no sustituyen validación física de teléfono/gafas, integración institucional real ni evaluación representativa de reconocimiento. El comparador clínico coteja campos explícitos; no prescribe. El alcance del conjunto policial se detalla en el [guion](DEMO.es.md).

[← Proyecto](../README.es.md) · [English](HACKATHON.md)
