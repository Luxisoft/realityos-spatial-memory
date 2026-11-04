-- Add missing public profile display translations after social profiles exist.
-- Original fields, private references, consent and membership are never changed.
-- Only the unchanged prepared copy qualifies; owner edits and deletions win.

-- Lucía Fernández
UPDATE user_profiles SET display_text = '{"headline": {"es": "Médica rural", "en": "Rural physician", "source": "Rural physician"}, "biography": {"es": "Trabajo en atención primaria y programas comunitarios de prevención. En mi tiempo libre cultivo plantas y recorro caminos de montaña.", "en": "I work in primary care and community prevention programs. In my spare time I grow plants and walk mountain trails.", "source": "I work in primary care and community prevention programs. In my spare time I grow plants and walk mountain trails."}, "gender": {"source": "Mujer", "en": "Female", "es": "Femenino"}, "hometown": {"source": "Cusco, Perú", "en": "Cusco, Peru", "es": "Cusco, Perú"}, "location": {"source": "Cusco, Perú", "en": "Cusco, Peru", "es": "Cusco, Perú"}}'
WHERE user_id = '284746e9ff385c44b7ececc2076d7efc'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Rural physician'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Médica rural'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Rural physician'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Rural physician'
  AND biography = 'I work in primary care and community prevention programs. In my spare time I grow plants and walk mountain trails.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Trabajo en atención primaria y programas comunitarios de prevención. En mi tiempo libre cultivo plantas y recorro caminos de montaña.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I work in primary care and community prevention programs. In my spare time I grow plants and walk mountain trails.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I work in primary care and community prevention programs. In my spare time I grow plants and walk mountain trails.'
  AND gender = 'Mujer'
  AND hometown = 'Cusco, Perú'
  AND location = 'Cusco, Perú'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Mujer' AND f.hometown = 'Cusco, Perú' AND f.location = 'Cusco, Perú');

-- Adrián Navarro
UPDATE user_profiles SET display_text = '{"headline": {"es": "Ingeniero de movilidad", "en": "Mobility engineer", "source": "Mobility engineer"}, "biography": {"es": "Trabajo en proyectos de movilidad urbana y espacios públicos. Los fines de semana salgo en bicicleta y cocino con amigos.", "en": "I work on urban mobility and public space projects. On weekends I cycle and cook with friends.", "source": "I work on urban mobility and public space projects. On weekends I cycle and cook with friends."}, "gender": {"source": "Hombre", "en": "Male", "es": "Masculino"}, "hometown": {"source": "Valencia, España", "en": "Valencia, Spain", "es": "Valencia, España"}, "location": {"source": "Valencia, España", "en": "Valencia, Spain", "es": "Valencia, España"}}'
WHERE user_id = '64894dc4a54d5d72809e9e2c16a6a45e'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Mobility engineer'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Ingeniero de movilidad'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Mobility engineer'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Mobility engineer'
  AND biography = 'I work on urban mobility and public space projects. On weekends I cycle and cook with friends.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Trabajo en proyectos de movilidad urbana y espacios públicos. Los fines de semana salgo en bicicleta y cocino con amigos.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I work on urban mobility and public space projects. On weekends I cycle and cook with friends.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I work on urban mobility and public space projects. On weekends I cycle and cook with friends.'
  AND gender = 'Hombre'
  AND hometown = 'Valencia, España'
  AND location = 'Valencia, España'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Hombre' AND f.hometown = 'Valencia, España' AND f.location = 'Valencia, España');

-- Samira Haddad
UPDATE user_profiles SET display_text = '{"headline": {"es": "Diseñadora de producto", "en": "Product designer", "source": "Product designer"}, "biography": {"es": "Investigo cómo hacer más accesibles los productos digitales. Me interesan la cerámica, las bibliotecas y los viajes en tren.", "en": "I research ways to make digital products more accessible. I enjoy ceramics, libraries and train travel.", "source": "I research ways to make digital products more accessible. I enjoy ceramics, libraries and train travel."}, "gender": {"source": "Mujer", "en": "Female", "es": "Femenino"}}'
WHERE user_id = '673b66dd7a2d56569464936f43445b7b'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Product designer'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Diseñadora de producto'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Product designer'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Product designer'
  AND biography = 'I research ways to make digital products more accessible. I enjoy ceramics, libraries and train travel.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Investigo cómo hacer más accesibles los productos digitales. Me interesan la cerámica, las bibliotecas y los viajes en tren.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I research ways to make digital products more accessible. I enjoy ceramics, libraries and train travel.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I research ways to make digital products more accessible. I enjoy ceramics, libraries and train travel.'
  AND gender = 'Mujer'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Mujer');

