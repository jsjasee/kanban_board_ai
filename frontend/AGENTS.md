# Frontend codebase guide

## Scope

This directory is a frontend-only demo of the Kanban UI. It is a Next.js 16 app using React 19, TypeScript, Tailwind CSS v4, and `@dnd-kit` for drag and drop.

## Entry points

- `src/app/page.tsx` renders `KanbanBoard` as the whole page.
- `src/app/layout.tsx` sets metadata and loads `Space Grotesk` for display text and `Manrope` for body text.
- `src/app/globals.css` defines the shared color variables and basic global styling.

## Main feature flow

- `src/components/KanbanBoard.tsx` owns the full board state in local React state.
- Initial data and board helpers live in `src/lib/kanban.ts`.
- The board supports:
  - renaming fixed columns
  - adding cards
  - deleting cards
  - moving cards within and across columns with drag and drop
- There is no persistence, auth, backend integration, or AI wiring in this directory yet.

## Component map

- `KanbanBoard`: page-level state, drag sensors, drag overlay, and action handlers
- `KanbanColumn`: droppable column shell, column title input, sortable card list, add-card form
- `KanbanCard`: sortable card item with delete action
- `KanbanCardPreview`: drag overlay preview for the active card
- `NewCardForm`: local open/close form state for creating a card

## Data model

`src/lib/kanban.ts` defines:

- `Card`: `{ id, title, details }`
- `Column`: `{ id, title, cardIds }`
- `BoardData`: `{ columns, cards }`

The board is normalized:

- column order is stored in the `columns` array
- cards are stored by id in `cards`
- each column stores ordered `cardIds`

`moveCard` handles reorder and cross-column moves. `createId` generates client-side ids for new cards.

## Tests

- `src/lib/kanban.test.ts` covers `moveCard`
- `src/components/KanbanBoard.test.tsx` covers render, rename, add, and delete flows
- `tests/kanban.spec.ts` covers browser-level render, add-card, and drag-and-drop flows with Playwright
- `src/test/setup.ts` configures the unit test environment for Vitest and Testing Library

## Reviewer notes

- State is intentionally simple and local to `KanbanBoard`.
- Column titles are editable inline and are not validated beyond normal input behavior.
- New cards require a non-empty title; blank details fall back to `"No details yet."`
- The current app is optimized for the MVP demo, not for persistence or multi-user behavior.
