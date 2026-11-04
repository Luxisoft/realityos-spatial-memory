[English](../../en/testing/SOCIAL_DIRECTORY.md) · [API / Postman](../api/API.md) · [Documentación](../INDEX.md)

# Directorio social local

Meta Social Media tiene trece perfiles sintéticos buscables, cada uno con un avatar separado y tres fotos privadas de referencia. Sus tres cuentas de acceso publican una presentación ordinaria cada una usando sus avatares. El grupo también contiene tres publicaciones ordinarias de video. Las referencias privadas nunca aparecen como publicaciones, medios genéricos ni miniaturas de resultados.

Las filas de perfiles se instalan mediante el [SQL social inicial](../../../simulator/database/002-social-profiles.sql) y la [adición de tres perfiles](../../../simulator/database/006-social-profiles.sql). La inicialización local utiliza el flujo de enrolamiento protegido existente y registra cada revisión una sola vez. Los reinicios conservan ediciones y eliminaciones. Siguen vigentes pertenencia al grupo, consentimiento y permisos biométricos; instalar datos de prueba no autoriza otras cuentas ni personas nuevas.

La adición contiene Gabriel Herrera, Adrián Navarro y Paula Méndez. Cada avatar proporcionado tiene tres referencias privadas distintas generadas con la herramienta de imágenes integrada, conservando la identidad del personaje en escenas de parque, terraza de café e interior junto a una ventana. La procedencia y los hashes permanecen en el manifiesto de medios. El directorio completo tiene trece avatares y treinta y nueve referencias privadas; ninguno de los perfiles nuevos amplía el selector de seis cuentas.

| Ubicación | Finalidad |
| --- | --- |
| [Avatares](../../../simulator/media/meta-social/avatars/) | Imágenes separadas que pueden mostrarse como avatar de perfil. |
| [Referencias privadas](../../../simulator/media/meta-social/private-references/) | Tres referencias distintas por perfil sintético preparado. |
| [Avatares de cuentas](../../../simulator/media/shared/accounts/) | Imágenes de las seis cuentas de acceso locales. |
| [Manifiesto de medios](../../../simulator/media/manifest.csv) | Fuente, licencia y SHA-256 de los recursos locales organizados. |

La aplicación consulta perfiles, membresías y publicaciones en PostgreSQL. No hay un directorio JSON ni otro catálogo de publicaciones para atender consultas. El SQL es una entrada de instalación; los cambios posteriores utilizan las tablas y APIs de la aplicación.

Los gráficos históricos conservados para regresiones están en `simulator/media/regression/`. No crean grupos retirados ni perfiles adicionales. El alcance local continúa siendo Police y Meta Social Media.
