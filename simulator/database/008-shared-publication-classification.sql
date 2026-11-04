-- Review prepared publication classification once, using the shared SQL initializer.
-- Only unchanged prepared classifications with active owners/memberships qualify.
-- Manual categories/tags, hidden/deleted publications and edited source facts are preserved.
-- Person status is recorded case data, never inferred from a portrait or video.
-- Clip labels describe the existing captions only; they assert no identities or incidents.
CREATE TEMP TABLE classification_posts (post_id UUID PRIMARY KEY, workspace_id UUID NOT NULL, category_key TEXT NOT NULL);
CREATE TEMP TABLE classification_tags (post_id UUID NOT NULL, name_key TEXT NOT NULL, PRIMARY KEY (post_id, name_key));

-- meta-social:pexels-12557513
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'public space videos'
FROM publications p
WHERE p.id = 'c6af2491f99551e59a3084f0045ec2c9'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '63297a1bbc7f52df9b76cf3c33739bb7'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:pexels-12557513'
  AND p.hidden = FALSE
  AND p.category_id = 'c7047e35fc7454bdb4ad20b7604d7138'
  AND p.caption = 'Pedestrians and cyclists in a tree-lined park'
  AND p.note_text = p.caption
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '07da1d8a5c2e5cbcb300d40cda47fcde' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Public spaces' AND t.name_key = 'public spaces')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'e824b9874b3b56bd8ee3a2b11e8d4aef' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'People walking' AND t.name_key = 'people walking');

-- meta-social:pexels-33802407
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'public space videos'
FROM publications p
WHERE p.id = 'c1de88652d045a04a56cc29caaa7963c'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '484b780027455aa4aa0f3d3ed603acf6'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:pexels-33802407'
  AND p.hidden = FALSE
  AND p.category_id = 'c7047e35fc7454bdb4ad20b7604d7138'
  AND p.caption = 'People walking along a city sidewalk'
  AND p.note_text = p.caption
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '07da1d8a5c2e5cbcb300d40cda47fcde' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Public spaces' AND t.name_key = 'public spaces')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'e824b9874b3b56bd8ee3a2b11e8d4aef' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'People walking' AND t.name_key = 'people walking');

-- meta-social:pexels-3699519
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'public space videos'
FROM publications p
WHERE p.id = '9b3e3f5710545f36a378902058bc34cc'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '9467affefe045ed8ae5c4d4bb7c5ac23'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:pexels-3699519'
  AND p.hidden = FALSE
  AND p.category_id = 'c7047e35fc7454bdb4ad20b7604d7138'
  AND p.caption = 'A winter walk through the park'
  AND p.note_text = p.caption
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '07da1d8a5c2e5cbcb300d40cda47fcde' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Public spaces' AND t.name_key = 'public spaces')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'e824b9874b3b56bd8ee3a2b11e8d4aef' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'People walking' AND t.name_key = 'people walking');

-- meta-social:social-introduction:elena-marquez
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '9c941832fbbb5bd1a4f85a97cd82acb2'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '484b780027455aa4aa0f3d3ed603acf6'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:social-introduction:elena-marquez'
  AND p.hidden = FALSE
  AND p.category_id = 'a0886350239847179fa1ccb46aae2d9e'
  AND p.caption = 'Elena Marquez — Hello, everyone'
  AND p.note_text = 'Ideas, photographs and projects worth sharing. Welcome to our social space.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Community' AND t.name_key = 'community')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5a210c7c04d64fa4b13084b48f4ef974' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Introductions' AND t.name_key = 'introductions');

-- meta-social:social-introduction:mateo-rios
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '274fc4bb223852fc9bc5e8ed8829ec8d'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '9467affefe045ed8ae5c4d4bb7c5ac23'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:social-introduction:mateo-rios'
  AND p.hidden = FALSE
  AND p.category_id = 'a0886350239847179fa1ccb46aae2d9e'
  AND p.caption = 'Mateo Rios — Hello, everyone'
  AND p.note_text = 'A place to exchange experiences, discover new perspectives and keep in touch.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Community' AND t.name_key = 'community')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5a210c7c04d64fa4b13084b48f4ef974' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Introductions' AND t.name_key = 'introductions');

