-- Repair earlier local installations whose catalog terms received random UUIDs.

-- Recognize only the original scoped vocabulary, publication copy and recorded facts.

-- Accept the two delivered source-reference formats; reuse original bytes by verified provenance.

-- Existing identities, manual revision history, hidden/deleted rows and pending uploads are preserved.

CREATE TEMP TABLE legacy_case_posts (post_id UUID PRIMARY KEY, workspace_id UUID NOT NULL, category_key TEXT NOT NULL);

CREATE TEMP TABLE legacy_case_tags (post_id UUID NOT NULL, name_key TEXT NOT NULL, PRIMARY KEY (post_id, name_key));

CREATE TEMP TABLE legacy_case_terms (id UUID PRIMARY KEY, workspace_id UUID NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL, name_key TEXT NOT NULL, display_text JSON NOT NULL);

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'social content'
FROM publications p
WHERE p.id = 'c6af2491f99551e59a3084f0045ec2c9'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '63297a1bbc7f52df9b76cf3c33739bb7'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '0b54cc4fd3bdea236e6254b4910b795eea7594ff690dcdf2ae34f9ce33895479' AND asset.mime_type = 'video/mp4' AND asset.byte_size = 42388147 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('meta-social:pexels-12557513')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Cycling' AND t.name_key = 'cycling' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Cycling' AND ((t.display_text -> 'name') ->> 'en') = 'Cycling' AND ((t.display_text -> 'name') ->> 'es') = 'Ciclismo')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Outdoor life' AND ((t.display_text -> 'name') ->> 'es') = 'Vida al aire libre' AND ((t.display_text -> 'name') ->> 'en') = 'Outdoor life')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Public spaces' AND t.name_key = 'public spaces' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public spaces' AND ((t.display_text -> 'name') ->> 'es') = 'Espacios públicos' AND ((t.display_text -> 'name') ->> 'en') = 'Public spaces')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'People walking' AND t.name_key = 'people walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'People walking' AND ((t.display_text -> 'name') ->> 'es') = 'Personas caminando' AND ((t.display_text -> 'name') ->> 'en') = 'People walking')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'video' FROM legacy_case_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'everyday life' FROM legacy_case_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'social content'
FROM publications p
WHERE p.id = 'c1de88652d045a04a56cc29caaa7963c'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '484b780027455aa4aa0f3d3ed603acf6'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'b24838d5c2482a9ea923668aa829015f6645fb540f1380098ad06a0221ca317f' AND asset.mime_type = 'video/mp4' AND asset.byte_size = 65217080 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('meta-social:pexels-33802407')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'City sidewalk' AND t.name_key = 'city sidewalk' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'City sidewalk' AND ((t.display_text -> 'name') ->> 'en') = 'City sidewalk' AND ((t.display_text -> 'name') ->> 'es') = 'Acera urbana')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Outdoor life' AND ((t.display_text -> 'name') ->> 'es') = 'Vida al aire libre' AND ((t.display_text -> 'name') ->> 'en') = 'Outdoor life')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Public spaces' AND t.name_key = 'public spaces' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public spaces' AND ((t.display_text -> 'name') ->> 'es') = 'Espacios públicos' AND ((t.display_text -> 'name') ->> 'en') = 'Public spaces')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'People walking' AND t.name_key = 'people walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'People walking' AND ((t.display_text -> 'name') ->> 'es') = 'Personas caminando' AND ((t.display_text -> 'name') ->> 'en') = 'People walking')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'video' FROM legacy_case_posts WHERE post_id = 'c1de88652d045a04a56cc29caaa7963c';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'everyday life' FROM legacy_case_posts WHERE post_id = 'c1de88652d045a04a56cc29caaa7963c';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'social content'
FROM publications p
WHERE p.id = '9b3e3f5710545f36a378902058bc34cc'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '9467affefe045ed8ae5c4d4bb7c5ac23'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'd053076c8b6adfce97847e8063af66722ca43fcdd29417d4b86c53e744a34c03' AND asset.mime_type = 'video/mp4' AND asset.byte_size = 14501150 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('meta-social:pexels-3699519')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Winter' AND t.name_key = 'winter' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Winter' AND ((t.display_text -> 'name') ->> 'en') = 'Winter' AND ((t.display_text -> 'name') ->> 'es') = 'Invierno')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Outdoor life' AND ((t.display_text -> 'name') ->> 'es') = 'Vida al aire libre' AND ((t.display_text -> 'name') ->> 'en') = 'Outdoor life')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Public spaces' AND t.name_key = 'public spaces' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public spaces' AND ((t.display_text -> 'name') ->> 'es') = 'Espacios públicos' AND ((t.display_text -> 'name') ->> 'en') = 'Public spaces')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'People walking' AND t.name_key = 'people walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'People walking' AND ((t.display_text -> 'name') ->> 'es') = 'Personas caminando' AND ((t.display_text -> 'name') ->> 'en') = 'People walking')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'video' FROM legacy_case_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'everyday life' FROM legacy_case_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '9c941832fbbb5bd1a4f85a97cd82acb2'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '484b780027455aa4aa0f3d3ed603acf6'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'd8e3a49a4bb4a75a0f37d02e85f727defa7effb715391cbf6acfd0b2a213624f' AND asset.mime_type = 'image/png' AND asset.byte_size = 2089875 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('meta-social:social-introduction:elena-marquez', 'social-introduction:elena-marquez')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Introductions' AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Community' AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Photography' AND t.name_key = 'photography' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Photography' AND ((t.display_text -> 'name') ->> 'en') = 'Photography' AND ((t.display_text -> 'name') ->> 'es') = 'Fotografía')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Projects' AND t.name_key = 'projects' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Projects' AND ((t.display_text -> 'name') ->> 'en') = 'Projects' AND ((t.display_text -> 'name') ->> 'es') = 'Proyectos')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad' AND ((t.display_text -> 'name') ->> 'source') = 'Community')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones' AND ((t.display_text -> 'name') ->> 'source') = 'Introductions')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'personal introduction' FROM legacy_case_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'community' FROM legacy_case_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '274fc4bb223852fc9bc5e8ed8829ec8d'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '9467affefe045ed8ae5c4d4bb7c5ac23'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'a8dae1068161975e0527c566d80059bfeef5d92b2d0eeafd74471399ee5de899' AND asset.mime_type = 'image/png' AND asset.byte_size = 2006618 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('meta-social:social-introduction:mateo-rios', 'social-introduction:mateo-rios')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Introductions' AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Experiences' AND t.name_key = 'experiences' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Experiences' AND ((t.display_text -> 'name') ->> 'en') = 'Experiences' AND ((t.display_text -> 'name') ->> 'es') = 'Experiencias')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Community' AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad' AND ((t.display_text -> 'name') ->> 'source') = 'Community')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones' AND ((t.display_text -> 'name') ->> 'source') = 'Introductions')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'personal introduction' FROM legacy_case_posts WHERE post_id = '274fc4bb223852fc9bc5e8ed8829ec8d';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'community' FROM legacy_case_posts WHERE post_id = '274fc4bb223852fc9bc5e8ed8829ec8d';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '83f449740fe357c2ae3a5b8b223ec53e'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '63297a1bbc7f52df9b76cf3c33739bb7'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'a15344dbdc6f7e4190e21a143d30bd11e7bf909c6883d86be812e73a09146b94' AND asset.mime_type = 'image/png' AND asset.byte_size = 2184128 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('meta-social:social-introduction:sarah-chen', 'social-introduction:sarah-chen')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Introductions' AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Community' AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Stories' AND t.name_key = 'stories' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Stories' AND ((t.display_text -> 'name') ->> 'en') = 'Stories' AND ((t.display_text -> 'name') ->> 'es') = 'Historias')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Photography' AND t.name_key = 'photography' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Photography' AND ((t.display_text -> 'name') ->> 'en') = 'Photography' AND ((t.display_text -> 'name') ->> 'es') = 'Fotografía')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name = 'Community' AND t.name_key = 'community' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Community' AND ((t.display_text -> 'name') ->> 'es') = 'Comunidad' AND ((t.display_text -> 'name') ->> 'source') = 'Community')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name = 'Introductions' AND t.name_key = 'introductions' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Introductions' AND ((t.display_text -> 'name') ->> 'es') = 'Presentaciones' AND ((t.display_text -> 'name') ->> 'source') = 'Introductions')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'personal introduction' FROM legacy_case_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'community' FROM legacy_case_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'audiovisual material'
FROM publications p
WHERE p.id = '41b2b8cf66c65e3cbf41025c47bb0245'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '2283574ab70934888dccb9ea213c29c9b777b3e8fffd1c1fca816c247f266655' AND asset.mime_type = 'video/mp4' AND asset.byte_size = 89802548 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:pexels-25757454')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Cycling' AND t.name_key = 'cycling' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Cycling' AND ((t.display_text -> 'name') ->> 'en') = 'Cycling' AND ((t.display_text -> 'name') ->> 'es') = 'Ciclismo')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Outdoor life' AND ((t.display_text -> 'name') ->> 'es') = 'Vida al aire libre' AND ((t.display_text -> 'name') ->> 'en') = 'Outdoor life')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Public spaces' AND t.name_key = 'public spaces' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public spaces' AND ((t.display_text -> 'name') ->> 'es') = 'Espacios públicos' AND ((t.display_text -> 'name') ->> 'en') = 'Public spaces')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'People walking' AND t.name_key = 'people walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'People walking' AND ((t.display_text -> 'name') ->> 'es') = 'Personas caminando' AND ((t.display_text -> 'name') ->> 'en') = 'People walking')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'observation video' FROM legacy_case_posts WHERE post_id = '41b2b8cf66c65e3cbf41025c47bb0245';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'audiovisual material'
FROM publications p
WHERE p.id = 'a64f19f460f752ca8a6daaa9b1947492'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '79d8da4c40a102b69d7d021d55bd81271547049ccc1ba660646ff0408109dfb9' AND asset.mime_type = 'video/mp4' AND asset.byte_size = 89900324 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:pexels-29401365')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Overcast day' AND t.name_key = 'overcast day' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Overcast day' AND ((t.display_text -> 'name') ->> 'en') = 'Overcast day' AND ((t.display_text -> 'name') ->> 'es') = 'Día nublado')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Outdoor life' AND ((t.display_text -> 'name') ->> 'es') = 'Vida al aire libre' AND ((t.display_text -> 'name') ->> 'en') = 'Outdoor life')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Public spaces' AND t.name_key = 'public spaces' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public spaces' AND ((t.display_text -> 'name') ->> 'es') = 'Espacios públicos' AND ((t.display_text -> 'name') ->> 'en') = 'Public spaces')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'People walking' AND t.name_key = 'people walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'People walking' AND ((t.display_text -> 'name') ->> 'es') = 'Personas caminando' AND ((t.display_text -> 'name') ->> 'en') = 'People walking')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'observation video' FROM legacy_case_posts WHERE post_id = 'a64f19f460f752ca8a6daaa9b1947492';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'audiovisual material'
FROM publications p
WHERE p.id = '24b0b2ee56d35f83b90c67961c8ab23f'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '9427e378da00add8d9b287961597697b30f7615047bf45d3ff9d62cd6505264c' AND asset.mime_type = 'video/mp4' AND asset.byte_size = 20931925 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:pexels-30614848')
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
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Public space videos' AND t.name_key = 'public space videos' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((t.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Walking' AND t.name_key = 'walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Walking' AND ((t.display_text -> 'name') ->> 'en') = 'Walking' AND ((t.display_text -> 'name') ->> 'es') = 'Caminata')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Park' AND t.name_key = 'park' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Park' AND ((t.display_text -> 'name') ->> 'en') = 'Park' AND ((t.display_text -> 'name') ->> 'es') = 'Parque')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Spring' AND t.name_key = 'spring' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Spring' AND ((t.display_text -> 'name') ->> 'en') = 'Spring' AND ((t.display_text -> 'name') ->> 'es') = 'Primavera')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Outdoor life' AND ((t.display_text -> 'name') ->> 'es') = 'Vida al aire libre' AND ((t.display_text -> 'name') ->> 'en') = 'Outdoor life')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Public spaces' AND t.name_key = 'public spaces' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Public spaces' AND ((t.display_text -> 'name') ->> 'es') = 'Espacios públicos' AND ((t.display_text -> 'name') ->> 'en') = 'Public spaces')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'People walking' AND t.name_key = 'people walking' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'People walking' AND ((t.display_text -> 'name') ->> 'es') = 'Personas caminando' AND ((t.display_text -> 'name') ->> 'en') = 'People walking')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'observation video' FROM legacy_case_posts WHERE post_id = '24b0b2ee56d35f83b90c67961c8ab23f';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = 'be1c4ea01ab856d1abdebd7ff0d8f81b'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'e8496f623ccf9b5e916496403bc4bedce65dc907eb18384679b9af5cf8da9c02' AND asset.mime_type = 'image/png' AND asset.byte_size = 2250926 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-01', 'police-case:security-person-01')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'e0b2f6bdb1845457b6e53791a42ec1f2' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-01' AND r.version = 1 AND r.title = 'Adrián Salcedo' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0001' AND (r.data ->> 'full_name') = 'Adrián Salcedo' AND (r.data ->> 'birth_date') = '1989-04-17' AND (r.data ->> 'occupation') = 'Coordinador de logística' AND (r.data ->> 'residence') = '17 Calle del Puerto, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0101' AND (r.data ->> 'email') = 'adrian.salcedo@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-001' AND (r.data ->> 'warrant_issued_at') = '2026-10-27' AND (r.data ->> 'issuing_judge') = 'Camila Torres' AND (r.data ->> 'issuing_court') = 'Juzgado 1 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia por investigación de hurto de mercancía' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'true' AND (r.data ->> 'case_number') = 'PR-PJ-2026-0141' AND (r.data ->> 'procedural_status') = 'Audiencia preliminar pendiente; sin sentencia' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura o un proceso abierto no constituye una condena.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active judicial proceedings' AND t.name_key = 'active judicial proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'es') IN ('Procesos judiciales activos', 'Proceso judicial activo'))
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM legacy_case_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active judicial proceedings' FROM legacy_case_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '5344161d0fa651e0ae4892a37e3e65c6'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'bbdda34ae568de22cf8bb6b0dbf24c3cc6acef6842eb26eb4326516c85c8ed68' AND asset.mime_type = 'image/png' AND asset.byte_size = 2400589 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-02', 'police-case:security-person-02')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '909d1a6da90855acabca10a4269ff2a1' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-02' AND r.version = 1 AND r.title = 'Esteban Pardo' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0002' AND (r.data ->> 'full_name') = 'Esteban Pardo' AND (r.data ->> 'birth_date') = '1968-09-23' AND (r.data ->> 'occupation') = 'Comerciante' AND (r.data ->> 'residence') = '82 Avenida Central, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0102' AND (r.data ->> 'email') = 'esteban.pardo@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-002' AND (r.data ->> 'warrant_issued_at') = '2026-10-28' AND (r.data ->> 'issuing_judge') = 'Javier Cortés' AND (r.data ->> 'issuing_court') = 'Juzgado 2 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia por investigación de fraude comercial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'true' AND (r.data ->> 'case_number') = 'PR-PJ-2026-0142' AND (r.data ->> 'procedural_status') = 'Etapa de investigación; sin sentencia' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura o un proceso abierto no constituye una condena.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active judicial proceedings' AND t.name_key = 'active judicial proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'Active judicial proceedings' AND ((t.display_text -> 'name') ->> 'es') IN ('Procesos judiciales activos', 'Proceso judicial activo'))
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM legacy_case_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active judicial proceedings' FROM legacy_case_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '4384e305ef325c7d9b8d6bd2c80c8b05'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '52d401bdd3a549799907d1a1c0c9397fa85c47de392a8c876b22c5d871b78c1c' AND asset.mime_type = 'image/png' AND asset.byte_size = 2651523 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-03', 'police-case:security-person-03')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '11aeb71325b258d893fb649de535e9a4' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-03' AND r.version = 1 AND r.title = 'Valeria Navarro' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0003' AND (r.data ->> 'full_name') = 'Valeria Navarro' AND (r.data ->> 'birth_date') = '1992-12-08' AND (r.data ->> 'occupation') = 'Contadora' AND (r.data ->> 'residence') = '31 Calle de los Olmos, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0103' AND (r.data ->> 'email') = 'valeria.navarro@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-003' AND (r.data ->> 'warrant_issued_at') = '2026-10-29' AND (r.data ->> 'issuing_judge') = 'Julia Rivas' AND (r.data ->> 'issuing_court') = 'Juzgado 3 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia requerida por orden judicial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura o un proceso abierto no constituye una condena.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM legacy_case_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '5217d89a1dba5d0fb6a5f51b10e22c13'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'ba2414f3cf26baff8a1a6e17065c38c3c6ba01c82b41c39b9055796cf5ba2f7c' AND asset.mime_type = 'image/png' AND asset.byte_size = 2293600 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-04', 'police-case:security-person-04')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'f2482f95e0675eb2b4768e7ff99d1d2a' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-04' AND r.version = 1 AND r.title = 'Lucía Cárdenas' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0004' AND (r.data ->> 'full_name') = 'Lucía Cárdenas' AND (r.data ->> 'birth_date') = '1995-06-12' AND (r.data ->> 'occupation') = 'Diseñadora gráfica' AND (r.data ->> 'residence') = '46 Paseo del Parque, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0104' AND (r.data ->> 'email') = 'lucia.cardenas@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '3a13e840a41456a4b85a3f0a4930b37b'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'd4629ff9bc4f5613799574c7f66b9b006774fdac0df8efcb186a5597411892cd' AND asset.mime_type = 'image/png' AND asset.byte_size = 2521977 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-05', 'police-case:security-person-05')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'b325103f59155714afb0e24f9c97ca82' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-05' AND r.version = 1 AND r.title = 'Tomás Beltrán' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0005' AND (r.data ->> 'full_name') = 'Tomás Beltrán' AND (r.data ->> 'birth_date') = '1987-02-20' AND (r.data ->> 'occupation') = 'Electricista' AND (r.data ->> 'residence') = '109 Calle del Roble, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0105' AND (r.data ->> 'email') = 'tomas.beltran@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '4fe1617c8a1b50089508572418d8f17c'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'cf1badb91b8561e29112aa1a6a4d7c8208e30e0475bc8b4f667c141cd3124585' AND asset.mime_type = 'image/png' AND asset.byte_size = 2216786 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-06', 'police-case:security-person-06')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '65050ead0c4f56c4b6695032f55b7f46' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-06' AND r.version = 1 AND r.title = 'Nicolás Acosta' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0006' AND (r.data ->> 'full_name') = 'Nicolás Acosta' AND (r.data ->> 'birth_date') = '1991-08-30' AND (r.data ->> 'occupation') = 'Mecánico automotriz' AND (r.data ->> 'residence') = '24 Avenida del Taller, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0106' AND (r.data ->> 'email') = 'nicolas.acosta@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '11a0c84493245994bd3099f55ff1c7da'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '0c5bdbc278182da188b9a9ca1a5505d56b7e3a32f72ec2e30ca4837dc1344133' AND asset.mime_type = 'image/png' AND asset.byte_size = 2289347 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-07', 'police-case:security-person-07')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'b0ea039f74905caea44043cbdcaad329' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-07' AND r.version = 1 AND r.title = 'Mariana Solano' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0007' AND (r.data ->> 'full_name') = 'Mariana Solano' AND (r.data ->> 'birth_date') = '1994-11-02' AND (r.data ->> 'occupation') = 'Docente de primaria' AND (r.data ->> 'residence') = '63 Calle de la Escuela, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0107' AND (r.data ->> 'email') = 'mariana.solano@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = 'b531b3d7de89559f91732114c30a4310'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '07d631d4b49822b7b436fed2175f7338abda9752251025e0f6b798797549f5c0' AND asset.mime_type = 'image/png' AND asset.byte_size = 2243234 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-08', 'police-case:security-person-08')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '1597fbaef5da5a23821276ca14f81e81' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-08' AND r.version = 1 AND r.title = 'Rafael Méndez' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0008' AND (r.data ->> 'full_name') = 'Rafael Méndez' AND (r.data ->> 'birth_date') = '1985-01-09' AND (r.data ->> 'occupation') = 'Analista de inventarios' AND (r.data ->> 'residence') = '55 Calle del Mercado, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0108' AND (r.data ->> 'email') = 'rafael.mendez@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '118407b2480157209ab9729c18c14294'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '4dba6a37e67508de942b2bd3a583a0e39c1db9146ff0b65fd8fe33ee7481e37e' AND asset.mime_type = 'image/png' AND asset.byte_size = 2490123 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-09', 'police-case:security-person-09')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'ba59535813655989a48718c54f48e066' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-09' AND r.version = 1 AND r.title = 'Camila Fuentes' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0009' AND (r.data ->> 'full_name') = 'Camila Fuentes' AND (r.data ->> 'birth_date') = '1998-03-26' AND (r.data ->> 'occupation') = 'Bibliotecaria' AND (r.data ->> 'residence') = '12 Paseo de los Cedros, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0109' AND (r.data ->> 'email') = 'camila.fuentes@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '118407b2480157209ab9729c18c14294';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '118407b2480157209ab9729c18c14294';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '118407b2480157209ab9729c18c14294';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '0a691133f51f583a840e3187f5222b39'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '65395583ad5cf60873952fcb2d7a76db34dfb16dfc4cbb1247df5f4134fe556f' AND asset.mime_type = 'image/png' AND asset.byte_size = 2732511 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-10', 'police-case:security-person-10')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'cde43426901a5c9386012f78935464d2' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-10' AND r.version = 1 AND r.title = 'Asha Mehta' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 19 AND (r.data ->> 'identifier') = 'PRP-0010' AND (r.data ->> 'full_name') = 'Asha Mehta' AND (r.data ->> 'birth_date') = '1967-07-19' AND (r.data ->> 'occupation') = 'Traductora' AND (r.data ->> 'residence') = '90 Avenida del Lago, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0110' AND (r.data ->> 'email') = 'asha.mehta@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-03T15:30:00-05:00' AND (r.data ->> 'notes') = 'Sin antecedentes, órdenes de captura ni procesos judiciales registrados.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'No warrants or criminal history' AND t.name_key = 'no warrants or criminal history' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'en') = 'No warrants or criminal history' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes ni antecedentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 3
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '8b7e666b35da56f7aac5233f1d4e8a31'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '383a7f9deca5f1b573b851b2e122e7786ea0a657a925a08c8e2fea21cb5f1305' AND asset.mime_type = 'image/png' AND asset.byte_size = 2036328 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-11')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'f33c891776ae50f5a46324dbc1e1e618' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-11' AND r.version = 1 AND r.title = 'Bruno Escobar' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0011' AND (r.data ->> 'full_name') = 'Bruno Escobar' AND (r.data ->> 'birth_date') = '1991-04-16' AND (r.data ->> 'occupation') = 'Técnico de mantenimiento' AND (r.data ->> 'residence') = '111 Avenida del Río, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0111' AND (r.data ->> 'email') = 'bruno.escobar@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-011' AND (r.data ->> 'warrant_issued_at') = '2026-11-04' AND (r.data ->> 'issuing_judge') = 'Julia Rivas' AND (r.data ->> 'issuing_court') = 'Juzgado 3 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia requerida por orden judicial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura no constituye una condena. Sin antecedentes penales ni procesos judiciales activos registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'false' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'false' AND CAST((r.data -> 'search_order_reference') AS TEXT) = 'null' AND CAST((r.data -> 'search_order_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_reference') AS TEXT) = 'null' AND CAST((r.data -> 'reported_missing_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_location') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_details') AS TEXT) = 'null')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM legacy_case_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = 'b50ca97e42c65cd0bc63c5b788f5adc5'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = 'c01da76031303e8f4ca501b114c7377e6b45e753820dcf4ad2019ce086c4cc39' AND asset.mime_type = 'image/png' AND asset.byte_size = 2082838 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-12')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '5952f4f57b5d5f908dc1e37e1fe5d4eb' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-12' AND r.version = 1 AND r.title = 'Daniel Serrano' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0012' AND (r.data ->> 'full_name') = 'Daniel Serrano' AND (r.data ->> 'birth_date') = '1987-09-22' AND (r.data ->> 'occupation') = 'Coordinador de logística' AND (r.data ->> 'residence') = '112 Calle del Bosque, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0112' AND (r.data ->> 'email') = 'daniel.serrano@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'true' AND (r.data ->> 'warrant_reference') = 'PR-OC-2026-012' AND (r.data ->> 'warrant_issued_at') = '2026-11-04' AND (r.data ->> 'issuing_judge') = 'Julia Rivas' AND (r.data ->> 'issuing_court') = 'Juzgado 3 de Control de Garantías de Pacific Ridge' AND (r.data ->> 'warrant_purpose') = 'Comparecencia requerida por orden judicial' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Una orden de captura no constituye una condena. Sin antecedentes penales ni procesos judiciales activos registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'false' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'false' AND CAST((r.data -> 'search_order_reference') AS TEXT) = 'null' AND CAST((r.data -> 'search_order_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_reference') AS TEXT) = 'null' AND CAST((r.data -> 'reported_missing_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_at') AS TEXT) = 'null' AND CAST((r.data -> 'last_seen_location') AS TEXT) = 'null' AND CAST((r.data -> 'missing_report_details') AS TEXT) = 'null')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Active arrest warrants' AND t.name_key = 'active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'Active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Órdenes de captura vigentes')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active arrest warrant' FROM legacy_case_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '3aea3d079405548eaaa4238021f34cc2'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '00f137827c77b060d56891c13d257045f84013484c37ab3b0d16bedfda6d8217' AND asset.mime_type = 'image/png' AND asset.byte_size = 2245412 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-13')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '4323a3148c5f5be6a66ad8a09e20b615' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-13' AND r.version = 1 AND r.title = 'Samuel Ortega' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0013' AND (r.data ->> 'full_name') = 'Samuel Ortega' AND (r.data ->> 'birth_date') = '1995-02-11' AND (r.data ->> 'occupation') = 'Bibliotecario' AND (r.data ->> 'residence') = '113 Avenida del Lago, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0113' AND (r.data ->> 'email') = 'samuel.ortega@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-013' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-013' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Parque del Lago, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM legacy_case_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = 'f5e89d22320e5876ad3152b069d904b0'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '2688d72227ad2b04e1f72ef4dfed399566fe88263832c1b68f4280eb4d632ea7' AND asset.mime_type = 'image/png' AND asset.byte_size = 2222948 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-14')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = '7ad48993912a54aeb249958a3e5abdab' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-14' AND r.version = 1 AND r.title = 'Elena Duarte' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0014' AND (r.data ->> 'full_name') = 'Elena Duarte' AND (r.data ->> 'birth_date') = '1989-06-14' AND (r.data ->> 'occupation') = 'Diseñadora gráfica' AND (r.data ->> 'residence') = '114 Calle del Parque, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0114' AND (r.data ->> 'email') = 'elena.duarte@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-014' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-014' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Plaza Central, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM legacy_case_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '7aef2e4bae7355eba0e906555fd88163'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '5cdf0007c8fc3e3ef546eed648dfe9d23bc210d48183b46fd12ea43a236b7820' AND asset.mime_type = 'image/png' AND asset.byte_size = 2276230 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-15')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'b664fcd98b395de6972e2a0de21bef6d' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-15' AND r.version = 1 AND r.title = 'Isabel Mora' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0015' AND (r.data ->> 'full_name') = 'Isabel Mora' AND (r.data ->> 'birth_date') = '1993-11-02' AND (r.data ->> 'occupation') = 'Profesora' AND (r.data ->> 'residence') = '115 Avenida de los Olmos, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0115' AND (r.data ->> 'email') = 'isabel.mora@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-015' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-015' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Biblioteca Municipal, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM legacy_case_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';

