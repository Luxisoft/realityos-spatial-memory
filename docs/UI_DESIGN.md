# Dirección visual: panel y Display

**Público y trabajo principal.** Operadores de taller y jurados deben poder
comprobar, en segundos, que una respuesta procede de una observación real y no
de una conjetura.

**Tokens.** Papel de inventario `#F1F0EA`; tinta `#17211F`; azul de
calibración `#2355D9`; amarillo de evidencia `#F0BF24`; óxido de alerta
`#A95030`; niebla `#D7DDD7`.

**Tipografía.** Una pila condensada de sistema para títulos (`Arial Narrow`,
`Roboto Condensed`) recuerda etiquetas de almacén; una sans de sistema legible
para tareas; una monoespaciada para IDs, fecha y confianza.

**Layout.** El panel funciona como una hoja de inspección: una barra vertical
para decidir modo, una cabecera que declara espacio y estado, y una placa de
evidencia grande. Display elimina la navegación y conserva solo pregunta,
fotografía, última observación y acción de audio.

**Firma.** La *placa de evidencia* enmarca la foto con una regla de coordenadas
y una etiqueta de integridad: convierte el resaltado y el hash en parte de la
lectura, no en decoración. Esta elección evita la estética genérica de dashboard
y hace visible la promesa del producto.

**Accesibilidad.** Foco visible, contraste alto, controles de teclado, no se
depende solo de color y se respeta `prefers-reduced-motion`.


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