-- Thiago Costa
UPDATE user_profiles SET display_text = '{"headline": {"es": "Chef y emprendedor", "en": "Chef and entrepreneur", "source": "Chef and entrepreneur"}, "biography": {"es": "Dirijo una cocina de temporada con ingredientes de productores locales. Los fines de semana exploro mercados y nuevas recetas.", "en": "I run a seasonal kitchen using ingredients from local growers. On weekends I explore markets and new recipes.", "source": "I run a seasonal kitchen using ingredients from local growers. On weekends I explore markets and new recipes."}, "gender": {"source": "Hombre", "en": "Male", "es": "Masculino"}, "hometown": {"source": "São Paulo, Brasil", "en": "São Paulo, Brazil", "es": "São Paulo, Brasil"}, "location": {"source": "São Paulo, Brasil", "en": "São Paulo, Brazil", "es": "São Paulo, Brasil"}}'
WHERE user_id = '69bc07dea39954c7ac2eee33ff4b43da'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Chef and entrepreneur'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Chef y emprendedor'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Chef and entrepreneur'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Chef and entrepreneur'
  AND biography = 'I run a seasonal kitchen using ingredients from local growers. On weekends I explore markets and new recipes.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Dirijo una cocina de temporada con ingredientes de productores locales. Los fines de semana exploro mercados y nuevas recetas.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I run a seasonal kitchen using ingredients from local growers. On weekends I explore markets and new recipes.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I run a seasonal kitchen using ingredients from local growers. On weekends I explore markets and new recipes.'
  AND gender = 'Hombre'
  AND hometown = 'São Paulo, Brasil'
  AND location = 'São Paulo, Brasil'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Hombre' AND f.hometown = 'São Paulo, Brasil' AND f.location = 'São Paulo, Brasil');

-- Valentina Rojas
UPDATE user_profiles SET display_text = '{"headline": {"es": "Arquitecta sostenible", "en": "Sustainable architect", "source": "Sustainable architect"}, "biography": {"es": "Diseño espacios de bajo impacto ambiental y jardines para barrios urbanos. Disfruto el senderismo y la fotografía de arquitectura.", "en": "I design low-impact spaces and gardens for urban neighborhoods. I enjoy hiking and architectural photography.", "source": "I design low-impact spaces and gardens for urban neighborhoods. I enjoy hiking and architectural photography."}, "gender": {"source": "Mujer", "en": "Female", "es": "Femenino"}}'
WHERE user_id = '6f837252172c53a88002c110ede4733a'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Sustainable architect'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Arquitecta sostenible'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Sustainable architect'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Sustainable architect'
  AND biography = 'I design low-impact spaces and gardens for urban neighborhoods. I enjoy hiking and architectural photography.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Diseño espacios de bajo impacto ambiental y jardines para barrios urbanos. Disfruto el senderismo y la fotografía de arquitectura.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I design low-impact spaces and gardens for urban neighborhoods. I enjoy hiking and architectural photography.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I design low-impact spaces and gardens for urban neighborhoods. I enjoy hiking and architectural photography.'
  AND gender = 'Mujer'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Mujer');

-- Camila Torres
UPDATE user_profiles SET display_text = '{"headline": {"es": "Bióloga marina", "en": "Marine biologist", "source": "Marine biologist"}, "biography": {"es": "Estudio ecosistemas costeros y participo en proyectos de conservación marina. Practico natación y dibujo especies del Caribe.", "en": "I study coastal ecosystems and participate in marine conservation projects. I swim and draw Caribbean species.", "source": "I study coastal ecosystems and participate in marine conservation projects. I swim and draw Caribbean species."}, "gender": {"source": "Mujer", "en": "Female", "es": "Femenino"}}'
WHERE user_id = '837129a9fce45e1a89788689569b3a16'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Marine biologist'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Bióloga marina'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Marine biologist'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Marine biologist'
  AND biography = 'I study coastal ecosystems and participate in marine conservation projects. I swim and draw Caribbean species.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Estudio ecosistemas costeros y participo en proyectos de conservación marina. Practico natación y dibujo especies del Caribe.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I study coastal ecosystems and participate in marine conservation projects. I swim and draw Caribbean species.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I study coastal ecosystems and participate in marine conservation projects. I swim and draw Caribbean species.'
  AND gender = 'Mujer'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Mujer');

-- Amina Diallo
UPDATE user_profiles SET display_text = '{"headline": {"es": "Analista de datos", "en": "Data analyst", "source": "Data analyst"}, "biography": {"es": "Convierto datos en herramientas para planificar proyectos educativos. Me apasionan el jazz, la lectura y las caminatas junto al mar.", "en": "I turn data into tools for planning education projects. I enjoy jazz, reading and walks by the sea.", "source": "I turn data into tools for planning education projects. I enjoy jazz, reading and walks by the sea."}, "gender": {"source": "Mujer", "en": "Female", "es": "Femenino"}}'
WHERE user_id = 'a689f3b94c0950e49a8d5c47cfdaee08'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Data analyst'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Analista de datos'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Data analyst'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Data analyst'
  AND biography = 'I turn data into tools for planning education projects. I enjoy jazz, reading and walks by the sea.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Convierto datos en herramientas para planificar proyectos educativos. Me apasionan el jazz, la lectura y las caminatas junto al mar.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I turn data into tools for planning education projects. I enjoy jazz, reading and walks by the sea.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I turn data into tools for planning education projects. I enjoy jazz, reading and walks by the sea.'
  AND gender = 'Mujer'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Mujer');

