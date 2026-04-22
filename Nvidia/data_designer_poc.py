# /// script
# requires-python = ">=3.10"
# dependencies = ["openai", "pandas", "httpx"]
# ///
"""
Data Designer 방식 PoC: Seed Data → 리뷰 생성 → 필드 추출
GPU 환경에서는 NeMo Data Designer + vLLM으로 전환 가능

Flow:
  SamplerColumn (intent, category, season)
  → LLMTextColumn (한국어 패션 리뷰 생성)
  → LLMStructuredColumn (속성 추출)
  → LLMJudgeColumn (품질 평가)
"""
import json
import os
import time
import random
import httpx
from openai import OpenAI
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ── NIM Client ───────────────────────────────────────────
http_client = httpx.Client(verify=False, timeout=60.0)
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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",
    http_client=http_client,
)
MODEL = "nvidia/nemotron-3-nano-30b-a3b"

def call_llm(system: str, user: str, max_tokens: int = 1024) -> str:
    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            return r.choices[0].message.content or ""
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise


# ══════════════════════════════════════════════════════════
# Step 1: SamplerColumn — 결정론적 속성 샘플링
# ══════════════════════════════════════════════════════════
print("=" * 60)
print("Step 1: SamplerColumn — Intent/Category/Season 샘플링")
print("=" * 60)

INTENTS = [
    "하객룩", "출근룩", "데이트룩", "꾸안꾸", "캠퍼스룩",
    "비즈니스캐주얼", "고프코어", "미니멀룩", "여름시원룩", "겨울방한",
]

CATEGORIES = [
    "원피스", "자켓", "코트", "니트", "블라우스",
    "슬랙스", "청바지", "스커트", "가디건", "티셔츠",
    "트렌치코트", "패딩", "트위드자켓", "셔츠", "레깅스",
]

SEASONS = ["봄", "여름", "가을", "겨울"]
GENDERS = ["여성", "남성"]
RATINGS = [1, 2, 3, 4, 5]

# 실제 리뷰에서 seed 텍스트 로드
seed_df = pd.read_json(os.path.join(DATA_DIR, "clothing_reviews.jsonl"), lines=True)
seed_positive = seed_df[seed_df["rating"] >= 4]["text"].tolist()[:20]
seed_negative = seed_df[seed_df["rating"] <= 2]["text"].tolist()[:20]

# 10개 샘플 생성
samples = []
random.seed(42)
for i in range(10):
    samples.append({
        "intent": random.choice(INTENTS),
        "category": random.choice(CATEGORIES),
        "season": random.choice(SEASONS),
        "gender": random.choice(GENDERS),
        "target_rating": random.choice([1, 2, 4, 5]),
    })

print(f"생성할 샘플: {len(samples)}개")
for s in samples:
    print(f"  {s['intent']} / {s['category']} / {s['season']} / {s['gender']} / {s['target_rating']}점")


# ══════════════════════════════════════════════════════════
# Step 2: LLMTextColumn — Seed 기반 리뷰 생성
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 2: LLMTextColumn — 리뷰 생성")
print("=" * 60)

seed_examples_pos = "\n".join([f"- {t[:100]}" for t in seed_positive[:5]])
seed_examples_neg = "\n".join([f"- {t[:100]}" for t in seed_negative[:5]])

GENERATE_PROMPT = f"""당신은 한국 이커머스(네이버쇼핑, 무신사 등) 고객 리뷰를 작성하는 역할입니다.

실제 한국인 쇼핑몰 고객처럼 자연스러운 구어체로 리뷰를 작성하세요.
이모티콘(ㅎㅎ, ㅠㅠ, ~~), 줄임말, 인터넷 용어를 자연스럽게 사용하세요.

참고 실제 리뷰 (긍정):
{seed_examples_pos}

참고 실제 리뷰 (부정):
{seed_examples_neg}

규칙:
1. 리뷰는 80~200자 사이로 작성
2. 해당 상황/스타일에 맞는 구체적인 착용 경험을 포함
3. 소재, 핏, 색상, 계절감 등 구체적 속성을 자연스럽게 언급
4. 별점에 맞는 톤 유지 (1-2점: 불만, 4-5점: 만족)
5. 리뷰 텍스트만 출력하세요. 다른 설명 없이."""

generated = []
for i, sample in enumerate(samples):
    user_msg = (
        f"다음 조건의 패션 상품 리뷰를 작성하세요:\n"
        f"- 상황/스타일: {sample['intent']}\n"
        f"- 상품 카테고리: {sample['category']}\n"
        f"- 계절: {sample['season']}\n"
        f"- 성별: {sample['gender']}\n"
        f"- 별점: {sample['target_rating']}점 (5점 만점)\n\n"
        f"리뷰:"
    )

    review = call_llm(GENERATE_PROMPT, user_msg, max_tokens=300)
    review = review.strip().strip('"').strip("'")

    sample["generated_review"] = review
    generated.append(sample)

    sentiment = "긍정" if sample["target_rating"] >= 4 else "부정"
    print(f"\n  [{i+1}/10] [{sentiment}] {sample['intent']}/{sample['category']}/{sample['season']}")
    print(f"    → {review[:120]}...")

    time.sleep(0.5)


