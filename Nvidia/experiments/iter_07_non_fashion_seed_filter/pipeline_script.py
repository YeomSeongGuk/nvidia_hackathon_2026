# /// script
# requires-python = ">=3.10"
# dependencies = ["nemo-curator>=1.1.0", "pandas", "pyarrow", "data-designer", "openai", "httpx", "pydantic", "datasets", "ray"]
# ///

"""
NeMo Curator Data Pipeline: Personalized Fashion Reviews
-------------------------------------------------------
This script implements a comprehensive stage-based pipeline:
1. Stage 1.0: Extract & Filter Fashion Seed Data (Naver reviews).
2. Stage 1.1: Generate Personalized Synthetic Data (Korean Personas + LLM).
   - Generates product titles and attributes.
   - Generates contextual reviews based on personas.
3. Stage 1.1.5: Fuzzy Deduplication (with fallback to exact dedup).
4. Stage 1.2: Quality Filtering using NeMo Curator heuristic filters.
"""

import os
import json
import random
import re
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import httpx
from pydantic import BaseModel
from datasets import load_dataset

from nemo_curator.stages.base import ProcessingStage


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED LLM OUTPUT
# ============================================================================

class ProductAttributes(BaseModel):
    """Product attributes schema for structured LLM output."""
    color: str      # 颜色 (e.g., "블랙", "화이트", "네이비")
    style: str      # 스타일 (e.g., "캐주얼", "포멀", "스트릿")
    size: str       # 사이즈 (e.g., "S", "M", "L", "FREE")
from nemo_curator.tasks import DocumentBatch
from data_designer.config import custom_column_generator

# ============================================================================
# 1. CONFIGURATION
# ============================================================================

@dataclass
class PipelineConfig:
    """Global configuration for the data pipeline."""
    seed_data_size: int = 50
    generate_size: int = 30
    
    # Directory settings
    stage_1_0_dir: str = "data/stage_1_0"
    stage_1_1_dir: str = "data/stage_1_1"
    stage_1_1_5_dir: str = "data/stage_1_1_5"
    stage_1_2_dir: str = "data/stage_1_2"
    cache_dir: str = "cache"
    
    # LLM configuration (Friendli AI)
    llm_api_key: str = "dummy"
    #llm_base_url: str = "https://api.friendli.ai/dedicated/v1"
    #llm_model: str = "depc5orithvevxj"
    llm_base_url: str = "http://localhost:5000/v1"
    llm_model: str = "nemotron"
    
    # Other settings
    text_field: str = "raw_text"
    random_seed: int = 42

FASHION_KEYWORDS = [
    "바지", "셔츠", "원피스", "자켓", "코트", "니트", "블라우스", "치마", "신발", 
    "가방", "옷", "착용", "스타일", "청바지", "니트", "슬랙스", "패딩", 
    "점퍼", "가디건", "원피스", "구두", "운동화", "샌들", "슬리퍼", "백팩"
]

# H7: 2-layer fashion filter. The baseline include-list alone lets
# non-fashion products slip through because words like "신발" appear
# inside product-adjacent strings (e.g. "신발 정리 수납함", "신발장").
# EXCLUDE_KEYWORDS rejects those rows.
FASHION_EXCLUDE_KEYWORDS = [
    # Storage / organizer accessories
    "정리함", "정리 박스", "정리 바구니", "수납함", "수납 박스", "보관함",
    "정리 수납", "선반", "신발장", "옷장 정리", "옷걸이", "행거",
    # Cleaning / maintenance
    "세탁볼", "세탁망", "섬유 탈취", "섬유탈취",
    "세제", "린스", "탈취제", "방향제", "향수",
    # Tools / unrelated
    "드라이기", "고데기", "면도기",
    # Pet / baby / non-apparel "가방"s
    "기저귀 가방", "유아용", "반려견 가방",
]

# ============================================================================
# 2. UTILITY FUNCTIONS
# ============================================================================

