"""Pydantic schemas for the analyzed-data pipeline.

`CuratedDoc` accepts two equivalent field names per concept via pydantic
`AliasChoices`, so both of these are valid input lines:

    # Stage 1.2 output style (what processed_reviews.jsonl actually uses)
    {"doc_id": "rv_001", "raw_text": "...", "metadata": {"rating": 5}}

    # PoC-era schema
    {"curated_id": "curated_rv_001", "clean_text": "...", "pipeline_metadata": {...}}

`Attributes` also coerces string "null" / "none" / "n/a" / "..." to real
`None` - some LLMs (e.g. GLM-5.1) emit "null" as a string rather than JSON
null, which would otherwise pollute downstream aggregation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


_RATING_TO_QUALITY = {5: 0.95, 4: 0.85, 3: 0.70, 2: 0.60, 1: 0.50}
_NULL_STRINGS = {"null", "none", "n/a", "na", "", "...", "\u2026", "nil"}


def _maybe_none(v: Any) -> Any:
    if isinstance(v, str) and v.strip().lower() in _NULL_STRINGS:
        return None
    return v


class CuratedDoc(BaseModel):
    """A single upstream doc. Tolerant of Stage 1.2's schema."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    curated_id: str = Field(
        validation_alias=AliasChoices("curated_id", "doc_id"),
    )
    clean_text: str = Field(
        validation_alias=AliasChoices("clean_text", "raw_text"),
    )
    pipeline_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("pipeline_metadata", "metadata"),
    )

    @property
    def quality_score(self) -> float:
        """Prefer explicit quality_score; otherwise derive from rating."""
        explicit = self.pipeline_metadata.get("quality_score")
        if explicit is not None:
            try:
                return float(explicit)
            except (TypeError, ValueError):
                pass
        rating = self.pipeline_metadata.get("rating")
        if rating is not None:
            try:
                return _RATING_TO_QUALITY.get(int(rating), 0.70)
            except (TypeError, ValueError):
                pass
        return 1.0


class Attributes(BaseModel):
    material: Optional[str] = None
    fit: Optional[str] = None
    color: Optional[str] = None
    style: Optional[str] = None
    season: Optional[str] = None

    @field_validator("material", "fit", "color", "style", "season", mode="before")
    @classmethod
    def _coerce_nullish(cls, v: Any) -> Any:
        return _maybe_none(v)


class ExtractedIntent(BaseModel):
    """Stage 2.1 output: per-document extraction result."""

    source_curated_id: str
    raw_intent: str
    attributes: Attributes
    sentiment: str  # positive | negative | neutral
    extracted_keywords: List[str] = Field(default_factory=list)
    source_quality_score: float
    llm_meta: Dict[str, Any] = Field(default_factory=dict)


class IntentCluster(BaseModel):
    """Stage 2.2 output: one canonical intent with its variant surface forms."""

    cluster_id: str
    canonical_name: str
    raw_intents: List[str]
    source_curated_ids: List[str]
    member_count: int


class MappedAttribute(BaseModel):
    attribute_key: str  # material | fit | color | style | season
    attribute_value: str
    weight: float


class DataLineage(BaseModel):
    total_evidence_count: int
    source_doc_ids: List[str]


class AnalyzedIntent(BaseModel):
    """Stage 2.3 output: final analyzed data per canonical intent."""

    intent_keyword: str
    mapped_attributes: List[MappedAttribute]
    data_lineage: DataLineage
    last_updated: str


class ExpandedIntent(BaseModel):
    """Stage 2.4 output: each canonical intent expanded with natural-language
    chatbot queries that real users would type (so the retrieval layer can
    match conversational queries to the canonical).
    """

    intent_keyword: str
    natural_queries: List[str] = Field(default_factory=list)
    mapped_attributes: List[MappedAttribute] = Field(default_factory=list)
    data_lineage: DataLineage
    last_updated: str
    expansion_meta: Dict[str, Any] = Field(default_factory=dict)