-- meta-social:social-introduction:sarah-chen
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'introductions'
FROM publications p
WHERE p.id = '83f449740fe357c2ae3a5b8b223ec53e'
  AND p.workspace_id = '3ea760d883945dddb1d7ad27bd996b17'
  AND p.owner_id = '63297a1bbc7f52df9b76cf3c33739bb7'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'meta-social:social-introduction:sarah-chen'
  AND p.hidden = FALSE
  AND p.category_id = 'a0886350239847179fa1ccb46aae2d9e'
  AND p.caption = 'Sarah Chen — Hello, everyone'
  AND p.note_text = 'Sharing small discoveries and the stories behind each photograph.'
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Community' AND t.name_key = 'community')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = '5a210c7c04d64fa4b13084b48f4ef974' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Introductions' AND t.name_key = 'introductions');

-- security:pexels-25757454
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'public space videos'
FROM publications p
WHERE p.id = '41b2b8cf66c65e3cbf41025c47bb0245'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:pexels-25757454'
  AND p.hidden = FALSE
  AND p.category_id = '52316594eb6958deb1fc39bef28fc183'
  AND p.caption = 'Pedestrians and cyclists in Ibirapuera Park'
  AND p.note_text = p.caption
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a473651384b851d0bb19c0581689c8c6' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Public spaces' AND t.name_key = 'public spaces')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'f648dd109f0c54b18009df6ea149c997' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'People walking' AND t.name_key = 'people walking');

-- security:pexels-29401365
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'public space videos'
FROM publications p
WHERE p.id = 'a64f19f460f752ca8a6daaa9b1947492'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:pexels-29401365'
  AND p.hidden = FALSE
  AND p.category_id = '52316594eb6958deb1fc39bef28fc183'
  AND p.caption = 'People walking through a park on an overcast day'
  AND p.note_text = p.caption
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a473651384b851d0bb19c0581689c8c6' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Public spaces' AND t.name_key = 'public spaces')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'f648dd109f0c54b18009df6ea149c997' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'People walking' AND t.name_key = 'people walking');

-- security:pexels-30614848
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'public space videos'
FROM publications p
WHERE p.id = '24b0b2ee56d35f83b90c67961c8ab23f'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:pexels-30614848'
  AND p.hidden = FALSE
  AND p.category_id = '52316594eb6958deb1fc39bef28fc183'
  AND p.caption = 'Walking through an Edinburgh park in spring'
  AND p.note_text = p.caption
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Outdoor life' AND t.name_key = 'outdoor life')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 2
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'a473651384b851d0bb19c0581689c8c6' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Public spaces' AND t.name_key = 'public spaces')
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'f648dd109f0c54b18009df6ea149c997' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'People walking' AND t.name_key = 'people walking');

