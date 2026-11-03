# README graphics / Gráficos del README

[English project](../../../README.md) · [Proyecto en español](../../../README.es.md)

The headers were generated and localized with Codex's built-in image tool. They depict fictional adults and a simulated interface; they are not screenshots or hardware validation. The supplied [app logo](../../../android/app/src/main/res/drawable-nodpi/icon_app.png) was the visual reference. The original logo asset is unchanged.

Las portadas se generaron y localizaron con la herramienta integrada de imágenes de Codex. Muestran adultos ficticios e interfaz simulada; no son capturas ni validación de hardware. El [logo de la app](../../../android/app/src/main/res/drawable-nodpi/icon_app.png) se usó como referencia visual. Su archivo original se conserva.

| Asset / Recurso | Purpose / Función |
| --- | --- |
| [banner-en.png](banner-en.png) · [banner-es.png](banner-es.png) | Compact biometric-search header / Portada compacta de búsqueda biométrica. |
| [use-cases-en.svg](use-cases-en.svg) · [use-cases-es.svg](use-cases-es.svg) | Police, nursing, social and memory / Policial, enfermería, social y memoria. |
| [biometric-flow-en.svg](biometric-flow-en.svg) · [biometric-flow-es.svg](biometric-flow-es.svg) | Enrollment, search and candidate lookup / Enrolamiento, búsqueda y candidatos. |

The PNG masters preserve the generated resolution. READMEs limit header width to 896 px; with the generated aspect ratio this is under 300 px high, and scales down on narrower screens. Body diagrams are editable SVG source, drawn directly from the documented contracts; no generated decorative objects. Mermaid diagrams remain in the Markdown source. Language buttons are local SVGs.

Los PNG conservan la resolución generada. Los README limitan la portada a 896 px de ancho: con su proporción queda por debajo de 300 px de alto y se reduce en pantallas estrechas. Los diagramas del cuerpo son SVG editables, dibujados a partir de los contratos documentados. Los diagramas Mermaid permanecen en el Markdown. Los botones de idioma son SVG locales.

## English header prompt / Prompt de portada en inglés

```text
Create an original professional software-project README banner for RealityOS. Use the provided image only as the EXACT app logo reference: preserve its blue square and white circular arrow mark, do not invent a new logo. Canvas request: very wide horizontal 1200 x 300 pixels, exactly 4:1 aspect ratio, designed to remain readable at no more than 300px displayed height. This is a compact header, not a poster. Deep navy background with restrained electric blue accents and clean white typography. Left third: actual supplied app logo beside the large word "RealityOS"; under it two concise lines "Facial recognition" and "Connected records. Spatial memory." Small readable footer "Simulated demonstration". Right two thirds: photorealistic fictional adult woman wearing black Ray-Ban smart glasses, shown three-quarter profile looking toward a different fictional adult person with a clearly visible face; elegant subtle blue facial bounding box around that other person's face. Foreground Android phone showing a polished RealityOS biometric search software mockup with that same other person's portrait, a clean facial bounding box, a matching candidate portrait, the exact labels "Face search", "Candidate", and "Open record". Make the smartphone and the relationship between the glasses, face and candidate record understandable in the small height. Sophisticated product photography composition for software engineers. All people entirely synthetic, not celebrities. The result represents a consensual biometric demo, not live surveillance. Do not use identification probability percentages, police badges, weapons, real personal names, real accounts, secret keys or invented official partnerships. No calendars, lamps, flashlight props, decorative clipart or floating app icons. No extra text. Keep all subjects, wordmark and logo within the 4:1 safe margins; opaque background.
```

## Spanish localization prompt / Prompt de localización al español

```text
Create the Spanish localization of this exact compact RealityOS README banner. Preserve the existing app logo exactly, the two fictional adults, the woman with Ray-Ban smart glasses, the biometric bounding boxes, smartphone composition, lighting, deep navy and blue colors, opaque background and wide aspect ratio. It will be displayed at 900 x 300 pixels maximum. Keep every "RealityOS" wordmark and Ray-Ban branding unchanged. Replace "Facial recognition" with exactly "Reconocimiento facial". Replace "Connected records. Spatial memory." with exactly "Expedientes conectados. Memoria espacial." Use clean line wrapping if necessary, without overlapping the woman's face. Replace "Simulated demonstration" with exactly "Demostración simulada". In the phone replace "Face search" with exactly "Búsqueda facial", "Candidate" with exactly "Candidato", and "Open record" with exactly "Ver expediente". All explanatory text in Spanish with correct accents. No new elements, no percentages, no extra text. Keep it a restrained professional software README header.
```

## Diagram specification / Especificación de diagramas

Use native SVG, white cards on a light background, dark technical typography and blue/teal/purple service accents. Show directed edges and short labels. The use-case diagram has one row for each actor, input, capability and result. The biometric diagram separates authorized enrollment from read-only search, connects the workspace index to cosine-similarity ranking, and distinguishes `matches` from `matches_records`. Keep English and Spanish layouts equivalent. Do not merge biometric processing with the object pipeline or represent similarity as an identity probability.

SVG nativo, tarjetas blancas sobre fondo claro, tipografía técnica oscura y acentos azul/verde/morado. Flechas dirigidas y etiquetas cortas. Una fila por caso de uso: entrada, capacidades y resultado. Separar enrolamiento autorizado y búsqueda biométrica; conectar el índice del espacio con el ranking por similitud coseno; distinguir `matches` de `matches_records`. Mantener composiciones equivalentes EN/ES. El procesamiento de objetos permanece separado de la biometría; la similitud no representa probabilidad de identidad.