def save_to_jsonl(df: pd.DataFrame, path: str, text_field: str):
    """Saves DataFrame to JSONL with consistent hackathon schema."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for _, r in df.iterrows():
            # Build persona_info dictionary dynamically
            persona_info = {
                "age": r.get("age"),
                "sex": r.get("sex"),
                "occupation": r.get("occupation"),
                "province": r.get("province"),
                "district": r.get("district"),
                "character": r.get("persona"),
                "hobbies": r.get("hobbies_and_interests")
            }
            persona_info = {k: v for k, v in persona_info.items() if v is not None}
            
            # Handle product_attributes JSON parsing
            attrs = r.get("product_attributes", {})
            if isinstance(attrs, str):
                try:
                    attrs = json.loads(attrs)
                except (json.JSONDecodeError, TypeError):
                    pass

            record = {
                "source_type": "review",
                "doc_id": r.get("doc_id", ""),
                "product_title": r.get("product_title", ""),
                "product_attributes": attrs,
                "raw_text": r.get(text_field, ""),
                "product_id": r.get("product_id", ""),
                "timestamp": r.get("timestamp", ""),
                "persona_info": persona_info,
                "metadata": {"rating": int(r.get("rating", 3))}
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ============================================================================
# 3. STAGE 1.0: SEED DATA EXTRACTION
# ============================================================================

def extract_seed_data(data_path: str, config: PipelineConfig) -> pd.DataFrame:
    """Loads, filters for fashion, and samples seed data.

    H7: two-layer keyword filter. Include-only was matching non-apparel
    items whose descriptions happen to contain "신발" or "옷" (e.g. a
    shoe organizer, laundry bag). Adding an exclude-list drops those.
    """
    print("\nStep 1: Loading & Filtering Fashion Seed Data (Stage 1.0) [H7 2-layer]")

    # Load raw TSV
    df = pd.read_csv(data_path, sep="\t", header=None, names=["rating", "text"])
    df = df.dropna(subset=["text"])

    # Include filter
    include_mask = df["text"].str.contains("|".join(FASHION_KEYWORDS), na=False)
    # Exclude filter (reject any row that contains an excluded term)
    exclude_mask = df["text"].str.contains("|".join(FASHION_EXCLUDE_KEYWORDS), na=False)

    fashion_df = df[include_mask & (~exclude_mask)].copy().reset_index(drop=True)
    print(
        f"  Include matches: {int(include_mask.sum())}  "
        f"Exclude drops: {int((include_mask & exclude_mask).sum())}  "
        f"After 2-layer filter: {len(fashion_df)}"
    )

    # Sample seeds
    random.seed(config.random_seed)
    seed_df = fashion_df.sample(
        n=min(len(fashion_df), config.seed_data_size),
        random_state=config.random_seed
    ).reset_index(drop=True)

    # Save intermediate
    os.makedirs(config.stage_1_0_dir, exist_ok=True)
    seed_df.to_json(
        os.path.join(config.stage_1_0_dir, "seed_data.jsonl"),
        orient="records", lines=True, force_ascii=False
    )
    return seed_df

# ============================================================================
# 4. STAGE 1.1: SYNTHETIC GENERATION
# ============================================================================

class NaverContextParams(BaseModel):
    """Parameters for the custom review context injector."""
    reviews: list[dict[str, Any]]

@custom_column_generator(side_effect_columns=["seed_review", "seed_rating"])
def inject_naver_review(row, generator_params: NaverContextParams):
    """Injects a random Naver review as context for the persona."""
    selected = random.choice(generator_params.reviews)
    row_dict = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
    row_dict["naver_context"] = True
    row_dict["seed_review"] = selected["text"]
    row_dict["seed_rating"] = selected["rating"]
    return row_dict

class DataDesignerStage(ProcessingStage):
    """NeMo Curator ProcessingStage wrapper for Data-Designer."""
    def __init__(self, config_builder, llm_base_url, llm_api_key, generate_size):
        super().__init__()
        self.config_builder = config_builder
        self.llm_base_url = llm_base_url
        self.llm_api_key = llm_api_key
        self.generate_size = generate_size

    def process(self, batch: DocumentBatch) -> DocumentBatch:
        from data_designer.interface.data_designer import DataDesigner
        from data_designer.config.models import ModelProvider
        
        provider = ModelProvider(
            name="friendli", 
            endpoint=self.llm_base_url, 
            api_key=self.llm_api_key, 
            provider_type="openai",
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        
        designer = DataDesigner(model_providers=[provider])
        results = designer.preview(
            config_builder=self.config_builder, 
            num_records=self.generate_size
        )
        return DocumentBatch(
            task_id=batch.task_id, 
            dataset_name=batch.dataset_name, 
            data=results.dataset
        )

def run_data_designer_stage(seed_df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Orchestrates the LLM generation of personalized fashion reviews."""
    print("\nStep 2: Generating Personalized Fashion Synthetic Data (Stage 1.1)")
    
    import data_designer.config as dd
    from data_designer.config.models import ModelConfig, ChatCompletionInferenceParams
    
    # 1. Load Persona Data
    try:
        persona_ds = load_dataset("nvidia/Nemotron-Personas-Korea", split="train")
        persona_df = persona_ds.select(range(min(len(persona_ds), config.generate_size * 10))).to_pandas()
    except Exception as e:
        print(f"[Warning] Hub loading failed ({e}). Using dummy personas.")
        persona_df = pd.DataFrame([{
            'age': 30, 'sex': 'Female', 'occupation': 'Designer', 
            'province': 'Seoul', 'district': 'Gangnam', 'persona': 'Fashionista', 
            'hobbies_and_interests': 'Shopping'
        }] * config.generate_size)
    
    # 2. LLM Config (max_parallel_requests=32 to respect rate limits)
    model_config = ModelConfig(
        alias=config.llm_model, 
        model=config.llm_model, 
        provider="friendli", 
        skip_health_check=True, 
        inference_parameters=ChatCompletionInferenceParams(
            temperature=0.8, 
            max_tokens=500, 
            max_parallel_requests=32,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
    )
    
    builder = dd.DataDesignerConfigBuilder(model_configs=[model_config])
    builder.with_seed_dataset(dd.DataFrameSeedSource(df=persona_df))
    
    # 3. Setup Data-Designer Schema
    
    # A. Inject Naver Seed Context
    builder.add_column(
        name="naver_context", 
        column_type="custom", 
        generator_function=inject_naver_review, 
        generator_params=NaverContextParams(reviews=seed_df.to_dict(orient="records"))
    )
    
    # B. Generate Product Title
    title_prompt = """리뷰 내용을 참고하여 해당 패션 상품의 제목을 생성하세요.

[리뷰 내용]: {{ seed_review }}

요구사항:
1. 반드시 한국어로 작성
2. 브랜드명 + 상품 종류 + 특징 형식 (예: "유니클로 오버핏 니트 스웨터", "자라 슬림핏 청바지")
3. 15-30자 이내
4. 상품 제목만 출력 (설명 없이)"""

    builder.add_column(
        name="product_title",
        column_type="llm-text",
        model_alias=config.llm_model,
        prompt=title_prompt
    )
    
    # C. Generate Product Attributes (Structured JSON Output)
    attr_prompt = """For the fashion product '{{ product_title }}', provide attributes.
Color should be in Korean (e.g., 블랙, 화이트, 네이비).
Style should describe the fashion style (e.g., 캐주얼, 포멀, 스트릿).
Size should be a standard size (e.g., S, M, L, XL, FREE)."""

    builder.add_column(
        name="product_attributes",
        column_type="llm-structured",
        model_alias=config.llm_model,
        prompt=attr_prompt,
        output_format=ProductAttributes
    )

    # D. Generate Personalized Review
    review_prompt = """당신은 아래 페르소나의 입장에서 패션 상품 리뷰를 작성해야 합니다.

[페르소나 정보]
- 나이: {{ age }}세
- 성별: {{ sex }}
- 직업: {{ occupation }}
- 거주지: {{ province }}
- 성격: {{ persona }}
- 취미: {{ hobbies_and_interests }}

[상품 정보]
- 상품명: {{ product_title }}
- 속성: {{ product_attributes }}

[참고 리뷰]: '{{ seed_review }}' ({{ seed_rating }}점)

[작성 요구사항]
1. 반드시 한국어로 작성
2. 페르소나의 성격, 취미, 직업을 반영한 어투와 관점으로 작성
3. 구매 의도를 포함 (예: 출근용, 데이트용, 운동용, 여행용 등)
4. 20-80자 이내
5. 리뷰 텍스트만 출력 (설명 없이)"""

    builder.add_column(
        name="raw_text",
        column_type="llm-text",
        model_alias=config.llm_model,
        prompt=review_prompt,
        system_prompt="당신은 패션 리뷰 전문가입니다. 주어진 페르소나의 성격, 취미, 성별, 직업에 맞춰 자연스러운 리뷰를 창작하세요. 입력 문장을 그대로 복사하지 마세요."
    )
    
    # E. Samplers & Expressions
    builder.add_column(name="doc_id", column_type="sampler", sampler_type="uuid", params={"prefix": "rv"})
    builder.add_column(name="product_id", column_type="sampler", sampler_type="uuid", params={"prefix": "P_", "short_form": True})
    builder.add_column(name="timestamp", column_type="sampler", sampler_type="datetime", params={"start": "2024-04-21", "end": "2026-04-21", "unit": "s"})
    builder.add_column(name="rating", column_type="expression", expr="{{ seed_rating }}")
    
    # 4. Execute
    stage = DataDesignerStage(builder, config.llm_base_url, config.llm_api_key, config.generate_size)
    result_df = stage.process(DocumentBatch(task_id="g", dataset_name="f", data=pd.DataFrame())).to_pandas()
    
    # 5. Save intermediate
    os.makedirs(config.stage_1_1_dir, exist_ok=True)
    save_to_jsonl(result_df, os.path.join(config.stage_1_1_dir, "synthetic_data.jsonl"), config.text_field)
    return result_df

# ============================================================================
# 5. STAGE 1.1.5: FUZZY DEDUPLICATION
# ============================================================================

def run_fuzzy_deduplication(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Identifies and removes duplicate reviews using MinHash LSH."""
    print("\nStep 3: Fuzzy Deduplication (Stage 1.1.5)")
    try:
        from nemo_curator.stages.deduplication.fuzzy.workflow import FuzzyDeduplicationWorkflow
        from nemo_curator.backends.experimental.ray_actor_pool.executor import RayActorPoolExecutor
        
        # Prepare input parquet
        input_path = os.path.join(config.cache_dir, "fuzzy_input")
        os.makedirs(input_path, exist_ok=True)
        df.to_parquet(os.path.join(input_path, "data.parquet"), index=False)
        
        # Setup workflow
        workflow = FuzzyDeduplicationWorkflow(
            cache_path=os.path.join(config.cache_dir, "fuzzy_cache"),
            output_path=os.path.join(config.stage_1_1_5_dir, "fuzzy_output"),
            input_path=input_path,
            input_filetype="parquet",
            text_field=config.text_field,
            seed=config.random_seed,
            char_ngrams=24,
            num_bands=20,
            minhashes_per_band=13
        )
        
        import ray
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
        
        workflow.run(executor=RayActorPoolExecutor())
        
        # Load removal IDs
        dup_ids_path = os.path.join(config.stage_1_1_5_dir, "fuzzy_output", "IdentifyDuplicatesStage")
        if os.path.exists(dup_ids_path):
            dup_ids = set()
            for f in os.listdir(dup_ids_path):
                if f.endswith(".parquet"):
                    dup_ids.update(pd.read_parquet(os.path.join(dup_ids_path, f))["doc_id"].tolist())
            
            deduped_df = df[~df["doc_id"].isin(dup_ids)].reset_index(drop=True)
            print(f"  Fuzzy Dedup removed {len(df) - len(deduped_df)} duplicates.")
            return deduped_df
        return df
    except Exception as e:
        print(f"[Warning] Fuzzy Dedup fallback (Exact Dedup): {e}")
        return df.drop_duplicates(subset=[config.text_field]).reset_index(drop=True)

# ============================================================================
# 6. STAGE 1.2: QUALITY FILTERING
# ============================================================================

def run_quality_filtering(df: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Applies NeMo Curator filters to ensure text quality."""
    print("\nStep 4: Quality Filtering (Stage 1.2)")
    
    from nemo_curator.stages.text.modules import ScoreFilter
    from nemo_curator.stages.text.filters.heuristic_filter import WordCountFilter, NonAlphaNumericFilter
    
    batch = DocumentBatch(task_id="f", dataset_name="s", data=df)
    
    # Filter definitions
    filters = [
        (WordCountFilter(min_words=5, lang="ko"), "wc"),
        (NonAlphaNumericFilter(max_non_alpha_numeric_to_text_ratio=0.85), "na")
    ]
    
    for f, s in filters:
        batch = ScoreFilter(filter_obj=f, text_field=config.text_field, score_field=s).process(batch)
        print(f"  After {f.__class__.__name__}: {batch.num_items} records.")
    
    return batch.to_pandas().drop(
        columns=[c for c in batch.to_pandas().columns if c.endswith("_score")], 
        errors="ignore"
    )

# ============================================================================
# 7. MAIN ORCHESTRATOR
# ============================================================================

def run_pipeline(data_path: str, seed_size: int = 50, generate_size: int = 30):
    """Main orchestrator for the NeMo Curator Hackathon pipeline."""
    config = PipelineConfig(seed_data_size=seed_size, generate_size=generate_size)
    
    # 1.0 Seed Data
    seed_df = extract_seed_data(data_path, config)
    print(f"[Volume] Stage 1.0 (Seed Data): {len(seed_df):,}")
    
    # 1.1 Synthetic Generation
    synthetic_df = run_data_designer_stage(seed_df, config)
    print(f"[Volume] Stage 1.1 (Synthetic Data): {len(synthetic_df):,}")
    
    # 1.1.5 Fuzzy Dedup
    deduped_df = run_fuzzy_deduplication(synthetic_df, config)
    print(f"[Volume] Stage 1.1.5 (Deduped Data): {len(deduped_df):,}")
    
    # 1.2 Quality Filters
    filtered_df = run_quality_filtering(deduped_df, config)
    print(f"[Volume] Stage 1.2 (Filtered Results): {len(filtered_df):,}")
    
    # Save Final
    save_to_jsonl(
        filtered_df, 
        os.path.join(config.stage_1_2_dir, "processed_reviews.jsonl"), 
        config.text_field
    )
    print(f"\nPipeline Complete. Final results in {config.stage_1_2_dir}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NeMo Curator Personalized Fashion Review Pipeline")
    parser.add_argument("--data-path", default="data/naver_shopping.txt", help="Input TSV path")
    parser.add_argument("--generate-size", type=int, default=5, help="Number of records to generate")
    
    args = parser.parse_args()
    run_pipeline(data_path=args.data_path, generate_size=args.generate_size)
