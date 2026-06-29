# Project plan

## Part 1: Plan

- [x] Rewrite this plan with reviewable checklists, tests, and success criteria.
- [x] Add `frontend/AGENTS.md` describing the current demo frontend.
- Tests: manual doc review for scope, order, and consistency with `AGENTS.md`.
- Success: user approves this plan before implementation work continues.

## Part 2: Scaffolding

- [x] Create FastAPI app scaffold in `backend/`.
- [x] Add Docker setup and cross-platform start/stop scripts in `scripts/`.
- [x] Serve a simple HTML page and one example API response from the container.
- Tests: build container, start locally, hit `/` and `/api/health`.
- Success: one local command path starts the container and both routes work.

## Part 3: Add in Frontend

- [x] Build the existing Next.js frontend as static assets.
- [x] Serve the built frontend from FastAPI at `/`.
- [x] Keep current Kanban interactions working in the served app.
- Tests: frontend unit tests, e2e smoke test, browser check of `/`.
- Success: the demo Kanban loads through the backend-served app.

## Part 4: Fake sign in

- [x] Add a login screen in front of the board.
- [x] Accept only `user` / `password`.
- [x] Add logout and return to the login screen on logout.
- Tests: happy path login, invalid login, logout flow.
- Success: unauthenticated users cannot reach the board UI.

## Part 5: Database modeling

- [ ] Define a SQLite schema that supports multiple users and one board per user for now.
- [ ] Store board state as JSON and document the approach in `docs/`.
- [ ] Get user sign-off before implementing database-backed routes.
- Tests: schema review and document review.
- Success: schema and storage approach are approved.

## Part 6: Backend

- [ ] Add routes to read a user's board.
- [ ] Add routes to update board data for that user.
- [ ] Create the SQLite database automatically if missing.
- Tests: backend unit tests for create, read, update, and missing-db startup.
- Success: backend persists and returns board state correctly.

## Part 7: Frontend + Backend

- [ ] Replace in-memory board state bootstrap with backend fetch/load.
- [ ] Save board edits through the API.
- [ ] Keep drag, rename, add, and delete flows working against persisted data.
- Tests: frontend integration tests plus e2e persistence checks.
- Success: refreshing the page preserves the latest board state.

## Part 8: AI connectivity

- [ ] Add backend OpenRouter client configuration from `.env`.
- [ ] Use model `openai/gpt-oss-120b`.
- [ ] Add a simple connectivity path that asks `2+2`.
- Tests: mocked unit test plus one real connectivity check when env is present.
- Success: backend can complete a basic OpenRouter request.

## Part 9: Structured AI board updates

- [ ] Send board JSON, user message, and conversation history to the model.
- [ ] Require structured output with chat reply and optional board update payload.
- [ ] Validate and apply returned board updates safely in the backend.
- Tests: schema validation tests, no-op response test, board-update response test.
- Success: AI responses can optionally modify persisted board data.

## Part 10: AI sidebar UI

- [ ] Add a sidebar chat UI to the frontend.
- [ ] Send chat messages to the backend AI endpoint.
- [ ] Refresh the board automatically when AI returns updates.
- Tests: component tests for chat flow and e2e test for AI-driven board change.
- Success: users can chat in-app and see AI board edits reflected immediately.