-- security:police-case:security-person-01
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = 'be1c4ea01ab856d1abdebd7ff0d8f81b'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-01'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Adrián Salcedo'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'e0b2f6bdb1845457b6e53791a42ec1f2' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'true' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-02
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '5344161d0fa651e0ae4892a37e3e65c6'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-02'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Esteban Pardo'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '909d1a6da90855acabca10a4269ff2a1' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'true' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-03
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '4384e305ef325c7d9b8d6bd2c80c8b05'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-03'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Valeria Navarro'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '11aeb71325b258d893fb649de535e9a4' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-04
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '5217d89a1dba5d0fb6a5f51b10e22c13'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-04'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Lucía Cárdenas'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'f2482f95e0675eb2b4768e7ff99d1d2a' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-05
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '3a13e840a41456a4b85a3f0a4930b37b'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-05'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Tomás Beltrán'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'b325103f59155714afb0e24f9c97ca82' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-06
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '4fe1617c8a1b50089508572418d8f17c'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-06'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Nicolás Acosta'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '65050ead0c4f56c4b6695032f55b7f46' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-07
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '11a0c84493245994bd3099f55ff1c7da'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-07'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Mariana Solano'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'b0ea039f74905caea44043cbdcaad329' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-08
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = 'b531b3d7de89559f91732114c30a4310'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-08'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Rafael Méndez'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '1597fbaef5da5a23821276ca14f81e81' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-09
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '118407b2480157209ab9729c18c14294'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-09'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Camila Fuentes'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'ba59535813655989a48718c54f48e066' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-10
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'no warrants or criminal history'
FROM publications p
WHERE p.id = '0a691133f51f583a840e3187f5222b39'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-10'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Asha Mehta'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'cde43426901a5c9386012f78935464d2' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND COALESCE(CAST(r.data -> 'is_missing' AS TEXT), 'false') = 'false' AND COALESCE(CAST(r.data -> 'has_active_search_order' AS TEXT), 'false') = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-11
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = '8b7e666b35da56f7aac5233f1d4e8a31'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-11'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Bruno Escobar'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'f33c891776ae50f5a46324dbc1e1e618' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND CAST(r.data -> 'is_missing' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_search_order' AS TEXT) = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-12
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'active arrest warrants'
FROM publications p
WHERE p.id = 'b50ca97e42c65cd0bc63c5b788f5adc5'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-12'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Daniel Serrano'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '5952f4f57b5d5f908dc1e37e1fe5d4eb' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND CAST(r.data -> 'is_missing' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_search_order' AS TEXT) = 'false' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-13
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '3aea3d079405548eaaa4238021f34cc2'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-13'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Samuel Ortega'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '4323a3148c5f5be6a66ad8a09e20b615' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND CAST(r.data -> 'is_missing' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_search_order' AS TEXT) = 'true' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-14
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = 'f5e89d22320e5876ad3152b069d904b0'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '6b70a3aa0e7b52348245a923d31bd2ec'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-14'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Elena Duarte'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = '7ad48993912a54aeb249958a3e5abdab' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND CAST(r.data -> 'is_missing' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_search_order' AS TEXT) = 'true' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-15
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '7aef2e4bae7355eba0e906555fd88163'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '002698d65b515f23a6b78f9ac69767a8'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-15'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Isabel Mora'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'b664fcd98b395de6972e2a0de21bef6d' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND CAST(r.data -> 'is_missing' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_search_order' AS TEXT) = 'true' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');

-- security:police-case:security-person-16
INSERT INTO classification_posts (post_id, workspace_id, category_key)
SELECT p.id, p.workspace_id, 'missing persons'
FROM publications p
WHERE p.id = '01357527c1cf5e70a689acd0545e7735'
  AND p.workspace_id = '09f6bc068d365e69a0506f690fe1168b'
  AND p.owner_id = '9e1da78288e05d07b552c5303c08721c'
  AND p.source = 'local-evaluation'
  AND p.source_ref = 'security:police-case:security-person-16'
  AND p.hidden = FALSE
  AND p.category_id = '820e166a7d7344f69e635b03e225f6c4'
  AND p.caption = 'Natalia Campos'
  AND p.note_text = (p.display_text -> 'note_text' ->> 'source')
  AND EXISTS (SELECT 1 FROM workspace_record_media rm JOIN workspace_records r ON r.id = rm.record_id WHERE rm.publication_id = p.id AND rm.media_id = p.media_id AND r.workspace_id = p.workspace_id AND r.id = 'f0243ecc7bd6591184a2e33cd6925aa5' AND r.status = 'active' AND CAST(r.data -> 'has_active_warrant' AS TEXT) = 'false' AND CAST(r.data -> 'has_active_proceedings' AS TEXT) = 'false' AND CAST(r.data -> 'is_missing' AS TEXT) = 'true' AND CAST(r.data -> 'has_active_search_order' AS TEXT) = 'true' AND r.data ->> 'criminal_history' = 'Sin condenas ni antecedentes penales registrados')
  AND EXISTS (SELECT 1 FROM users u JOIN workspace_members m ON m.user_id = u.id WHERE u.id = p.owner_id AND u.is_active = TRUE AND m.workspace_id = p.workspace_id)
  AND EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = p.category_id AND t.workspace_id = p.workspace_id AND t.kind = 'category' AND t.active = TRUE AND t.name = 'Person records' AND t.name_key = 'person records')
  AND (SELECT COUNT(*) FROM publication_tags pt WHERE pt.post_id = p.id) = 1
  AND EXISTS (SELECT 1 FROM publication_tags pt JOIN publication_terms t ON t.id = pt.term_id WHERE pt.post_id = p.id AND t.id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND t.workspace_id = p.workspace_id AND t.kind = 'tag' AND t.active = TRUE AND t.name = 'Case information' AND t.name_key = 'case information');
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'park' FROM classification_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'walking' FROM classification_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'cycling' FROM classification_posts WHERE post_id = 'c6af2491f99551e59a3084f0045ec2c9';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'city sidewalk' FROM classification_posts WHERE post_id = 'c1de88652d045a04a56cc29caaa7963c';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'walking' FROM classification_posts WHERE post_id = 'c1de88652d045a04a56cc29caaa7963c';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'park' FROM classification_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'walking' FROM classification_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'winter' FROM classification_posts WHERE post_id = '9b3e3f5710545f36a378902058bc34cc';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'community' FROM classification_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'photography' FROM classification_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'projects' FROM classification_posts WHERE post_id = '9c941832fbbb5bd1a4f85a97cd82acb2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'community' FROM classification_posts WHERE post_id = '274fc4bb223852fc9bc5e8ed8829ec8d';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'experiences' FROM classification_posts WHERE post_id = '274fc4bb223852fc9bc5e8ed8829ec8d';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'community' FROM classification_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'photography' FROM classification_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'stories' FROM classification_posts WHERE post_id = '83f449740fe357c2ae3a5b8b223ec53e';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'park' FROM classification_posts WHERE post_id = '41b2b8cf66c65e3cbf41025c47bb0245';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'walking' FROM classification_posts WHERE post_id = '41b2b8cf66c65e3cbf41025c47bb0245';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'cycling' FROM classification_posts WHERE post_id = '41b2b8cf66c65e3cbf41025c47bb0245';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'park' FROM classification_posts WHERE post_id = 'a64f19f460f752ca8a6daaa9b1947492';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'walking' FROM classification_posts WHERE post_id = 'a64f19f460f752ca8a6daaa9b1947492';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'overcast day' FROM classification_posts WHERE post_id = 'a64f19f460f752ca8a6daaa9b1947492';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'park' FROM classification_posts WHERE post_id = '24b0b2ee56d35f83b90c67961c8ab23f';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'walking' FROM classification_posts WHERE post_id = '24b0b2ee56d35f83b90c67961c8ab23f';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'spring' FROM classification_posts WHERE post_id = '24b0b2ee56d35f83b90c67961c8ab23f';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'active judicial proceedings' FROM classification_posts WHERE post_id = 'be1c4ea01ab856d1abdebd7ff0d8f81b';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'active judicial proceedings' FROM classification_posts WHERE post_id = '5344161d0fa651e0ae4892a37e3e65c6';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '4384e305ef325c7d9b8d6bd2c80c8b05';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '5217d89a1dba5d0fb6a5f51b10e22c13';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '3a13e840a41456a4b85a3f0a4930b37b';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '4fe1617c8a1b50089508572418d8f17c';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '11a0c84493245994bd3099f55ff1c7da';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = 'b531b3d7de89559f91732114c30a4310';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '118407b2480157209ab9729c18c14294';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '118407b2480157209ab9729c18c14294';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '118407b2480157209ab9729c18c14294';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '0a691133f51f583a840e3187f5222b39';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '8b7e666b35da56f7aac5233f1d4e8a31';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = 'b50ca97e42c65cd0bc63c5b788f5adc5';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'active search order' FROM classification_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'active search order' FROM classification_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'active search order' FROM classification_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'portrait' FROM classification_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'active search order' FROM classification_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';

INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '3aea3d079405548eaaa4238021f34cc2';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = 'f5e89d22320e5876ad3152b069d904b0';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '7aef2e4bae7355eba0e906555fd88163';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active arrest warrants' FROM classification_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';
INSERT INTO classification_tags (post_id, name_key) SELECT post_id, 'no active proceedings' FROM classification_posts WHERE post_id = '01357527c1cf5e70a689acd0545e7735';

-- category: Active arrest warrants
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '0880d312f23e5b3389c72c8e742f1325', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Active arrest warrants', 'active arrest warrants', TRUE, '{"name": {"source": "Active arrest warrants", "en": "Active arrest warrants", "es": "Órdenes de captura vigentes"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND cp.category_key = 'active arrest warrants')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '0880d312f23e5b3389c72c8e742f1325' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name_key = 'active arrest warrants'))
ON CONFLICT DO NOTHING;

-- category: Missing persons
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '3a0e6fa44305565a9b916543535c2fcc', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Missing persons', 'missing persons', TRUE, '{"name": {"source": "Missing persons", "en": "Missing persons", "es": "Personas desaparecidas"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND cp.category_key = 'missing persons')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '3a0e6fa44305565a9b916543535c2fcc' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name_key = 'missing persons'))
ON CONFLICT DO NOTHING;

-- category: No warrants or criminal history
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '1419ad5c7cb758edac50b7ea77a2f211', '09f6bc068d365e69a0506f690fe1168b', 'category', 'No warrants or criminal history', 'no warrants or criminal history', TRUE, '{"name": {"source": "No warrants or criminal history", "en": "No warrants or criminal history", "es": "Sin órdenes ni antecedentes"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND cp.category_key = 'no warrants or criminal history')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '1419ad5c7cb758edac50b7ea77a2f211' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name_key = 'no warrants or criminal history'))
ON CONFLICT DO NOTHING;

-- category: Public space videos
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '2a3508ea47675f9ab9842266cda7c6b5', '09f6bc068d365e69a0506f690fe1168b', 'category', 'Public space videos', 'public space videos', TRUE, '{"name": {"source": "Public space videos", "en": "Public space videos", "es": "Videos de espacios públicos"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND cp.category_key = 'public space videos')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '2a3508ea47675f9ab9842266cda7c6b5' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'category' AND t.name_key = 'public space videos'))
ON CONFLICT DO NOTHING;

-- tag: Active judicial proceedings
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '19bf084012155d08a4365789cbb1a7cd', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active judicial proceedings', 'active judicial proceedings', TRUE, '{"name": {"source": "Active judicial proceedings", "en": "Active judicial proceedings", "es": "Procesos judiciales activos"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'active judicial proceedings')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '19bf084012155d08a4365789cbb1a7cd' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'active judicial proceedings'))
ON CONFLICT DO NOTHING;