-- Mateo Silva
UPDATE user_profiles SET display_text = '{"headline": {"es": "Ingeniero de sonido", "en": "Sound engineer", "source": "Sound engineer"}, "biography": {"es": "Grabo proyectos musicales independientes y trabajo en acústica de estudios. Comparto rutas de ciclismo y sesiones de música en vivo.", "en": "I record independent music projects and work on studio acoustics. I share cycling routes and live music sessions.", "source": "I record independent music projects and work on studio acoustics. I share cycling routes and live music sessions."}, "gender": {"source": "Hombre", "en": "Male", "es": "Masculino"}}'
WHERE user_id = 'b51915e29a445ee1971a96af89f87be7'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Sound engineer'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Ingeniero de sonido'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Sound engineer'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Sound engineer'
  AND biography = 'I record independent music projects and work on studio acoustics. I share cycling routes and live music sessions.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Grabo proyectos musicales independientes y trabajo en acústica de estudios. Comparto rutas de ciclismo y sesiones de música en vivo.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I record independent music projects and work on studio acoustics. I share cycling routes and live music sessions.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I record independent music projects and work on studio acoustics. I share cycling routes and live music sessions.'
  AND gender = 'Hombre'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Hombre');

-- Noah Williams
UPDATE user_profiles SET display_text = '{"headline": {"es": "Fotógrafo documental", "en": "Documentary photographer", "source": "Documentary photographer"}, "biography": {"es": "Documento historias de barrios, música y vida cotidiana. Me gusta descubrir pequeños cafés y coleccionar libros de fotografía.", "en": "I document neighborhood stories, music and daily life. I enjoy discovering small cafes and collecting photography books.", "source": "I document neighborhood stories, music and daily life. I enjoy discovering small cafes and collecting photography books."}, "gender": {"source": "No binario", "en": "Non-binary", "es": "No binario"}}'
WHERE user_id = 'bd16cf3ee3095336bdc4e78040a3ba2f'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Documentary photographer'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Fotógrafo documental'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Documentary photographer'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Documentary photographer'
  AND biography = 'I document neighborhood stories, music and daily life. I enjoy discovering small cafes and collecting photography books.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Documento historias de barrios, música y vida cotidiana. Me gusta descubrir pequeños cafés y coleccionar libros de fotografía.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I document neighborhood stories, music and daily life. I enjoy discovering small cafes and collecting photography books.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I document neighborhood stories, music and daily life. I enjoy discovering small cafes and collecting photography books.'
  AND gender = 'No binario'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'No binario');

-- Ren Ito
UPDATE user_profiles SET display_text = '{"headline": {"es": "Ilustrador editorial", "en": "Editorial illustrator", "source": "Editorial illustrator"}, "biography": {"es": "Creo ilustraciones para libros y revistas culturales. Combino técnicas de tinta y color digital; también disfruto la cocina y el cine.", "en": "I create illustrations for books and cultural magazines. I combine ink and digital color techniques and enjoy cooking and film.", "source": "I create illustrations for books and cultural magazines. I combine ink and digital color techniques and enjoy cooking and film."}, "gender": {"source": "No binario", "en": "Non-binary", "es": "No binario"}, "hometown": {"source": "Lima, Perú", "en": "Lima, Peru", "es": "Lima, Perú"}, "location": {"source": "Lima, Perú", "en": "Lima, Peru", "es": "Lima, Perú"}}'
WHERE user_id = 'c7a80e44b05a5e89adf710d6e900c47d'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Editorial illustrator'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Ilustrador editorial'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Editorial illustrator'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Editorial illustrator'
  AND biography = 'I create illustrations for books and cultural magazines. I combine ink and digital color techniques and enjoy cooking and film.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Creo ilustraciones para libros y revistas culturales. Combino técnicas de tinta y color digital; también disfruto la cocina y el cine.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I create illustrations for books and cultural magazines. I combine ink and digital color techniques and enjoy cooking and film.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I create illustrations for books and cultural magazines. I combine ink and digital color techniques and enjoy cooking and film.'
  AND gender = 'No binario'
  AND hometown = 'Lima, Perú'
  AND location = 'Lima, Perú'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'No binario' AND f.hometown = 'Lima, Perú' AND f.location = 'Lima, Perú');

