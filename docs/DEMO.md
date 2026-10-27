# Demo: Taller RealityOS

1. Inicie Compose en META_MODE=mock.
2. Ejecute el seed sintético e ingrese con la credencial configurada.
3. Seleccione Taller RealityOS. El seed crea Bodega A, tres estanterías,
   Nivel 2, mesa de trabajo y evidencia de los seis objetos demo: taladro
   amarillo, martillo, llave inglesa, destornillador, caja de herramientas y
   cargador de baterías.
4. In Query, ask: “Where is the yellow drill?”. The response
   muestra “visto por última vez”, geometría amarilla sobre foto BYTEA y el
   marcador SIMULADA.
5. Use Escuchar respuesta si el navegador soporta Web Speech.
6. En Registrar seleccione zona y cargue una foto. Consultar no incluye captura.
7. Abra /display/ para el recorrido compacto de Display.

El seed genera una ilustración propia con Pillow y no incluye fotos de terceros
ni clientes.

Para una prueba manual, explícita y con consentimiento usando fotos propias,
consulte [Manual photo test](MANUAL_PHOTO_TEST.md).
