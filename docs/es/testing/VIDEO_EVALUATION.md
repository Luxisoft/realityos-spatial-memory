[EN](../../en/testing/VIDEO_EVALUATION.md) · [RealityOS](../README.md) · [Postman](../api/POSTMAN.md)

# Evaluación local de videos

El grupo Memory contiene cuatro grabaciones con licencia y dos objetos revisados por video. El SQL local instala sus bytes originales en la base de datos de la aplicación. Police contiene dieciséis publicaciones con retratos vinculadas a sus expedientes y tres videos; Meta Social Media contiene tres presentaciones de cuentas y tres videos. Las seis grabaciones añadidas están disponibles en las galerías de sus grupos. Los intervalos de objetos revisados que aparecen abajo corresponden a los cuatro videos de Memory.

En Postman abre **Localhost requests → 00 Local scenarios → Sonoran Neurological Institute → Video …**. Inicia los cuatro servicios locales y espera a que termine la indexación con tu clave privada de Meta. La selección de cuenta es automática y no requiere contraseñas publicadas. Server requests permanece desactivado.

Cada consulta debe recuperar la publicación esperada, un fotograma dentro del intervalo observado, localización SAM y la descarga original. `gallery_matches` contiene evidencia aunque `found`, propio de Register, sea `false`. «Última vez visto» describe evidencia grabada, no la ubicación actual del objeto. El idioma guardado en la cuenta prevalece sobre el solicitado.

## Matriz de pruebas

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

Busca un violín en ES y EN: no debe aparecer evidencia coincidente. Una cuenta ajena al grupo debe recibir 403 al consultar su espacio y 403/404 al descargar su publicación.

## Procedencia y reproducción

Las fuentes, licencias y hashes SHA-256 se conservan en el [manifiesto de recursos](../../../simulator/media/manifest.csv). La [matriz QA](../../../tests/fixtures/video-evaluation.json) contiene preguntas, intervalos observados e historial de anotaciones. No almacena IDs operativos de publicaciones ni se carga como detecciones del modelo. Al generar Postman se resuelve el hash de cada grabación contra la publicación instalada por el mismo SQL de la aplicación local.

```bash
make install
.venv/bin/python scripts/build_api_docs.py
make docs-check
```

La documentación se genera en una base SQLite aislada en memoria. No conecta a un runtime instalado, inicia sesiones ni llama a proveedores. PostgreSQL local sigue siendo la fuente de verdad del runtime.

## Evidencia de ejecución

El [recibo histórico del servidor](../../assets/storage/video-evaluation-verification.json) documenta la evaluación anterior y sus grupos retirados. No es un resultado del conjunto local actual. La validación nueva con modelos reales y dispositivos Android/gafas requiere otra ejecución sobre la instalación local inicializada.
