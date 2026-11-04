[English](../../en/project/GRAPHICS.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Gráficos y procedencia

Las portadas y miniaturas se generaron con la herramienta de imágenes de Codex. Muestran personas ficticias e interfaces simuladas. El [logo original](../../../android/app/src/main/res/drawable-nodpi/icon_app.png) se conserva. Los gráficos sirven para presentar el proyecto; las pruebas ejecutadas se documentan en el [estado de implementación](IMPLEMENTATION_STATUS.md).

| Recurso | Uso |
| --- | --- |
| [banner-en.png](../../assets/readme/banner-en.png) · [banner-es.png](../../assets/readme/banner-es.png) | Portada por idioma |
| [example-police.png](../../assets/readme/example-police.png) | Escenario policial |
| [example-nursing.png](../../assets/readme/example-nursing.png) | Escenario de enfermería |
| [example-social.png](../../assets/readme/example-social.png) | Consulta de perfiles autorizados |
| [example-memory.png](../../assets/readme/example-memory.png) | Escenario de memoria |
| [face-lookup.svg](../../assets/readme/face-lookup.svg) | Flujo facial: retrato, representación, índice autorizado, candidatos y contexto |

Los prompts exactos se conservan en [HEADER_PROMPTS.json](../../assets/readme/HEADER_PROMPTS.json) y [THUMBNAIL_PROMPTS.json](../../assets/readme/THUMBNAIL_PROMPTS.json). Los originales mantienen su resolución; las portadas se muestran hasta 896 px de ancho y las miniaturas hasta 160 × 90 px. Los SVG y Mermaid permanecen editables, con explicaciones localizadas fuera de las imágenes.

El diagrama local del [README](../README.md#architecture) refleja los cuatro servicios de [Compose local](../../../infrastructure/docker-compose.local.yml), las tareas del [worker](../../../backend/app/tasks.py) y las [voces instaladas en Android](../../../android/app/src/main/java/com/luxisoft/realityos/MainActivity.kt). Las miniaturas enlazan los videos conceptuales conservados en `demo-video/`; la ilustración de perfiles representa una función, no un cuarto grupo inicial.

La procedencia de las ilustraciones de acceso Android está en [entry/PROMPTS.json](../../assets/entry/PROMPTS.json); se conservan porque acompañan recursos utilizados por la app.

El selector local muestra fotos de perfil y usa un [avatar ilustrado predeterminado](../../../android/app/src/main/res/drawable-nodpi/default_account_avatar.png) cuando falta la foto o no carga. Se generó con la herramienta de imágenes integrada; el prompt exacto está en [DEFAULT_AVATAR_PROMPT.json](../../assets/entry/DEFAULT_AVATAR_PROMPT.json).
