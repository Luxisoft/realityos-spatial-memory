-- Apply the owner-approved operational taxonomy once through the shared local SQL loader.
-- Only intact prepared publications and their existing membership qualify.
-- Case statuses come from the recorded facts; no judicial state is inferred from videos.
-- Owner edits, hidden/deleted publications, pending uploads and private biometric data remain intact.
CREATE TEMP TABLE use_case_posts (post_id UUID PRIMARY KEY, workspace_id UUID NOT NULL, category_key TEXT NOT NULL);
CREATE TEMP TABLE use_case_tags (post_id UUID NOT NULL, name_key TEXT NOT NULL, PRIMARY KEY (post_id, name_key));
CREATE TEMP TABLE use_case_terms (id UUID PRIMARY KEY, workspace_id UUID NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL, name_key TEXT NOT NULL, display_text JSON NOT NULL);

-- meta-social:pexels-12557513
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'social content'
FROM publications p
WHERE p.id = 'c6af2491f99551e59a3084f0045ec2c9'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '63297a1bbc7f52df9b76cf3c33739bb7'
  AND p.media_id = '83ce8dd028b258fcbf692d5757ea46db'
  AND p.category_id = '62a47280210f5a399e2f7bebaaa1e0bf'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:pexels-12557513'
  AND p.caption = 'Pedestrians and cyclists in a tree-lined park'
  AND p.note_text = 'Pedestrians and cyclists in a tree-lined park'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Pedestrians and cyclists in a tree-lined park'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Peatones y ciclistas en un parque arbolado'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Pedestrians and cyclists in a tree-lined park'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Pedestrians and cyclists in a tree-lined park'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Peatones y ciclistas en un parque arbolado'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Pedestrians and cyclists in a tree-lined park'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '62a47280210f5a399e2f7bebaaa1e0bf' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '0b0ed757af98520aa9d008ba1490ba9b' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Cycling' AND t.name_key = 'cycling' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Cycling' AND ((t.display_text -> 'name') ->> 'en') = 'Cycling' AND ((t.display_text -> 'name') ->> 'es') = 'Ciclismo')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '3eb9712f94085d3e8e1b55a98ba13605' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a74bd4bb8c335a238389c15fbaca1b39' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'video' FROM use_case_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'everyday life' FROM use_case_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';

-- meta-social:pexels-33802407
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'social content'
FROM publications p
WHERE p.id = 'c1de88652d045a04a56cc29caaa7963c'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '484b780027455aa4aa0f3d3ed603acf6'
  AND p.media_id = 'b63c0aeae3bf5dd1b42859111e7f674b'
  AND p.category_id = '62a47280210f5a399e2f7bebaaa1e0bf'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:pexels-33802407'
  AND p.caption = 'People walking along a city sidewalk'
  AND p.note_text = 'People walking along a city sidewalk'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'People walking along a city sidewalk'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Personas caminando por una acera de la ciudad'
  AND ((p.display_text -> 'caption') ->> 'en') = 'People walking along a city sidewalk'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'People walking along a city sidewalk'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Personas caminando por una acera de la ciudad'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'People walking along a city sidewalk'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '62a47280210f5a399e2f7bebaaa1e0bf' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '3eb9712f94085d3e8e1b55a98ba13605' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'e2c30e2d28ae58a8b73c2b99ba69b396' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'City sidewalk' AND t.name_key = 'city sidewalk' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'City sidewalk' AND ((t.display_text -> 'name') ->> 'en') = 'City sidewalk' AND ((t.display_text -> 'name') ->> 'es') = 'Acera urbana');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'video' FROM use_case_posts WHERE post_id = 'c1de88652d045a04a56cc29caaa7963c';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'everyday life' FROM use_case_posts WHERE post_id = 'c1de88652d045a04a56cc29caaa7963c';

-- meta-social:pexels-3699519
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'social content'
FROM publications p
WHERE p.id = '9b3e3f5710545f36a378902058bc34cc'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '9467affefe045ed8ae5c4d4bb7c5ac23'
  AND p.media_id = '3f4b85ec60d651dcbe345adda60c0714'
  AND p.category_id = '62a47280210f5a399e2f7bebaaa1e0bf'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:pexels-3699519'
  AND p.caption = 'A winter walk through the park'
  AND p.note_text = 'A winter walk through the park'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'A winter walk through the park'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Paseo de invierno por el parque'
  AND ((p.display_text -> 'caption') ->> 'en') = 'A winter walk through the park'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'A winter walk through the park'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Paseo de invierno por el parque'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'A winter walk through the park'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '62a47280210f5a399e2f7bebaaa1e0bf' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '3eb9712f94085d3e8e1b55a98ba13605' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '9dca3192b8f65aa89cdf196283c4ce10' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Winter' AND t.name_key = 'winter' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Winter' AND ((t.display_text -> 'name') ->> 'en') = 'Winter' AND ((t.display_text -> 'name') ->> 'es') = 'Invierno')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a74bd4bb8c335a238389c15fbaca1b39' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'video' FROM use_case_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'everyday life' FROM use_case_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';

-- meta-social:social-introduction:elena-marquez
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '9c941832fbbb5bd1a4f85a97cd82acb2'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '484b780027455aa4aa0f3d3ed603acf6'
  AND p.media_id = '68d1933a53435ad49bb4c4dce72f1fe2'
  AND p.category_id = '0fc6533b32c35498bc999821bc630a4e'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:social-introduction:elena-marquez'
  AND p.caption = 'Elena Marquez — Hello, everyone'
  AND p.note_text = 'Ideas, photographs and projects worth sharing. Welcome to our social space.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Elena Marquez — Hello, everyone'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Elena Marquez — Hola a todos'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Elena Marquez — Hello, everyone'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Ideas, photographs and projects worth sharing. Welcome to our social space.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Ideas, fotografías y proyectos que vale la pena compartir. Bienvenidos a nuestro espacio social.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Ideas, photographs and projects worth sharing. Welcome to our social space.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0fc6533b32c35498bc999821bc630a4e' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Introductions' AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '68fd385f063a5827894e9c7854274d23' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Community' AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'c33b3e1207795dc9a5697a526a5f7b5c' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Photography' AND t.name_key = 'photography' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Photography' AND ((t.display_text -> 'name') ->> 'en') = 'Photography' AND ((t.display_text -> 'name') ->> 'es') = 'Fotografía')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'f395bff7a83452e5ab69f95ab4f2890b' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Projects' AND t.name_key = 'projects' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Projects' AND ((t.display_text -> 'name') ->> 'en') = 'Projects' AND ((t.display_text -> 'name') ->> 'es') = 'Proyectos');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'personal introduction' FROM use_case_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'community' FROM use_case_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';

-- meta-social:social-introduction:mateo-rios
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '274fc4bb223852fc9bc5e8ed8829ec8d'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '9467affefe045ed8ae5c4d4bb7c5ac23'
  AND p.media_id = '771cf8dbd0e95b14ab85e2059493492c'
  AND p.category_id = '0fc6533b32c35498bc999821bc630a4e'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:social-introduction:mateo-rios'
  AND p.caption = 'Mateo Rios — Hello, everyone'
  AND p.note_text = 'A place to exchange experiences, discover new perspectives and keep in touch.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Mateo Rios — Hello, everyone'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Mateo Rios — Hola a todos'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Mateo Rios — Hello, everyone'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'A place to exchange experiences, discover new perspectives and keep in touch.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Un espacio para intercambiar experiencias, descubrir nuevas perspectivas y mantenernos en contacto.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'A place to exchange experiences, discover new perspectives and keep in touch.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0fc6533b32c35498bc999821bc630a4e' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Introductions' AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '2002638d207e5407b4c107010bd5fadc' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Experiences' AND t.name_key = 'experiences' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Experiences' AND ((t.display_text -> 'name') ->> 'en') = 'Experiences' AND ((t.display_text -> 'name') ->> 'es') = 'Experiencias')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '68fd385f063a5827894e9c7854274d23' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Community' AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'personal introduction' FROM use_case_posts WHERE post_id = '274fc4bb223852fc9bc5e8ed8829ec8d';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'community' FROM use_case_posts WHERE post_id = '274fc4bb223852fc9bc5e8ed8829ec8d';