-- tag: Active search order
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '202706e1405f52a582aff8827ad1064c', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Active search order', 'active search order', TRUE, '{"name": {"source": "Active search order", "en": "Active search order", "es": "Orden de búsqueda vigente"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'active search order')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '202706e1405f52a582aff8827ad1064c' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'active search order'))
ON CONFLICT DO NOTHING;

-- tag: Cycling
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'de0765905929588390cc530f03ebc852', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Cycling', 'cycling', TRUE, '{"name": {"source": "Cycling", "en": "Cycling", "es": "Ciclismo"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'cycling')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'de0765905929588390cc530f03ebc852' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'cycling'))
ON CONFLICT DO NOTHING;

-- tag: No active arrest warrants
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '5c49c93dc6b45ad5acc8e84af5359eac', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No active arrest warrants', 'no active arrest warrants', TRUE, '{"name": {"source": "No active arrest warrants", "en": "No active arrest warrants", "es": "Sin órdenes de captura"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'no active arrest warrants')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '5c49c93dc6b45ad5acc8e84af5359eac' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'no active arrest warrants'))
ON CONFLICT DO NOTHING;

-- tag: No active proceedings
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '016ba574633a567bb4a9b739cd820f4d', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'No active proceedings', 'no active proceedings', TRUE, '{"name": {"source": "No active proceedings", "en": "No active proceedings", "es": "Sin procesos activos"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'no active proceedings')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '016ba574633a567bb4a9b739cd820f4d' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'no active proceedings'))
ON CONFLICT DO NOTHING;

