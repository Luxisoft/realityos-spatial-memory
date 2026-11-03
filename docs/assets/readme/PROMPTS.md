# README graphics / Gráficos del README

[English project](../../../README.md) · [Proyecto en español](../../../README.es.md)

The headers were generated and localized with Codex's built-in image tool. They depict fictional adults and a simulated interface; they are not screenshots or hardware validation. The supplied [app logo](../../../android/app/src/main/res/drawable-nodpi/icon_app.png) was the visual reference. The original logo asset is unchanged.

Las portadas se generaron y localizaron con la herramienta integrada de imágenes de Codex. Muestran adultos ficticios e interfaz simulada; no son capturas ni validación de hardware. El [logo de la app](../../../android/app/src/main/res/drawable-nodpi/icon_app.png) se usó como referencia visual. Su archivo original se conserva.

| Asset / Recurso | Purpose / Función |
| --- | --- |
| [banner-en.png](banner-en.png) · [banner-es.png](banner-es.png) | Compact biometric-search header / Portada compacta de búsqueda biométrica. |
| [example-police.png](example-police.png) | Independent police scenario / Ejemplo policial independiente. |
| [example-nursing.png](example-nursing.png) | Independent nursing scenario / Ejemplo de enfermería independiente. |
| [example-social.png](example-social.png) | Independent social scenario / Ejemplo social independiente. |
| [example-memory.png](example-memory.png) | Independent memory scenario / Ejemplo de memoria independiente. |
| [face-lookup.svg](face-lookup.svg) | Text-free facial lookup schematic / Esquema de búsqueda facial sin texto incrustado. |

The PNG masters preserve the generated resolution. READMEs limit header width to 896 px; with the generated aspect ratio this is under 300 px high, and scales down on narrower screens. Thumbnails display at up to 160 × 90 px, adapting to the table width. Their fictional scenes contain no embedded text, so both languages use the same assets with localized alt text and table descriptions. The SVG schematic uses icons and arrows; its explanation and the Mermaid architecture remain editable Markdown. Language buttons are local SVGs.

Los PNG conservan la resolución generada. Los README limitan la portada a 896 px de ancho: con su proporción queda por debajo de 300 px de alto y se reduce en pantallas estrechas. Las miniaturas se muestran hasta 160 × 90 px, adaptándose al ancho de la tabla. Sus escenas ficticias no llevan texto incrustado: ambos idiomas comparten recursos con textos alternativos y tablas localizados. El esquema SVG usa iconos y flechas; su explicación y la arquitectura Mermaid permanecen como Markdown editable. Los botones de idioma son SVG locales.

## English header prompt / Prompt de portada en inglés

```text
Create an original professional software-project README banner for RealityOS. Use the provided image only as the EXACT app logo reference: preserve its blue square and white circular arrow mark, do not invent a new logo. Canvas request: very wide horizontal 1200 x 300 pixels, exactly 4:1 aspect ratio, designed to remain readable at no more than 300px displayed height. This is a compact header, not a poster. Deep navy background with restrained electric blue accents and clean white typography. Left third: actual supplied app logo beside the large word "RealityOS"; under it two concise lines "Facial recognition" and "Connected records. Spatial memory." Small readable footer "Simulated demonstration". Right two thirds: photorealistic fictional adult woman wearing black Ray-Ban smart glasses, shown three-quarter profile looking toward a different fictional adult person with a clearly visible face; elegant subtle blue facial bounding box around that other person's face. Foreground Android phone showing a polished RealityOS biometric search software mockup with that same other person's portrait, a clean facial bounding box, a matching candidate portrait, the exact labels "Face search", "Candidate", and "Open record". Make the smartphone and the relationship between the glasses, face and candidate record understandable in the small height. Sophisticated product photography composition for software engineers. All people entirely synthetic, not celebrities. The result represents a consensual biometric demo, not live surveillance. Do not use identification probability percentages, police badges, weapons, real personal names, real accounts, secret keys or invented official partnerships. No calendars, lamps, flashlight props, decorative clipart or floating app icons. No extra text. Keep all subjects, wordmark and logo within the 4:1 safe margins; opaque background.
```

## Spanish localization prompt / Prompt de localización al español

```text
Create the Spanish localization of this exact compact RealityOS README banner. Preserve the existing app logo exactly, the two fictional adults, the woman with Ray-Ban smart glasses, the biometric bounding boxes, smartphone composition, lighting, deep navy and blue colors, opaque background and wide aspect ratio. It will be displayed at 900 x 300 pixels maximum. Keep every "RealityOS" wordmark and Ray-Ban branding unchanged. Replace "Facial recognition" with exactly "Reconocimiento facial". Replace "Connected records. Spatial memory." with exactly "Expedientes conectados. Memoria espacial." Use clean line wrapping if necessary, without overlapping the woman's face. Replace "Simulated demonstration" with exactly "Demostración simulada". In the phone replace "Face search" with exactly "Búsqueda facial", "Candidate" with exactly "Candidato", and "Open record" with exactly "Ver expediente". All explanatory text in Spanish with correct accents. No new elements, no percentages, no extra text. Keep it a restrained professional software README header.
```

## Thumbnail prompts / Prompts de miniaturas

The four thumbnails were generated with Codex's **built-in image generation**, without external reference photos. Exact prompts are preserved in [THUMBNAIL_PROMPTS.json](THUMBNAIL_PROMPTS.json). They request fictional adults, realistic scenes, a coherent navy/blue palette, no text or logos, and a simple composition readable at thumbnail size. These are illustrative previews, not product screenshots or evidence of a completed device test.

Las cuatro miniaturas se generaron con **generación de imágenes integrada de Codex**, sin fotos externas de referencia. Los prompts exactos están en [THUMBNAIL_PROMPTS.json](THUMBNAIL_PROMPTS.json). Solicitan adultos ficticios, escenas realistas, paleta azul coherente, ausencia de textos y logos y una composición legible a tamaño de miniatura. Son vistas conceptuales, no capturas del producto ni evidencia de una prueba en dispositivo.

## Diagram specification / Especificación del diagrama

Use native SVG with five icon groups linked by directed arrows: input portrait, facial representation, authorized workspace index, ranked candidates and profile/record lookup. No visible text, paragraphs or decorative objects in the SVG. Keep enrollment explicit and prior to lookup in the surrounding explanation; describe `matches` and `matches_records` there. Mermaid shows separate biometric, record/profile and object-processing components. Similarity is not an identity probability. The four example scenes have no connecting arrows.

SVG nativo con cinco grupos de iconos enlazados por flechas: retrato de entrada, representación facial, índice autorizado del espacio, candidatos ordenados y perfil/expediente. Sin texto visible, párrafos ni objetos decorativos en el SVG. Explicar fuera de la imagen el enrolamiento explícito previo y los campos `matches` y `matches_records`. Mermaid muestra por separado biometría, expedientes/perfiles y procesamiento de objetos. La similitud no es probabilidad de identidad. Las cuatro escenas de ejemplo no están conectadas mediante flechas.