-- meta-social:social-introduction:sarah-chen
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '83f449740fe357c2ae3a5b8b223ec53e'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '63297a1bbc7f52df9b76cf3c33739bb7'
  AND p.media_id = '46bef77fd9c7553d964a8d05bab101ac'
  AND p.category_id = '0fc6533b32c35498bc999821bc630a4e'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:social-introduction:sarah-chen'
  AND p.caption = 'Sarah Chen — Hello, everyone'
  AND p.note_text = 'Sharing small discoveries and the stories behind each photograph.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Sarah Chen — Hello, everyone'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Sarah Chen — Hola a todos'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Sarah Chen — Hello, everyone'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Sharing small discoveries and the stories behind each photograph.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Compartiendo pequeños descubrimientos y las historias detrás de cada fotografía.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Sharing small discoveries and the stories behind each photograph.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0fc6533b32c35498bc999821bc630a4e' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Introductions' AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '68fd385f063a5827894e9c7854274d23' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Community' AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '84fe3811d7af5cfa871389ea39f86f28' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Stories' AND t.name_key = 'stories' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Stories' AND ((t.display_text -> 'name') ->> 'en') = 'Stories' AND ((t.display_text -> 'name') ->> 'es') = 'Historias')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'c33b3e1207795dc9a5697a526a5f7b5c' AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Photography' AND t.name_key = 'photography' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Photography' AND ((t.display_text -> 'name') ->> 'en') = 'Photography' AND ((t.display_text -> 'name') ->> 'es') = 'Fotografía');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'personal introduction' FROM use_case_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'community' FROM use_case_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';

-- security:pexels-25757454
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'audiovisual material'
FROM publications p
WHERE p.id = '41b2b8cf66c65e3cbf41025c47bb0245'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.media_id = '298305f8e5325ecfb89a4211da686c8f'
  AND p.category_id = '2a3508ea47675f9ab9842266cda7c6b5'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:pexels-25757454'
  AND p.caption = 'Pedestrians and cyclists in Ibirapuera Park'
  AND p.note_text = 'Pedestrians and cyclists in Ibirapuera Park'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Pedestrians and cyclists in Ibirapuera Park'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Peatones y ciclistas en el parque Ibirapuera'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Pedestrians and cyclists in Ibirapuera Park'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Pedestrians and cyclists in Ibirapuera Park'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Peatones y ciclistas en el parque Ibirapuera'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Pedestrians and cyclists in Ibirapuera Park'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '2a3508ea47675f9ab9842266cda7c6b5' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '6f4530d2cf135600a3e63d58bdba9471' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '928f6c5f58685b3fb4214b64a4b80be4' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'de0765905929588390cc530f03ebc852' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Cycling' AND t.name_key = 'cycling' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Cycling' AND ((t.display_text -> 'name') ->> 'en') = 'Cycling' AND ((t.display_text -> 'name') ->> 'es') = 'Ciclismo');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'observation video' FROM use_case_posts WHERE post_id = '41b2b8cf66c65e3cbf41025c47bb0245';

-- security:pexels-29401365
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'audiovisual material'
FROM publications p
WHERE p.id = 'a64f19f460f752ca8a6daaa9b1947492'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = 'e2afbb0511d3521685589d8a52ec1a17'
  AND p.category_id = '2a3508ea47675f9ab9842266cda7c6b5'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:pexels-29401365'
  AND p.caption = 'People walking through a park on an overcast day'
  AND p.note_text = 'People walking through a park on an overcast day'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'People walking through a park on an overcast day'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Personas caminando por un parque en un día nublado'
  AND ((p.display_text -> 'caption') ->> 'en') = 'People walking through a park on an overcast day'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'People walking through a park on an overcast day'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Personas caminando por un parque en un día nublado'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'People walking through a park on an overcast day'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '2a3508ea47675f9ab9842266cda7c6b5' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '6f4530d2cf135600a3e63d58bdba9471' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '928f6c5f58685b3fb4214b64a4b80be4' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'e44b598aad515e859ba2e1598b3d6248' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Overcast day' AND t.name_key = 'overcast day' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Overcast day' AND ((t.display_text -> 'name') ->> 'en') = 'Overcast day' AND ((t.display_text -> 'name') ->> 'es') = 'Día nublado');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'observation video' FROM use_case_posts WHERE post_id = 'a64f19f460f752ca8a6daaa9b1947492';

-- security:pexels-30614848
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'audiovisual material'
FROM publications p
WHERE p.id = '24b0b2ee56d35f83b90c67961c8ab23f'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.media_id = '3219ce60caa45dbab4e73dc8549fd147'
  AND p.category_id = '2a3508ea47675f9ab9842266cda7c6b5'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:pexels-30614848'
  AND p.caption = 'Walking through an Edinburgh park in spring'
  AND p.note_text = 'Walking through an Edinburgh park in spring'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Walking through an Edinburgh park in spring'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Paseo por un parque de Edimburgo en primavera'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Walking through an Edinburgh park in spring'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Walking through an Edinburgh park in spring'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Paseo por un parque de Edimburgo en primavera'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Walking through an Edinburgh park in spring'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '2a3508ea47675f9ab9842266cda7c6b5' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '6f4530d2cf135600a3e63d58bdba9471' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '928f6c5f58685b3fb4214b64a4b80be4' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'fc95a832ac625dd5aa579c8219b95f09' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Spring' AND t.name_key = 'spring' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Spring' AND ((t.display_text -> 'name') ->> 'en') = 'Spring' AND ((t.display_text -> 'name') ->> 'es') = 'Primavera');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'observation video' FROM use_case_posts WHERE post_id = '24b0b2ee56d35f83b90c67961c8ab23f';

-- security:police-case:security-person-01
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = 'be1c4ea01ab856d1abdebd7ff0d8f81b'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = '0cf605c26aa650dda5b9e60fee7c0cc6'
  AND p.category_id = '0880d312f23e5b3389c72c8e742f1325'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-01'
  AND p.caption = 'Adrián Salcedo'
  AND p.note_text = 'Identifier: PRP-0001
Full name: Adrián Salcedo
Date of birth: 1989-04-17
Occupation: Logistics coordinator
Address: 17 Calle del Puerto, Pacific Ridge
Phone: +1-202-555-0101
Email: adrian.salcedo@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: Preliminary hearing pending; no judgment
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-001
Issue date: 2026-10-27
Issuing judge: Camila Torres
Issuing court: Pacific Ridge Judicial Oversight Court 1
Purpose of warrant: Appearance in an investigation of merchandise theft
Case number: PR-PJ-2026-0141'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Adrián Salcedo'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Adrián Salcedo'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Adrián Salcedo'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0001
Full name: Adrián Salcedo
Date of birth: 1989-04-17
Occupation: Logistics coordinator
Address: 17 Calle del Puerto, Pacific Ridge
Phone: +1-202-555-0101
Email: adrian.salcedo@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: Preliminary hearing pending; no judgment
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-001
Issue date: 2026-10-27
Issuing judge: Camila Torres
Issuing court: Pacific Ridge Judicial Oversight Court 1
Purpose of warrant: Appearance in an investigation of merchandise theft
Case number: PR-PJ-2026-0141'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0001
Nombre completo: Adrián Salcedo
Fecha de nacimiento: 1989-04-17
Ocupación: Coordinador de logística
Domicilio: 17 Calle del Puerto, Pacific Ridge
Teléfono: +1-202-555-0101
Correo: adrian.salcedo@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Vigente
Proceso judicial: Audiencia preliminar pendiente; sin sentencia
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Una orden de captura o un proceso abierto no constituye una condena.
Número de orden: PR-OC-2026-001
Fecha de expedición: 2026-10-27
Juez que ordena: Camila Torres
Despacho judicial: Juzgado 1 de Control de Garantías de Pacific Ridge
Objeto de la orden: Comparecencia por investigación de hurto de mercancía
Número de proceso: PR-PJ-2026-0141'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0001
Full name: Adrián Salcedo
Date of birth: 1989-04-17
Occupation: Logistics coordinator
Address: 17 Calle del Puerto, Pacific Ridge
Phone: +1-202-555-0101
Email: adrian.salcedo@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: Preliminary hearing pending; no judgment
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-001
Issue date: 2026-10-27
Issuing judge: Camila Torres
Issuing court: Pacific Ridge Judicial Oversight Court 1
Purpose of warrant: Appearance in an investigation of merchandise theft
Case number: PR-PJ-2026-0141'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0880d312f23e5b3389c72c8e742f1325' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '19bf084012155d08a4365789cbb1a7cd' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active judicial proceedings' AND t.name_key = 'active judicial proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Procesos judiciales activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'e0b2f6bdb1845457b6e53791a42ec1f2' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-01' AND r.version = 1 AND r.title = 'Adrián Salcedo' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0001' AND (r.data ->> 'full_name') = 'Adrián Salcedo' AND (r.data ->> 'birth_date') = '1989-04-17' AND (r.data ->> 'occupation') = 'Coordinador de logística' AND (r.data ->> 'residence') = '17 Calle del Puerto, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0101' AND (r.data ->> 'email') = 'adrian.salcedo@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-001' AND (r.data ->> 'warrant_issued_at') = '2026-10-27' AND (r.data ->> 'issuing_judge') = 'Camila Torres' AND (r.data ->> 'issuing_court') = 'Juzgado 1 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia por investigación de hurto de mercancía' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'true' AND (r.data ->> 'case_number') = 'PR-PJ-2026-0141' AND (r.data ->> 'procedural_status') = 'Audiencia preliminar pendiente; sin sentencia' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura o un proceso abierto no constituye una condena.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM use_case_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active judicial proceedings' FROM use_case_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';

