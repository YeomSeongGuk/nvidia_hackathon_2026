"""Local debugging harness for Stage 1.1 (Data Designer synthetic generation).

Runs the exact same Data Designer config the team's `data_pipeline_nemo.py`
uses, but standalone (no NeMo Curator ProcessingStage wrapper), pointing at
a port-forwarded vLLM server. Purpose: observe what `designer.preview()`
actually returns so we can explain why `product_title` and `raw_text` end
up as empty strings in the team's JSONL output.

Prereq:
    brev port-forward coupang -p 5000:5000
    cd /Users/sgyeom/Nvidia && source .venv/bin/activate
    python scripts/run_stage1_generator_local.py --generate-size 3

Flags:
    --generate-size   how many synthetic records to generate (default 3)
    --base-url        OpenAI-compatible endpoint (default http://localhost:5000/v1)
    --model           served model id (default nemotron)
    --personas        how many persona rows to load from HF (default 30)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

from data_designer.interface.data_designer import DataDesigner
from data_designer.config.models import (
    ChatCompletionInferenceParams,
    ModelConfig,
    ModelProvider,
)
from data_designer.config import custom_column_generator
import data_designer.config as dd


# ---------------------------------------------------------------------------
# Same ProductAttributes schema as the team pipeline
# ---------------------------------------------------------------------------

class ProductAttributes(BaseModel):
    color: str
    style: str
    size: str


class NaverContextParams(BaseModel):
    reviews: list[dict[str, Any]]


@custom_column_generator(side_effect_columns=["seed_review", "seed_rating"])
def inject_naver_review(row, generator_params: NaverContextParams):
    selected = random.choice(generator_params.reviews)
    row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    row_dict["naver_context"] = True
    row_dict["seed_review"] = selected["text"]
    row_dict["seed_rating"] = selected["rating"]
    return row_dict


# ---------------------------------------------------------------------------
# Seed personas and Naver reviews
# ---------------------------------------------------------------------------

def _load_personas(n: int) -> pd.DataFrame:
    """Try HuggingFace first; fall back to a tiny hand-written set so the
    debug script still runs offline or behind corp SSL."""
    try:
        from datasets import load_dataset

        ds = load_dataset("nvidia/Nemotron-Personas-Korea", split="train")
        return ds.select(range(min(len(ds), n))).to_pandas()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] HF persona load failed: {exc}. Using tiny fallback.")
        return pd.DataFrame(
            [
                {
                    "age": 28,
                    "sex": "여자",
                    "occupation": "디자이너",
                    "province": "서울",
                    "district": "강남구",
                    "persona": "트렌드에 민감한 20대 후반 직장인",
                    "hobbies_and_interests": "주말 브런치, 카페 탐방",
                },
                {
                    "age": 41,
                    "sex": "남자",
                    "occupation": "영업 관리자",
                    "province": "경기",
                    "district": "수원시",
                    "persona": "실용적이고 가성비를 중시하는 40대 가장",
                    "hobbies_and_interests": "주말 등산, 자전거",
                },
                {
                    "age": 22,
                    "sex": "여자",
                    "occupation": "대학생",
                    "province": "부산",
                    "district": "해운대구",
                    "persona": "SNS 공유를 즐기는 활동적인 대학생",
                    "hobbies_and_interests": "카페 투어, 바다 산책",
                },
            ][:n]
        )


def _load_naver_reviews() -> list[dict[str, Any]]:
    path = Path("data/naver_shopping.txt")
    if not path.exists():
        print(f"[warn] {path} not found, using baked-in 2 rows.")
        return [
            {"text": "아주좋아요 바지 정말 좋아서2개 더 구매했어요", "rating": 5},
            {"text": "택배가 엉망이네용", "rating": 2},
        ]
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[:200]:
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        try:
            rating = int(parts[0])
        except ValueError:
            continue
        rows.append({"text": parts[1].strip(), "rating": rating})
    return rows[:20]


# ---------------------------------------------------------------------------
# Prompts (verbatim from the team file)
# ---------------------------------------------------------------------------

TITLE_PROMPT = """리뷰 내용을 참고하여 해당 패션 상품의 제목을 생성하세요.

[리뷰 내용]: {{ seed_review }}

