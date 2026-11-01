# Social directory fixtures

`PROFILE_ROWS` in `scripts/seed_social_directory.py` describes 20 deterministic
test identities. Source portraits live in `source/` (identity anchors only);
`scripts/generate_directory_photos.py` renders 10 genuinely different
Muse-anchored scenes per profile under ignored `muse/` (1 anchor + 10 forked
takes, InsightFace-validated), and the seed imports them through the same
BYTEA and InsightFace path used by Facebook media. Avatars stay in ignored
`generated/`. No synthetic videos ship with directory profiles.

`workshop/` holds the 15 same-shop takes (9 day, 6 night) published in the
"Mechanic Workshop" group (5 members, day/night shifts) plus the original
shop video.

The generated identities do not represent real people. Production behavior is
not mocked: the deployed face engine, workspace membership and authorization
rules remain active.
