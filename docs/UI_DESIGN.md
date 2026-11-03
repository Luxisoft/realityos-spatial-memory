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
