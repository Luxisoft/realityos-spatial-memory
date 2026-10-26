# RealityOS agent conventions

## Code discovery

This project uses codebase-memory-mcp when it is available. Prefer graph tools
in this order: `search_graph`, `trace_path`, `get_code_snippet`,
`query_graph`, then `get_architecture`. Fall back to `rg` for literals,
configuration and non-code files, or when the graph is unavailable.

## Structure and commands

- Keep shared backend contracts in `backend/`; API and worker must not diverge.
- Keep browser UI in `frontend/`, Display UI in `display-webapp/`, and phone
  and Wearables code in `android/`.
- Store synthetic fixtures only in `simulator/`; never commit credentials or
  customer media.
- Prefer commands exposed by the root `Makefile`. Before handoff, run the
  smallest relevant formatter, type/lint check, test and build.

## Security and product invariants

- PostgreSQL `BYTEA` is the source of truth for original captured media.
- Scope every workspace resource query by authenticated membership.
- Register is explicit and writable; Query never starts capture or fabricates evidence.
- State observation dates as “last seen” and keep visual confidence separate
  from confidence that an item remains there now.
- `MODEL_API_KEY`, JWT secrets and database credentials remain server-side.
- Mock outputs are deterministic and visibly labelled simulated.
- Confirm current official Meta endpoint/SDK signatures before coding Live.

## Validation

- Add tests with changes and cover permission and workspace isolation.
- Do not claim an Android build, device test, live Meta request, Docker run or
  PR unless it has actually run in the applicable environment.
- Update `docs/IMPLEMENTATION_STATUS.md` for incomplete external integrations.
