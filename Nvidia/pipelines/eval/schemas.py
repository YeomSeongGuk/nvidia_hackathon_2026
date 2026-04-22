"""Pydantic schemas for LLM-as-Judge evaluation across all pipeline stages.

One module per stage's worth of schemas, arranged top→down in pipeline order:
Stage 1.1 → 1.2 → 2.1 → 2.2 → 2.3 → 2.4. Each stage has a `*JudgeResult`
(exactly what the LLM judge returns in JSON) and a `*JudgeRecord` (persisted
to `judge.jsonl`, combining the judge verdict + the unit under test + meta).

Every stage also has a `*SummaryRow` that lands as one line in the
append-only `summary.jsonl`, so metrics-over-time is grep-able / pandas-able.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


ATTR_KEYS = ("material", "fit", "color", "style", "season")


# ===========================================================================
# STAGE 1.1 - synthetic review generation (Data Designer output)
# ===========================================================================
# Evaluates the output of Stage 1.1 (`data_pipeline_vllm.py` / team's
# `data_pipeline_nemo.py`): per-record quality of the generated fashion
# review including product_title, product_attributes, and raw_text.
# Specifically designed to surface the issues we observed in the 10K run
# (reasoning-leak into titles, mode-collapsed attributes, persona drift).

STAGE_1_1_FAILURE_MODES = (
    "title_reasoning_leak",       # model wrote its self-verification into product_title
    "title_length_violation",     # title outside 15-30 char spec
    "title_format_violation",     # missing brand+category+feature shape
    "attr_ungrounded",            # at least one attribute value not supported by raw_text
    "attr_mono_value",            # all attributes default ('캐주얼', 'M', ...) — collapse
    "non_fashion_item",           # title/raw_text is about non-fashion product
    "persona_drift",              # raw_text ignores persona hobbies/occupation/age
    "missing_tpo",                # raw_text has no occasion / style cue
    "length_violation",           # raw_text outside 80-200 char spec
    "rating_sentiment_mismatch",  # rating=5 but review tone is negative (or vice-versa)
    "language_issue",             # not fully Korean, gibberish, template leak
)


class AttrGrounded(BaseModel):
    """Per-attribute grounding check for Stage 1.1 synthetic output.

    Stage 1.1 generates `product_attributes = {color, style, size}`; judge
    verifies each attribute value is consistent with / mentioned in the
    synthesised `raw_text` rather than a default / hallucinated value.
    """

    key: str                                  # "color" | "style" | "size"
    value: str
    mentioned_in_text: bool
    plausible_for_product: bool


class Stage1_1JudgeResult(BaseModel):
    """Per-synthetic-record judge output."""

    is_fashion: bool = Field(
        description="True when the generated record is about a clothing / footwear / bag / accessory product."
    )
    title_within_spec: bool = Field(
        description="True when product_title length is roughly 15-30 chars AND does not contain newlines / '→' / '글자'."
    )
    title_format_ok: bool = Field(
        description="True when title follows '브랜드 + 상품종류 + 특징' shape (brand + category + feature)."
    )
    title_has_reasoning_leak: bool = Field(
        description="True when product_title contains the model's self-verification chain (e.g. character-count checking, '다시 조정', arrows)."
    )
    raw_text_within_spec: bool = Field(
        description="True when raw_text length is roughly 80-200 characters and is coherent Korean."
    )
    raw_text_naturalness: int = Field(
        ge=1, le=5,
        description="How naturally written the Korean review is (1=broken, 5=native).",
    )
    persona_reflection: int = Field(
        ge=1, le=5,
        description="How well the review embodies the assigned persona (hobbies/occupation/age/character). 1=ignored, 5=rich reflection.",
    )
    has_tpo_signal: bool = Field(
        description="True when the review mentions at least one occasion / setting / style context (출근, 하객, 등산, 데일리, 등)."
    )
    attributes_grounded: List[AttrGrounded] = Field(
        default_factory=list,
        description="Per-attribute grounding verdict for product_attributes.",
    )
    rating_sentiment_consistent: bool = Field(
        description="True when the review tone matches the star rating (5→positive, 1-2→negative, 3→neutral)."
    )
    failure_modes: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Stage1_1JudgeRecord(BaseModel):
    """Persisted record: echoed synthetic doc + judge verdict."""

    doc_id: str
    product_title: str
    product_attributes: Dict[str, Any]
    raw_text: str
    persona_info: Dict[str, Any] = Field(default_factory=dict)
    rating: Optional[int] = None
    judge: Stage1_1JudgeResult
    judge_model: str
    judge_tokens: Optional[int] = None


class Stage1_1SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_1_1"
    judge_model: str
    provider: str
    n_evaluated: int
    fashion_rate: float
    title_within_spec_rate: float
    title_format_ok_rate: float
    title_reasoning_leak_rate: float
    raw_text_within_spec_rate: float
    avg_raw_text_naturalness: Optional[float]
    avg_persona_reflection: Optional[float]
    has_tpo_rate: float
    attr_grounded_rate: Optional[float]   # fraction of (record, attr) where grounded
    rating_sentiment_consistent_rate: float
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""


# ===========================================================================
# STAGE 1.1.5 - dedup effectiveness (LLM dedup-miss finder)
# ===========================================================================
# The dedup stage (fuzzy / exact / semantic) has already run. We show the
# judge the SURVIVING records and ask which of them still look like
# near-duplicates of each other. Anything flagged = dedup miss.
#
# Unlike other stages this is ONE call per judge for the whole set, not
# per-record.

STAGE_1_1_5_FAILURE_MODES = (
    "near_duplicate_missed",    # a group of records that should have been dedup-collapsed
    "low_dedup_reduction",      # reduction_rate well below what a judge would have picked
    "wrong_removal",            # a dedup candidate that shouldn't have been collapsed (informational)
)


class NearDuplicateGroup(BaseModel):
    """A set of doc_ids the judge believes are semantically equivalent."""

    doc_ids: List[str] = Field(
        description="Doc IDs from the deduped set; len >= 2."
    )
    reason: str = Field(
        default="",
        description="Short justification (e.g. 'both praise the tweed jacket for a wedding').",
    )
    severity: str = Field(
        default="medium",
        description="'low' | 'medium' | 'high' — how clearly the group should have collapsed.",
    )


class Stage1_1_5JudgeResult(BaseModel):
    """Judge verdict for the whole deduped set (one JSON per judge model)."""

    near_duplicate_groups: List[NearDuplicateGroup] = Field(default_factory=list)
    dedup_in_count: int = Field(description="records shown in the 'before' set (Stage 1.1 synthetic)")
    dedup_out_count: int = Field(description="records shown in the 'after' set (Stage 1.1.5 output)")
    dedup_miss_count: int = Field(
        description="sum of (group.size - 1) across near_duplicate_groups",
    )
    reasoning: str = ""


class Stage1_1_5JudgeRecord(BaseModel):
    """Persisted record: one per (iter, judge_model)."""

    stage: str = "stage_1_1_5"
    dedup_in_count: int
    dedup_out_count: int
    judge: Stage1_1_5JudgeResult
    judge_model: str
    judge_tokens: Optional[int] = None


class Stage1_1_5SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_1_1_5"
    judge_model: str
    provider: str
    dedup_in_count: int
    dedup_out_count: int
    dedup_reduction_rate: float       # (in - out) / in
    dedup_miss_count: int
    dedup_miss_rate: float            # miss / out
    largest_miss_cluster_size: int
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""


# ===========================================================================
# STAGE 1.2 - curated document quality (what NeMo Curator leaks downstream)
# ===========================================================================

STAGE_1_2_FAILURE_MODES = (
    "non_fashion_item",     # text is about cosmetics / golf / electronics / …
    "too_short",            # <20 chars of actual content
    "noise_text",           # gibberish, emoji-only, broken
    "pii_leak",             # phone / email / name appears
    "language_issue",       # wrong language declared, mixed garbage
    "duplicate_suspect",    # looks like a duplicate of another doc
)


class Stage1_2JudgeResult(BaseModel):
    """Per-curated-doc judge output."""

    is_fashion: bool = Field(
        description="True if the text is clearly about clothing / footwear / bags / accessories."
    )
    has_tpo_signal: bool = Field(
        description="True if the text contains at least a hint of a TPO/style context."
    )
    text_quality: int = Field(
        ge=1, le=5,
        description="Overall usefulness for downstream extraction (5=rich, 1=useless).",
    )
    language: str = Field(
        description="Detected dominant language: 'ko' | 'en' | 'mixed' | 'other'."
    )
    noise_level: str = Field(
        description="'none' | 'low' | 'medium' | 'high'"
    )
    pii_leak: bool = False
    failure_modes: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Stage1_2JudgeRecord(BaseModel):
    """Persisted record: echoed curated doc + judge verdict."""

    curated_id: str
    clean_text: str
    rating: Optional[int] = None
    source_type: Optional[str] = None
    judge: Stage1_2JudgeResult
    judge_model: str
    judge_tokens: Optional[int] = None


class Stage1_2SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_1_2"
    judge_model: str
    provider: str
    n_evaluated: int
    fashion_rate: float
    has_tpo_rate: float
    avg_text_quality: Optional[float]
    pii_rate: float
    noise_hist: Dict[str, int]
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""


# ===========================================================================
# STAGE 2.1 - per-doc intent/attribute extraction
# ===========================================================================

STAGE_2_1_FAILURE_MODES = (
    "hallucinated_intent",
    "product_type_as_intent",
    "subjective_attribute_value",
    "noise_attribute_value",
    "missed_tpo",
    "general_wear_with_attrs",   # R2 violation: general_wear but attrs set
    "sentiment_rating_mismatch",
    "language_issue",
)


class AttrJudge(BaseModel):
    """Judge verdict for a single extracted attribute key."""

    present_in_text: bool
    groundedness: Optional[int] = Field(default=None, description="1-5 or null")
    concrete: Optional[bool] = Field(
        default=None,
        description="True if concrete product attribute; False if subjective/vague.",
    )


class Stage2_1JudgeResult(BaseModel):
    intent_groundedness: int = Field(ge=1, le=5)
    intent_type_valid: bool
    general_wear_false_negative: Optional[bool] = None
    attributes: Dict[str, AttrJudge]
    failure_modes: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Stage2_1JudgeRecord(BaseModel):
    source_curated_id: str
    review_text: str
    rating: Optional[int] = None
    raw_intent: str
    extracted_attributes: Dict[str, Optional[str]]
    extracted_sentiment: str
    judge: Stage2_1JudgeResult
    sentiment_rating_agreement: Optional[bool] = None
    sentiment_rating_reason: str = ""
    judge_model: str
    judge_tokens: Optional[int] = None


class Stage2_1SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_2_1"
    judge_model: str
    provider: str
    n_evaluated: int
    avg_intent_groundedness: Optional[float]
    intent_type_valid_rate: float
    general_wear_rate: float
    general_wear_false_negative_rate: Optional[float]
    sentiment_rating_agreement_rate: Optional[float]
    attribute_concrete_rate: Dict[str, Optional[float]]
    attribute_groundedness_avg: Dict[str, Optional[float]]
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""


# ===========================================================================
# STAGE 2.2 - cluster coherence + canonical naming
# ===========================================================================

STAGE_2_2_FAILURE_MODES = (
    "heterogeneous_cluster",        # members span different TPOs
    "wrong_canonical",              # canonical doesn't represent members
    "non_korean_canonical",         # canonical violates Korean-output rule
    "too_broad_canonical",          # canonical is vague ("룩", "기타")
    "should_split",                 # judge thinks cluster must split
    "duplicate_with_other",         # canonical duplicates another cluster's
)


class Stage2_2JudgeResult(BaseModel):
    """Per-cluster verdict."""

    cluster_coherent: bool
    canonical_fit: int = Field(ge=1, le=5)
    canonical_language_ok: bool
    should_split: bool
    split_suggestion: List[List[str]] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Stage2_2JudgeRecord(BaseModel):
    cluster_id: str
    canonical_name: str
    raw_intents: List[str]
    member_count: int
    judge: Stage2_2JudgeResult
    judge_model: str
    judge_tokens: Optional[int] = None


class DuplicateCanonicalPair(BaseModel):
    """Cross-cluster duplicate hit (informational; judge did pairwise check)."""

    canonical_a: str
    canonical_b: str
    confidence: int = Field(ge=1, le=5)
    reason: str = ""


class Stage2_2SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_2_2"
    judge_model: str
    provider: str
    n_clusters: int
    coherent_rate: float
    avg_canonical_fit: Optional[float]
    non_korean_canonical_count: int
    should_split_count: int
    duplicate_pairs_found: int
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""


# ===========================================================================
# STAGE 2.3 - final aggregated attributes per canonical intent
# ===========================================================================

STAGE_2_3_FAILURE_MODES = (
    "subjective_value",                 # a top-K value is an adjective
    "noise_value",                      # a top-K value is "...", empty-ish
    "duplicate_values",                 # e.g. "린넨" and "linen" both present
    "wrong_attribute_for_intent",       # intent=운동복 + material=tweed
    "low_evidence_high_weight",         # evidence_count<3 but weight>=0.8
    "non_fashion_intent",               # intent itself is not a clothing TPO
)


class MappedAttrJudge(BaseModel):
    """Per mapped attribute verdict inside an AnalyzedIntent."""

    key: str  # material | fit | color | style | season
    value: str
    weight: float
    concrete: bool
    fits_intent: bool
    duplicate_suspect: Optional[str] = Field(
        default=None,
        description="If this value duplicates another (e.g. 'linen' vs '린넨'), set to the duplicate string.",
    )


class Stage2_3JudgeResult(BaseModel):
    overall_usefulness: int = Field(ge=1, le=5)
    attributes: List[MappedAttrJudge]
    evidence_reliable: bool
    failure_modes: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Stage2_3JudgeRecord(BaseModel):
    intent_keyword: str
    total_evidence_count: int
    mapped_attributes: List[Dict[str, Any]]  # echoed raw for worst-K rendering
    judge: Stage2_3JudgeResult
    judge_model: str
    judge_tokens: Optional[int] = None


class Stage2_3SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_2_3"
    judge_model: str
    provider: str
    n_intents: int
    avg_overall_usefulness: Optional[float]
    attr_concrete_rate: float
    attr_fits_intent_rate: float
    duplicate_value_count: int
    evidence_reliable_rate: float
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""


# ===========================================================================
# STAGE 2.4 - natural-language query expansion per canonical intent
# ===========================================================================
# Stage 2.4 (`pipelines.stage_2_4_expand`) turns one canonical intent like
# "하객룩" into N realistic chatbot user queries. This judge verifies that
# the queries sound like real users, don't parrot the canonical name, and
# weave in the mapped attributes naturally (without listing them all).

STAGE_2_4_FAILURE_MODES = (
    "canonical_name_repeat",       # queries parrot the canonical (e.g. "하객룩 추천" × 5)
    "low_query_diversity",         # queries are near-duplicates of one another
    "unnatural_korean",            # broken grammar, awkward phrasing, unnatural chatbot tone
    "attribute_overlisting",       # every attribute dumped into one sentence (unnatural)
    "attribute_ungrounded",        # query uses an attribute not in mapped_attributes and not plausible
    "not_korean",                  # query is not Korean (English leak, Chinese chars)
    "garbled_output",              # obvious token corruption (e.g. "몇enaar")
    "wrong_intent",                # query doesn't fit the canonical intent at all
    "too_generic",                 # query gives no useful retrieval signal
    "product_listing",             # query reads like a product listing not a user question
)


class QueryJudge(BaseModel):
    """Verdict for one natural-language query."""

    query: str
    natural_korean: bool
    repeats_canonical: bool
    fits_intent: bool
    language_ok: bool = True            # Korean only, no code/English bleed
    garbled: bool = False               # broken tokens
    style: str = Field(
        default="unknown",
        description="one of 'question' | 'command' | 'descriptive' | 'mixed' | 'unknown'",
    )


class Stage2_4JudgeResult(BaseModel):
    """Per-canonical verdict for its full set of natural_queries."""

    queries: List[QueryJudge]
    query_diversity: int = Field(
        ge=1, le=5,
        description="1=near-identical, 3=some paraphrase variety, 5=clearly distinct intents/styles.",
    )
    attribute_weaving: int = Field(
        ge=1, le=5,
        description="How naturally mapped_attributes are woven into queries (1=not used / overlisted; 5=subtle, partial).",
    )
    canonical_coverage: int = Field(
        ge=1, le=5,
        description="How well the query set covers the scope of the canonical intent (1=narrow facet only; 5=multi-facet).",
    )
    overall_usefulness: int = Field(
        ge=1, le=5,
        description="Would these queries usefully expand a retrieval index for this canonical? (5 = production-quality)",
    )
    failure_modes: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Stage2_4JudgeRecord(BaseModel):
    """Persisted record: echoed ExpandedIntent + judge verdict."""

    intent_keyword: str
    mapped_attributes: List[Dict[str, Any]]   # echoed for worst-K rendering
    natural_queries: List[str]
    total_evidence_count: int
    judge: Stage2_4JudgeResult
    judge_model: str
    judge_tokens: Optional[int] = None


class Stage2_4SummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str
    stage: str = "stage_2_4"
    judge_model: str
    provider: str
    n_intents: int
    n_queries_total: int
    avg_query_diversity: Optional[float]
    avg_attribute_weaving: Optional[float]
    avg_canonical_coverage: Optional[float]
    avg_overall_usefulness: Optional[float]
    per_query_natural_rate: float            # fraction of queries judged naturally-Korean
    per_query_fits_intent_rate: float
    canonical_repeat_rate: float             # fraction of queries that parrot canonical name
    garbled_count: int
    failure_modes: Dict[str, int]
    duration_sec: float
    tag: str = ""