-- security:police-case:security-person-02
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '5344161d0fa651e0ae4892a37e3e65c6'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.media_id = 'a15e735b242b5293ab43ad3743d351e2'
  AND p.category_id = '0880d312f23e5b3389c72c8e742f1325'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-02'
  AND p.caption = 'Esteban Pardo'
  AND p.note_text = 'Identifier: PRP-0002
Full name: Esteban Pardo
Date of birth: 1968-09-23
Occupation: Shopkeeper
Address: 82 Avenida Central, Pacific Ridge
Phone: +1-202-555-0102
Email: esteban.pardo@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: Investigation stage; no judgment
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-002
Issue date: 2026-10-28
Issuing judge: Javier Cortés
Issuing court: Pacific Ridge Judicial Oversight Court 2
Purpose of warrant: Appearance in an investigation of commercial fraud
Case number: PR-PJ-2026-0142'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Esteban Pardo'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Esteban Pardo'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Esteban Pardo'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0002
Full name: Esteban Pardo
Date of birth: 1968-09-23
Occupation: Shopkeeper
Address: 82 Avenida Central, Pacific Ridge
Phone: +1-202-555-0102
Email: esteban.pardo@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: Investigation stage; no judgment
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-002
Issue date: 2026-10-28
Issuing judge: Javier Cortés
Issuing court: Pacific Ridge Judicial Oversight Court 2
Purpose of warrant: Appearance in an investigation of commercial fraud
Case number: PR-PJ-2026-0142'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0002
Nombre completo: Esteban Pardo
Fecha de nacimiento: 1968-09-23
Ocupación: Comerciante
Domicilio: 82 Avenida Central, Pacific Ridge
Teléfono: +1-202-555-0102
Correo: esteban.pardo@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Vigente
Proceso judicial: Etapa de investigación; sin sentencia
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Una orden de captura o un proceso abierto no constituye una condena.
Número de orden: PR-OC-2026-002
Fecha de expedición: 2026-10-28
Juez que ordena: Javier Cortés
Despacho judicial: Juzgado 2 de Control de Garantías de Pacific Ridge
Objeto de la orden: Comparecencia por investigación de fraude comercial
Número de proceso: PR-PJ-2026-0142'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0002
Full name: Esteban Pardo
Date of birth: 1968-09-23
Occupation: Shopkeeper
Address: 82 Avenida Central, Pacific Ridge
Phone: +1-202-555-0102
Email: esteban.pardo@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: Investigation stage; no judgment
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-002
Issue date: 2026-10-28
Issuing judge: Javier Cortés
Issuing court: Pacific Ridge Judicial Oversight Court 2
Purpose of warrant: Appearance in an investigation of commercial fraud
Case number: PR-PJ-2026-0142'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0880d312f23e5b3389c72c8e742f1325' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '19bf084012155d08a4365789cbb1a7cd' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active judicial proceedings' AND t.name_key = 'active judicial proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Procesos judiciales activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '909d1a6da90855acabca10a4269ff2a1' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-02' AND r.version = 1 AND r.title = 'Esteban Pardo' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0002' AND (r.data ->> 'full_name') = 'Esteban Pardo' AND (r.data ->> 'birth_date') = '1968-09-23' AND (r.data ->> 'occupation') = 'Comerciante' AND (r.data ->> 'residence') = '82 Avenida Central, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0102' AND (r.data ->> 'email') = 'esteban.pardo@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-002' AND (r.data ->> 'warrant_issued_at') = '2026-10-28' AND (r.data ->> 'issuing_judge') = 'Javier Cortés' AND (r.data ->> 'issuing_court') = 'Juzgado 2 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia por investigación de fraude comercial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'true' AND (r.data ->> 'case_number') = 'PR-PJ-2026-0142' AND (r.data ->> 'procedural_status') = 'Etapa de investigación; sin sentencia' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura o un proceso abierto no constituye una condena.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM use_case_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active judicial proceedings' FROM use_case_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';

-- security:police-case:security-person-03
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '4384e305ef325c7d9b8d6bd2c80c8b05'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.media_id = '758334d7325d5683b6323602f37491db'
  AND p.category_id = '0880d312f23e5b3389c72c8e742f1325'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-03'
  AND p.caption = 'Valeria Navarro'
  AND p.note_text = 'Identifier: PRP-0003
Full name: Valeria Navarro
Date of birth: 1992-12-08
Occupation: Accountant
Address: 31 Calle de los Olmos, Pacific Ridge
Phone: +1-202-555-0103
Email: valeria.navarro@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-003
Issue date: 2026-10-29
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Valeria Navarro'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Valeria Navarro'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Valeria Navarro'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0003
Full name: Valeria Navarro
Date of birth: 1992-12-08
Occupation: Accountant
Address: 31 Calle de los Olmos, Pacific Ridge
Phone: +1-202-555-0103
Email: valeria.navarro@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-003
Issue date: 2026-10-29
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0003
Nombre completo: Valeria Navarro
Fecha de nacimiento: 1992-12-08
Ocupación: Contadora
Domicilio: 31 Calle de los Olmos, Pacific Ridge
Teléfono: +1-202-555-0103
Correo: valeria.navarro@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Vigente
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Una orden de captura o un proceso abierto no constituye una condena.
Número de orden: PR-OC-2026-003
Fecha de expedición: 2026-10-29
Juez que ordena: Julia Rivas
Despacho judicial: Juzgado 3 de Control de Garantías de Pacific Ridge
Objeto de la orden: Comparecencia requerida por orden judicial'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0003
Full name: Valeria Navarro
Date of birth: 1992-12-08
Occupation: Accountant
Address: 31 Calle de los Olmos, Pacific Ridge
Phone: +1-202-555-0103
Email: valeria.navarro@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: An arrest warrant or an open proceeding does not constitute a conviction.
Warrant number: PR-OC-2026-003
Issue date: 2026-10-29
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0880d312f23e5b3389c72c8e742f1325' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '11aeb71325b258d893fb649de535e9a4' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-03' AND r.version = 1 AND r.title = 'Valeria Navarro' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0003' AND (r.data ->> 'full_name') = 'Valeria Navarro' AND (r.data ->> 'birth_date') = '1992-12-08' AND (r.data ->> 'occupation') = 'Contadora' AND (r.data ->> 'residence') = '31 Calle de los Olmos, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0103' AND (r.data ->> 'email') = 'valeria.navarro@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-003' AND (r.data ->> 'warrant_issued_at') = '2026-10-29' AND (r.data ->> 'issuing_judge') = 'Julia Rivas' AND (r.data ->> 'issuing_court') = 'Juzgado 3 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia requerida por orden judicial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura o un proceso abierto no constituye una condena.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM use_case_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';

-- security:police-case:security-person-04
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '5217d89a1dba5d0fb6a5f51b10e22c13'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = 'cc54a634941958e08bca2dc9deec44ef'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-04'
  AND p.caption = 'Lucía Cárdenas'
  AND p.note_text = 'Identifier: PRP-0004
Full name: Lucía Cárdenas
Date of birth: 1995-06-12
Occupation: Graphic designer
Address: 46 Paseo del Parque, Pacific Ridge
Phone: +1-202-555-0104
Email: lucia.cardenas@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Lucía Cárdenas'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Lucía Cárdenas'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Lucía Cárdenas'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0004
Full name: Lucía Cárdenas
Date of birth: 1995-06-12
Occupation: Graphic designer
Address: 46 Paseo del Parque, Pacific Ridge
Phone: +1-202-555-0104
Email: lucia.cardenas@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0004
Nombre completo: Lucía Cárdenas
Fecha de nacimiento: 1995-06-12
Ocupación: Diseñadora gráfica
Domicilio: 46 Paseo del Parque, Pacific Ridge
Teléfono: +1-202-555-0104
Correo: lucia.cardenas@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0004
Full name: Lucía Cárdenas
Date of birth: 1995-06-12
Occupation: Graphic designer
Address: 46 Paseo del Parque, Pacific Ridge
Phone: +1-202-555-0104
Email: lucia.cardenas@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'f2482f95e0675eb2b4768e7ff99d1d2a' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-04' AND r.version = 1 AND r.title = 'Lucía Cárdenas' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0004' AND (r.data ->> 'full_name') = 'Lucía Cárdenas' AND (r.data ->> 'birth_date') = '1995-06-12' AND (r.data ->> 'occupation') = 'Diseñadora gráfica' AND (r.data ->> 'residence') = '46 Paseo del Parque, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0104' AND (r.data ->> 'email') = 'lucia.cardenas@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';

