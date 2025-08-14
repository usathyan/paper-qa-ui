# UI Reorganization Proposal (Data Scientist Workflow)

This document reorganizes the UI to align with the UX principles and end‑to‑end flow in `docs/UX-strategy.md`, without changing functionality.

## Layout Overview
- Left rail (sticky, narrow)
  - Project/Corpus
  - Query Builder (Original/Rewritten; filter chips)
  - Curation Controls
  - Display Toggles
  - Saved Queries
  - Export
- Center workspace (tabs)
  - Plan
  - Retrieval
  - Evidence
  - Conflicts
  - Synthesis
- Right rail (sticky, narrow)
  - Research Intelligence (live)
  - Metadata
  - Session Log
  - Quick Actions

## Tabs (Center Workspace)
### Plan
- Original vs Rewritten (side by side). Rewritten is editable.
- Filter chips below Rewritten (years, venues, fields, species, type, outcomes) with Bias/Hard mode badges.
- “Query Used” strip shows exact string sent downstream.

### Retrieval
- Single tall “Live Analysis Progress” panel:
  - Scope summary chips (years/venues/fields/mode).
  - Progress (selected / evidence_k), cutoff note.
  - MMR/cutoff visuals (compact charts).
  - Status log (last N events), pinned at panel bottom.

### Evidence
- Top summary: selected, ≥cutoff, unique venues, preprint share, years histogram, diversity score.
- Two columns: left facets (years slider + histogram, venues typeahead, fields list); right evidence cards (title/citation, venue/year/page/score/flags, snippet; include/exclude/pin; per-doc cap inline when toggled).
- Bottom sticky mini-bar: curation summary (score cutoff, per-doc cap, max sources) with quick edits.

### Conflicts
- Table list: Entity | #mixed | sample sources | Expand.
- Expanded row: polarity groups with excerpt tiles; “view full” minimal modal.
- “Unresolved conflicts” counter pinned.

### Synthesis
- Split: Answer (left) and Critique (right), same panel styling; both scrollable.
- “Provenance” drawer reveals included sources, filters, rewrite string, and event timeline.

## Rails
### Left Rail
- Project/Corpus: upload/list summary.
- Query Builder: Original/Rewritten (compact), “Use Rewritten”. Filter chips row.
- Curation Controls: score cutoff, per‑doc cap, max sources (one‑line help text each).
- Display Toggles: flags, conflicts, charts, dense layout.
- Saved Queries: named snapshots list.
- Export: JSON, CSV, Trace, Bundle.

### Right Rail
- Research Intelligence: compact cards.
- Metadata: simple list of metrics.
- Session Log: recent events; clicking focuses relevant tab/section.
- Quick Actions: clear session, export bundle.

## Navigation
- Stepper: Plan → Retrieval → Evidence → Conflicts → Synthesis. Dim future tabs (soft gating), no hard blocks.

## Consistency
- Typography: 16px / 1.55 across panels; small tags normalized to 1em.
- Containers: use the same HTML panel styling across Answer/Sources/Intelligence/Metadata/Analysis.
- Spacing: consistent margins (8–12px) and panel paddings.
- Heights: Live Analysis ~70vh; other panels max ~600px.

## Empty/Edge States
- Neutral empty messages in each tab; inline error blocks with clear retry.

## Responsive
- Rails collapse to accordions above/below center area on narrow screens.

## Incremental Migration
1) Add tab shell and rails.
2) Move existing blocks into new tabs/rails; unify to HTML panels; normalize fonts.
3) Tidy spacing, heights, and empty states.
4) Add stepper + soft gating visuals; link session log entries to sections.
