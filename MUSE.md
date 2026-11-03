# RealityOS — Muse conventions

Project conventions live in `AGENTS.md` and are binding. Start with
`docs/es/project/PROJECT_CONTEXT.md` for the repo map and current state.

## Protected: biometric face-search module

The face-search vertical (`backend/app/faces.py`, migration
`20261028_0009_faces`, `/v1/faces/*` routes, `tests/test_faces.py`,
biometric-consent/search UI) is a deliberate, consent-gated product feature
ordered by the project owner.

- Keep it an isolated arm: never merge it into the object Register/Query
  pipeline. Shared infrastructure (auth, BYTEA media, worker) plus a read-only
  display lookup of synced Facebook profile fields is the only coupling.
- Do not delete, disable, stub out or refactor it away as cleanup, and do not
  reintroduce a "never biometric" restriction: the owner explicitly lifted that
  restriction on 2026-10-28.
- Changes to this module require an explicit user request naming it.