-- security:police-case:security-person-05
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '3a13e840a41456a4b85a3f0a4930b37b'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.media_id = '644c968c495f55f386c89143641c7787'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-05'
  AND p.caption = 'Tomás Beltrán'
  AND p.note_text = 'Identifier: PRP-0005
Full name: Tomás Beltrán
Date of birth: 1987-02-20
Occupation: Electrician
Address: 109 Calle del Roble, Pacific Ridge
Phone: +1-202-555-0105
Email: tomas.beltran@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Tomás Beltrán'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Tomás Beltrán'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Tomás Beltrán'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0005
Full name: Tomás Beltrán
Date of birth: 1987-02-20
Occupation: Electrician
Address: 109 Calle del Roble, Pacific Ridge
Phone: +1-202-555-0105
Email: tomas.beltran@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0005
Nombre completo: Tomás Beltrán
Fecha de nacimiento: 1987-02-20
Ocupación: Electricista
Domicilio: 109 Calle del Roble, Pacific Ridge
Teléfono: +1-202-555-0105
Correo: tomas.beltran@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0005
Full name: Tomás Beltrán
Date of birth: 1987-02-20
Occupation: Electrician
Address: 109 Calle del Roble, Pacific Ridge
Phone: +1-202-555-0105
Email: tomas.beltran@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'b325103f59155714afb0e24f9c97ca82' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-05' AND r.version = 1 AND r.title = 'Tomás Beltrán' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0005' AND (r.data ->> 'full_name') = 'Tomás Beltrán' AND (r.data ->> 'birth_date') = '1987-02-20' AND (r.data ->> 'occupation') = 'Electricista' AND (r.data ->> 'residence') = '109 Calle del Roble, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0105' AND (r.data ->> 'email') = 'tomas.beltran@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';

-- security:police-case:security-person-06
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '4fe1617c8a1b50089508572418d8f17c'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.media_id = '1617362b32085478a77a378c8ca4cd93'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-06'
  AND p.caption = 'Nicolás Acosta'
  AND p.note_text = 'Identifier: PRP-0006
Full name: Nicolás Acosta
Date of birth: 1991-08-30
Occupation: Automotive mechanic
Address: 24 Avenida del Taller, Pacific Ridge
Phone: +1-202-555-0106
Email: nicolas.acosta@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Nicolás Acosta'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Nicolás Acosta'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Nicolás Acosta'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0006
Full name: Nicolás Acosta
Date of birth: 1991-08-30
Occupation: Automotive mechanic
Address: 24 Avenida del Taller, Pacific Ridge
Phone: +1-202-555-0106
Email: nicolas.acosta@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0006
Nombre completo: Nicolás Acosta
Fecha de nacimiento: 1991-08-30
Ocupación: Mecánico automotriz
Domicilio: 24 Avenida del Taller, Pacific Ridge
Teléfono: +1-202-555-0106
Correo: nicolas.acosta@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0006
Full name: Nicolás Acosta
Date of birth: 1991-08-30
Occupation: Automotive mechanic
Address: 24 Avenida del Taller, Pacific Ridge
Phone: +1-202-555-0106
Email: nicolas.acosta@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '65050ead0c4f56c4b6695032f55b7f46' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-06' AND r.version = 1 AND r.title = 'Nicolás Acosta' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0006' AND (r.data ->> 'full_name') = 'Nicolás Acosta' AND (r.data ->> 'birth_date') = '1991-08-30' AND (r.data ->> 'occupation') = 'Mecánico automotriz' AND (r.data ->> 'residence') = '24 Avenida del Taller, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0106' AND (r.data ->> 'email') = 'nicolas.acosta@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';

-- security:police-case:security-person-07
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '11a0c84493245994bd3099f55ff1c7da'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = 'e306f764edb25e18b6a76695818f49e1'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-07'
  AND p.caption = 'Mariana Solano'
  AND p.note_text = 'Identifier: PRP-0007
Full name: Mariana Solano
Date of birth: 1994-11-02
Occupation: Primary school teacher
Address: 63 Calle de la Escuela, Pacific Ridge
Phone: +1-202-555-0107
Email: mariana.solano@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Mariana Solano'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Mariana Solano'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Mariana Solano'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0007
Full name: Mariana Solano
Date of birth: 1994-11-02
Occupation: Primary school teacher
Address: 63 Calle de la Escuela, Pacific Ridge
Phone: +1-202-555-0107
Email: mariana.solano@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0007
Nombre completo: Mariana Solano
Fecha de nacimiento: 1994-11-02
Ocupación: Docente de primaria
Domicilio: 63 Calle de la Escuela, Pacific Ridge
Teléfono: +1-202-555-0107
Correo: mariana.solano@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0007
Full name: Mariana Solano
Date of birth: 1994-11-02
Occupation: Primary school teacher
Address: 63 Calle de la Escuela, Pacific Ridge
Phone: +1-202-555-0107
Email: mariana.solano@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'b0ea039f74905caea44043cbdcaad329' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-07' AND r.version = 1 AND r.title = 'Mariana Solano' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0007' AND (r.data ->> 'full_name') = 'Mariana Solano' AND (r.data ->> 'birth_date') = '1994-11-02' AND (r.data ->> 'occupation') = 'Docente de primaria' AND (r.data ->> 'residence') = '63 Calle de la Escuela, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0107' AND (r.data ->> 'email') = 'mariana.solano@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';

-- security:police-case:security-person-08
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = 'b531b3d7de89559f91732114c30a4310'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.media_id = '3f9d7991b94652ecbdfd9689a4593cfd'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-08'
  AND p.caption = 'Rafael Méndez'
  AND p.note_text = 'Identifier: PRP-0008
Full name: Rafael Méndez
Date of birth: 1985-01-09
Occupation: Inventory analyst
Address: 55 Calle del Mercado, Pacific Ridge
Phone: +1-202-555-0108
Email: rafael.mendez@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Rafael Méndez'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Rafael Méndez'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Rafael Méndez'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0008
Full name: Rafael Méndez
Date of birth: 1985-01-09
Occupation: Inventory analyst
Address: 55 Calle del Mercado, Pacific Ridge
Phone: +1-202-555-0108
Email: rafael.mendez@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0008
Nombre completo: Rafael Méndez
Fecha de nacimiento: 1985-01-09
Ocupación: Analista de inventarios
Domicilio: 55 Calle del Mercado, Pacific Ridge
Teléfono: +1-202-555-0108
Correo: rafael.mendez@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0008
Full name: Rafael Méndez
Date of birth: 1985-01-09
Occupation: Inventory analyst
Address: 55 Calle del Mercado, Pacific Ridge
Phone: +1-202-555-0108
Email: rafael.mendez@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '1597fbaef5da5a23821276ca14f81e81' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-08' AND r.version = 1 AND r.title = 'Rafael Méndez' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0008' AND (r.data ->> 'full_name') = 'Rafael Méndez' AND (r.data ->> 'birth_date') = '1985-01-09' AND (r.data ->> 'occupation') = 'Analista de inventarios' AND (r.data ->> 'residence') = '55 Calle del Mercado, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0108' AND (r.data ->> 'email') = 'rafael.mendez@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';

-- security:police-case:security-person-09
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '118407b2480157209ab9729c18c14294'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.media_id = '7376383de49a590492e429c7fa693d80'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-09'
  AND p.caption = 'Camila Fuentes'
  AND p.note_text = 'Identifier: PRP-0009