-- tag: Overcast day
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'e44b598aad515e859ba2e1598b3d6248', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Overcast day', 'overcast day', TRUE, '{"name": {"source": "Overcast day", "en": "Overcast day", "es": "Día nublado"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'overcast day')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'e44b598aad515e859ba2e1598b3d6248' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'overcast day'))
ON CONFLICT DO NOTHING;

-- tag: Park
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '928f6c5f58685b3fb4214b64a4b80be4', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Park', 'park', TRUE, '{"name": {"source": "Park", "en": "Park", "es": "Parque"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'park')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '928f6c5f58685b3fb4214b64a4b80be4' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'park'))
ON CONFLICT DO NOTHING;

-- tag: Portrait
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'a4838f25e4c0527abac01d410b8261b6', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Portrait', 'portrait', TRUE, '{"name": {"source": "Portrait", "en": "Portrait", "es": "Retrato"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'portrait')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'a4838f25e4c0527abac01d410b8261b6' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'portrait'))
ON CONFLICT DO NOTHING;

-- tag: Spring
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'fc95a832ac625dd5aa579c8219b95f09', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Spring', 'spring', TRUE, '{"name": {"source": "Spring", "en": "Spring", "es": "Primavera"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'spring')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'fc95a832ac625dd5aa579c8219b95f09' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'spring'))
ON CONFLICT DO NOTHING;

