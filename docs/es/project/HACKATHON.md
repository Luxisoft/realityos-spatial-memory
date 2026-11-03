<p align="center">
  <a href="../../en/project/HACKATHON.md"><img src="../../assets/readme/language-en.svg" alt="Read in English" height="32"></a>
  <a href="HACKATHON.md"><img src="../../assets/readme/language-es-active.svg" alt="Español — seleccionado" height="32"></a>
</p>

# Entrega y revisión de requisitos

**[Checklist operativo de aceptación](../testing/IMPLEMENTATION_CHECKLIST.md)** · [Láminas listas para cámara](../testing/QA_VISUAL_FIXTURES.md). Registra pruebas manuales y evidencia técnica por versión antes de cerrar la entrega.

[← Proyecto](../README.md) · [Guion de demo](../guides/DEMO.md) · [Estado técnico](IMPLEMENTATION_STATUS.md)

**Fuente:** guía completa de participantes aportada por el propietario el 3 de noviembre de 2026, publicada en [Event Details](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details), y [bases oficiales](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver). La guía no prescribe una plantilla de README. Esta revisión organiza las evidencias que necesita el jurado y distingue requisitos de participación, entrega y documentación.

## Requisitos y evidencia

| Requisito de la guía | Evidencia / estado |
| --- | --- |
| Resolver uno de los problemas propuestos | **Encaje documentado:** Build for Your World, mediante capacidades reutilizables de reconocimiento, contexto y memoria. Los cuatro escenarios son ejemplos independientes. La categoría inscrita debe confirmarse. |
| Incorporar modelos Meta | **Implementado:** Muse Spark 1.3, SAM 3.1 y Muse Voice Transcribe, con [contratos](../integrations/META_INTEGRATION.md) y [proveedores](../../../backend/app/providers/). DAT es la interfaz de gafas; InsightFace y ElevenLabs son componentes distintos. No se exige usar todos los modelos enumerados en la guía. |
| Repositorio público / open source | **Verificado:** GitHub informa `PUBLIC` y licencia [Apache 2.0](../../../LICENSE). Las dependencias conservan sus propias condiciones. |
| Trabajo nuevo y aportaciones identificables | **Desglose disponible abajo.** Hay una base anterior al período de construcción indicado; no se presenta todo el repositorio como nuevo. |
| Video accesible de tres minutos | **Pendiente:** enlace a una grabación real centrada en aportaciones del evento. Los videos conceptuales no satisfacen por sí solos esta evidencia. [Guion de 180 segundos](../guides/DEMO.md#video). |
| Máximo cuatro participantes; representante y todos los integrantes declarados | **Pendiente de datos de inscripción.** No se deduce el equipo a partir de autores de Git ni se publica información privada. |
| Participantes admitidos y elegibles; bases aceptadas | **Comprobación en la inscripción:** aceptación, restricciones geográficas y de sanciones, afiliaciones excluidas y aceptación de bases. El repositorio no acredita esas condiciones personales. |
| Un proyecto por equipo y un track | **Pendiente de confirmación en CV:** Indie Developer o Startups, sin inventar la selección. |
| Enviar antes del 4 de noviembre, 21:00 EST | **Pendiente de comprobante:** [portal CV](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit). Equivale a las 21:00 de Bogotá. Publicar en GitHub no envía la candidatura. |
| Derechos de uso y cumplimiento de políticas | **Revisión abierta:** ver exclusiones y licencias abajo. No se declara cumplimiento integral. |

La guía distingue una primera fase de viabilidad y uso de Meta, una evaluación de 0–10 y una final con cinco proyectos por track. El texto recibido omite la tabla de puntuaciones; los pesos previamente publicados en las bases son impacto 30 %, herramientas Meta 25 %, profundidad técnica 20 % y demo 25 %. Las evidencias están en [capacidades y modelos](../README.md#architecture), [pruebas](../../../tests/) y [validaciones fechadas](IMPLEMENTATION_STATUS.md).

<a id="contributions"></a>

## Base y aportaciones del evento

La guía sitúa el kickoff el **26 de octubre** y la construcción del **27 de octubre al 4 de noviembre**. Se adopta conservadoramente el segundo intervalo, con fechas convertidas a **America/New_York (ET)**. Los timestamps de Git ayudan a localizar aportaciones; no prueban por sí solos cuándo se escribió cada línea ni determinan elegibilidad.

| Parte | Referencia revisable | Cómo presentarla |
| --- | --- | --- |
| Base hasta el 26, 23:49 ET | [`3ab8c63`](https://github.com/Luxisoft/realityos-spatial-memory/commit/3ab8c63) | Plataforma inicial, captura/consulta de objetos, despliegue, gateway y búsqueda ya existentes. Identificar como base. |
| Video acotado desde el 27, 00:01 ET | [`5bb0607`](https://github.com/Luxisoft/realityos-spatial-memory/commit/5bb0607) | Nuevas capacidades de video; el commit figura como 26, 23:01 en Bogotá, pero ya es 27 en ET. |
| Segmentación y gafas, 27 de octubre ET | [`a35c9ac`](https://github.com/Luxisoft/realityos-spatial-memory/commit/a35c9ac) · [`8babc43`](https://github.com/Luxisoft/realityos-spatial-memory/commit/8babc43) | Refinamiento SAM y host Android/DAT con captura y voz. |
| Biometría, social y localización, commit del 1 de noviembre ET | [`052471e`](https://github.com/Luxisoft/realityos-spatial-memory/commit/052471e) | Consentimiento/enrolamiento/búsqueda facial, perfiles y experiencia social. El commit agrupa trabajo: el registro técnico documenta sus verificaciones. |
| Expedientes y búsqueda facial de personas, 2 de noviembre ET | [`7f5f79d`](https://github.com/Luxisoft/realityos-spatial-memory/commit/7f5f79d) · [`99a83e0`](https://github.com/Luxisoft/realityos-spatial-memory/commit/99a83e0) | Registros versionados, relaciones, adjuntos y enlace explícito de retratos a expedientes. |

[Comparación de la base con el estado auditado](https://github.com/Luxisoft/realityos-spatial-memory/compare/3ab8c63...5e6fd89). La demo debe señalar las aportaciones concretas; usar la base para ejecutarlas no convierte esa base en trabajo nuevo. La guía contempla productos existentes para startups; no consta el track de este proyecto ni una resolución del organizador sobre la frontera kickoff/construcción.

## Revisión de proyectos excluidos

| Exclusión | Resultado de la revisión |
| --- | --- |
| IA que genere consejo médico | El [comparador](../../../backend/app/workspaces/clinical.py) coteja campos y no llama a un modelo; exige revisión profesional y no registra administraciones. La [consulta contextual](../../../backend/app/workspaces/search.py) prohíbe prescribir o autorizar medicación en su instrucción. Esto no demuestra que toda respuesta generada sea segura: falta revisar las salidas reales de la demo clínica. Mantener el caso como consulta de registros y discrepancias, sin consejo terapéutico. |
| RAG básico o analizador simple de imágenes | El proyecto incluye enrolamiento facial, evidencia visual persistida, segmentación, captura DAT e integración versionada. La demo debe demostrar estas implementaciones; una explicación o un chat aislado no sustituye la evidencia técnica. La decisión de admisión es del jurado. |
| Chatbot educativo simple; selección laboral; nutrición; personalidad; deporte | No son las funciones presentadas. Un perfil o CV autorizado no se describe como evaluación de personalidad ni selección de candidatos laborales. |
| Política o guerra | Los ejemplos documentados no son políticos ni militares. El escenario policial describe expedientes y evidencia autorizados, no predicción criminal ni decisiones automáticas. |
| Violaciones legales, éticas o de plataforma | Existen controles de espacio, consentimiento y candidatos sujetos a confirmación. Estos controles no equivalen a aprobación del organizador o del proveedor; confirmar condiciones aplicables, especialmente para biometría y gafas. |
| Código, datos o recursos sin derechos | Ver revisión de procedencia y licencias siguiente. No se ha cerrado una auditoría de todos los componentes transitivos. |

<a id="rights"></a>

## Procedencia y licencias

**Revisión realizada:** [terceros, recursos y derechos de uso](THIRD_PARTY.md), con inventario de 93 paquetes Python y 210 dependencias Android, versiones y fuentes de licencia. El código propio conserva [Apache 2.0](../../../LICENSE).

**Autorizaciones pendientes de evidencia:** uso de los pesos InsightFace `buffalo_l` y términos/política DAT disponibles con la cuenta Meta. La guía de terceros indica exactamente qué constancia falta. La procedencia de los videos y los derechos de la voz se cierran con el material final. La revisión documental no equivale a autorización de esos usos.

**Pendientes de cierre:** video de tres minutos, equipo/track, revisión de salidas de la demo, derechos de modelos y términos aplicables, y comprobante de envío. La documentación queda preparada para revisar esos puntos; no se declara aprobación ni elegibilidad completa.

[← Proyecto](../README.md) · [English](../../en/project/HACKATHON.md)