Full name: Camila Fuentes
Date of birth: 1998-03-26
Occupation: Librarian
Address: 12 Paseo de los Cedros, Pacific Ridge
Phone: +1-202-555-0109
Email: camila.fuentes@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Camila Fuentes'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Camila Fuentes'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Camila Fuentes'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0009
Full name: Camila Fuentes
Date of birth: 1998-03-26
Occupation: Librarian
Address: 12 Paseo de los Cedros, Pacific Ridge
Phone: +1-202-555-0109
Email: camila.fuentes@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0009
Nombre completo: Camila Fuentes
Fecha de nacimiento: 1998-03-26
Ocupación: Bibliotecaria
Domicilio: 12 Paseo de los Cedros, Pacific Ridge
Teléfono: +1-202-555-0109
Correo: camila.fuentes@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0009
Full name: Camila Fuentes
Date of birth: 1998-03-26
Occupation: Librarian
Address: 12 Paseo de los Cedros, Pacific Ridge
Phone: +1-202-555-0109
Email: camila.fuentes@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'ba59535813655989a48718c54f48e066' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-09' AND r.version = 1 AND r.title = 'Camila Fuentes' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0009' AND (r.data ->> 'full_name') = 'Camila Fuentes' AND (r.data ->> 'birth_date') = '1998-03-26' AND (r.data ->> 'occupation') = 'Bibliotecaria' AND (r.data ->> 'residence') = '12 Paseo de los Cedros, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0109' AND (r.data ->> 'email') = 'camila.fuentes@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '118407b2480157209ab9729c18c14294';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '118407b2480157209ab9729c18c14294';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '118407b2480157209ab9729c18c14294';

-- security:police-case:security-person-10
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '0a691133f51f583a840e3187f5222b39'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = '95f3f7de103f55caaa85626b4543bc73'
  AND p.category_id = '1419ad5c7cb758edac50b7ea77a2f211'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-10'
  AND p.caption = 'Asha Mehta'
  AND p.note_text = 'Identifier: PRP-0010
Full name: Asha Mehta
Date of birth: 1967-07-19
Occupation: Translator
Address: 90 Avenida del Lago, Pacific Ridge
Phone: +1-202-555-0110
Email: asha.mehta@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'en') = 'Asha Mehta'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Asha Mehta'
  AND ((p.display_text -> 'caption') ->> 'source') = 'Asha Mehta'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0010
Full name: Asha Mehta
Date of birth: 1967-07-19
Occupation: Translator
Address: 90 Avenida del Lago, Pacific Ridge
Phone: +1-202-555-0110
Email: asha.mehta@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0010
Nombre completo: Asha Mehta
Fecha de nacimiento: 1967-07-19
Ocupación: Traductora
Domicilio: 90 Avenida del Lago, Pacific Ridge
Teléfono: +1-202-555-0110
Correo: asha.mehta@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Última revisión: 3 de noviembre de 2026, 15:30 (UTC−05:00)
Observaciones: Sin antecedentes, órdenes de captura ni procesos judiciales registrados.'
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0010
Full name: Asha Mehta
Date of birth: 1967-07-19
Occupation: Translator
Address: 90 Avenida del Lago, Pacific Ridge
Phone: +1-202-555-0110
Email: asha.mehta@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Last reviewed: November 3, 2026, 15:30 (UTC−05:00)
Notes: No criminal record, arrest warrants or judicial proceedings registered.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '1419ad5c7cb758edac50b7ea77a2f211' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'cde43426901a5c9386012f78935464d2' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-10' AND r.version = 1 AND r.title = 'Asha Mehta' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0010' AND (r.data ->> 'full_name') = 'Asha Mehta' AND (r.data ->> 'birth_date') = '1967-07-19' AND (r.data ->> 'occupation') = 'Traductora' AND (r.data ->> 'residence') = '90 Avenida del Lago, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0110' AND (r.data ->> 'email') = 'asha.mehta@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';

-- security:police-case:security-person-11
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '8b7e666b35da56f7aac5233f1d4e8a31'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = '5f95d2b1eb8756a28c80524ad08eb63a'
  AND p.category_id = '0880d312f23e5b3389c72c8e742f1325'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-11'
  AND p.caption = 'Bruno Escobar'
  AND p.note_text = 'Identifier: PRP-0011
