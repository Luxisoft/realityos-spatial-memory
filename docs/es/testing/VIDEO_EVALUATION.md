[EN](../../en/testing/VIDEO_EVALUATION.md) · [RealityOS](../README.md) · [Postman](../api/POSTMAN.md)

# Evaluación con videos reales

Doce grabaciones con licencia, cuatro por cada grupo existente. Muestran acciones completas con objetos identificables: recoger llaves, guardar pertenencias, preparar instrumental, transportar muestras y revisar evidencia. Los escenarios son ficticios; el análisis y la evidencia deben proceder del proveedor real.

En Postman: **Server requests → 00 Live scenarios → Police / Nursing / Memory → Video …**. Cada consulta lleva la cuenta, el grupo y la pregunta. Las cuentas públicas están en [API](../api/API.md#quick-start). En Android, entra con la misma cuenta, selecciona su grupo y utiliza la pregunta indicada.

La respuesta debe recuperar la publicación indicada, un fotograma dentro del intervalo, el objeto señalado por SAM y el original descargable. `gallery_matches` contiene la evidencia de publicaciones aunque `found` sea `false`: ese campo corresponde a Register. «Última observación» describe lo que quedó grabado; no prueba que el objeto siga allí. Una preferencia de idioma guardada en la cuenta prevalece sobre el idioma solicitado.

## Matriz de pruebas

### Policía

| Video y autor | Cuenta propietaria | Pregunta | Intervalo visible |
| --- | --- | --- | --- |
| [10482314](https://www.pexels.com/video/lifting-keys-from-ground-with-pliers-10482314/) · cottonbro studio | `alex-rivera` | Busca las llaves recogidas del suelo. | 0–11 s |
| [10482314](https://www.pexels.com/video/lifting-keys-from-ground-with-pliers-10482314/) · cottonbro studio | `alex-rivera` | Busca el marcador amarillo de evidencia. | 0–9 s |
| [10482446](https://www.pexels.com/video/technician-taking-picture-of-evidence-at-night-10482446/) · cottonbro studio | `alex-rivera` | Busca el maletín abierto de recolección de evidencias. | 0–26.76 s |
| [10482446](https://www.pexels.com/video/technician-taking-picture-of-evidence-at-night-10482446/) · cottonbro studio | `alex-rivera` | Busca la cinta de delimitación. | 0–26.76 s |
| [8382402](https://www.pexels.com/video/detective-reviewing-evidences-8382402/) · cottonbro studio | `maya-johnson` | Busca la lámpara articulada del escritorio. | 0–8 s |
| [8382402](https://www.pexels.com/video/detective-reviewing-evidences-8382402/) · cottonbro studio | `maya-johnson` | Busca las fotografías impresas sobre la mesa. | 0–8 s |
| [8963860](https://www.pexels.com/video/close-up-footage-of-a-man-using-walkie-talkie-8963860/) · Mikael Blomkvist | `daniel-kim` | Busca el radio de comunicación que sostiene en la mano. | 0–7.54 s |
| [8963860](https://www.pexels.com/video/close-up-footage-of-a-man-using-walkie-talkie-8963860/) · Mikael Blomkvist | `daniel-kim` | Busca los protectores auditivos amarillos alrededor del cuello. | 0–7.54 s |

### Enfermería

| Video y autor | Cuenta propietaria | Pregunta | Intervalo visible |
| --- | --- | --- | --- |
| [8413544](https://www.pexels.com/video/syringes-on-metal-tray-8413544/) · SHVETS production | `elena-marquez` | Busca las jeringas de la bandeja. | 0–8.4 s |
| [8413544](https://www.pexels.com/video/syringes-on-metal-tray-8413544/) · SHVETS production | `elena-marquez` | Busca las pinzas metálicas junto a la bandeja. | 0–8.4 s |
| [8381611](https://www.pexels.com/video/medical-practitioner-walking-in-the-hallway-while-holding-a-cart-with-samples-of-specimen-8381611/) · Pavel Danilyuk | `elena-marquez` | Busca el carro de material en el pasillo. | 0–9.68 s |
| [8381611](https://www.pexels.com/video/medical-practitioner-walking-in-the-hallway-while-holding-a-cart-with-samples-of-specimen-8381611/) · Pavel Danilyuk | `elena-marquez` | Busca los tubos de ensayo en el carro. | 3–9.68 s |
| [6036527](https://www.pexels.com/video/a-person-getting-dental-tools-from-the-drawer-6036527/) · Gustavo Fring | `mateo-rios` | Busca los instrumentos dentales dentro del cajón. | 0–15.215 s |
| [6036527](https://www.pexels.com/video/a-person-getting-dental-tools-from-the-drawer-6036527/) · Gustavo Fring | `mateo-rios` | Busca las pinzas del cajón de instrumental. | 0–15.215 s |
| [7585003](https://www.pexels.com/video/assisting-with-medical-equipment-7585003/) · cottonbro studio | `sarah-chen` | Busca las tijeras sobre la tela azul. | 0–21.76 s |
| [7585003](https://www.pexels.com/video/assisting-with-medical-equipment-7585003/) · cottonbro studio | `sarah-chen` | Busca el martillo del instrumental. | 0–21.76 s |

### Memoria

| Video y autor | Cuenta propietaria | Pregunta | Intervalo visible |
| --- | --- | --- | --- |
| [7986194](https://www.pexels.com/video/a-person-getting-keys-on-the-table-7986194/) · SHVETS production | `noah-brooks` | Busca las llaves sobre la mesa de madera. | 0–4.5 s |
| [7986194](https://www.pexels.com/video/a-person-getting-keys-on-the-table-7986194/) · SHVETS production | `noah-brooks` | Busca las gafas de sol oscuras. | 0–7.04 s |
| [5828599](https://www.pexels.com/video/a-person-putting-things-on-it-s-bag-5828599/) · Polina | `noah-brooks` | Busca el portátil junto a la mochila. | 0–19 s |
| [5828599](https://www.pexels.com/video/a-person-putting-things-on-it-s-bag-5828599/) · Polina | `noah-brooks` | Busca la billetera marrón. | 0–27 s |
| [5615158](https://www.pexels.com/video/top-view-of-cooking-vegetables-5615158/) · KATRIN BOLOVTSOVA | `lucia-vega` | Busca el rallador de cocina. | 0–26.1 s |
| [5615158](https://www.pexels.com/video/top-view-of-cooking-vegetables-5615158/) · KATRIN BOLOVTSOVA | `lucia-vega` | Busca la cuchara de madera. | 0–26.1 s |
| [8034068](https://www.pexels.com/video/man-looking-a-documents-8034068/) · Edmond Dantès | `owen-patel` | Busca los documentos con secciones amarillas. | 0–13.64 s |
| [8034068](https://www.pexels.com/video/man-looking-a-documents-8034068/) · Edmond Dantès | `owen-patel` | Busca las gafas redondas de montura metálica. | 0–13.64 s |

## Ausencias y permisos

Pregunta por un violín en cada grupo, en ES y EN: se espera `no_match` y ninguna evidencia inventada. Una cuenta de otro grupo debe recibir 403 al consultar el espacio y 403/404 al descargar su publicación.

## Procedencia y mantenimiento

Fuentes, autores, licencia, hashes y duración: [manifiesto de candidatos](../../../simulator/real-scenes/video-candidate-manifest.json). Preguntas, intervalos y publicaciones esperadas: [anotaciones de evaluación](../../../simulator/real-scenes/video-evaluation.json). Las anotaciones se prepararon revisando los videos y nunca se cargan como detecciones del modelo. Las revisiones conservan las preguntas iniciales que fallaron. Esta matriz es una demostración seleccionada, no una medición general de precisión. Se conservan las grabaciones completas, sin bucles, recortes arbitrarios ni ampliación desde baja resolución.

```bash
python scripts/prepare_evaluation_videos.py
# Run inside the authenticated backend runtime:
python scripts/renew_evaluation_videos.py --phase inventory --journal .runtime/video-evaluation/journal.json
python scripts/renew_evaluation_videos.py --phase stage --journal .runtime/video-evaluation/journal.json
python scripts/renew_evaluation_videos.py --phase index --journal .runtime/video-evaluation/journal.json
python scripts/verify_evaluation_videos.py --journal .runtime/video-evaluation/journal.json --output .runtime/video-evaluation/acceptance.json --resume
```

La activación exige 48 búsquedas positivas, seis negativas, seis pruebas de aislamiento, 12 descargas con hash correcto y revisión visual de los fotogramas. El recibo HTTP no aprueba por sí solo esa revisión visual. `activate` requiere además `--receipt` y `--credentials-file` privados; verifica por lectura ambas generaciones en el bucket, vincula su procedencia y selecciona la carpeta nueva para sincronización cada 15 minutos. Mantiene los identificadores de las 36 fotos y oculta solo los 12 videos sustituidos. `rollback`, con el mismo diario, recupera su visibilidad y la carpeta anterior verificada. No elimina los objetos externos.

## Estado de la ejecución

Candidatos cargados y análisis real en curso. La activación y la matriz completa aún no se han aprobado. La prueba física con Android y gafas se registra por separado.