요구사항:
1. 반드시 한국어로 작성
2. 브랜드명 + 상품 종류 + 특징 형식 (예: "유니클로 오버핏 니트 스웨터", "자라 슬림핏 청바지")
3. 15-30자 이내
4. 상품 제목만 출력 (설명 없이)"""

ATTR_PROMPT = """For the fashion product '{{ product_title }}', provide attributes.
Color should be in Korean (e.g., 블랙, 화이트, 네이비).
Style should describe the fashion style (e.g., 캐주얼, 포멀, 스트릿).
Size should be a standard size (e.g., S, M, L, XL, FREE)."""

REVIEW_PROMPT = """당신은 아래 페르소나의 입장에서 패션 상품 리뷰를 작성해야 합니다.

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
4. 80-200자"""


# ---------------------------------------------------------------------------
# Main debug flow
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate-size", type=int, default=3)
    ap.add_argument("--base-url", default="http://localhost:5000/v1")
    ap.add_argument("--api-key", default="dummy")
    ap.add_argument("--model", default="nemotron")
    ap.add_argument("--personas", type=int, default=30)
    ap.add_argument("--dump", default="data/stage_1_1_local/preview.jsonl")
    args = ap.parse_args()

    print(f"[cfg] endpoint={args.base_url}  model={args.model}  n={args.generate_size}")

    # --- 1. Provider + ModelConfig ---------------------------------------
    # Nemotron-Super is a reasoning model; without `enable_thinking=False`
    # it often returns `content=""` while writing its full answer into the
    # `reasoning` channel only. `extra_body.chat_template_kwargs` is the
    # standard way to surface this flag through an OpenAI-compatible client.
    thinking_off = {"chat_template_kwargs": {"enable_thinking": False}}
    provider = ModelProvider(
        name="local-vllm",
        endpoint=args.base_url,
        api_key=args.api_key,
        provider_type="openai",
        extra_body=thinking_off,
    )
    model_config = ModelConfig(
        alias=args.model,
        model=args.model,
        provider="local-vllm",
        skip_health_check=True,
        inference_parameters=ChatCompletionInferenceParams(
            temperature=0.8,
            max_tokens=500,
            max_parallel_requests=1,
            extra_body=thinking_off,
        ),
    )

    # --- 2. Personas + seed reviews -------------------------------------
    personas = _load_personas(args.personas)
    seed_reviews = _load_naver_reviews()
    print(f"[seed] {len(personas)} personas, {len(seed_reviews)} naver reviews")

    # --- 3. Build the same 4-column Data Designer config ----------------
    builder = dd.DataDesignerConfigBuilder(model_configs=[model_config])
    builder.with_seed_dataset(dd.DataFrameSeedSource(df=personas))

    builder.add_column(
        name="naver_context",
        column_type="custom",
        generator_function=inject_naver_review,
        generator_params=NaverContextParams(reviews=seed_reviews),
    )
    builder.add_column(
        name="product_title",
        column_type="llm-text",
        model_alias=args.model,
        prompt=TITLE_PROMPT,
    )
    builder.add_column(
        name="product_attributes",
        column_type="llm-structured",
        model_alias=args.model,
        prompt=ATTR_PROMPT,
        output_format=ProductAttributes,
    )
    builder.add_column(
        name="raw_text",
        column_type="llm-text",
        model_alias=args.model,
        prompt=REVIEW_PROMPT,
    )

    # --- 4. Run preview --------------------------------------------------
    designer = DataDesigner(model_providers=[provider])
    print(f"[run] designer.preview(num_records={args.generate_size}) ...")
    results = designer.preview(config_builder=builder, num_records=args.generate_size)

    # --- 5. Inspect returned object --------------------------------------
    print("\n[inspect] results type:", type(results).__name__)
    print("[inspect] results attrs:", [a for a in dir(results) if not a.startswith("_")])

    dataset = getattr(results, "dataset", None)
    print("[inspect] results.dataset type:", type(dataset).__name__)

    if isinstance(dataset, pd.DataFrame):
        df = dataset
    elif hasattr(dataset, "to_pandas"):
        df = dataset.to_pandas()
    else:
        df = pd.DataFrame(list(dataset))

    print(f"[inspect] columns: {list(df.columns)}")
    print(f"[inspect] shape:   {df.shape}")

    # Show each record compactly; truncate long strings so the terminal
    # stays readable.
    print("\n[records]")
    for i, row in df.iterrows():
        print(f"--- row {i} ---")
        for col in df.columns:
            v = row[col]
            s = repr(v)
            if len(s) > 160:
                s = s[:160] + "..."
            print(f"  {col:<22} = {s}")

    # --- 6. Dump JSONL for downstream inspection -------------------------
    out = Path(args.dump)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for _, row in df.iterrows():
            rec: dict[str, Any] = {}
            for col in df.columns:
                v = row[col]
                try:
                    json.dumps(v, ensure_ascii=False)
                    rec[col] = v
                except TypeError:
                    rec[col] = str(v)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\n[dump] wrote {len(df)} records -> {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