Full name: Bruno Escobar
Date of birth: 1991-04-16
Occupation: Maintenance technician
Address: 111 Avenida del Río, Pacific Ridge
Phone: +1-202-555-0111
Email: bruno.escobar@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Missing person: No
Active missing-person search order: No
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: An arrest warrant does not constitute a conviction. No criminal record or active judicial proceedings registered.
Warrant number: PR-OC-2026-011
Issue date: 2026-11-04
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Bruno Escobar'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Bruno Escobar'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Bruno Escobar'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0011
Full name: Bruno Escobar
Date of birth: 1991-04-16
Occupation: Maintenance technician
Address: 111 Avenida del Río, Pacific Ridge
Phone: +1-202-555-0111
Email: bruno.escobar@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Missing person: No
Active missing-person search order: No
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: An arrest warrant does not constitute a conviction. No criminal record or active judicial proceedings registered.
Warrant number: PR-OC-2026-011
Issue date: 2026-11-04
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0011
Nombre completo: Bruno Escobar
Fecha de nacimiento: 1991-04-16
Ocupación: Técnico de mantenimiento
Domicilio: 111 Avenida del Río, Pacific Ridge
Teléfono: +1-202-555-0111
Correo: bruno.escobar@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Vigente
Proceso judicial: Sin procesos judiciales activos registrados
Persona desaparecida: No
Orden de búsqueda activa: No
Última revisión: 4 de noviembre de 2026, 12:00 (UTC−05:00)
Observaciones: Una orden de captura no constituye una condena. Sin antecedentes penales ni procesos judiciales activos registrados.
Número de orden: PR-OC-2026-011
Fecha de expedición: 2026-11-04
Juez que ordena: Julia Rivas
Despacho judicial: Juzgado 3 de Control de Garantías de Pacific Ridge
Objeto de la orden: Comparecencia requerida por orden judicial'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0011
Full name: Bruno Escobar
Date of birth: 1991-04-16
Occupation: Maintenance technician
Address: 111 Avenida del Río, Pacific Ridge
Phone: +1-202-555-0111
Email: bruno.escobar@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Missing person: No
Active missing-person search order: No
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: An arrest warrant does not constitute a conviction. No criminal record or active judicial proceedings registered.
Warrant number: PR-OC-2026-011
Issue date: 2026-11-04
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0880d312f23e5b3389c72c8e742f1325' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'f33c891776ae50f5a46324dbc1e1e618' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-11' AND r.version = 1 AND r.title = 'Bruno Escobar' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0011' AND (r.data ->> 'full_name') = 'Bruno Escobar' AND (r.data ->> 'birth_date') = '1991-04-16' AND (r.data ->> 'occupation') = 'Técnico de mantenimiento' AND (r.data ->> 'residence') = '111 Avenida del Río, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0111' AND (r.data ->> 'email') = 'bruno.escobar@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-011' AND (r.data ->> 'warrant_issued_at') = '2026-11-04' AND (r.data ->> 'issuing_judge') = 'Julia Rivas' AND (r.data ->> 'issuing_court') = 'Juzgado 3 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia requerida por orden judicial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura no constituye una condena. Sin antecedentes penales ni procesos judiciales activos registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'false' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'false' AND CAST((r.data -> 'search_order_reference') AS TEXT) = 'null' AND CAST((r.data -> 'search_order_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_reference') AS TEXT) = 'null' AND CAST((r.data -> 'reported_missing_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_location') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_details') AS TEXT) = 'null');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM use_case_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';

-- security:police-case:security-person-12
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = 'b50ca97e42c65cd0bc63c5b788f5adc5'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.media_id = 'dcd3950d72085bd48d4c21df14fca415'
  AND p.category_id = '0880d312f23e5b3389c72c8e742f1325'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-12'
  AND p.caption = 'Daniel Serrano'
  AND p.note_text = 'Identifier: PRP-0012
Full name: Daniel Serrano
Date of birth: 1987-09-22
Occupation: Logistics coordinator
Address: 112 Calle del Bosque, Pacific Ridge
Phone: +1-202-555-0112
Email: daniel.serrano@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Missing person: No
Active missing-person search order: No
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: An arrest warrant does not constitute a conviction. No criminal record or active judicial proceedings registered.
Warrant number: PR-OC-2026-012
Issue date: 2026-11-04
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Daniel Serrano'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Daniel Serrano'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Daniel Serrano'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0012
Full name: Daniel Serrano
Date of birth: 1987-09-22
Occupation: Logistics coordinator
Address: 112 Calle del Bosque, Pacific Ridge
Phone: +1-202-555-0112
Email: daniel.serrano@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Missing person: No
Active missing-person search order: No
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: An arrest warrant does not constitute a conviction. No criminal record or active judicial proceedings registered.
Warrant number: PR-OC-2026-012
Issue date: 2026-11-04
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0012
Nombre completo: Daniel Serrano
Fecha de nacimiento: 1987-09-22
Ocupación: Coordinador de logística
Domicilio: 112 Calle del Bosque, Pacific Ridge
Teléfono: +1-202-555-0112
Correo: daniel.serrano@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Vigente
Proceso judicial: Sin procesos judiciales activos registrados
Persona desaparecida: No
Orden de búsqueda activa: No
Última revisión: 4 de noviembre de 2026, 12:00 (UTC−05:00)
Observaciones: Una orden de captura no constituye una condena. Sin antecedentes penales ni procesos judiciales activos registrados.
Número de orden: PR-OC-2026-012
Fecha de expedición: 2026-11-04
Juez que ordena: Julia Rivas
Despacho judicial: Juzgado 3 de Control de Garantías de Pacific Ridge
Objeto de la orden: Comparecencia requerida por orden judicial'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0012
Full name: Daniel Serrano
Date of birth: 1987-09-22
Occupation: Logistics coordinator
Address: 112 Calle del Bosque, Pacific Ridge
Phone: +1-202-555-0112
Email: daniel.serrano@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: Active
Judicial proceedings: No active judicial proceedings registered
Missing person: No
Active missing-person search order: No
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: An arrest warrant does not constitute a conviction. No criminal record or active judicial proceedings registered.
Warrant number: PR-OC-2026-012
Issue date: 2026-11-04
Issuing judge: Julia Rivas
Issuing court: Pacific Ridge Judicial Oversight Court 3
Purpose of warrant: Appearance required by judicial order'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '0880d312f23e5b3389c72c8e742f1325' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '5952f4f57b5d5f908dc1e37e1fe5d4eb' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-12' AND r.version = 1 AND r.title = 'Daniel Serrano' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0012' AND (r.data ->> 'full_name') = 'Daniel Serrano' AND (r.data ->> 'birth_date') = '1987-09-22' AND (r.data ->> 'occupation') = 'Coordinador de logística' AND (r.data ->> 'residence') = '112 Calle del Bosque, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0112' AND (r.data ->> 'email') = 'daniel.serrano@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-012' AND (r.data ->> 'warrant_issued_at') = '2026-11-04' AND (r.data ->> 'issuing_judge') = 'Julia Rivas' AND (r.data ->> 'issuing_court') = 'Juzgado 3 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia requerida por orden judicial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura no constituye una condena. Sin antecedentes penales ni procesos judiciales activos registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'false' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'false' AND CAST((r.data -> 'search_order_reference') AS TEXT) = 'null' AND CAST((r.data -> 'search_order_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_reference') AS TEXT) = 'null' AND CAST((r.data -> 'reported_missing_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_location') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_details') AS TEXT) = 'null');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM use_case_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';

-- security:police-case:security-person-13
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '3aea3d079405548eaaa4238021f34cc2'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.media_id = 'bb5d38e796155055b9ff389d6d5538fc'
  AND p.category_id = '3a0e6fa44305565a9b916543535c2fcc'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-13'
  AND p.caption = 'Samuel Ortega'
  AND p.note_text = 'Identifier: PRP-0013
Full name: Samuel Ortega
Date of birth: 1995-02-11
Occupation: Librarian
Address: 113 Avenida del Lago, Pacific Ridge
Phone: +1-202-555-0113
Email: samuel.ortega@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-013
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-013
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Lake Park, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Samuel Ortega'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Samuel Ortega'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Samuel Ortega'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0013
Full name: Samuel Ortega
Date of birth: 1995-02-11
Occupation: Librarian
Address: 113 Avenida del Lago, Pacific Ridge
Phone: +1-202-555-0113
Email: samuel.ortega@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-013
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-013
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Lake Park, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0013
Nombre completo: Samuel Ortega
Fecha de nacimiento: 1995-02-11
Ocupación: Bibliotecario
Domicilio: 113 Avenida del Lago, Pacific Ridge
Teléfono: +1-202-555-0113
Correo: samuel.ortega@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Persona desaparecida: Sí
Orden de búsqueda activa: Sí
Última revisión: 4 de noviembre de 2026, 12:00 (UTC−05:00)
Observaciones: Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.
Número de orden de búsqueda: PR-OB-2026-013
Fecha de orden de búsqueda: 2026-11-04
Reporte de desaparición: PR-DES-2026-013
Desaparición reportada: 4 de noviembre de 2026, 08:00 (UTC−05:00)
Última vez visto: 3 de noviembre de 2026, 18:00 (UTC−05:00)
Lugar de última observación: Parque del Lago, Pacific Ridge
Detalle del reporte: Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0013
Full name: Samuel Ortega
Date of birth: 1995-02-11
Occupation: Librarian
Address: 113 Avenida del Lago, Pacific Ridge
Phone: +1-202-555-0113
Email: samuel.ortega@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-013
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-013
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Lake Park, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '3a0e6fa44305565a9b916543535c2fcc' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '202706e1405f52a582aff8827ad1064c' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '4323a3148c5f5be6a66ad8a09e20b615' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-13' AND r.version = 1 AND r.title = 'Samuel Ortega' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0013' AND (r.data ->> 'full_name') = 'Samuel Ortega' AND (r.data ->> 'birth_date') = '1995-02-11' AND (r.data ->> 'occupation') = 'Bibliotecario' AND (r.data ->> 'residence') = '113 Avenida del Lago, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0113' AND (r.data ->> 'email') = 'samuel.ortega@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-013' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-013' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Parque del Lago, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM use_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';

-- security:police-case:security-person-14
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = 'f5e89d22320e5876ad3152b069d904b0'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.media_id = 'b0757822f7015284a092b90e85bb5d24'
  AND p.category_id = '3a0e6fa44305565a9b916543535c2fcc'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-14'
  AND p.caption = 'Elena Duarte'
  AND p.note_text = 'Identifier: PRP-0014
Full name: Elena Duarte
Date of birth: 1989-06-14
Occupation: Graphic designer
Address: 114 Calle del Parque, Pacific Ridge
Phone: +1-202-555-0114
Email: elena.duarte@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-014
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-014
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Central Square, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Elena Duarte'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Elena Duarte'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Elena Duarte'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0014
Full name: Elena Duarte
Date of birth: 1989-06-14
Occupation: Graphic designer
Address: 114 Calle del Parque, Pacific Ridge
Phone: +1-202-555-0114
Email: elena.duarte@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-014
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-014
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Central Square, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0014
Full name: Elena Duarte
Date of birth: 1989-06-14
Occupation: Graphic designer
Address: 114 Calle del Parque, Pacific Ridge
Phone: +1-202-555-0114
Email: elena.duarte@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-014
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-014
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Central Square, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0014
Nombre completo: Elena Duarte
Fecha de nacimiento: 1989-06-14
Ocupación: Diseñadora gráfica
Domicilio: 114 Calle del Parque, Pacific Ridge
Teléfono: +1-202-555-0114
Correo: elena.duarte@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Persona desaparecida: Sí
Orden de búsqueda activa: Sí
Última revisión: 4 de noviembre de 2026, 12:00 (UTC−05:00)
Observaciones: Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.
Número de orden de búsqueda: PR-OB-2026-014
Fecha de orden de búsqueda: 2026-11-04
Reporte de desaparición: PR-DES-2026-014
Desaparición reportada: 4 de noviembre de 2026, 08:00 (UTC−05:00)
Lugar de última observación: Plaza Central, Pacific Ridge
Detalle del reporte: Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.
Última vez vista: 3 de noviembre de 2026, 18:00 (UTC−05:00)'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '3a0e6fa44305565a9b916543535c2fcc' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '202706e1405f52a582aff8827ad1064c' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '7ad48993912a54aeb249958a3e5abdab' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-14' AND r.version = 1 AND r.title = 'Elena Duarte' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0014' AND (r.data ->> 'full_name') = 'Elena Duarte' AND (r.data ->> 'birth_date') = '1989-06-14' AND (r.data ->> 'occupation') = 'Diseñadora gráfica' AND (r.data ->> 'residence') = '114 Calle del Parque, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0114' AND (r.data ->> 'email') = 'elena.duarte@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-014' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-014' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Plaza Central, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM use_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';

-- security:police-case:security-person-15
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '7aef2e4bae7355eba0e906555fd88163'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.media_id = 'c95e621d31c35f9b9d24656d202d1250'
  AND p.category_id = '3a0e6fa44305565a9b916543535c2fcc'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-15'
  AND p.caption = 'Isabel Mora'
  AND p.note_text = 'Identifier: PRP-0015
Full name: Isabel Mora
Date of birth: 1993-11-02
Occupation: Teacher
Address: 115 Avenida de los Olmos, Pacific Ridge
Phone: +1-202-555-0115
Email: isabel.mora@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-015
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-015
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Municipal Library, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Isabel Mora'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Isabel Mora'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Isabel Mora'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0015
Full name: Isabel Mora
Date of birth: 1993-11-02
Occupation: Teacher
Address: 115 Avenida de los Olmos, Pacific Ridge
Phone: +1-202-555-0115
Email: isabel.mora@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-015
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-015
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Municipal Library, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0015
Full name: Isabel Mora
Date of birth: 1993-11-02
Occupation: Teacher
Address: 115 Avenida de los Olmos, Pacific Ridge
Phone: +1-202-555-0115
Email: isabel.mora@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-015
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-015
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: Municipal Library, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0015
Nombre completo: Isabel Mora
Fecha de nacimiento: 1993-11-02
Ocupación: Profesora
Domicilio: 115 Avenida de los Olmos, Pacific Ridge
Teléfono: +1-202-555-0115
Correo: isabel.mora@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Persona desaparecida: Sí
Orden de búsqueda activa: Sí
Última revisión: 4 de noviembre de 2026, 12:00 (UTC−05:00)
Observaciones: Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.
Número de orden de búsqueda: PR-OB-2026-015
Fecha de orden de búsqueda: 2026-11-04
Reporte de desaparición: PR-DES-2026-015
Desaparición reportada: 4 de noviembre de 2026, 08:00 (UTC−05:00)
Lugar de última observación: Biblioteca Municipal, Pacific Ridge
Detalle del reporte: Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.
Última vez vista: 3 de noviembre de 2026, 18:00 (UTC−05:00)'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '3a0e6fa44305565a9b916543535c2fcc' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '202706e1405f52a582aff8827ad1064c' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'b664fcd98b395de6972e2a0de21bef6d' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-15' AND r.version = 1 AND r.title = 'Isabel Mora' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0015' AND (r.data ->> 'full_name') = 'Isabel Mora' AND (r.data ->> 'birth_date') = '1993-11-02' AND (r.data ->> 'occupation') = 'Profesora' AND (r.data ->> 'residence') = '115 Avenida de los Olmos, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0115' AND (r.data ->> 'email') = 'isabel.mora@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-015' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-015' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Biblioteca Municipal, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM use_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';

-- security:police-case:security-person-16
INSERT INTO use_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '01357527c1cf5e70a689acd0545e7735'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.media_id = 'a7abaeb64ae15946b962a65354be7b6d'
  AND p.category_id = '3a0e6fa44305565a9b916543535c2fcc'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-16'
  AND p.caption = 'Natalia Campos'
  AND p.note_text = 'Identifier: PRP-0016
Full name: Natalia Campos
Date of birth: 1998-03-27
Occupation: Quality analyst
Address: 116 Calle del Río, Pacific Ridge
Phone: +1-202-555-0116
Email: natalia.campos@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-016
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-016
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: North Terminal, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND p.hidden = FALSE
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(p.display_text AS TEXT)) LIKE '{%' THEN p.display_text ELSE '{}' END)) = 2
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'caption') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'caption') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'caption') ->> 'source') = 'Natalia Campos'
  AND ((p.display_text -> 'caption') ->> 'en') = 'Natalia Campos'
  AND ((p.display_text -> 'caption') ->> 'es') = 'Natalia Campos'
  AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((p.display_text -> 'note_text') AS TEXT)) LIKE '{%' THEN (p.display_text -> 'note_text') ELSE '{}' END)) = 3
  AND ((p.display_text -> 'note_text') ->> 'source') = 'Identifier: PRP-0016
