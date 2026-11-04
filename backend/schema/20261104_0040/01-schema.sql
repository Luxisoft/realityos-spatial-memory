-- Frozen schema at Alembic revision 20261104_0040. Do not regenerate from current models.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE workspace_role AS ENUM ('ADMIN', 'REGISTER', 'QUERY');

CREATE TYPE device_status AS ENUM ('active', 'revoked');

CREATE TYPE capture_status AS ENUM ('OPEN', 'CLOSED');

CREATE TYPE media_kind AS ENUM ('IMAGE', 'VIDEO', 'FRAME', 'MASK', 'CROP');

CREATE TYPE verification_status AS ENUM ('PENDING', 'VERIFIED', 'REJECTED');

CREATE TYPE fact_provenance AS ENUM ('visible_text', 'visual', 'temporal', 'manual', 'legacy');

CREATE TYPE processing_operation AS ENUM ('analysis', 'segmentation', 'video_tracking');

CREATE TYPE job_status AS ENUM ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'UNCERTAIN');

CREATE TABLE users (
	id UUID NOT NULL,
	email VARCHAR(320) NOT NULL,
	display_name VARCHAR(160) NOT NULL,
	password_hash VARCHAR(512) NOT NULL,
	is_active BOOLEAN NOT NULL,
	preferred_language VARCHAR(2),
	is_guest BOOLEAN NOT NULL,
	device_id VARCHAR(128),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_device_id ON users (device_id);

CREATE TABLE local_evaluation_state (
	name VARCHAR(80) NOT NULL,
	manifest_hash VARCHAR(64) NOT NULL,
	counts JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (name)
);

CREATE TABLE account_attempts (
	key VARCHAR(64) NOT NULL,
	"window" INTEGER NOT NULL,
	count INTEGER NOT NULL,
	PRIMARY KEY (key)
);

CREATE TABLE workspaces (
	display_text JSON NOT NULL,
	id UUID NOT NULL,
	name VARCHAR(160) NOT NULL,
	description TEXT,
	created_by_id UUID NOT NULL,
	join_pin VARCHAR(9),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	FOREIGN KEY(created_by_id) REFERENCES users (id),
	UNIQUE (join_pin)
);

CREATE TABLE refresh_tokens (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	jti VARCHAR(64) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	revoked_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_refresh_tokens_jti ON refresh_tokens (jti);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);

CREATE TABLE facebook_identities (
	subject VARCHAR(128) NOT NULL,
	user_id UUID NOT NULL,
	PRIMARY KEY (subject),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE chat_messages (
	id SERIAL NOT NULL,
	user_id UUID NOT NULL,
	role VARCHAR(8) NOT NULL,
	kind VARCHAR(8) NOT NULL,
	text TEXT NOT NULL,
	evidence_url VARCHAR(1024),
	audio_duration_ms INTEGER NOT NULL,
	gallery JSON NOT NULL,
	simulated BOOLEAN NOT NULL,
	quick_replies JSON NOT NULL,
	response_language VARCHAR(16),
	template_data JSON,
	face_action BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_chat_messages_user_id ON chat_messages (user_id);

CREATE TABLE facebook_profiles (
	user_id UUID NOT NULL,
	email VARCHAR(320),
	birthday VARCHAR(32),
	age_min INTEGER,
	age_max INTEGER,
	gender VARCHAR(32),
	hometown VARCHAR(160),
	location VARCHAR(160),
	profile_link VARCHAR(512),
	picture_url VARCHAR(1024),
	friends_count INTEGER,
	likes_count INTEGER,
	photos_count INTEGER,
	videos_count INTEGER,
	granted_scopes JSON NOT NULL,
	import_status VARCHAR(16) NOT NULL,
	imported_photos INTEGER NOT NULL,
	imported_videos INTEGER NOT NULL,
	sync_diagnostics JSON NOT NULL,
	skipped_media INTEGER NOT NULL,
	picture_imported BOOLEAN NOT NULL,
	import_error VARCHAR(500),
	synced_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE facebook_friends (
	owner_user_id UUID NOT NULL,
	facebook_id VARCHAR(128) NOT NULL,
	name VARCHAR(160) NOT NULL,
	picture_url VARCHAR(1024),
	profile_link VARCHAR(1024),
	PRIMARY KEY (owner_user_id, facebook_id),
	FOREIGN KEY(owner_user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_facebook_friends_owner ON facebook_friends (owner_user_id);

CREATE TABLE facebook_posts (
	fb_id VARCHAR(128) NOT NULL,
	user_id UUID NOT NULL,
	message TEXT,
	fb_created_time VARCHAR(64),
	permalink VARCHAR(1024),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (fb_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_facebook_post_user ON facebook_posts (user_id);

CREATE INDEX ix_facebook_posts_user_id ON facebook_posts (user_id);

CREATE TABLE password_accounts (
	user_id UUID NOT NULL,
	username VARCHAR(64) NOT NULL,
	provisioned_by UUID,
	verified_at TIMESTAMP WITH TIME ZONE,
	revoked_before TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	UNIQUE (username),
	FOREIGN KEY(provisioned_by) REFERENCES users (id)
);

CREATE TABLE account_challenges (
	digest VARCHAR(64) NOT NULL,
	user_id UUID NOT NULL,
	purpose VARCHAR(16) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	consumed_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (digest),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_account_challenges_user_id ON account_challenges (user_id);

CREATE TABLE biometric_consents (
	user_id UUID NOT NULL,
	notice_version VARCHAR(80) NOT NULL,
	consented_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	revoked_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE face_verifications (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	result VARCHAR(16) NOT NULL,
	score FLOAT,
	threshold FLOAT NOT NULL,
	engine VARCHAR(80) NOT NULL,
	simulated BOOLEAN NOT NULL,
	verified_for_synced_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_face_verification_user ON face_verifications (user_id);

CREATE INDEX ix_face_verifications_user_id ON face_verifications (user_id);

CREATE TABLE biometric_setups (
	user_id UUID NOT NULL,
	completed_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE workspace_members (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	user_id UUID NOT NULL,
	role workspace_role NOT NULL,
	can_invite BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_workspace_member UNIQUE (workspace_id, user_id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_workspace_members_user_id ON workspace_members (user_id);

CREATE INDEX ix_workspace_members_workspace_id ON workspace_members (workspace_id);

CREATE TABLE devices (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	device_identifier VARCHAR(96) NOT NULL,
	label VARCHAR(160) NOT NULL,
	credential_hash VARCHAR(128) NOT NULL,
	status device_status NOT NULL,
	created_by_id UUID NOT NULL,
	last_seen_at TIMESTAMP WITH TIME ZONE,
	revoked_at TIMESTAMP WITH TIME ZONE,
	metadata JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_device_identifier UNIQUE (device_identifier),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(created_by_id) REFERENCES users (id)
);

CREATE INDEX ix_device_workspace_status ON devices (workspace_id, status);

CREATE INDEX ix_devices_workspace_id ON devices (workspace_id);

CREATE TABLE zones (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	parent_id UUID,
	name VARCHAR(160) NOT NULL,
	kind VARCHAR(32) NOT NULL,
	sort_order INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_zone_path UNIQUE (workspace_id, parent_id, name),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(parent_id) REFERENCES zones (id)
);

CREATE INDEX ix_zones_workspace_id ON zones (workspace_id);

CREATE TABLE tracked_objects (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	canonical_name VARCHAR(240) NOT NULL,
	category VARCHAR(120),
	attributes JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_object_workspace_name UNIQUE (workspace_id, canonical_name),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
);

CREATE INDEX ix_object_workspace_name ON tracked_objects (workspace_id, canonical_name);

CREATE INDEX ix_tracked_objects_workspace_id ON tracked_objects (workspace_id);

CREATE TABLE chat_audio (
	id SERIAL NOT NULL,
	message_id INTEGER NOT NULL,
	user_id UUID NOT NULL,
	audio BYTEA NOT NULL,
	mime_type VARCHAR(32) NOT NULL,
	duration_ms INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(message_id) REFERENCES chat_messages (id) ON DELETE CASCADE,
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_chat_audio_user_id ON chat_audio (user_id);

CREATE INDEX ix_chat_audio_message_id ON chat_audio (message_id);

CREATE TABLE publication_terms (
	display_text JSON NOT NULL,
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	kind VARCHAR(16) NOT NULL,
	name VARCHAR(80) NOT NULL,
	name_key VARCHAR(160) NOT NULL,
	active BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_publication_term_name UNIQUE (workspace_id, kind, name_key),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE
);

CREATE INDEX ix_publication_terms_workspace_id ON publication_terms (workspace_id);

CREATE TABLE group_invites (
	code VARCHAR(128) NOT NULL,
	workspace_id UUID NOT NULL,
	active BOOLEAN NOT NULL,
	PRIMARY KEY (code),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
);

CREATE TABLE chat_message_translations (
	message_id INTEGER NOT NULL,
	language VARCHAR(2) NOT NULL,
	source_hash VARCHAR(64) NOT NULL,
	text TEXT NOT NULL,
	quick_replies JSON NOT NULL,
	status VARCHAR(16) NOT NULL,
	simulated BOOLEAN NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (message_id, language, source_hash),
	FOREIGN KEY(message_id) REFERENCES chat_messages (id) ON DELETE CASCADE
);

CREATE TABLE storage_connections (
	id UUID NOT NULL,
	owner_id UUID NOT NULL,
	name VARCHAR(160) NOT NULL,
	provider VARCHAR(16) NOT NULL,
	endpoint VARCHAR(2048) NOT NULL,
	bucket VARCHAR(63) NOT NULL,
	region VARCHAR(80) NOT NULL,
	prefix VARCHAR(1024) NOT NULL,
	secret TEXT NOT NULL,
	active BOOLEAN NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	workspace_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(owner_id) REFERENCES users (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
);

CREATE INDEX ix_storage_connections_owner_id ON storage_connections (owner_id);

CREATE TABLE workspace_connections (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	created_by_id UUID NOT NULL,
	name VARCHAR(160) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	active BOOLEAN NOT NULL,
	source_url VARCHAR(2048),
	secret_encrypted TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id),
	FOREIGN KEY(created_by_id) REFERENCES users (id),
	UNIQUE (token_hash)
);

CREATE INDEX ix_workspace_connections_workspace_id ON workspace_connections (workspace_id);

CREATE TABLE device_assignments (
	id UUID NOT NULL,
	device_id UUID NOT NULL,
	operator_label VARCHAR(160) NOT NULL,
	external_reference VARCHAR(160),
	effective_from TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	effective_to TIMESTAMP WITH TIME ZONE,
	attested_by_id UUID NOT NULL,
	notice_version VARCHAR(80) NOT NULL,
	attested_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(device_id) REFERENCES devices (id) ON DELETE CASCADE,
	FOREIGN KEY(attested_by_id) REFERENCES users (id)
);

CREATE INDEX ix_device_assignment_active ON device_assignments (device_id, effective_to);

CREATE INDEX ix_device_assignments_device_id ON device_assignments (device_id);

CREATE TABLE object_aliases (
	id UUID NOT NULL,
	object_id UUID NOT NULL,
	alias VARCHAR(240) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_object_alias UNIQUE (object_id, alias),
	FOREIGN KEY(object_id) REFERENCES tracked_objects (id) ON DELETE CASCADE
);

CREATE INDEX ix_object_aliases_object_id ON object_aliases (object_id);

CREATE INDEX ix_object_aliases_alias ON object_aliases (alias);

CREATE TABLE audit_events (
	id UUID NOT NULL,
	workspace_id UUID,
	actor_id UUID,
	device_id UUID,
	event_type VARCHAR(120) NOT NULL,
	entity_type VARCHAR(80) NOT NULL,
	entity_id UUID,
	payload JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id),
	FOREIGN KEY(actor_id) REFERENCES users (id),
	FOREIGN KEY(device_id) REFERENCES devices (id)
);

CREATE INDEX ix_audit_events_actor_id ON audit_events (actor_id);

CREATE INDEX ix_audit_events_event_type ON audit_events (event_type);

CREATE INDEX ix_audit_events_device_id ON audit_events (device_id);

CREATE INDEX ix_audit_events_workspace_id ON audit_events (workspace_id);

CREATE TABLE storage_imports (
	id UUID NOT NULL,
	connection_id UUID NOT NULL,
	request_key VARCHAR(128) NOT NULL,
	payload_hash VARCHAR(64) NOT NULL,
	revision INTEGER DEFAULT '1' NOT NULL,
	workspace_id UUID,
	items JSON NOT NULL,
	status VARCHAR(24) NOT NULL,
	lease_until TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (connection_id, request_key),
	FOREIGN KEY(connection_id) REFERENCES storage_connections (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
);

CREATE INDEX ix_storage_imports_status ON storage_imports (status);

CREATE INDEX ix_storage_imports_connection_id ON storage_imports (connection_id);

CREATE TABLE storage_syncs (
	id UUID NOT NULL,
	connection_id UUID NOT NULL,
	prefix VARCHAR(1024) NOT NULL,
	workspace_id UUID,
	interval_minutes INTEGER NOT NULL,
	enabled BOOLEAN NOT NULL,
	next_run TIMESTAMP WITH TIME ZONE NOT NULL,
	cursor TEXT,
	error VARCHAR(200),
	seen_keys JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(connection_id) REFERENCES storage_connections (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id)
);

CREATE INDEX ix_storage_syncs_connection_id ON storage_syncs (connection_id);

CREATE TABLE workspace_import_runs (
	id UUID NOT NULL,
	connection_id UUID NOT NULL,
	request_key VARCHAR(128) NOT NULL,
	payload_hash VARCHAR(64) NOT NULL,
	result JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (connection_id, request_key),
	FOREIGN KEY(connection_id) REFERENCES workspace_connections (id)
);

CREATE INDEX ix_workspace_import_runs_connection_id ON workspace_import_runs (connection_id);

CREATE TABLE workspace_records (
	display_text JSON NOT NULL,
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	connection_id UUID NOT NULL,
	external_id VARCHAR(160) NOT NULL,
	kind VARCHAR(32) NOT NULL,
	title VARCHAR(200) NOT NULL,
	data JSON NOT NULL,
	related_ids JSON NOT NULL,
	version INTEGER NOT NULL,
	status VARCHAR(16) NOT NULL,
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	simulated BOOLEAN NOT NULL,
	biometric_authorized BOOLEAN NOT NULL,
	biometric_basis VARCHAR(200),
	biometric_authorized_by UUID,
	biometric_authorized_at TIMESTAMP WITH TIME ZONE,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (connection_id, external_id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id),
	FOREIGN KEY(connection_id) REFERENCES workspace_connections (id),
	FOREIGN KEY(biometric_authorized_by) REFERENCES users (id)
);

CREATE INDEX ix_workspace_records_connection_id ON workspace_records (connection_id);

CREATE INDEX ix_workspace_records_workspace_id ON workspace_records (workspace_id);

CREATE INDEX ix_workspace_records_kind ON workspace_records (kind);

CREATE TABLE capture_sessions (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	zone_id UUID,
	created_by_id UUID,
	device_id UUID,
	device_assignment_id UUID,
	origin VARCHAR(16) NOT NULL,
	status capture_status NOT NULL,
	started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	closed_at TIMESTAMP WITH TIME ZONE,
	consent_confirmed BOOLEAN NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(zone_id) REFERENCES zones (id),
	FOREIGN KEY(created_by_id) REFERENCES users (id),
	FOREIGN KEY(device_id) REFERENCES devices (id),
	FOREIGN KEY(device_assignment_id) REFERENCES device_assignments (id)
);

CREATE INDEX ix_capture_sessions_workspace_id ON capture_sessions (workspace_id);

CREATE INDEX ix_capture_sessions_device_id ON capture_sessions (device_id);

CREATE TABLE workspace_record_revisions (
	id UUID NOT NULL,
	record_id UUID NOT NULL,
	version INTEGER NOT NULL,
	snapshot JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (record_id, version),
	FOREIGN KEY(record_id) REFERENCES workspace_records (id)
);

CREATE INDEX ix_workspace_record_revisions_record_id ON workspace_record_revisions (record_id);

CREATE TABLE workspace_record_notes (
	id UUID NOT NULL,
	record_id UUID NOT NULL,
	actor_id UUID NOT NULL,
	text TEXT NOT NULL,
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(record_id) REFERENCES workspace_records (id),
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE INDEX ix_workspace_record_notes_record_id ON workspace_record_notes (record_id);

CREATE TABLE media_assets (
	id UUID NOT NULL,
	workspace_id UUID NOT NULL,
	capture_session_id UUID,
	parent_asset_id UUID,
	kind media_kind NOT NULL,
	mime_type VARCHAR(127) NOT NULL,
	original_bytes BYTEA NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	byte_size INTEGER NOT NULL,
	width INTEGER,
	height INTEGER,
	captured_at TIMESTAMP WITH TIME ZONE,
	metadata JSON NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_media_session_hash UNIQUE (capture_session_id, sha256),
	FOREIGN KEY(workspace_id) REFERENCES workspaces (id) ON DELETE CASCADE,
	FOREIGN KEY(capture_session_id) REFERENCES capture_sessions (id) ON DELETE SET NULL,
	FOREIGN KEY(parent_asset_id) REFERENCES media_assets (id)
);

CREATE INDEX ix_media_assets_capture_session_id ON media_assets (capture_session_id);

CREATE INDEX ix_media_workspace_sha256 ON media_assets (workspace_id, sha256);

CREATE INDEX ix_media_assets_workspace_id ON media_assets (workspace_id);

CREATE TABLE media_asset_chunks (
	asset_id UUID NOT NULL,
	chunk_index INTEGER NOT NULL,
	content BYTEA NOT NULL,
	byte_size INTEGER NOT NULL,
	PRIMARY KEY (asset_id, chunk_index),
	FOREIGN KEY(asset_id) REFERENCES media_assets (id) ON DELETE CASCADE
);
