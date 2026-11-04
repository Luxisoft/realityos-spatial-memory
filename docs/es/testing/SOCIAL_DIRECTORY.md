[English](../../en/testing/SOCIAL_DIRECTORY.md) · [API / Postman](../api/API.md) · [Documentación](../INDEX.md)

# Directorio social local

Meta Social Media tiene diez perfiles sintéticos buscables, cada uno con un avatar separado y tres fotos privadas de referencia. Sus tres cuentas de acceso publican una presentación ordinaria cada una usando sus avatares. El grupo también contiene tres publicaciones ordinarias de video. Las referencias privadas nunca aparecen como publicaciones, medios genéricos ni miniaturas de resultados.

Las filas de perfiles se instalan mediante el [SQL social versionado](../../../simulator/database/002-social-profiles.sql). La inicialización local utiliza el flujo de enrolamiento protegido existente y registra su finalización una sola vez. Los reinicios conservan ediciones y eliminaciones. Siguen vigentes pertenencia al grupo, consentimiento y permisos biométricos; instalar datos de prueba no autoriza otras cuentas ni personas nuevas.

| Ubicación | Finalidad |
| --- | --- |
| [Avatares](../../../simulator/media/meta-social/avatars/) | Imágenes separadas que pueden mostrarse como avatar de perfil. |
| [Referencias privadas](../../../simulator/media/meta-social/private-references/) | Tres referencias distintas por perfil sintético preparado. |
| [Avatares de cuentas](../../../simulator/media/shared/accounts/) | Imágenes de las nueve cuentas de acceso locales. |
| [Manifiesto de medios](../../../simulator/media/manifest.csv) | Fuente, licencia y SHA-256 de los recursos locales organizados. |

La aplicación consulta perfiles, membresías y publicaciones en PostgreSQL. No hay un directorio JSON ni otro catálogo de publicaciones para atender consultas. El SQL es una entrada de instalación; los cambios posteriores utilizan las tablas y APIs de la aplicación.

Los gráficos históricos conservados para regresiones están en `simulator/media/regression/`. No crean grupos retirados ni perfiles adicionales. El alcance local continúa siendo Police, Meta Social Media y Memory.
