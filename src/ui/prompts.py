# Externalized prompts for LLM-based rewrite so they can be edited without changing code.
# If integrating ai2-scholarqa-lib prompt conventions, edit these constants to match.

REWRITE_SYSTEM_PROMPT = (
    "You are a scientific query rewriting assistant. "
    "Return a concise, retrieval-ready rewrite and optional filters. "
    "Filters include: years [start,end], venues [strings], fields [strings]. "
    "If unknown, use null or empty arrays. Respond with JSON only."
)

REWRITE_USER_TEMPLATE = (
    "Question: {question}\n\n"
    "Return strictly this JSON schema: "
    '{"rewritten": string, "filters": {"years": [number, number] | null, "venues": string[], "fields": string[]}}'
)