# ══════════════════════════════════════════════════════════
# Step 3: LLMStructuredColumn — 구조화 필드 추출
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 3: LLMStructuredColumn — 필드 추출")
print("=" * 60)

EXTRACT_PROMPT = """당신은 패션 리뷰에서 구조화된 속성을 추출하는 전문가입니다.
리뷰 텍스트를 분석하여 아래 JSON을 반환하세요. 모든 값은 한국어로 작성합니다.
리뷰에서 직접 언급되거나 강하게 추론 가능한 속성만 입력하고, 아니면 null로 두세요.

JSON만 출력하세요:
```json
{
  "intent": "착용 상황/스타일 (예: 하객룩, 출근룩, 데이트룩 등)",
  "attributes": {
    "material": "소재 또는 null",
    "fit": "핏/사이즈감 또는 null",
    "color": "색상 또는 null",
    "style": "스타일 특징 또는 null",
    "season": "계절 또는 null"
  },
  "sentiment": "긍정/부정/중립",
  "customer_keywords": ["고객이 사용한 감성적 표현 3~5개"]
}
```"""

results = []
for i, item in enumerate(generated):
    review = item["generated_review"]

    content = call_llm(EXTRACT_PROMPT, f"리뷰: {review}", max_tokens=400)

    # JSON 추출
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        parsed["_source_intent"] = item["intent"]
        parsed["_source_category"] = item["category"]
        parsed["_source_season"] = item["season"]
        parsed["_source_gender"] = item["gender"]
        parsed["_source_rating"] = item["target_rating"]
        parsed["review_text"] = review

        results.append(parsed)

        match = "✓" if parsed.get("intent","") == item["intent"] or item["intent"] in parsed.get("intent","") else "△"
        print(f"\n  [{i+1}] {match} 입력intent={item['intent']} → 추출intent={parsed.get('intent','?')}")
        print(f"    attrs: {json.dumps(parsed.get('attributes',{}), ensure_ascii=False)}")
        print(f"    keys:  {parsed.get('customer_keywords', [])}")

    except (json.JSONDecodeError, Exception) as e:
        print(f"\n  [{i+1}] 파싱 실패: {str(e)[:50]}")

    time.sleep(0.5)


# ══════════════════════════════════════════════════════════
# Step 4: LLMJudgeColumn — 품질 평가
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 4: LLMJudgeColumn — 품질 평가")
print("=" * 60)

JUDGE_PROMPT = """당신은 합성 데이터 품질 심사관입니다.
생성된 패션 리뷰의 품질을 1~5점으로 평가하세요.

평가 기준:
- 자연스러움: 실제 한국인 고객이 쓴 것처럼 자연스러운가?
- 구체성: 소재, 핏, 색상 등 구체적 속성이 언급되었는가?
- 일관성: 별점과 리뷰 톤이 일치하는가?
- 유용성: Semantic Bridge 구축에 활용 가능한 정보가 있는가?

JSON만 출력:
```json
{"score": 1~5, "reason": "한 줄 평가 사유"}
```"""

for i, item in enumerate(results):
    content = call_llm(
        JUDGE_PROMPT,
        f"별점: {item['_source_rating']}점\n리뷰: {item['review_text']}",
        max_tokens=100,
    )
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        judge = json.loads(content)
        item["quality_score"] = judge.get("score", 0)
        item["quality_reason"] = judge.get("reason", "")
        print(f"  [{i+1}] {item['quality_score']}점 — {item['quality_reason'][:60]}")
    except Exception:
        item["quality_score"] = 0
        item["quality_reason"] = "평가 실패"
        print(f"  [{i+1}] 평가 실패")

    time.sleep(0.3)


# ══════════════════════════════════════════════════════════
# 결과 저장 + 통계
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("결과 요약")
print("=" * 60)

if results:
    out_path = os.path.join(DATA_DIR, "data_designer_poc.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    avg_score = sum(r.get("quality_score", 0) for r in results) / len(results)
    intents_match = sum(
        1 for r in results
        if r.get("_source_intent","") in r.get("intent","") or r.get("intent","") in r.get("_source_intent","")
    )

    print(f"""
┌────────────────────────────────────────────┐
│  Data Designer PoC 결과                     │
├────────────────────────────────────────────┤
│  생성 리뷰: {len(results)}건                          │
│  Intent 매칭: {intents_match}/{len(results)} ({intents_match/len(results)*100:.0f}%)                    │
│  평균 품질 점수: {avg_score:.1f}/5                     │
│                                            │
│  저장: data/data_designer_poc.jsonl         │
└────────────────────────────────────────────┘

GPU 환경에서는 이 로직을 NeMo Data Designer YAML로 전환:
  - SamplerColumn → intent, category, season 분포 제어
  - LLMTextColumn → vLLM + Nemotron 3로 리뷰 생성
  - LLMStructuredColumn → Pydantic 스키마로 필드 추출
  - LLMJudgeColumn → 품질 필터링 자동화
""")
