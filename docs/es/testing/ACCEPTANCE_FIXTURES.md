[English](../../en/testing/ACCEPTANCE_FIXTURES.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Recursos sintéticos de aceptación

Estos recursos se usan en el [checklist](IMPLEMENTATION_CHECKLIST.md) y las [láminas de cámara](QA_VISUAL_FIXTURES.md).

- [CV v1](../../../simulator/acceptance/cv-v1.pdf): una página, cargo ficticio **Inventory assistant**.
- [CV v2](../../../simulator/acceptance/cv-v2.pdf): sustitución, cargo ficticio **Equipment coordinator**.
- Ambos PDF contienen texto ficticio de QA, usan Helvetica y se generaron localmente.
- Las láminas reutilizan imágenes sintéticas de `simulator/workspaces/assets/`.
- QA admin y miembro tienen enrolamientos sintéticos explícitos. Reader conserva la ausencia de consentimiento; outsider comienza fuera del grupo QA.
- Accesos privados, IDs y resultados se guardan en `.runtime/`. Las tres cuentas públicas autorizadas se describen en la [guía API](../api/API.md#quick-start).

Conserva el registro de cada ejecución antes de iniciar otra. Identifica el nuevo APK, release del servidor y fecha. Los recursos también forman parte de la preparación del [bucket demo](../guides/STORAGE_CONNECTIONS.md).
