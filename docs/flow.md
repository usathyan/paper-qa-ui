### Paper-QA UI Flows (User → UI → Functions)

This document summarizes how interactions in the Gradio UI map to functions in the codebase and external systems. Each Mermaid diagram shows a visual flow from user actions to the functions executed and any external calls.

Note: File/function names reference src/ui/paperqa2_ui.py unless otherwise noted.


### Rewrite (Plan tab)

User triggers rewrite via Enter in Question or clicking ↻ Rewrite.

```mermaid
flowchart LR
  U["User"] -->|"Enter or Click ↻ Rewrite"| UI["_preview_rewrite"]
  UI --> RW["llm_decompose_query"]
  RW --> LLM["LiteLLM (provider)"]
  LLM --> RW
  RW --> UI
  UI --> ST["app_state.rewrite_info"]
  UI --> RT["rewritten_textbox (editable)"]
  UI --> RS["rewrite_status banner"]
```

```mermaid
sequenceDiagram
  actor U as User
  participant Q as "Gradio Textbox: question_input"
  participant RB as "Gradio Button: rewrite_button"
  participant UI as "_preview_rewrite(q, cfg)"
  participant RW as "llm_decompose_query(question, settings)"
  participant LLM as "LiteLLM provider"
  participant ST as "app_state.rewrite_info"
  participant RT as "Gradio Textbox: rewritten_textbox"
  participant RS as "Gradio HTML: rewrite_status"

  U->>Q: Type question
  U->>Q: Press Enter
  Q->>UI: submit(question, config)
  U->>RB: (alternative) Click ↻ Rewrite
  RB->>UI: click(question, config)

  UI->>RW: call
  RW->>LLM: litellm.acompletion (REWRITE prompts)
  LLM-->>RW: response JSON/string
  RW-->>UI: rewritten and filters

  UI->>ST: set original, rewritten, filters
  UI->>RT: update value = rewritten
  UI->>RS: update value = LLM rewrite used (model …)
```

Key points:
- No retrieval required; rewrite is question-only with REWRITE prompts.
- Logs include the full user prompt and raw response (truncated) for visibility.


### Ask Question (high-level, no internals yet)

Clicking "Ask Question" runs retrieval + synthesis. This is a high-level outline only.

```mermaid
flowchart LR
  U[User] -->|Click Ask Question| BTN["Gradio Button: run_button"]
  BTN --> AW["ask_with_progress"]
  AW -->|stream pre-evidence| SAP["stream_analysis_progress"]
  AW -->|final answer step| PQ["process_question"]
  SAP -->|updates| UI1["inline_analysis and status"]
  PQ -->|updates| UI2["answer, sources, metadata, intelligence"]
```

Notes:
- The exact retrieval/synthesis internals will be documented in the next step.
- The final query used is whatever is in rewritten_textbox (editable) or the original if empty.


### Uploading PDF Documents

Selecting PDFs in the left rail triggers processing and indexing.

```mermaid
sequenceDiagram
  actor U as User
  participant F as "Gradio File: file_upload"
  participant P as "process_uploaded_files(files)"
  participant FS as "Local FS: ./papers"
  participant ST as "status_tracker and uploaded_docs"
  participant US as "Gradio Textbox: upload_status"
  participant ER as "Gradio Textbox: error_display"

  U->>F: Select/Drop PDF(s)
  F->>P: change(files)
  P->>FS: copy to ./papers
  P->>ST: append uploaded_docs
  P->>ST: add_status Indexed
  P-->>F: returns status_msg and error
  F->>US: set status text
  F->>ER: set error text (if any)
  ST->>ST: add_status Processing complete
```

Notes:
- No auto-retrieval is triggered on completion.
- The right-rail Session Log mirrors status_tracker messages.


### Query Builder Options (Plan → affects later retrieval)

Changing configuration and curation toggles updates settings/state used by Ask.

```mermaid
flowchart TB
  subgraph UI["Plan / Query Builder"]
    CD["Dropdown: config_dropdown"]
    LD["Checkbox: litellm_debug_toggle"]
    CT["Checkbox: critique_toggle"]
    BR["Checkbox: bias_retrieval_toggle"]
    SC["Slider: score_cutoff_slider"]
    PDC["Number: per_doc_cap_number"]
    MS["Number: max_sources_number"]
    SF["Checkbox: show_flags_toggle"]
    SCF["Checkbox: show_conflicts_toggle"]
  end

  CD -->|change| CFG["_on_config_change"]
  CFG --> S1["initialize_settings"]
  LD -->|change| LOG["_set_litellm_debug"]
  LOG --> L1["set env/log levels"]

  SC --> CUR["app_state.curation"]
  PDC --> CUR
  MS --> CUR
  SF --> TOG["app_state.ui_toggles"]
  SCF --> TOG
  CT --> AW["ask_with_progress"]
  BR --> AW
```

Notes:
- config_dropdown initializes settings (provider/model); affects rewrite and Ask.
- litellm_debug_toggle sets LITELLM_LOG=DEBUG and raises logger levels.
- Curation controls (score_cutoff, per_doc_cap, max_sources) are stored in app_state.curation and applied inside ask_with_progress before retrieval.
- bias_retrieval_toggle only augments the query if rewrite toggles are enabled within ask_with_progress (currently default OFF).
- critique_toggle, show_flags_toggle, show_conflicts_toggle influence optional outputs/formatting in the Synthesis and Evidence displays.


### Components and Functions Reference

- UI components: question_input, rewrite_button, rewritten_textbox, run_button, file_upload, upload_status, inline_analysis, answer_display, sources_display, metadata_display, intelligence_display.
- Rewrite functions: _preview_rewrite(q, cfg), llm_decompose_query(question, settings), rewrite_query(question, settings) (heuristic fallback).
- Ask entrypoint: ask_with_progress (streams progress and final results). Internals will be covered next.
- Upload processing: process_uploaded_files_async/files(), status mirrored via status_tracker.
- Config/Debug: _on_config_change, _set_litellm_debug.


### Future (Next Step)
- Detail the internals for Ask Question: pre-evidence streaming (stream_analysis_progress, _run_pre_evidence_in_thread, Docs.aget_evidence callbacks) and final synthesis (process_question), with sequence diagrams and data structures.
