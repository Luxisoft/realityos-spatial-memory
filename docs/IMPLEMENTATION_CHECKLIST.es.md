<p align="center"><a href="IMPLEMENTATION_CHECKLIST.md"><img src="assets/readme/language-en.svg" alt="English" height="32"></a> <a href="IMPLEMENTATION_CHECKLIST.es.md"><img src="assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Comprobaciones de aceptación

[← Documentación](README.es.md) · [API / Postman](API.es.md)

## Guía de lectura

| Tema | Qué debes saber |
| --- | --- |
| **API y permisos** | Verificar autenticación, roles, aislamiento de espacios y lectura de medios; no marcar aprobado sin ejecución. |
| **Evidencia** | Comprobar original BYTEA, idempotencia, última observación, ausencia de evidencia y consultas sin captura. |
| **Biometría** | Verificar consentimiento, autorización y candidatos; muestras sintéticas no miden precisión representativa. |
| **Cliente** | Comprobar EN/ES, carga/error, permisos, navegación y APK; pruebas físicas requieren registro independiente. |
| **Publicación** | Revisar secretos, enlaces, artefactos, resultado CI y requisitos de hackathon. El checklist original mantiene sus marcas históricas. |

```mermaid
flowchart LR
    N0["Cambio"] --> N1["Pruebas"] --> N2["Evidencia"] --> N3["Entrega"]
```

## Procedimientos y evidencia

La referencia original conserva los detalles técnicos, ejemplos y verificaciones fechadas en su idioma de origen. Las instrucciones de componentes retirados son historia; usa las guías de instalación actuales para operar.
[↗ Referencia original completa](reference/IMPLEMENTATION_CHECKLIST.legacy.md)
[API ](API.es.md) · [IMPLEMENTATION STATUS ](IMPLEMENTATION_STATUS.es.md) · [HACKATHON ](HACKATHON.es.md)

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