-- tag: Walking
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '6f4530d2cf135600a3e63d58bdba9471', '09f6bc068d365e69a0506f690fe1168b', 'tag', 'Walking', 'walking', TRUE, '{"name": {"source": "Walking", "en": "Walking", "es": "Caminata"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND ct.name_key = 'walking')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '6f4530d2cf135600a3e63d58bdba9471' OR (t.workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND t.kind = 'tag' AND t.name_key = 'walking'))
ON CONFLICT DO NOTHING;

-- category: Introductions
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '0fc6533b32c35498bc999821bc630a4e', '3ea760d883945dddb1d7ad27bd996b17', 'category', 'Introductions', 'introductions', TRUE, '{"name": {"source": "Introductions", "en": "Introductions", "es": "Presentaciones"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND cp.category_key = 'introductions')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '0fc6533b32c35498bc999821bc630a4e' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name_key = 'introductions'))
ON CONFLICT DO NOTHING;

-- category: Public space videos
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '62a47280210f5a399e2f7bebaaa1e0bf', '3ea760d883945dddb1d7ad27bd996b17', 'category', 'Public space videos', 'public space videos', TRUE, '{"name": {"source": "Public space videos", "en": "Public space videos", "es": "Videos de espacios públicos"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND cp.category_key = 'public space videos')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '62a47280210f5a399e2f7bebaaa1e0bf' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'category' AND t.name_key = 'public space videos'))
ON CONFLICT DO NOTHING;

-- tag: City sidewalk
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'e2c30e2d28ae58a8b73c2b99ba69b396', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'City sidewalk', 'city sidewalk', TRUE, '{"name": {"source": "City sidewalk", "en": "City sidewalk", "es": "Acera urbana"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'city sidewalk')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'e2c30e2d28ae58a8b73c2b99ba69b396' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'city sidewalk'))
ON CONFLICT DO NOTHING;

