# Láminas de prueba — abrir en la computadora
[Checklist](IMPLEMENTATION_CHECKLIST.md) · [English](../../en/testing/QA_VISUAL_FIXTURES.md) · [Español](QA_VISUAL_FIXTURES.md)

Abre esta página renderizada en GitHub en la computadora. Haz clic en una imagen para ampliarla; apunta la cámara del teléfono a la pantalla. No descargues retratos al teléfono. En escenas con varias personas, muestra la imagen completa con zoom suficiente. Evita reflejos y encuadra solo las fotos.

**Datos sintéticos.** Reutilizar un retrato enrolado verifica integración, no precisión representativa. Se mantienen todos los permisos y controles de calidad. Estas imágenes no se usan para suplantar el login Facebook; ese recorrido usa tu propia cuenta y rostro.

<a id="meta-social"></a>
## Meta Social Media

Entra con Elena Marquez, Mateo Rios o Sarah Chen, selecciona Meta Social Media y acepta el consentimiento de búsqueda si la app lo solicita. Abre cualquiera de estos avatares en la computadora y usa la búsqueda de personas existente. Son trece perfiles adicionales, distintos de Policía y de las cuentas del selector.

Cada perfil tiene tres fotos diferentes de referencia privadas y un avatar separado. Los avatares de esta tabla no se enrolan; las 39 referencias no se publican en la galería ni se muestran como miniaturas de resultados. La búsqueda conserva su motor, umbrales, permisos y lógica existentes.

El registro y la importación Meta están representados por datos sintéticos locales; no se ha realizado OAuth ni una importación de Facebook. Los perfiles conservan procedencia interna y consentimiento de escenario. No se modifica el consentimiento de las tres cuentas de acceso.

| Perfil | Abrir avatar para consultar | Actividad |
| --- | --- | --- |
| Valentina Rojas | [Avatar](../../../simulator/media/meta-social/avatars/valentina-rojas.png) | Arquitecta sostenible |
| Mateo Silva | [Avatar](../../../simulator/media/meta-social/avatars/mateo-silva.png) | Ingeniero de sonido |
| Samira Haddad | [Avatar](../../../simulator/media/meta-social/avatars/samira-haddad.png) | Diseñadora de producto |
| Thiago Costa | [Avatar](../../../simulator/media/meta-social/avatars/thiago-costa.png) | Chef y emprendedor |
| Lucía Fernández | [Avatar](../../../simulator/media/meta-social/avatars/lucia-fernandez.png) | Médica rural |
| Noah Williams | [Avatar](../../../simulator/media/meta-social/avatars/noah-williams.png) | Fotógrafo documental |
| Camila Torres | [Avatar](../../../simulator/media/meta-social/avatars/camila-torres.png) | Bióloga marina |
| Diego Mendoza | [Avatar](../../../simulator/media/meta-social/avatars/diego-mendoza.png) | Técnico en robótica |
| Amina Diallo | [Avatar](../../../simulator/media/meta-social/avatars/amina-diallo.png) | Analista de datos |
| Ren Ito | [Avatar](../../../simulator/media/meta-social/avatars/ren-ito.png) | Ilustrador editorial |
| Gabriel Herrera | [Avatar](../../../simulator/media/meta-social/avatars/gabriel-herrera.png) | Perfil autorizado adicional |
| Adrián Navarro | [Avatar](../../../simulator/media/meta-social/avatars/adrian-navarro.png) | Perfil autorizado adicional |
| Paula Méndez | [Avatar](../../../simulator/media/meta-social/avatars/paula-mendez.png) | Perfil autorizado adicional |

<a id="search-cases"></a>
## Policía: escenas para probar búsquedas

Las cuatro escenas de `Personas/cases` se conservan completas y sin cambios. Según el propietario, cada una incluye tres personajes de `Personas/profile`, además de otras personas del entorno. Los diez retratos originales de referencia ya pertenecen a los expedientes policiales; las escenas nuevas son **solo entradas de consulta**, fuera de publicaciones y registros de cualquier grupo.