Full name: Natalia Campos
Date of birth: 1998-03-27
Occupation: Quality analyst
Address: 116 Calle del Río, Pacific Ridge
Phone: +1-202-555-0116
Email: natalia.campos@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-016
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-016
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: North Terminal, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'en') = 'Identifier: PRP-0016
Full name: Natalia Campos
Date of birth: 1998-03-27
Occupation: Quality analyst
Address: 116 Calle del Río, Pacific Ridge
Phone: +1-202-555-0116
Email: natalia.campos@example.com
Criminal history: No convictions or criminal record registered
Arrest warrant: No warrants registered
Judicial proceedings: No active judicial proceedings registered
Missing person: Yes
Active missing-person search order: Yes
Last reviewed: November 4, 2026, 12:00 (UTC−05:00)
Notes: Reported missing. The search order seeks to locate this person; it is not an arrest warrant. No criminal record or judicial proceedings registered.
Search order number: PR-OB-2026-016
Search order issue date: 2026-11-04
Missing-person report: PR-DES-2026-016
Reported missing: November 4, 2026, 08:00 (UTC−05:00)
Last seen: November 3, 2026, 18:00 (UTC−05:00)
Last-seen location: North Terminal, Pacific Ridge
Report details: Missing-person report received; an active search seeks to locate the person, without an arrest warrant.'
  AND ((p.display_text -> 'note_text') ->> 'es') = 'Identificador: PRP-0016
