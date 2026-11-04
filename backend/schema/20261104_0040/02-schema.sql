CREATE TABLE object_observations (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	object_id UUID NOT NULL,
	zone_id UUID,
	media_asset_id UUID NOT NULL,
	mask_asset_id UUID,
	capture_session_id UUID,
	created_by_id UUID,
	muse_bounding_box JSON,
	bounding_box JSON,
	spatial_description TEXT,
	relationships JSON NOT NULL,
	seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
	visual_confidence FLOAT NOT NULL,
	model_name VARCHAR(120) NOT NULL,
	verification_status verification_status NOT NULL,
	verified_by_id UUID,
	verified_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(object_id) REFERENCES tracked_objects (id) ON DELETE CASCADE,
	FOREIGN KEY(zone_id) REFERENCES zones (id),
	FOREIGN KEY(media_asset_id) REFERENCES media_assets (id),
	FOREIGN KEY(mask_asset_id) REFERENCES media_assets (id),
	FOREIGN KEY(capture_session_id) REFERENCES capture_sessions (id),
	FOREIGN KEY(created_by_id) REFERENCES users (id),
	FOREIGN KEY(verified_by_id) REFERENCES users (id)
);

CREATE INDEX ix_object_observations_object_id ON object_observations (object_id);

CREATE INDEX ix_observation_object_verified_seen ON object_observations (object_id, verification_status, seen_at);

CREATE INDEX ix_object_observations_workspace_id ON object_observations (workspace_id);

