[English](../../en/testing/ACCEPTANCE_FIXTURES.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Recursos sintéticos de aceptación

Estos recursos se usan en el [checklist](IMPLEMENTATION_CHECKLIST.md) y las [láminas de cámara](QA_VISUAL_FIXTURES.md).

- [CV v1](../../../simulator/media/regression/documents/cv-v1.pdf): una página, cargo ficticio **Inventory assistant**.
- [CV v2](../../../simulator/media/regression/documents/cv-v2.pdf): sustitución, cargo ficticio **Equipment coordinator**.
- Ambos PDF contienen texto ficticio de QA, usan Helvetica y se generaron localmente.
- Las láminas reutilizan imágenes sintéticas de `simulator/media/regression/`.
- QA admin y miembro tienen enrolamientos sintéticos explícitos. Reader conserva la ausencia de consentimiento; outsider comienza fuera del grupo QA.
- Accesos privados, IDs y resultados se guardan en `.runtime/`. Los ejemplos Postman locales obtienen sus cuentas e IDs de una base aislada inicializada con SQL; no se publican credenciales.

Conserva el registro de cada ejecución antes de iniciar otra. Identifica el nuevo APK, release del servidor y fecha. Los recursos también forman parte de la preparación del [bucket demo](../guides/STORAGE_CONNECTIONS.md).
