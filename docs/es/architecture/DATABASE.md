# Datos y persistencia

[English](../../en/architecture/DATABASE.md) · [Documentación](../INDEX.md) · [API / Postman](../api/API.md)

PostgreSQL es la fuente de verdad de ambos entornos. Cuentas, grupos, permisos, expedientes, publicaciones y sus textos ES/EN se consultan en la base de datos. El instalador local importa los datos SQL una vez; la API no combina esas consultas con archivos de catálogo.

| Datos | Persistencia |
| --- | --- |
| Originales | `media_assets.original_bytes`; videos grandes en `media_asset_chunks.content`, ordenados y con hash completo. |
| Objetos | `tracked_objects` y `object_observations` conservan identidad lógica, evidencia y fecha de última observación. |
| Publicaciones | Grupo obligatorio; las copias comparten original y mantienen comentarios/reacciones independientes. `gallery_evidence` conserva evidencia versionada. |
| Expedientes | Registros, vínculos de medios y traducciones almacenados; acceso sujeto a pertenencia vigente. |
| Perfiles | Avatar separado de referencias privadas y CV. Las respuestas públicas no exponen originales privados. |
| Biometría | Consentimientos y enrolamientos protegidos, separados del flujo de objetos/publicaciones. |
| Acceso local | `local_access_accounts` relaciona exclusivamente las seis cuentas seleccionables con sus grupos. |
| Instalación local | Recibos versionados en BD evitan repetir inicializaciones o recuperar datos borrados al reiniciar. |

## Esquema nuevo y actualizaciones

El punto de entrada compartido es `python -m app.runtime.schema`. Para una base PostgreSQL vacía instala el SQL inmutable de `backend/schema/20261104_0040/`, registra esa revisión y aplica Alembic hasta `head`. El snapshot incluye índices y el diario histórico de cuarentena; no se calcula desde los modelos actuales durante el arranque.

Una base versionada existente solo recibe las migraciones pendientes. Una base con tablas y sin `alembic_version` se rechaza sin modificar sus datos. El bloqueo transaccional PostgreSQL coordina inicializadores concurrentes. Las migraciones históricas se conservan sin editar; la revisión `20261104_0041` añade la tabla de acceso local. El estado del código no indica qué revisión tiene actualmente el servidor.

Las pruebas usan PostgreSQL efímero, schemas aislados y el mismo instalador: verifican la base vacía, equivalencia con columnas/claves/índices de los modelos después de Alembic, idempotencia, rechazo de bases sin versión y conservación de una fila editada. SQLite se reserva a pruebas donde no hacen falta semánticas PostgreSQL.

## Datos y recursos de evaluación

`simulator/database/` contiene el conjunto SQL de instalación; `simulator/media/` contiene únicamente recursos locales organizados por uso, junto a `manifest.csv` de procedencia/licencia/hash. Los módulos de `app.local` validan el entorno antes de instalar. Sus recibos y cambios pertenecen a la misma transacción: un error no debe dejar una instalación marcada como completada.

El conjunto vigente tiene dos grupos y seis cuentas de acceso. Pacific Ridge Police Department tiene dieciséis retratos y expedientes enlazados a publicaciones, además de tres videos. Meta Social Media tiene presentaciones de sus tres cuentas, tres videos y trece perfiles sintéticos adicionales con referencias privadas. Los perfiles adicionales no amplían el selector de seis cuentas. El retiro local versionado elimina Sonoran/Memory y sus recursos exclusivos. Los reinicios conservan ediciones, eliminaciones, pertenencia y consentimientos de los grupos vigentes.

La carga inicial copia los archivos verificados a BYTEA. Las consultas posteriores utilizan la BD incluso si los recursos de instalación dejan de estar disponibles. Los originales de referencias biométricas nunca se publican; solo el avatar separado se muestra.

## Conservación y privacidad

Las conexiones S3/R2 son fuentes privadas del servidor y no sustituyen BYTEA. Cambiar o desconectar una fuente retira sus copias importadas, sin borrar objetos externos. Los bytes compartidos solo se retiran cuando no quedan referencias válidas de grupos, perfiles, expedientes o biometría.

Los cambios históricos de publicaciones personales/sin grupo no se recuperan con una reversión del esquema. Ningún comando de desarrollo autoriza modificar datos del servidor en uso. `make migrate ENV_FILE=.env.local` y `make seed ENV_FILE=.env.local` deben apuntar al entorno local elegido.

[Arquitectura](ARCHITECTURE.md) · [Expedientes](../guides/WORKSPACE_DATA.md) · [Seguridad](SECURITY.md)