-- tag: Community
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '68fd385f063a5827894e9c7854274d23', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Community', 'community', TRUE, '{"name": {"source": "Community", "en": "Community", "es": "Comunidad"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'community')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '68fd385f063a5827894e9c7854274d23' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'community'))
ON CONFLICT DO NOTHING;

-- tag: Cycling
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '0b0ed757af98520aa9d008ba1490ba9b', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Cycling', 'cycling', TRUE, '{"name": {"source": "Cycling", "en": "Cycling", "es": "Ciclismo"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'cycling')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '0b0ed757af98520aa9d008ba1490ba9b' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'cycling'))
ON CONFLICT DO NOTHING;

-- tag: Experiences
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '2002638d207e5407b4c107010bd5fadc', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Experiences', 'experiences', TRUE, '{"name": {"source": "Experiences", "en": "Experiences", "es": "Experiencias"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'experiences')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '2002638d207e5407b4c107010bd5fadc' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'experiences'))
ON CONFLICT DO NOTHING;

-- tag: Park
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'a74bd4bb8c335a238389c15fbaca1b39', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Park', 'park', TRUE, '{"name": {"source": "Park", "en": "Park", "es": "Parque"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'park')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'a74bd4bb8c335a238389c15fbaca1b39' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'park'))
ON CONFLICT DO NOTHING;

-- tag: Photography
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'c33b3e1207795dc9a5697a526a5f7b5c', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Photography', 'photography', TRUE, '{"name": {"source": "Photography", "en": "Photography", "es": "Fotografía"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'photography')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'c33b3e1207795dc9a5697a526a5f7b5c' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'photography'))
ON CONFLICT DO NOTHING;

-- tag: Projects
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT 'f395bff7a83452e5ab69f95ab4f2890b', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Projects', 'projects', TRUE, '{"name": {"source": "Projects", "en": "Projects", "es": "Proyectos"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'projects')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = 'f395bff7a83452e5ab69f95ab4f2890b' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'projects'))
ON CONFLICT DO NOTHING;

-- tag: Stories
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '84fe3811d7af5cfa871389ea39f86f28', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Stories', 'stories', TRUE, '{"name": {"source": "Stories", "en": "Stories", "es": "Historias"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'stories')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '84fe3811d7af5cfa871389ea39f86f28' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'stories'))
ON CONFLICT DO NOTHING;

-- tag: Walking
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '3eb9712f94085d3e8e1b55a98ba13605', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Walking', 'walking', TRUE, '{"name": {"source": "Walking", "en": "Walking", "es": "Caminata"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'walking')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '3eb9712f94085d3e8e1b55a98ba13605' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'walking'))
ON CONFLICT DO NOTHING;

-- tag: Winter
INSERT INTO "publication_terms" (id, workspace_id, kind, name, name_key, active, display_text)
SELECT '9dca3192b8f65aa89cdf196283c4ce10', '3ea760d883945dddb1d7ad27bd996b17', 'tag', 'Winter', 'winter', TRUE, '{"name": {"source": "Winter", "en": "Winter", "es": "Invierno"}}'
WHERE EXISTS (SELECT 1 FROM classification_posts cp JOIN classification_tags ct ON ct.post_id = cp.post_id WHERE cp.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND ct.name_key = 'winter')
  AND NOT EXISTS (SELECT 1 FROM publication_terms t WHERE t.id = '9dca3192b8f65aa89cdf196283c4ce10' OR (t.workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND t.kind = 'tag' AND t.name_key = 'winter'))
ON CONFLICT DO NOTHING;