CREATE TABLE publications (
	display_text JSON NOT NULL,
	id UUID NOT NULL,
	owner_id UUID NOT NULL,
	shared_from_id UUID,
	category_id UUID,
	media_id UUID NOT NULL,
	caption TEXT NOT NULL,
	note_text TEXT NOT NULL,
	note_source VARCHAR(16) NOT NULL,
	search_text TEXT NOT NULL,
	ai_labels JSON NOT NULL,
	ai_detections JSON NOT NULL,
	active_index_run_id UUID,
	evidence_version INTEGER DEFAULT '0' NOT NULL,
	ai_caption TEXT NOT NULL,
	face_count INTEGER NOT NULL,
	indexed_at TIMESTAMP WITH TIME ZONE,
	index_error TEXT,
	source VARCHAR(32) NOT NULL,
	source_ref VARCHAR(160),
	published_at TIMESTAMP WITH TIME ZONE NOT NULL,
	hidden BOOLEAN NOT NULL,
	workspace_id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_publication_source UNIQUE (owner_id, source, source_ref),
	CONSTRAINT uq_publication_group_copy UNIQUE (shared_from_id, workspace_id),
	FOREIGN KEY(owner_id) REFERENCES users (id),
	FOREIGN KEY(shared_from_id) REFERENCES publications (id),
	FOREIGN KEY(category_id) REFERENCES publication_terms (id) ON DELETE SET NULL,
	FOREIGN KEY(media_id) REFERENCES media_assets (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
);

CREATE INDEX ix_publication_feed ON publications (workspace_id, published_at, id);

CREATE INDEX ix_publications_owner_id ON publications (owner_id);

CREATE INDEX ix_publications_shared_from_id ON publications (shared_from_id);

CREATE INDEX ix_publications_category_id ON publications (category_id);

CREATE TABLE user_profiles (
	display_text JSON NOT NULL,
	user_id UUID NOT NULL,
	birthday DATE,
	gender VARCHAR(32),
	hometown VARCHAR(160),
	location VARCHAR(160),
	headline VARCHAR(240) NOT NULL,
	biography TEXT NOT NULL,
	phone VARCHAR(64) NOT NULL,
	website VARCHAR(1024) NOT NULL,
	social_links JSON NOT NULL,
	avatar_media_id UUID,
	cv_bytes BYTEA,
	cv_filename VARCHAR(255),
	cv_mime_type VARCHAR(128),
	cv_sha256 VARCHAR(64),
	cv_text TEXT,
	cv_context TEXT,
	cv_status VARCHAR(16) NOT NULL,
	cv_error VARCHAR(500),
	cv_simulated BOOLEAN NOT NULL,
	cv_updated_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(avatar_media_id) REFERENCES media_assets (id) ON DELETE SET NULL
);

CREATE TABLE facebook_media (
	fb_id VARCHAR(128) NOT NULL,
	user_id UUID NOT NULL,
	kind VARCHAR(8) NOT NULL,
	source_url VARCHAR(2048),
	caption TEXT,
	fb_created_time VARCHAR(64),
	width INTEGER,
	height INTEGER,
	imported_media_id UUID,
	PRIMARY KEY (fb_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(imported_media_id) REFERENCES media_assets (id) ON DELETE SET NULL
);

CREATE INDEX ix_facebook_media_user_id ON facebook_media (user_id);

CREATE INDEX ix_facebook_media_user ON facebook_media (user_id);

CREATE TABLE face_enrollments (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	media_asset_id UUID NOT NULL,
	face_index INTEGER NOT NULL,
	embedding_model VARCHAR(80) NOT NULL,
	embedding BYTEA NOT NULL,
	bounding_box JSON NOT NULL,
	quality FLOAT NOT NULL,
	source VARCHAR(16) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_face_enrollment UNIQUE (user_id, media_asset_id, face_index),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(media_asset_id) REFERENCES media_assets (id) ON DELETE CASCADE
);

CREATE INDEX ix_face_enrollment_user ON face_enrollments (user_id);

CREATE INDEX ix_face_enrollments_user_id ON face_enrollments (user_id);

CREATE TABLE object_facts (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	object_id UUID NOT NULL,
	observation_id UUID,
	fact_type VARCHAR(64) NOT NULL,
	value_text VARCHAR(500),
	normalized_value VARCHAR(500),
	numeric_value FLOAT,
	unit VARCHAR(40),
	confidence FLOAT NOT NULL,
	provenance fact_provenance NOT NULL,
	evidence_geometry JSON,
	model_name VARCHAR(120) NOT NULL,
	verification_status verification_status NOT NULL,
	verified_by_id UUID,
	verified_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(object_id) REFERENCES tracked_objects (id) ON DELETE CASCADE,
	FOREIGN KEY(observation_id) REFERENCES object_observations (id) ON DELETE CASCADE,
	FOREIGN KEY(verified_by_id) REFERENCES users (id)
);

CREATE INDEX ix_object_facts_workspace_id ON object_facts (workspace_id);

CREATE INDEX ix_object_fact_workspace_type_status ON object_facts (workspace_id, fact_type, verification_status);

CREATE INDEX ix_object_fact_object_type ON object_facts (object_id, fact_type);

CREATE INDEX ix_object_facts_observation_id ON object_facts (observation_id);

CREATE INDEX ix_object_facts_object_id ON object_facts (object_id);

CREATE INDEX ix_object_facts_normalized_value ON object_facts (normalized_value);

CREATE TABLE object_activity_events (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	object_id UUID NOT NULL,
	observation_id UUID,
	capture_session_id UUID,
	device_id UUID,
	activity_type VARCHAR(64) NOT NULL,
	started_at TIMESTAMP WITH TIME ZONE NOT NULL,
	ended_at TIMESTAMP WITH TIME ZONE,
	start_pts_seconds FLOAT,
	end_pts_seconds FLOAT,
	confidence FLOAT NOT NULL,
	provenance fact_provenance NOT NULL,
	verification_status verification_status NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(object_id) REFERENCES tracked_objects (id) ON DELETE CASCADE,
	FOREIGN KEY(observation_id) REFERENCES object_observations (id),
	FOREIGN KEY(capture_session_id) REFERENCES capture_sessions (id),
	FOREIGN KEY(device_id) REFERENCES devices (id)
);

CREATE INDEX ix_object_activity_events_object_id ON object_activity_events (object_id);

CREATE INDEX ix_object_activity_events_device_id ON object_activity_events (device_id);

CREATE INDEX ix_activity_workspace_started ON object_activity_events (workspace_id, started_at);

CREATE INDEX ix_object_activity_events_workspace_id ON object_activity_events (workspace_id);

CREATE TABLE processing_jobs (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	media_asset_id UUID NOT NULL,
	capture_session_id UUID,
	observation_id UUID,
	operation processing_operation NOT NULL,
	status job_status NOT NULL,
	idempotency_key VARCHAR(160) NOT NULL,
	provider VARCHAR(80) NOT NULL,
	attempts INTEGER NOT NULL,
	result_metadata JSON NOT NULL,
	error_message TEXT,
	started_at TIMESTAMP WITH TIME ZONE,
	completed_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_job_workspace_idempotency UNIQUE (workspace_id, idempotency_key),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(media_asset_id) REFERENCES media_assets (id),
	FOREIGN KEY(capture_session_id) REFERENCES capture_sessions (id),
	FOREIGN KEY(observation_id) REFERENCES object_observations (id) ON DELETE CASCADE
);

CREATE INDEX ix_processing_jobs_workspace_id ON processing_jobs (workspace_id);

CREATE INDEX ix_processing_jobs_observation_id ON processing_jobs (observation_id);

CREATE TABLE query_history (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	user_id UUID NOT NULL,
	query_text TEXT NOT NULL,
	result_observation_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(result_observation_id) REFERENCES object_observations (id)
);

CREATE TABLE publication_tags (
	post_id UUID NOT NULL,
	term_id UUID NOT NULL,
	PRIMARY KEY (post_id, term_id),
	FOREIGN KEY(post_id) REFERENCES publications (id) ON DELETE CASCADE,
	FOREIGN KEY(term_id) REFERENCES publication_terms (id) ON DELETE CASCADE
);

CREATE INDEX ix_publication_tags_term_id ON publication_tags (term_id);

CREATE TABLE publication_likes (
	post_id UUID NOT NULL,
	user_id UUID NOT NULL,
	PRIMARY KEY (post_id, user_id),
	FOREIGN KEY(post_id) REFERENCES publications (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE publication_comments (
	id UUID NOT NULL,
	post_id UUID NOT NULL,
	user_id UUID NOT NULL,
	parent_id UUID,
	text TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(post_id) REFERENCES publications (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(parent_id) REFERENCES publication_comments (id)
);

CREATE INDEX ix_publication_comments_post_id ON publication_comments (post_id);

CREATE TABLE publication_reports (
	id UUID NOT NULL,
	post_id UUID NOT NULL,
	user_id UUID NOT NULL,
	reason TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (post_id, user_id),
	FOREIGN KEY(post_id) REFERENCES publications (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE publication_uploads (
	id UUID NOT NULL,
	owner_id UUID NOT NULL,
	request_key VARCHAR(64) NOT NULL,
	workspace_id UUID,
	category_id UUID,
	tag_ids JSON DEFAULT '[]' NOT NULL,
	original_bytes BYTEA NOT NULL,
	mime_type VARCHAR(64) NOT NULL,
	caption TEXT NOT NULL,
	note_text TEXT NOT NULL,
	note_source VARCHAR(16) NOT NULL,
	status VARCHAR(24) NOT NULL,
	duplicate_id UUID,
	expected_media_id UUID,
	result_id UUID,
	analysis JSON NOT NULL,
	error TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_upload_request UNIQUE (owner_id, request_key),
	FOREIGN KEY(owner_id) REFERENCES users (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id),
	FOREIGN KEY(category_id) REFERENCES publication_terms (id) ON DELETE SET NULL,
	FOREIGN KEY(duplicate_id) REFERENCES publications (id),
	FOREIGN KEY(expected_media_id) REFERENCES media_assets (id),
	FOREIGN KEY(result_id) REFERENCES publications (id)
);

CREATE INDEX ix_publication_uploads_status ON publication_uploads (status);

CREATE INDEX ix_publication_uploads_owner_id ON publication_uploads (owner_id);

CREATE TABLE publication_revisions (
	id UUID NOT NULL,
	post_id UUID NOT NULL,
	previous JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(post_id) REFERENCES publications (id)
);

CREATE INDEX ix_publication_revisions_post_id ON publication_revisions (post_id);

CREATE TABLE publication_duplicates (
	post_id UUID NOT NULL,
	canonical_id UUID NOT NULL,
	previous JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (post_id),
	FOREIGN KEY(post_id) REFERENCES publications (id),
	FOREIGN KEY(canonical_id) REFERENCES publications (id)
);

CREATE INDEX ix_publication_duplicates_canonical_id ON publication_duplicates (canonical_id);

CREATE TABLE publication_translations (
	post_id UUID NOT NULL,
	language VARCHAR(2) NOT NULL,
	text_hash VARCHAR(64) NOT NULL,
	translated_text TEXT NOT NULL,
	simulated BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (post_id, language, text_hash),
	FOREIGN KEY(post_id) REFERENCES publications (id) ON DELETE CASCADE
);

CREATE TABLE gallery_index_runs (
	id UUID NOT NULL,
	post_id UUID NOT NULL,
	media_id UUID NOT NULL,
	source_hash VARCHAR(64) NOT NULL,
	status VARCHAR(24) NOT NULL,
	stage VARCHAR(32) NOT NULL,
	attempt INTEGER NOT NULL,
	lease VARCHAR(36) NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	lease_until TIMESTAMP WITH TIME ZONE,
	progress JSON NOT NULL,
	error JSON,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(post_id) REFERENCES publications (id) ON DELETE CASCADE,
	FOREIGN KEY(media_id) REFERENCES media_assets (id)
);

CREATE INDEX ix_gallery_index_runs_post_id ON gallery_index_runs (post_id);

CREATE TABLE workspace_record_media (
	id UUID NOT NULL,
	record_id UUID NOT NULL,
	external_id VARCHAR(160) NOT NULL,
	media_id UUID NOT NULL,
	publication_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (record_id, external_id),
	FOREIGN KEY(record_id) REFERENCES workspace_records (id),
	FOREIGN KEY(media_id) REFERENCES media_assets (id),
	FOREIGN KEY(publication_id) REFERENCES publications (id)
);

CREATE INDEX ix_workspace_record_media_record_id ON workspace_record_media (record_id);

CREATE TABLE object_tracks (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	object_id UUID NOT NULL,
	source_media_asset_id UUID NOT NULL,
	processing_job_id UUID,
	model_name VARCHAR(120) NOT NULL,
	status VARCHAR(32) NOT NULL,
	last_seen_at TIMESTAMP WITH TIME ZONE,
	last_seen_pts_seconds FLOAT,
	metadata JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_video_track_object UNIQUE (source_media_asset_id, object_id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(object_id) REFERENCES tracked_objects (id) ON DELETE CASCADE,
	FOREIGN KEY(source_media_asset_id) REFERENCES media_assets (id) ON DELETE CASCADE,
	FOREIGN KEY(processing_job_id) REFERENCES processing_jobs (id)
);

CREATE INDEX ix_object_tracks_source_media_asset_id ON object_tracks (source_media_asset_id);

CREATE INDEX ix_object_tracks_object_id ON object_tracks (object_id);

CREATE INDEX ix_object_tracks_workspace_id ON object_tracks (workspace_id);

CREATE INDEX ix_object_track_workspace_status ON object_tracks (workspace_id, status);

CREATE TABLE gallery_evidence (
	id UUID NOT NULL,
	post_id UUID NOT NULL,
	media_id UUID NOT NULL,
	image_bytes BYTEA NOT NULL,
	content_hash VARCHAR(64) NOT NULL,
	frame_timestamp_ms INTEGER,
	detections JSON NOT NULL,
	version INTEGER NOT NULL,
	index_run_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(post_id) REFERENCES publications (id),
	FOREIGN KEY(media_id) REFERENCES media_assets (id),
	FOREIGN KEY(index_run_id) REFERENCES gallery_index_runs (id)
);

CREATE INDEX ix_gallery_evidence_index_run_id ON gallery_evidence (index_run_id);

CREATE INDEX ix_gallery_evidence_post_id ON gallery_evidence (post_id);

CREATE INDEX ix_gallery_evidence_media_id ON gallery_evidence (media_id);

CREATE INDEX ix_gallery_evidence_content_hash ON gallery_evidence (content_hash);

CREATE TABLE storage_objects (
	id UUID NOT NULL,
	connection_id UUID NOT NULL,
	revision INTEGER NOT NULL,
	key VARCHAR(1024) NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	workspace_id UUID,
	upload_id UUID,
	retired BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (connection_id, revision, key, workspace_id, upload_id),
	FOREIGN KEY(connection_id) REFERENCES storage_connections (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id),
	FOREIGN KEY(upload_id) REFERENCES publication_uploads (id)
);

CREATE INDEX ix_storage_objects_connection_id ON storage_objects (connection_id);

CREATE TABLE face_record_enrollments (
	id UUID NOT NULL,
	record_id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	media_asset_id UUID NOT NULL,
	record_media_id UUID,
	face_index INTEGER NOT NULL,
	embedding_model VARCHAR(80) NOT NULL,
	embedding BYTEA NOT NULL,
	bounding_box JSON NOT NULL,
	quality FLOAT NOT NULL,
	source VARCHAR(32) NOT NULL,
	authorized_by UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_face_record_enrollment UNIQUE (record_id, media_asset_id, face_index),
	FOREIGN KEY(record_id) REFERENCES workspace_records (id) ON DELETE CASCADE,
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(media_asset_id) REFERENCES media_assets (id) ON DELETE CASCADE,
	FOREIGN KEY(record_media_id) REFERENCES workspace_record_media (id) ON DELETE SET NULL,
	FOREIGN KEY(authorized_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_face_record_enrollment_workspace ON face_record_enrollments (workspace_id);

CREATE INDEX ix_face_record_enrollment_record ON face_record_enrollments (record_id);

CREATE TABLE object_track_segments (
	id UUID NOT NULL,
	track_id UUID NOT NULL,
	segment_index INTEGER NOT NULL,
	start_pts_seconds FLOAT NOT NULL,
	end_pts_seconds FLOAT NOT NULL,
	provider_file_id VARCHAR(160),
	request_state VARCHAR(32) NOT NULL,
	error_message TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_track_segment_index UNIQUE (track_id, segment_index),
	FOREIGN KEY(track_id) REFERENCES object_tracks (id) ON DELETE CASCADE
);

CREATE INDEX ix_object_track_segments_track_id ON object_track_segments (track_id);

CREATE TABLE object_track_frames (
	id UUID NOT NULL,
	track_id UUID NOT NULL,
	track_segment_id UUID,
	source_frame_index INTEGER NOT NULL,
	pts_seconds FLOAT NOT NULL,
	visible BOOLEAN NOT NULL,
	bounding_box JSON,
	mask_rle BYTEA,
	mask_width INTEGER,
	mask_height INTEGER,
	confidence FLOAT,
	simulated BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_track_source_frame UNIQUE (track_id, source_frame_index),
	FOREIGN KEY(track_id) REFERENCES object_tracks (id) ON DELETE CASCADE,
	FOREIGN KEY(track_segment_id) REFERENCES object_track_segments (id) ON DELETE CASCADE
);

CREATE INDEX ix_object_track_frames_track_id ON object_track_frames (track_id);

CREATE INDEX ix_track_frame_track_pts ON object_track_frames (track_id, pts_seconds);

CREATE INDEX ix_object_track_frames_track_segment_id ON object_track_frames (track_segment_id);

ALTER TABLE publications ADD CONSTRAINT fk_publication_active_index_run FOREIGN KEY(active_index_run_id) REFERENCES gallery_index_runs (id);

CREATE INDEX ix_tracked_objects_name_trgm ON tracked_objects USING gin (canonical_name gin_trgm_ops);

CREATE INDEX ix_tracked_objects_name_fts ON tracked_objects USING gin (to_tsvector('simple', canonical_name));

CREATE INDEX ix_object_aliases_alias_trgm ON object_aliases USING gin (alias gin_trgm_ops);

CREATE INDEX ix_object_aliases_alias_fts ON object_aliases USING gin (to_tsvector('simple', alias));

CREATE INDEX ix_publications_search_text_trgm ON publications USING gin (search_text gin_trgm_ops);

-- Historical migration journal, intentionally outside application ORM models.
CREATE TABLE biometric_publication_quarantine (post_id UUID PRIMARY KEY, previous_hidden BOOLEAN);