-- Diego Mendoza
UPDATE user_profiles SET display_text = '{"headline": {"es": "Técnico en robótica", "en": "Robotics technician", "source": "Robotics technician"}, "biography": {"es": "Construyo y mantengo sistemas de automatización para pequeños talleres. Disfruto reparar bicicletas y enseñar electrónica.", "en": "I build and maintain automation systems for small workshops. I enjoy repairing bicycles and teaching electronics.", "source": "I build and maintain automation systems for small workshops. I enjoy repairing bicycles and teaching electronics."}, "gender": {"source": "Hombre", "en": "Male", "es": "Masculino"}, "hometown": {"source": "Monterrey, México", "en": "Monterrey, Mexico", "es": "Monterrey, México"}, "location": {"source": "Monterrey, México", "en": "Monterrey, Mexico", "es": "Monterrey, México"}}'
WHERE user_id = 'd43af2d3a55e5c2e8ffea22dfb47b3fa'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Robotics technician'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Técnico en robótica'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Robotics technician'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Robotics technician'
  AND biography = 'I build and maintain automation systems for small workshops. I enjoy repairing bicycles and teaching electronics.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Construyo y mantengo sistemas de automatización para pequeños talleres. Disfruto reparar bicicletas y enseñar electrónica.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I build and maintain automation systems for small workshops. I enjoy repairing bicycles and teaching electronics.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I build and maintain automation systems for small workshops. I enjoy repairing bicycles and teaching electronics.'
  AND gender = 'Hombre'
  AND hometown = 'Monterrey, México'
  AND location = 'Monterrey, México'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Hombre' AND f.hometown = 'Monterrey, México' AND f.location = 'Monterrey, México');

-- Paula Méndez
UPDATE user_profiles SET display_text = '{"headline": {"es": "Diseñadora de comunicación", "en": "Communication designer", "source": "Communication designer"}, "biography": {"es": "Diseño contenidos para iniciativas culturales y comunitarias. Me gustan la lectura, la fotografía y los paseos por el parque.", "en": "I design content for cultural and community initiatives. I enjoy reading, photography and walks in the park.", "source": "I design content for cultural and community initiatives. I enjoy reading, photography and walks in the park."}, "gender": {"source": "Mujer", "en": "Female", "es": "Femenino"}}'
WHERE user_id = 'd93eec11a6435f87aeae7ae2922735c9'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Communication designer'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Diseñadora de comunicación'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Communication designer'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Communication designer'
  AND biography = 'I design content for cultural and community initiatives. I enjoy reading, photography and walks in the park.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Diseño contenidos para iniciativas culturales y comunitarias. Me gustan la lectura, la fotografía y los paseos por el parque.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I design content for cultural and community initiatives. I enjoy reading, photography and walks in the park.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I design content for cultural and community initiatives. I enjoy reading, photography and walks in the park.'
  AND gender = 'Mujer'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Mujer');

-- Gabriel Herrera
UPDATE user_profiles SET display_text = '{"headline": {"es": "Fotógrafo urbano", "en": "Urban photographer", "source": "Urban photographer"}, "biography": {"es": "Recorro parques y barrios para documentar la vida cotidiana. Me interesan la música y las rutas a pie.", "en": "I explore parks and neighborhoods to document everyday life. I enjoy music and walking routes.", "source": "I explore parks and neighborhoods to document everyday life. I enjoy music and walking routes."}, "gender": {"source": "Hombre", "en": "Male", "es": "Masculino"}}'
WHERE user_id = 'e9eac14d9f6553058dce33d1b118a62b'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text)) = 2
  AND headline = 'Urban photographer'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'headline')) = 3
  AND user_profiles.display_text -> 'headline' ->> 'es' = 'Fotógrafo urbano'
  AND user_profiles.display_text -> 'headline' ->> 'en' = 'Urban photographer'
  AND user_profiles.display_text -> 'headline' ->> 'source' = 'Urban photographer'
  AND biography = 'I explore parks and neighborhoods to document everyday life. I enjoy music and walking routes.'
  AND (SELECT COUNT(*) FROM json_each(user_profiles.display_text -> 'biography')) = 3
  AND user_profiles.display_text -> 'biography' ->> 'es' = 'Recorro parques y barrios para documentar la vida cotidiana. Me interesan la música y las rutas a pie.'
  AND user_profiles.display_text -> 'biography' ->> 'en' = 'I explore parks and neighborhoods to document everyday life. I enjoy music and walking routes.'
  AND user_profiles.display_text -> 'biography' ->> 'source' = 'I explore parks and neighborhoods to document everyday life. I enjoy music and walking routes.'
  AND gender = 'Hombre'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id JOIN facebook_profiles f ON f.user_id = u.id WHERE u.id = user_profiles.user_id AND u.is_active = TRUE AND m.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND f.gender = 'Hombre');
