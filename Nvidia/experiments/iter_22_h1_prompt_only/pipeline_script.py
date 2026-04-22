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
    """Loads, filters for fashion, and samples seed data."""
    print("\nStep 1: Loading & Filtering Fashion Seed Data (Stage 1.0)")
    
    # Load raw TSV
    df = pd.read_csv(data_path, sep="\t", header=None, names=["rating", "text"])
    df = df.dropna(subset=["text"])
    
    # Apply Fashion Filter
    mask = df["text"].str.contains("|".join(FASHION_KEYWORDS), na=False)
    fashion_df = df[mask].copy().reset_index(drop=True)
    
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

    # A2. H4v2: sample rating uniformly from 1..5. The raw Naver corpus
    # has NO rating=3 rows (verified: 0 rating-3 reviews in ~200k total),
    # so seed-side stratification (H4v1 iter_06) cannot produce them.
    # Detach synthetic rating from seed_rating entirely and assign it
    # via a category sampler. The review_prompt below is updated to
    # reference {{ rating }} (not seed_rating) so sentiment matches.
    builder.add_column(
        name="rating",
        column_type="sampler",
        sampler_type="category",
        params={"values": [1, 2, 3, 4, 5]},
    )
    
    # B. Generate Product Title
    # H1 (iter_01 validated, retested here alone): rewrite prompt to
    # discourage char-count self-verification and reasoning leakage.
    # iter_01 dropped leak 0.473 → 0.12 just from this prompt; we
    # stack it on iter_17's proven combo (H3 regex + H12 post-gen
    # filter + rest) WITHOUT the iter_18/20 prose-fallback + min-10
    # filter changes that collapsed title_format_ok_rate.
    title_prompt = """리뷰를 보고 해당 패션 상품의 제목을 한 줄로만 작성하세요.

[리뷰]: {{ seed_review }}

좋은 예시 (이 형식 그대로):
- 유니클로 오버핏 니트 스웨터
- 자라 슬림핏 블랙 청바지
- 무신사 기본 면 티셔츠
- H&M 플리츠 미디 원피스

절대 하지 말 것:
- 글자수 세기나 "(18자)" 같은 표기
- 수정 사항, 설명, 주석, 번호 매기기
- 여러 줄 출력 (줄바꿈 금지)
- 이유, 근거, 분석 등 reasoning 출력
- "브랜드명이 제공되지 않았다" 같은 meta-comment
- 리뷰 내용에 대한 평가나 판단

출력은 한국어 상품명 한 줄만. 다른 텍스트 금지."""

    builder.add_column(
        name="product_title",
        column_type="llm-text",
        model_alias=config.llm_model,
        prompt=title_prompt
    )
    
    # C. Generate Product Attributes (Structured JSON Output)
    # H5v2: attack mode collapse on style/color BUT don't over-correct.
    # iter_04 H5v1 said "한 가지 값(예: 캐주얼, 화이트)에 편중되지 마라"
    # — the model interpreted that too literally and ELIMINATED
    # 화이트/블랙 entirely (color_white_black_share went 0.72 → 0.0).
    # v2 rewords: focus on "fit to product+persona" not "avoid the
    # frequent colors". 화이트/블랙 remain valid choices if the product
    # is actually white/black.
    attr_prompt = """아래 상품과 페르소나에 어울리는 세부 속성을 JSON으로 출력하세요.

[상품]: {{ product_title }}
[참고 리뷰]: {{ seed_review }}
[페르소나 나이]: {{ age }}세
[페르소나 직업]: {{ occupation }}
[페르소나 성별]: {{ sex }}

속성 가이드라인:
- color: 한국어 구체 색상명. 아래 모두 사용 가능하다 (화이트/블랙도 정당한 선택이다).
  블랙, 화이트, 네이비, 그레이, 차콜, 베이지, 카멜, 브라운, 카키, 올리브,
  머스터드, 크림, 아이보리, 레드, 와인, 버건디, 핑크, 민트, 민트그린,
  블루, 스카이블루, 인디고, 라벤더, 퍼플, 플럼, 옐로우
- style: 상품과 페르소나에 어울리는 스타일.
  캐주얼, 미니멀, 스트릿, 포멀, 스포티, 클래식, 로맨틱, 빈티지, 프레피,
  시크, 페미닌, 아메카지, 워크웨어, Y2K, 아웃도어
- size: 상품 카테고리에 맞는 사이즈.
  S, M, L, XL, XXL, FREE, 85, 90, 95, 100, 105, 110,
  225, 230, 235, 240, 245, 250, 255, 260, 265, 270

선택 원칙:
1. 상품명과 [참고 리뷰]에 명시된/암시된 속성을 우선 반영하라.
2. 상품 카테고리가 신발이면 size는 숫자 사이즈, 상의/하의면 S-XL, FREE는
   원사이즈 상품에만.
3. 페르소나 연령/직업과의 어울림도 고려하라. 70대 무직 노인에게 Y2K 같은
   극단 선택을 굳이 붙이지 마라.

JSON 외 텍스트 금지."""

    builder.add_column(
        name="product_attributes",
        column_type="llm-structured",
        model_alias=config.llm_model,
        prompt=attr_prompt,
        output_format=ProductAttributes
    )

    # D. Generate Personalized Review
    # H8 + H11: persona binding AND attribute mention.
    # iter_11 showed H8 lifts persona_reflection 3.62 → 4.63 but drags
    # attr_grounded 0.51 → 0.35 because reviews now focus heavily on
    # persona context at the expense of mentioning product color/style/
    # size. H11 fixes that by requiring the review to explicitly name
    # the product's color and size (style is often implicit, so lighter
    # requirement on that).
    review_prompt = """당신은 아래 페르소나의 입장에서 이 패션 상품을 직접 사용해본 리뷰를 작성합니다.

[페르소나]
- 나이: {{ age }}세
- 성별: {{ sex }}
- 직업: {{ occupation }}
- 거주지: {{ province }} {{ district }}
- 성격: {{ persona }}
- 취미: {{ hobbies_and_interests }}

[상품]
- 상품명: {{ product_title }}
- 속성: {{ product_attributes }}

[참고할 진짜 리뷰 톤]: '{{ seed_review }}' (원본 {{ seed_rating }}점)
[당신의 평점]: {{ rating }}점

[규칙]
1. 한국어 한 문단 (60-140자). 여러 줄/번호 목록 금지.
2. 반드시 **color / style / size 세 속성을 모두 자연스럽게 리뷰에 언급**하라:
   - color 값(예: 베이지, 네이비): 반드시 해당 단어 그대로 포함.
   - size 값(예: M, FREE, 260): "M 사이즈가", "FREE 사이즈", "260 꼭 맞고"
     처럼 실제 피팅 맥락으로 언급.
   - style: 스타일 단어(예: 클래식, 미니멀, 스포티)를 문장에 녹이기.
3. 반드시 다음 페르소나 정보 중 **2개 이상**을 구체적으로 언급하라:
   - 취미 (예: "탄천 산책", "관악산 등산", "홈메이드 파스타")
   - 직업 맥락 (예: "회계 사무원 출근복으로", "강구조물 가공 작업복 아래")
   - 거주지 (예: "분당 정갈한 동네", "영주 촌에서")
   - 연령대 감성 (예: "70대 시선에는", "30대 직장인의 눈으로")
4. 착용 상황 하나 (출근, 등산, 데이트, 여행, 운동 중 택1).
5. 반드시 {{ rating }}점 평점 감성:
   - 1점: 강한 불만, 반품 의사
   - 2점: 아쉬움 위주 (단점>장점)
   - 3점: 장단점 혼재, 호불호 명확히 언급
   - 4점: 대체로 만족, 작은 아쉬움
   - 5점: 강한 만족, 재구매 의사
6. 리뷰 본문만 출력. 메타 설명/주석/"(N자)" 같은 표기 금지.

좋은 예시:
- "40대 분당 주민인데 탄천 산책길에 들고 가기 편한 베이지 크로스백이에요.
  FREE 사이즈라 체형 상관없이 편하고 미니멀 디자인이 직장인 출근용으로 딱입니다."
- "70대 경북 영주 살면서 고추밭 일하고 입기 좋은 두꺼운 네이비 셔츠입니다.
  L 사이즈가 넉넉해 투박한 손에도 소매가 안 걸리는 워크웨어 스타일이에요."
"""

    builder.add_column(
        name="raw_text",
        column_type="llm-text",
        model_alias=config.llm_model,
        prompt=review_prompt,
        system_prompt="당신은 패션 리뷰 전문가입니다. 주어진 페르소나의 성격, 취미, 성별, 직업에 맞춰 자연스러운 리뷰를 창작하세요. 입력 문장을 그대로 복사하지 마세요."
    )
    
    # E. Samplers & Expressions (rating moved above; synthetic `rating`
    # now comes from the category sampler, not seed_rating.)
    builder.add_column(name="doc_id", column_type="sampler", sampler_type="uuid", params={"prefix": "rv"})
    builder.add_column(name="product_id", column_type="sampler", sampler_type="uuid", params={"prefix": "P_", "short_form": True})
    builder.add_column(name="timestamp", column_type="sampler", sampler_type="datetime", params={"start": "2024-04-21", "end": "2026-04-21", "unit": "s"})
    
    # 4. Execute
    stage = DataDesignerStage(builder, config.llm_base_url, config.llm_api_key, config.generate_size)
    result_df = stage.process(DocumentBatch(task_id="g", dataset_name="f", data=pd.DataFrame())).to_pandas()

    # H3v3: tighter leak regex on top of H3's 30-char hard cap.
    # Analysis of iter_13/14 leaky titles shows patterns the iter_13
    # regex misses:
    #   - "...선물용 29자" (trailing digit+자 without parens)
    #   - "...(165cm 키 추천)" (parenthetical size notes)
    #   - "...28자" or "(28자)"
    #   - "(키 165 기준)"
    # H3v3 adds three more regexes on top of the existing leak suffix +
    # arrow + markdown kills; keeps 30-char hard cap (iter_13's H3).
    _LEAK_SUFFIX_RE = re.compile(r"\s*[\(\[]\s*\d+\s*자\s*[\)\]]\s*$")
    _LEAK_BARE_CHARCOUNT_RE = re.compile(r"\s+\d+\s*자\s*$")  # no parens
    _LEAK_PAREN_SIZE_NOTE_RE = re.compile(
        r"\s*\([^\)]*(?:cm|키|기준|추천|권장|size|사이즈)[^\)]*\)\s*$",
        re.IGNORECASE,
    )
    _ARROW_RE = re.compile(r"\s*(?:→|->|=>)\s*.*$", re.DOTALL)
    _MARKDOWN_META_RE = re.compile(r"\s*\*\*[^*]+\*\*.*$", re.DOTALL)

    def _clean_title(raw: Any) -> str:
        if not isinstance(raw, str):
            return ""
        s = raw.strip()
        # First non-empty line only.
        for line in s.splitlines():
            line = line.strip()
            if line:
                s = line
                break
        # Kill reasoning-chain tails first.
        s = _ARROW_RE.sub("", s)
        s = _MARKDOWN_META_RE.sub("", s)
        # Kill char-count annotations (with and without parens).
        s = _LEAK_SUFFIX_RE.sub("", s)
        s = _LEAK_BARE_CHARCOUNT_RE.sub("", s)
        # Kill parenthetical size/추천/키 notes at end.
        s = _LEAK_PAREN_SIZE_NOTE_RE.sub("", s)
        # Strip markdown emphasis wrappers.
        s = s.strip("*_`\"' ").strip()
        # Cap to 30 chars — hard stop (matches iter_13 H3 original).
        if len(s) > 30:
            s = s[:30]
        return s.strip()

    if "product_title" in result_df.columns:
        result_df["product_title"] = result_df["product_title"].map(_clean_title)

    # H12: post-gen fashion filter. Some synthetic records have
    # non-fashion product_titles (e.g. "신발 정리함 2단", "옷걸이 세트")
    # because the seed review mentioned a fashion-adjacent object even
    # though the product is not apparel. Drop those after generation.
    # Also drops records with empty / fallback titles from H3v2+ regex.
    _POST_GEN_EXCLUDE = [
        "정리함", "정리대", "수납함", "보관함", "신발장", "옷걸이", "행거", "선반",
        "세탁볼", "세탁망", "세제", "린스", "탈취제", "향수",
        "드라이기", "고데기", "면도기",
        "기저귀", "13개월", "아기옷", "베이비",
    ]

    def _is_fashion_title(t: Any) -> bool:
        if not isinstance(t, str) or not t.strip():
            return False
        if t.strip() == "패션 상품":  # fallback from H3v2 sanity regex
            return False
        for bad in _POST_GEN_EXCLUDE:
            if bad in t:
                return False
        return True

    before = len(result_df)
    result_df = result_df[result_df["product_title"].apply(_is_fashion_title)].reset_index(drop=True)
    dropped = before - len(result_df)
    print(
        f"  [H12 post-gen fashion filter] dropped {dropped} non-fashion "
        f"records, kept {len(result_df)}."
    )

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
    """Applies Korean-aware quality filters to ensure text quality.

    H9: the baseline used `NonAlphaNumericFilter(max=0.85)` which treats
    Hangul codepoints as non-alphanumeric. ~99% of Korean reviews were
    dropped as a result (iter_00 e2e retention = 0). Replace with:
      - min 20 Hangul characters (keeps only substantive Korean text)
      - max 500 chars (drops runaway reasoning leaks)
      - drop empty / non-string records
    WordCountFilter is removed too — Korean has no whitespace-separated
    word boundaries, so `min_words=5` was arbitrary anyway.
    """
    print("\nStep 4: Quality Filtering (Stage 1.2)")
    before = len(df)
    HANGUL_RE = re.compile(r"[\u3131-\u318E\uAC00-\uD7A3]")

    def _ok(txt):
        if not isinstance(txt, str):
            return False
        s = txt.strip()
        if not s:
            return False
        if len(s) > 500:
            return False
        if len(HANGUL_RE.findall(s)) < 20:
            return False
        return True

    mask = df[config.text_field].apply(_ok)
    filtered_df = df[mask].reset_index(drop=True)
    print(
        f"  After Korean-aware quality filter: {len(filtered_df)} records "
        f"(dropped {before - len(filtered_df)})."
    )
    return filtered_df

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
