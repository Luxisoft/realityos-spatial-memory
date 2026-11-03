# Identidad visual Android y autenticación

Android es la única app. El panel web y la web Display fueron retirados por
instrucción del propietario. Las páginas de confirmación y recuperación, y los
correos HTML con alternativa de texto, usan el tema de `RealityTheme.kt`.

Fondo `#262729`, texto `#F4F7F5`, acento `#62A9F8`, bordes `#363D45`,
tipografía sans del sistema y radios de 12 px. Los formularios tienen etiquetas
visibles, foco accesible, mensajes de estado y traducciones ES/EN.
El botón Continuar con correo abre ingreso, con enlaces para registro,
recuperación y reenvío. No se cambia el tema general Android.

## Native Meta Display and Android host — 2026-10-31

Keep the current LUXISOFT dark/blue Android tokens and system type scale.
The native DAT Display uses its supported built-in styles and icons. Home
contains only the product name, current destination and Search/Capture.
Search distinguishes app gallery from location registry before listening.

Evidence occupies a fixed landscape plate: contain the entire annotated image
inside a 600×280 black canvas, leaving space for last-seen date, visual
confidence, partial/simulated status and grouped navigation. Put title, notes,
voice replay and another query on the separate result actions screen. This
keeps portrait sources intact and avoids stacking full-width navigation rows.

The phone owns destination selection, connection state and recovery controls;
its existing Preview/Glasses/Controls navigation remains. The optical shell
and Debug-only camera view remain intact, now with an elapsed recording label.


## Compact shared Android profile header — 2026-11-02

The authenticated phone host uses one fixed 96 dp profile header below the
status inset: menu/back, 48 dp avatar with owner edit action, name/email, and
Facebook above Ray-Ban actions. Existing dark/blue tokens and system typography
remain. Location, hometown and other profile details begin collapsed; the
expanded details scroll within 40% of the window. The header is shared across
Profile, Work, Search and Ray-Ban; destination controls use a compact contextual
row. Full-screen media and login keep their dedicated presentation. Visited
profiles reuse the header without owner controls. Resume upload lives inside
Edit profile; EN/ES is a segmented selector inside the menu, persisted to the
account with an inline retryable save error. Identity reference photos never
form the publication grid; explicit phone/glasses photos and MP4s do.


## Formularios Android de cuenta — revisión gráfica

Ingreso, registro, recuperación, reenvío y confirmación comparten cabecera con
regreso y marca, una composición vectorial de observaciones conectadas y un
símbolo por acción. Los dibujos se renderizan localmente con Canvas e iconos
vectoriales; no hay bitmaps ni descargas de recursos. La ilustración cede espacio
al formulario al abrir el teclado. Registro usa una versión más compacta.

El fondo sigue siendo `#262729`, los campos usan `#2D3034`, texto secundario
`#AAB4AF` y acento `#62A9F8`. Título de 27 sp, campos con iconos y radios de 12 dp,
acción principal de al menos 56 dp, objetivos táctiles de 48 dp y márgenes de
24 dp. El texto oscuro del botón azul mejora su legibilidad sin cambiar el
tema general. Se conserva una sola pantalla de registro.

Los errores aparecen junto al campo al salir o enviar, con foco en el primer
error. El envío se bloquea únicamente durante la petición. Hay autofill,
Siguiente/Hecho, visibilidad de contraseña y estados de confirmación con correo
destinatario, corrección y reenvío. Las respuestas conservan la protección contra
enumeración de cuentas. Los gráficos son decorativos para TalkBack; los controles
tienen etiquetas y los mensajes anuncian sus cambios. Textos ES/EN.

`AccountEntryTest` recorre estados reales Compose y genera capturas en
`android/app/build/outputs/account-design/` con renderizado nativo Robolectric.
Incluye 320, 390 y 480 dp y texto al 200 %. Son capturas de Android en pruebas,
no una prueba de teléfono físico.

## Acceso inicial y Explora RealityOS — 2026-11-03

La entrada Facebook/correo comparte los márgenes, escala tipográfica, botones
de 56 dp y paleta del flujo de cuenta aprobado. La cabecera de marca y una
ilustración 3D introducen «Tu mundo, con contexto». El consentimiento existente
conserva su texto y funcionamiento; correo sigue siendo independiente. Carga
y error tienen estados visibles, y Explora RealityOS queda como acción secundaria.

El carrusel contiene seis escenas: visión general, policía, enfermería,
conexiones sociales, memoria visual y Android/gafas. Cada una tiene una
ilustración, una explicación breve y un ejemplo práctico. La evidencia siempre
se describe como última observación; los expedientes y perfiles requieren
autorización. Las escenas gráficas son ilustrativas, no datos de la aplicación.

Los recursos 3D son WebP locales de 1024 × 683, generados con image_gen integrado;
las seis imágenes suman 187 288 bytes. Los prompts y la referencia de estilo
están en `assets/entry/PROMPTS.json`; los archivos consumidos por Android viven
en `android/app/src/main/res/drawable-nodpi/intro_*.webp`.

La navegación permanece manual: gesto horizontal, anterior y siguiente,
indicador accesible y salida explícita. El pie permanece visible y el contenido
se desplaza en pantallas pequeñas o con texto grande. La primera visita permite
Saltar/Comenzar y la repetición Cerrar/Volver a la app. El host conserva la
preferencia de bienvenida y el destino de regreso; el pager restaura su página.
Los créditos y enlaces del autor cierran el recorrido.

`EntryExperienceTest` comprueba controles y produce capturas nativas Compose en
`android/app/build/outputs/entry-design/`, también retenidas por CI. Comparar
ES/EN, 320/390/480 dp y texto al 200 % antes de modificar la composición.