| Escena | Abrir imagen |
| --- | --- |
| Parque costero visto por una sola lente | [Caso 01](../../../simulator/media/regression/search/police/case-01.png) |
| Parque urbano tras la lente derecha | [Caso 02](../../../simulator/media/regression/search/police/case-02.png) |
| Parque urbano tras una lente derecha | [Caso 03](../../../simulator/media/regression/search/police/case-03.png) |
| Vida urbana junto al río | [Caso 04](../../../simulator/media/regression/search/police/case-04.png) |

Selecciona el grupo Policía con una cuenta autorizada y abre una escena en la computadora para la captura de consulta. No uses Publicar ni Registrar. No se asignaron identidades a las personas de cada escena: esa correspondencia no venía con los archivos. El [manifiesto](../../../simulator/media/manifest.csv) conserva procedencia, hashes y separación del contenido inicial; no otorga permisos ni consentimiento ni crea enrolamientos.

<a id="objects"></a>
## Expedientes policiales

### Pacific Ridge Police Department

Dieciséis expedientes de personajes ficticios tienen un retrato proporcionado por el propietario y una publicación vinculada. Cinco tienen orden de captura vigente y dos de ellas tienen procesos activos. Samuel Ortega, Elena Duarte, Isabel Mora y Natalia Campos tienen órdenes de búsqueda por desaparición independientes, sin órdenes de captura ni antecedentes. Se conservan las tres cuentas de acceso.

| Person / Persona | Portrait / Retrato | Status / Estado |
| --- | --- | --- |
| Adrián Salcedo | [PRP-0001](../../../simulator/media/police/portraits/person-01.png) | Orden vigente y proceso judicial |
| Esteban Pardo | [PRP-0002](../../../simulator/media/police/portraits/person-02.png) | Orden vigente y proceso judicial |
| Valeria Navarro | [PRP-0003](../../../simulator/media/police/portraits/person-03.png) | Orden vigente; sin proceso activo registrado |
| Lucía Cárdenas | [PRP-0004](../../../simulator/media/police/portraits/person-04.png) | Sin antecedentes, órdenes ni procesos |
| Tomás Beltrán | [PRP-0005](../../../simulator/media/police/portraits/person-05.png) | Sin antecedentes, órdenes ni procesos |
| Nicolás Acosta | [PRP-0006](../../../simulator/media/police/portraits/person-06.png) | Sin antecedentes, órdenes ni procesos |
| Mariana Solano | [PRP-0007](../../../simulator/media/police/portraits/person-07.png) | Sin antecedentes, órdenes ni procesos |
| Rafael Méndez | [PRP-0008](../../../simulator/media/police/portraits/person-08.png) | Sin antecedentes, órdenes ni procesos |
| Camila Fuentes | [PRP-0009](../../../simulator/media/police/portraits/person-09.png) | Sin antecedentes, órdenes ni procesos |
| Asha Mehta | [PRP-0010](../../../simulator/media/police/portraits/person-10.png) | Sin antecedentes, órdenes ni procesos |
| Bruno Escobar | [PRP-0011](../../../simulator/media/police/portraits/person-11.png) | Orden de captura vigente; sin condenas ni procesos activos |
| Daniel Serrano | [PRP-0012](../../../simulator/media/police/portraits/person-12.png) | Orden de captura vigente; sin condenas ni procesos activos |
| Samuel Ortega | [PRP-0013](../../../simulator/media/police/portraits/person-13.png) | Persona desaparecida con orden de búsqueda vigente; sin captura, antecedentes ni procesos |
| Elena Duarte | [PRP-0014](../../../simulator/media/police/portraits/person-14.png) | Persona desaparecida con orden de búsqueda vigente; sin captura, antecedentes ni procesos |
| Isabel Mora | [PRP-0015](../../../simulator/media/police/portraits/person-15.png) | Persona desaparecida con orden de búsqueda vigente; sin captura, antecedentes ni procesos |
| Natalia Campos | [PRP-0016](../../../simulator/media/police/portraits/person-16.png) | Persona desaparecida con orden de búsqueda vigente; sin captura, antecedentes ni procesos |


## Recursos para reemplazo de CV

[CV sintético v1](../../../simulator/media/regression/documents/cv-v1.pdf) · [CV sintético v2](../../../simulator/media/regression/documents/cv-v2.pdf). Usa solo una cuenta local desechable para probar carga y reemplazo; no incluyen información personal real.
