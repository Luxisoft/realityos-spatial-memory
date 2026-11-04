-- One-time local retirement of the Sonoran/Memory scenario; never run on server data.
-- Dependency-aware deletion follows in app.local.retirement. Shared/protected rows remain.
DELETE FROM local_access_accounts WHERE workspace_id = '8fd12f4c01525300874da162e05b0830' OR user_id IN ('e25476251c5053798e4cf7d8221074ee', '6330f2dc676c583288dc47d55549a5f3', 'c5f992730b595322a7307587d63e2d87');
DELETE FROM refresh_tokens WHERE user_id IN ('e25476251c5053798e4cf7d8221074ee', '6330f2dc676c583288dc47d55549a5f3', 'c5f992730b595322a7307587d63e2d87');
UPDATE users SET is_active = FALSE WHERE id IN ('e25476251c5053798e4cf7d8221074ee', '6330f2dc676c583288dc47d55549a5f3', 'c5f992730b595322a7307587d63e2d87');
UPDATE devices SET status = 'revoked' WHERE workspace_id = '8fd12f4c01525300874da162e05b0830';
UPDATE workspace_connections SET active = FALSE WHERE workspace_id = '8fd12f4c01525300874da162e05b0830';
UPDATE workspaces SET join_pin = NULL WHERE id = '8fd12f4c01525300874da162e05b0830';
UPDATE publications SET hidden = TRUE WHERE workspace_id = '8fd12f4c01525300874da162e05b0830';