Nombre completo: Natalia Campos
Fecha de nacimiento: 1998-03-27
Ocupación: Analista de calidad
Domicilio: 116 Calle del Río, Pacific Ridge
Teléfono: +1-202-555-0116
Correo: natalia.campos@example.com
Antecedentes penales: Sin condenas ni antecedentes penales registrados
Orden de captura: Sin órdenes registradas
Proceso judicial: Sin procesos judiciales activos registrados
Persona desaparecida: Sí
Orden de búsqueda activa: Sí
Última revisión: 4 de noviembre de 2026, 12:00 (UTC−05:00)
Observaciones: Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.
Número de orden de búsqueda: PR-OB-2026-016
Fecha de orden de búsqueda: 2026-11-04
Reporte de desaparición: PR-DES-2026-016
Desaparición reportada: 4 de noviembre de 2026, 08:00 (UTC−05:00)
Lugar de última observación: Terminal Norte, Pacific Ridge
Detalle del reporte: Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.
Última vez vista: 3 de noviembre de 2026, 18:00 (UTC−05:00)'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.id = '3a0e6fa44305565a9b916543535c2fcc' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '016ba574633a567bb4a9b739cd820f4d' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '202706e1405f52a582aff8827ad1064c' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5c49c93dc6b45ad5acc8e84af5359eac' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a4838f25e4c0527abac01d410b8261b6' AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'f0243ecc7bd6591184a2e33cd6925aa5' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-16' AND r.version = 1 AND r.title = 'Natalia Campos' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0016' AND (r.data ->> 'full_name') = 'Natalia Campos' AND (r.data ->> 'birth_date') = '1998-03-27' AND (r.data ->> 'occupation') = 'Analista de calidad' AND (r.data ->> 'residence') = '116 Calle del Río, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0116' AND (r.data ->> 'email') = 'natalia.campos@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-016' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-016' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Terminal Norte, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.');
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM use_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM use_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM use_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';
INSERT INTO use_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM use_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('0880d312f23e5b3389c72c8e742f1325', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Active arrest warrants', 'active arrest warrants', '{"name": {"source": "Active arrest warrants", "en": "Active arrest warrants", "es": "Órdenes de captura vigentes"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('086c678cc6a25d2ba430ed7e0f6724fd', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Audiovisual material', 'audiovisual material', '{"name": {"source": "Audiovisual material", "en": "Audiovisual material", "es": "Material audiovisual"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('3a0e6fa44305565a9b916543535c2fcc', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Missing persons', 'missing persons', '{"name": {"source": "Missing persons", "en": "Missing persons", "es": "Personas desaparecidas"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('1419ad5c7cb758edac50b7ea77a2f211', '09f6bc068d365e69a0506f690fe1168b', 'category', 'No warrants or criminal history', 'no warrants or criminal history', '{"name": {"source": "No warrants or criminal history", "en": "No warrants or criminal history", "es": "Sin órdenes ni antecedentes"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('c7a20164063755ad80a9133542e69dc4', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active arrest warrant', 'active arrest warrant', '{"name": {"source": "Active arrest warrant", "en": "Active arrest warrant", "es": "Orden de captura vigente"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('19bf084012155d08a4365789cbb1a7cd', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active judicial proceedings', 'active judicial proceedings', '{"name": {"source": "Active judicial proceedings", "en": "Active judicial proceedings", "es": "Proceso judicial activo"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('202706e1405f52a582aff8827ad1064c', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active search order', 'active search order', '{"name": {"source": "Active search order", "en": "Active search order", "es": "Orden de búsqueda vigente"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('5c49c93dc6b45ad5acc8e84af5359eac', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No active arrest warrants', 'no active arrest warrants', '{"name": {"source": "No active arrest warrants", "en": "No active arrest warrants", "es": "Sin órdenes de captura"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('016ba574633a567bb4a9b739cd820f4d', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No active proceedings', 'no active proceedings', '{"name": {"source": "No active proceedings", "en": "No active proceedings", "es": "Sin procesos activos"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('feedcac5c42a5eb2a199ca219311efc2', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No recorded criminal history', 'no recorded criminal history', '{"name": {"source": "No recorded criminal history", "en": "No recorded criminal history", "es": "Sin antecedentes registrados"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('1ea67585530757ad83d09cf00e2ead02', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Observation video', 'observation video', '{"name": {"source": "Observation video", "en": "Observation video", "es": "Video de observación"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('0fc6533b32c35498bc999821bc630a4e', '3ea760d883945dddb1d7ad27bd996b17', 'category', 'Introductions', 'introductions', '{"name": {"source": "Introductions", "en": "Introductions", "es": "Presentaciones"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('6e03557ad92b5c719bd17d6ed899620c', '3ea760d883945dddb1d7ad27bd996b17', 'category', 'Social content', 'social content', '{"name": {"source": "Social content", "en": "Social content", "es": "Contenido social"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('68fd385f063a5827894e9c7854274d23', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Community', 'community', '{"name": {"source": "Community", "en": "Community", "es": "Comunidad"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('6fc11d21a13f54058e7f6f305adffa5e', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Everyday life', 'everyday life', '{"name": {"source": "Everyday life", "en": "Everyday life", "es": "Vida cotidiana"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('28f3f7a4fe3c5d96adc11d0f6fdd29b8', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Personal introduction', 'personal introduction', '{"name": {"source": "Personal introduction", "en": "Personal introduction", "es": "Presentación personal"}}');
INSERT INTO use_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('88e34bccfc3552adbdb4b68a7fe9fb31', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Video', 'video', '{"name": {"source": "Video", "en": "Video", "es": "Video"}}');

-- A term archived or replaced by the owner is not restored implicitly.
DELETE FROM use_case_posts WHERE EXISTS (
    SELECT 1 FROM use_case_terms wanted JOIN publication_terms actual ON
      actual.id = wanted.id OR (actual.workspace_id = wanted.workspace_id AND actual.kind = wanted.kind AND actual.name_key = wanted.name_key)
    WHERE wanted.workspace_id = use_case_posts.workspace_id
      AND ((wanted.kind = 'category' AND wanted.name_key = use_case_posts.category_key)
           OR (wanted.kind = 'tag' AND EXISTS (SELECT 1 FROM use_case_tags ut WHERE ut.post_id = use_case_posts.post_id AND ut.name_key = wanted.name_key)))
      AND (actual.active = FALSE OR actual.workspace_id != wanted.workspace_id OR actual.kind != wanted.kind OR actual.name_key != wanted.name_key)
);
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT wanted.id, wanted.workspace_id, wanted.kind, wanted.name, wanted.name_key, TRUE, wanted.display_text
FROM use_case_terms wanted WHERE EXISTS (
    SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = wanted.workspace_id
      AND ((wanted.kind = 'category' AND cp.category_key = wanted.name_key)
           OR (wanted.kind = 'tag' AND EXISTS (SELECT 1 FROM use_case_tags ct WHERE ct.post_id = cp.post_id AND ct.name_key = wanted.name_key)))
) AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = wanted.id OR (t.workspace_id = wanted.workspace_id AND t.kind = wanted.kind AND t.name_key = wanted.name_key))
ON CONFLICT DO NOTHING;
DELETE FROM use_case_posts WHERE NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.workspace_id = use_case_posts.workspace_id AND t.kind = 'category' AND t.name_key = use_case_posts.category_key AND t.active = TRUE)
  OR EXISTS (SELECT 1 FROM use_case_tags ct WHERE ct.post_id = use_case_posts.post_id AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.workspace_id = use_case_posts.workspace_id AND t.kind = 'tag' AND t.name_key = ct.name_key AND t.active = TRUE));

-- Reclassify only the selected original rows; no new publication or media is created.
UPDATE publications SET category_id = (SELECT t.id FROM use_case_posts cp JOIN publication_terms t ON t.workspace_id = cp.workspace_id AND t.name_key = cp.category_key WHERE cp.post_id = publications.id AND t.kind = 'category' AND t.active = TRUE) WHERE id IN (SELECT post_id FROM use_case_posts);
DELETE FROM publication_tags WHERE post_id IN (SELECT post_id FROM use_case_posts);
INSERT INTO "publication_tags" (post_id, term_id) SELECT cp.post_id, t.id FROM use_case_posts cp JOIN use_case_tags ct ON ct.post_id = cp.post_id JOIN publication_terms t ON t.workspace_id = cp.workspace_id AND t.kind = 'tag' AND t.name_key = ct.name_key AND t.active = TRUE ON CONFLICT DO NOTHING;

-- Keep the existing term identity; only its untouched authored Spanish wording changes.
UPDATE publication_terms SET display_text = '{"name": {"source": "Active judicial proceedings", "en": "Active judicial proceedings", "es": "Proceso judicial activo"}}' WHERE publication_terms.id = '19bf084012155d08a4365789cbb1a7cd' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Active judicial proceedings' AND publication_terms.name_key = 'active judicial proceedings' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Active judicial proceedings' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Active judicial proceedings' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Procesos judiciales activos' AND EXISTS (SELECT 1 FROM use_case_posts cp JOIN use_case_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = publication_terms.workspace_id AND ct.name_key = publication_terms.name_key);

-- Retire untouched, unreferenced vocabulary: Cycling
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '0b0ed757af98520aa9d008ba1490ba9b' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Cycling' AND publication_terms.name_key = 'cycling' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Ciclismo'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Experiences
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '2002638d207e5407b4c107010bd5fadc' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Experiences' AND publication_terms.name_key = 'experiences' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Experiences' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Experiences' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Experiencias'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Public space videos
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '2a3508ea47675f9ab9842266cda7c6b5' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'category' AND publication_terms.name = 'Public space videos' AND publication_terms.name_key = 'public space videos' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Walking
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '3eb9712f94085d3e8e1b55a98ba13605' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Walking' AND publication_terms.name_key = 'walking' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Caminata'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Public space videos
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '62a47280210f5a399e2f7bebaaa1e0bf' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'category' AND publication_terms.name = 'Public space videos' AND publication_terms.name_key = 'public space videos' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Walking
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '6f4530d2cf135600a3e63d58bdba9471' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Walking' AND publication_terms.name_key = 'walking' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Caminata'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Stories
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '84fe3811d7af5cfa871389ea39f86f28' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Stories' AND publication_terms.name_key = 'stories' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Stories' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Stories' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Historias'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Park
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '928f6c5f58685b3fb4214b64a4b80be4' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Park' AND publication_terms.name_key = 'park' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Parque'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Winter
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = '9dca3192b8f65aa89cdf196283c4ce10' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Winter' AND publication_terms.name_key = 'winter' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Winter' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Winter' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Invierno'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Portrait
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'a4838f25e4c0527abac01d410b8261b6' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Portrait' AND publication_terms.name_key = 'portrait' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Portrait' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Portrait' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Retrato'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Park
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'a74bd4bb8c335a238389c15fbaca1b39' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Park' AND publication_terms.name_key = 'park' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Parque'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Photography
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'c33b3e1207795dc9a5697a526a5f7b5c' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Photography' AND publication_terms.name_key = 'photography' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Photography' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Photography' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Fotografía'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Cycling
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'de0765905929588390cc530f03ebc852' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Cycling' AND publication_terms.name_key = 'cycling' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Ciclismo'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: City sidewalk
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'e2c30e2d28ae58a8b73c2b99ba69b396' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'City sidewalk' AND publication_terms.name_key = 'city sidewalk' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'City sidewalk' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'City sidewalk' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Acera urbana'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Overcast day
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'e44b598aad515e859ba2e1598b3d6248' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Overcast day' AND publication_terms.name_key = 'overcast day' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Overcast day' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Overcast day' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Día nublado'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Projects
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'f395bff7a83452e5ab69f95ab4f2890b' AND publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Projects' AND publication_terms.name_key = 'projects' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Projects' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Projects' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Proyectos'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

-- Retire untouched, unreferenced vocabulary: Spring
UPDATE publication_terms SET active = FALSE WHERE publication_terms.id = 'fc95a832ac625dd5aa579c8219b95f09' AND publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Spring' AND publication_terms.name_key = 'spring' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Spring' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Spring' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Primavera'
  AND EXISTS (SELECT 1 FROM use_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');
DROP TABLE use_case_tags;
DROP TABLE use_case_posts;
DROP TABLE use_case_terms;