-- An archived/conflicting owner-defined target term must never be restored implicitly.
DELETE FROM classification_posts
WHERE NOT EXISTS (
    SELECT 1 FROM publication_terms t
    WHERE t.workspace_id = classification_posts.workspace_id AND t.kind = 'category'
      AND t.name_key = classification_posts.category_key AND t.active = TRUE
) OR EXISTS (
    SELECT 1 FROM classification_tags ct
    WHERE ct.post_id = classification_posts.post_id AND NOT EXISTS (
        SELECT 1 FROM publication_terms t
        WHERE t.workspace_id = classification_posts.workspace_id AND t.kind = 'tag'
          AND t.name_key = ct.name_key AND t.active = TRUE
    )
);
UPDATE publications SET category_id = (
    SELECT t.id FROM classification_posts cp JOIN publication_terms t
      ON t.workspace_id = cp.workspace_id AND t.name_key = cp.category_key
    WHERE cp.post_id = publications.id AND t.kind = 'category' AND t.active = TRUE
)
WHERE id IN (SELECT post_id FROM classification_posts);
DELETE FROM publication_tags WHERE post_id IN (SELECT post_id FROM classification_posts);
INSERT INTO "publication_tags" (post_id, term_id)
SELECT cp.post_id, t.id FROM classification_posts cp
JOIN classification_tags ct ON ct.post_id = cp.post_id
JOIN publication_terms t ON t.workspace_id = cp.workspace_id AND t.name_key = ct.name_key
WHERE t.kind = 'tag' AND t.active = TRUE
ON CONFLICT DO NOTHING;

-- Retire only unedited legacy vocabulary with no publication or upload references.
UPDATE publication_terms SET active = FALSE
WHERE id = '07da1d8a5c2e5cbcb300d40cda47fcde' AND workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND kind = 'tag'
  AND name = 'Public spaces' AND name_key = 'public spaces' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = '52316594eb6958deb1fc39bef28fc183' AND workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND kind = 'category'
  AND name = 'Outdoor life' AND name_key = 'outdoor life' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = '5a210c7c04d64fa4b13084b48f4ef974' AND workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND kind = 'tag'
  AND name = 'Introductions' AND name_key = 'introductions' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = '820e166a7d7344f69e635b03e225f6c4' AND workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND kind = 'category'
  AND name = 'Person records' AND name_key = 'person records' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = 'a0886350239847179fa1ccb46aae2d9e' AND workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND kind = 'category'
  AND name = 'Community' AND name_key = 'community' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = 'a473651384b851d0bb19c0581689c8c6' AND workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND kind = 'tag'
  AND name = 'Public spaces' AND name_key = 'public spaces' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = 'c7047e35fc7454bdb4ad20b7604d7138' AND workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND kind = 'category'
  AND name = 'Outdoor life' AND name_key = 'outdoor life' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = 'e824b9874b3b56bd8ee3a2b11e8d4aef' AND workspace_id = '3ea760d883945dddb1d7ad27bd996b17' AND kind = 'tag'
  AND name = 'People walking' AND name_key = 'people walking' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = 'ea0709e773f24d40aa3bc18bbc5dc26f' AND workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND kind = 'tag'
  AND name = 'Case information' AND name_key = 'case information' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
UPDATE publication_terms SET active = FALSE
WHERE id = 'f648dd109f0c54b18009df6ea149c997' AND workspace_id = '09f6bc068d365e69a0506f690fe1168b' AND kind = 'tag'
  AND name = 'People walking' AND name_key = 'people walking' AND active = TRUE
  AND NOT EXISTS (SELECT 1 FROM publications p WHERE p.category_id = publication_terms.id)
  AND NOT EXISTS (SELECT 1 FROM publication_tags pt WHERE pt.term_id = publication_terms.id)
  AND NOT EXISTS (
      SELECT 1 FROM publication_uploads u
      WHERE u.category_id = publication_terms.id
         OR LOWER(REPLACE(CAST(u.tag_ids AS TEXT), '-', '')) LIKE
            '%"' || LOWER(REPLACE(CAST(publication_terms.id AS TEXT), '-', '')) || '"%'
  );
DROP TABLE classification_tags;
DROP TABLE classification_posts;
