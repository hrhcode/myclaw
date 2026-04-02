# Knowledge Base Redesign

## Goals

- Move memory retrieval settings out of the memory page and into the settings page.
- Replace the current "long-term memory" page with a knowledge base page.
- Support RAG over user-managed knowledge.
- Let users upload Markdown files into the knowledge base.
- Let users save high-quality assistant replies into the knowledge base with one click.
- Keep short-term memory as conversation history, and use the knowledge base as retrieved supporting context.

## Product Model

### Short-term memory

- Source: current conversation messages.
- Scope: current conversation.
- Usage: included in model history as before.

### Knowledge base

- Source: uploaded Markdown files and saved assistant replies.
- Scope: session-scoped by default.
- Usage: indexed with embeddings and searched with the existing hybrid retrieval pipeline.

### Rules

- Not part of this change.
- If introduced later, rules should remain separate from the knowledge base because they are deterministic instructions rather than retrieved supporting context.

## Information Architecture

### Settings page

Add a new section named `Memory & Retrieval` with:

- `memory_top_k`
- `memory_min_score`
- `memory_use_hybrid`
- `memory_vector_weight`
- `memory_text_weight`
- `memory_enable_mmr`
- `memory_mmr_lambda`
- `memory_enable_temporal_decay`
- `memory_half_life_days`
- existing `memory_auto_extract`
- existing `memory_threshold`

### Knowledge base page

Replace the old memory page with:

- Summary cards
  - total items
  - markdown sources
  - saved replies
- Toolbar
  - upload Markdown
  - search
  - filter by source type
- Knowledge list
  - grouped document rows for uploaded Markdown
  - single rows for saved replies
- Actions
  - preview
  - delete

### Chat page

For assistant messages:

- add `Save to knowledge base` action
- open a lightweight form:
  - title
  - optional note/source label
- save the assistant message as a knowledge entry

## Data Model

Reuse `long_term_memory` as the storage table to avoid a large migration and preserve retrieval compatibility.

Add columns:

- `title`: human-readable title for display
- `content_type`: `note | markdown | assistant_reply`
- `group_id`: shared id for chunked uploads from the same Markdown file
- `origin_message_id`: original assistant message id when saved from chat

Column semantics:

- Markdown uploads are chunked into multiple rows that share the same `group_id`.
- Saved assistant replies are stored as a single row without chunking unless the content is very long.
- Existing long-term memory rows remain valid and are treated as `note`.

## Backend API

Keep existing `/memory/search` behavior so the agent loop continues to work.

Add knowledge-base oriented endpoints:

- `GET /knowledge`
  - returns grouped knowledge items for UI rendering
- `POST /knowledge/markdown`
  - multipart upload for Markdown files
  - chunks the document and stores chunk rows
- `POST /knowledge/from-message`
  - saves an assistant message into the knowledge base
- `DELETE /knowledge/{group_or_item_id}`
  - deletes a grouped Markdown upload or a single item

## Chunking Strategy

Use a lightweight Markdown-aware chunker:

- split on headings first
- merge small sections
- enforce a max character size per chunk
- keep chunk overlap for continuity

Initial targets:

- max chars per chunk: about 1200
- overlap: about 150

This is intentionally simple and stable for the current codebase.

## Retrieval Integration

No new retrieval pipeline is required.

The existing `hybrid_memory_search(...)` flow already:

- searches conversation messages
- searches `long_term_memory`
- merges and reranks results

The only change is conceptual:

- treat `long_term_memory` rows as knowledge entries
- display them as a knowledge base in the UI

## Auto Extraction

Keep current auto extraction behavior for now, but reframe it in the UI as:

- `Auto-save useful exchanges to knowledge base`

This remains a coarse capture path and should not replace explicit user curation.

## Migration and Compatibility

- Existing data in `long_term_memory` remains accessible.
- Existing retrieval settings remain unchanged.
- Existing search code keeps working.
- Existing API routes under `/memory/long-term` can remain for compatibility during transition.

## Execution Plan

1. Extend runtime schema and SQLAlchemy model.
2. Add knowledge-base API routes and grouping helpers.
3. Move retrieval controls into settings.
4. Replace the memory page with a knowledge base page.
5. Add assistant-message save action in chat UI.
6. Validate upload, retrieval, save, and delete flows.