INSERT INTO legacy_case_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '01357527c1cf5e70a689acd0545e7735'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND EXISTS (SELECT 1 FROM media_assets asset WHERE asset.id = p.media_id AND asset.workspace_id = p.workspace_id AND asset.sha256 = '03e1d0ede6774f3e5672d7f8416a669b5c90d9aa403a95efd81cad61a5c2beb9' AND asset.mime_type = 'image/png' AND asset.byte_size = 2478439 AND length(asset.original_bytes) = asset.byte_size AND asset.metadata ->> 'origin' IN ('local-evaluation', 'account-avatar'))
  AND p.source = 'local-evaluation'
  AND p.source_ref IN ('security:police-case:security-person-16')
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
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.id = 'f0243ecc7bd6591184a2e33cd6925aa5' AND r.workspace_id = p.workspace_id AND r.status = 'active' AND r.kind = 'person' AND r.external_id = 'security-person-16' AND r.version = 1 AND r.title = 'Natalia Campos' AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(r.data AS TEXT)) LIKE '{%' THEN r.data ELSE '{}' END)) = 28 AND (r.data ->> 'identifier') = 'PRP-0016' AND (r.data ->> 'full_name') = 'Natalia Campos' AND (r.data ->> 'birth_date') = '1998-03-27' AND (r.data ->> 'occupation') = 'Analista de calidad' AND (r.data ->> 'residence') = '116 Calle del Río, Pacific Ridge' AND (r.data ->> 'phone') = '+1-202-555-0116' AND (r.data ->> 'email') = 'natalia.campos@example.com' AND (r.data ->> 'criminal_history') = 'Sin condenas ni antecedentes penales registrados' AND CAST((r.data -> 'has_active_warrant') AS TEXT) = 'false' AND CAST((r.data -> 'warrant_reference') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_issued_at') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_judge') AS TEXT) = 'null' AND CAST((r.data -> 'issuing_court') AS TEXT) = 'null' AND CAST((r.data -> 'warrant_purpose') AS TEXT) = 'null' AND CAST((r.data -> 'has_active_proceedings') AS TEXT) = 'false' AND CAST((r.data -> 'case_number') AS TEXT) = 'null' AND (r.data ->> 'procedural_status') = 'Sin procesos judiciales activos registrados' AND (r.data ->> 'last_reviewed_at') = '2026-11-04T12:00:00-05:00' AND (r.data ->> 'notes') = 'Persona reportada desaparecida. La orden de búsqueda busca localizarla; no es una orden de captura. Sin antecedentes penales ni procesos judiciales registrados.' AND CAST((r.data -> 'is_missing') AS TEXT) = 'true' AND CAST((r.data -> 'has_active_search_order') AS TEXT) = 'true' AND (r.data ->> 'search_order_reference') = 'PR-OB-2026-016' AND (r.data ->> 'search_order_issued_at') = '2026-11-04' AND (r.data ->> 'missing_report_reference') = 'PR-DES-2026-016' AND (r.data ->> 'reported_missing_at') = '2026-11-04T08:00:00-05:00' AND (r.data ->> 'last_seen_at') = '2026-11-03T18:00:00-05:00' AND (r.data ->> 'last_seen_location') = 'Terminal Norte, Pacific Ridge' AND (r.data ->> 'missing_report_details') = 'Reporte de desaparición recibido; búsqueda de localización vigente, sin orden de captura.')
  AND NOT EXISTS (SELECT 1 FROM publication_revisions edited WHERE edited.post_id = p.id)
  AND ((EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Missing persons' AND t.name_key = 'missing persons' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'en') = 'Missing persons' AND ((t.display_text -> 'name') ->> 'es') = 'Personas desaparecidas')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 4
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active proceedings' AND t.name_key = 'no active proceedings' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'en') = 'No active proceedings' AND ((t.display_text -> 'name') ->> 'es') = 'Sin procesos activos')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Active search order' AND t.name_key = 'active search order' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Active search order' AND ((t.display_text -> 'name') ->> 'en') = 'Active search order' AND ((t.display_text -> 'name') ->> 'es') = 'Orden de búsqueda vigente')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'No active arrest warrants' AND t.name_key = 'no active arrest warrants' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'en') = 'No active arrest warrants' AND ((t.display_text -> 'name') ->> 'es') = 'Sin órdenes de captura')
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Portrait' AND t.name_key = 'portrait' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'source') = 'Portrait' AND ((t.display_text -> 'name') ->> 'en') = 'Portrait' AND ((t.display_text -> 'name') ->> 'es') = 'Retrato')) OR (EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name = 'Person records' AND t.name_key = 'person records' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Person records' AND ((t.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((t.display_text -> 'name') ->> 'source') = 'Person records')
    AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
    AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name = 'Case information' AND t.name_key = 'case information' AND t.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(t.display_text AS TEXT)) LIKE '{%' THEN t.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((t.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (t.display_text -> 'name') ELSE '{}' END)) = 3 AND ((t.display_text -> 'name') ->> 'en') = 'Case information' AND ((t.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((t.display_text -> 'name') ->> 'source') = 'Case information')));

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no recorded criminal history' FROM legacy_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM legacy_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM legacy_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';

INSERT INTO legacy_case_tags (post_id, name_key) SELECT post_id, 'active search order' FROM legacy_case_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('0880d312f23e5b3389c72c8e742f1325', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Active arrest warrants', 'active arrest warrants', '{"name": {"source": "Active arrest warrants", "en": "Active arrest warrants", "es": "Órdenes de captura vigentes"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('086c678cc6a25d2ba430ed7e0f6724fd', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Audiovisual material', 'audiovisual material', '{"name": {"source": "Audiovisual material", "en": "Audiovisual material", "es": "Material audiovisual"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('3a0e6fa44305565a9b916543535c2fcc', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Missing persons', 'missing persons', '{"name": {"source": "Missing persons", "en": "Missing persons", "es": "Personas desaparecidas"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('1419ad5c7cb758edac50b7ea77a2f211', '09f6bc068d365e69a0506f690fe1168b', 'category', 'No warrants or criminal history', 'no warrants or criminal history', '{"name": {"source": "No warrants or criminal history", "en": "No warrants or criminal history", "es": "Sin órdenes ni antecedentes"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('c7a20164063755ad80a9133542e69dc4', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active arrest warrant', 'active arrest warrant', '{"name": {"source": "Active arrest warrant", "en": "Active arrest warrant", "es": "Orden de captura vigente"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('19bf084012155d08a4365789cbb1a7cd', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active judicial proceedings', 'active judicial proceedings', '{"name": {"source": "Active judicial proceedings", "en": "Active judicial proceedings", "es": "Proceso judicial activo"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('202706e1405f52a582aff8827ad1064c', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active search order', 'active search order', '{"name": {"source": "Active search order", "en": "Active search order", "es": "Orden de búsqueda vigente"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('5c49c93dc6b45ad5acc8e84af5359eac', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No active arrest warrants', 'no active arrest warrants', '{"name": {"source": "No active arrest warrants", "en": "No active arrest warrants", "es": "Sin órdenes de captura"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('016ba574633a567bb4a9b739cd820f4d', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No active proceedings', 'no active proceedings', '{"name": {"source": "No active proceedings", "en": "No active proceedings", "es": "Sin procesos activos"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('feedcac5c42a5eb2a199ca219311efc2', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No recorded criminal history', 'no recorded criminal history', '{"name": {"source": "No recorded criminal history", "en": "No recorded criminal history", "es": "Sin antecedentes registrados"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('1ea67585530757ad83d09cf00e2ead02', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Observation video', 'observation video', '{"name": {"source": "Observation video", "en": "Observation video", "es": "Video de observación"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('0fc6533b32c35498bc999821bc630a4e', '3ea760d883945dddb1d7ad27bd996b17', 'category', 'Introductions', 'introductions', '{"name": {"source": "Introductions", "en": "Introductions", "es": "Presentaciones"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('6e03557ad92b5c719bd17d6ed899620c', '3ea760d883945dddb1d7ad27bd996b17', 'category', 'Social content', 'social content', '{"name": {"source": "Social content", "en": "Social content", "es": "Contenido social"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('68fd385f063a5827894e9c7854274d23', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Community', 'community', '{"name": {"source": "Community", "en": "Community", "es": "Comunidad"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('6fc11d21a13f54058e7f6f305adffa5e', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Everyday life', 'everyday life', '{"name": {"source": "Everyday life", "en": "Everyday life", "es": "Vida cotidiana"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('28f3f7a4fe3c5d96adc11d0f6fdd29b8', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Personal introduction', 'personal introduction', '{"name": {"source": "Personal introduction", "en": "Personal introduction", "es": "Presentación personal"}}');

INSERT INTO legacy_case_terms (id, workspace_id, kind, name, name_key, display_text) VALUES ('88e34bccfc3552adbdb4b68a7fe9fb31', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Video', 'video', '{"name": {"source": "Video", "en": "Video", "es": "Video"}}');

DELETE FROM legacy_case_posts WHERE EXISTS (
    SELECT 1 FROM legacy_case_terms wanted JOIN publication_terms actual ON
      actual.id = wanted.id OR (actual.workspace_id = wanted.workspace_id AND actual.kind = wanted.kind AND actual.name_key = wanted.name_key)
    WHERE wanted.workspace_id = legacy_case_posts.workspace_id
      AND ((wanted.kind = 'category' AND wanted.name_key = legacy_case_posts.category_key)
           OR (wanted.kind = 'tag' AND EXISTS (SELECT 1 FROM legacy_case_tags ut WHERE ut.post_id = legacy_case_posts.post_id AND ut.name_key = wanted.name_key)))
      AND (actual.active = FALSE OR actual.workspace_id != wanted.workspace_id OR actual.kind != wanted.kind OR actual.name_key != wanted.name_key)
);

INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT wanted.id, wanted.workspace_id, wanted.kind, wanted.name, wanted.name_key, TRUE, wanted.display_text
FROM legacy_case_terms wanted WHERE EXISTS (
    SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = wanted.workspace_id
      AND ((wanted.kind = 'category' AND cp.category_key = wanted.name_key)
           OR (wanted.kind = 'tag' AND EXISTS (SELECT 1 FROM legacy_case_tags ct WHERE ct.post_id = cp.post_id AND ct.name_key = wanted.name_key)))
) AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = wanted.id OR (t.workspace_id = wanted.workspace_id AND t.kind = wanted.kind AND t.name_key = wanted.name_key))
ON CONFLICT DO NOTHING;

DELETE FROM legacy_case_posts WHERE NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.workspace_id = legacy_case_posts.workspace_id AND t.kind = 'category' AND t.name_key = legacy_case_posts.category_key AND t.active = TRUE)
  OR EXISTS (SELECT 1 FROM legacy_case_tags ct WHERE ct.post_id = legacy_case_posts.post_id AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.workspace_id = legacy_case_posts.workspace_id AND t.kind = 'tag' AND t.name_key = ct.name_key AND t.active = TRUE));

UPDATE publications SET category_id = (SELECT t.id FROM legacy_case_posts cp JOIN publication_terms t ON t.workspace_id = cp.workspace_id AND t.name_key = cp.category_key WHERE cp.post_id = publications.id AND t.kind = 'category' AND t.active = TRUE) WHERE id IN (SELECT post_id FROM legacy_case_posts);

DELETE FROM publication_tags WHERE post_id IN (SELECT post_id FROM legacy_case_posts);

INSERT INTO "publication_tags" (post_id, term_id) SELECT cp.post_id, t.id FROM legacy_case_posts cp JOIN legacy_case_tags ct ON ct.post_id = cp.post_id JOIN publication_terms t ON t.workspace_id = cp.workspace_id AND t.kind = 'tag' AND t.name_key = ct.name_key AND t.active = TRUE ON CONFLICT DO NOTHING;

UPDATE publication_terms SET display_text = '{"name": {"source": "Active judicial proceedings", "en": "Active judicial proceedings", "es": "Proceso judicial activo"}}' WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Active judicial proceedings' AND publication_terms.name_key = 'active judicial proceedings' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Active judicial proceedings' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Active judicial proceedings' AND ((publication_terms.display_text -> 'name') ->> 'es') IN ('Procesos judiciales activos', 'Proceso judicial activo') AND EXISTS (SELECT 1 FROM legacy_case_posts cp JOIN legacy_case_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = publication_terms.workspace_id AND ct.name_key = publication_terms.name_key);

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Cycling' AND publication_terms.name_key = 'cycling' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Ciclismo'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Experiences' AND publication_terms.name_key = 'experiences' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Experiences' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Experiences' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Experiencias'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'category' AND publication_terms.name = 'Public space videos' AND publication_terms.name_key = 'public space videos' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Walking' AND publication_terms.name_key = 'walking' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Caminata'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'category' AND publication_terms.name = 'Public space videos' AND publication_terms.name_key = 'public space videos' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Public space videos' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Videos de espacios públicos'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Walking' AND publication_terms.name_key = 'walking' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Walking' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Caminata'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Stories' AND publication_terms.name_key = 'stories' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Stories' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Stories' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Historias'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Park' AND publication_terms.name_key = 'park' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Parque'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Winter' AND publication_terms.name_key = 'winter' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Winter' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Winter' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Invierno'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Portrait' AND publication_terms.name_key = 'portrait' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Portrait' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Portrait' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Retrato'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Park' AND publication_terms.name_key = 'park' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Park' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Parque'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Photography' AND publication_terms.name_key = 'photography' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Photography' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Photography' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Fotografía'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Cycling' AND publication_terms.name_key = 'cycling' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Cycling' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Ciclismo'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'City sidewalk' AND publication_terms.name_key = 'city sidewalk' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'City sidewalk' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'City sidewalk' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Acera urbana'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Overcast day' AND publication_terms.name_key = 'overcast day' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Overcast day' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Overcast day' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Día nublado'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Projects' AND publication_terms.name_key = 'projects' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Projects' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Projects' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Proyectos'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Spring' AND publication_terms.name_key = 'spring' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Spring' AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Spring' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Primavera'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'category' AND publication_terms.name = 'Person records' AND publication_terms.name_key = 'person records' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Person records' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Expedientes de personas' AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Person records'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Case information' AND publication_terms.name_key = 'case information' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Case information' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Información del expediente' AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Case information'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'category' AND publication_terms.name = 'Community' AND publication_terms.name_key = 'community' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Community' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Comunidad' AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Community'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

UPDATE publication_terms SET active = FALSE WHERE publication_terms.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND publication_terms.kind = 'tag' AND publication_terms.name = 'Introductions' AND publication_terms.name_key = 'introductions' AND publication_terms.active = TRUE AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST(publication_terms.display_text AS TEXT)) LIKE '{%' THEN publication_terms.display_text ELSE '{}' END)) = 1 AND (SELECT COUNT(*) FROM json_each(CASE WHEN LTRIM(CAST((publication_terms.display_text -> 'name') AS TEXT)) LIKE '{%' THEN (publication_terms.display_text -> 'name') ELSE '{}' END)) = 3 AND ((publication_terms.display_text -> 'name') ->> 'en') = 'Introductions' AND ((publication_terms.display_text -> 'name') ->> 'es') = 'Presentaciones' AND ((publication_terms.display_text -> 'name') ->> 'source') = 'Introductions'
  AND EXISTS (SELECT 1 FROM legacy_case_posts cp WHERE cp.workspace_id = publication_terms.workspace_id)
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_uploads u WHERE u.category_id = publication_terms.id OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%');

DROP TABLE legacy_case_tags;

DROP TABLE legacy_case_posts;

DROP TABLE legacy_case_terms;
