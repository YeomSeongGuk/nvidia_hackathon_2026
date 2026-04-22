# /// script
# requires-python = ">=3.10"
# dependencies = ["openai", "pandas", "httpx"]
# ///
"""
개선된 파이프라인: 패션 의류 리뷰만 정확히 필터링 + 사전 정의 Intent로 추출
"""
import pandas as pd
import json
import os
import time
import httpx
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── NIM API Client ───────────────────────────────────────────
http_client = httpx.Client(verify=False, timeout=60.0)
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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",
    http_client=http_client,
)
MODEL = "nvidia/nemotron-3-nano-30b-a3b"

def call_llm(system: str, user: str, max_tokens: int = 512) -> str:
    """NIM API 호출 + 재시도"""
    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            content = r.choices[0].message.content or ""
            return content
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise e


# ── Step 1: 의류/패션 리뷰만 정확히 필터링 ─────────────────────
print("=" * 60)
print("Step 1: 의류/패션 리뷰 필터링 (2단계)")
print("=" * 60)

df = pd.read_csv(
    os.path.join(DATA_DIR, "naver_shopping.txt"),
    sep="\t", header=None, names=["rating", "text"]
)
print(f"전체: {len(df):,}건")

# 1단계: 의류 전용 키워드 (범용 키워드 제거)
CLOTHING_KEYWORDS = [
    "바지", "셔츠", "원피스", "자켓", "코트", "니트", "블라우스", "치마",
    "스커트", "카디건", "후드", "맨투맨", "티셔츠", "레깅스", "청바지",
    "데님", "패딩", "점퍼", "조끼", "트렌치", "가디건", "슬랙스",
    "오버핏", "슬림핏", "루즈핏", "기장감", "핏이",
    "면소재", "린넨", "트위드", "캐시미어", "쉬폰",
    "운동화", "스니커즈", "구두", "부츠", "샌들",
    "상의", "하의", "아우터", "이너", "겉옷",
    "입었", "입고", "입어", "걸치", "착용",
    "코디", "데일리룩", "출근룩", "하객룩",
]

# 비패션 제외 키워드
EXCLUDE_KEYWORDS = [
    "의자", "테이블", "책상", "소파", "침대", "이불", "베개",
    "화장품", "크림", "세럼", "마스크팩", "샴푸",
    "차", "커피", "음료", "식품", "음식", "먹",
    "가전", "냉장고", "세탁기", "청소기", "에어컨",
    "핸드폰", "케이스", "충전", "이어폰",
]

mask_include = df["text"].str.contains("|".join(CLOTHING_KEYWORDS), na=False)
mask_exclude = df["text"].str.contains("|".join(EXCLUDE_KEYWORDS), na=False)
clothing_df = df[mask_include & ~mask_exclude].copy()
clothing_df = clothing_df[clothing_df["text"].str.len() > 30]  # 너무 짧은 리뷰 제거
clothing_df = clothing_df.reset_index(drop=True)
clothing_df["id"] = [f"review_{i:05d}" for i in range(len(clothing_df))]

print(f"의류 키워드 필터 후: {len(clothing_df):,}건")

# 2단계: LLM으로 10개 샘플 검증 (실제 의류 리뷰인지)
print("\nLLM 검증 (샘플 10건)...")
samples = clothing_df.sample(10, random_state=42)
verify_prompt = """다음 리뷰가 의류/신발/패션 악세서리에 대한 리뷰인지 판단하세요.
의류/신발/패션이면 "YES", 아니면 "NO"만 답하세요."""

correct = 0
for _, row in samples.iterrows():
    result = call_llm(verify_prompt, row["text"], max_tokens=10).strip().upper()
    is_fashion = "YES" in result
    if is_fashion:
        correct += 1
    print(f"  {'✓' if is_fashion else '✗'} [{row['rating']}] {row['text'][:60]}... → {result}")

print(f"패션 리뷰 비율: {correct}/10 ({correct*10}%)")

# 저장
clothing_df.to_json(
    os.path.join(DATA_DIR, "clothing_reviews.jsonl"),
    orient="records", lines=True, force_ascii=False
)
print(f"\n저장: data/clothing_reviews.jsonl ({len(clothing_df):,}건)")


# ── Step 2: 사전 정의 Intent로 구조화 추출 ─────────────────────
print("\n" + "=" * 60)
print("Step 2: Intent-Attribute 구조화 추출 (20건 테스트)")
print("=" * 60)

INTENT_LIST = [
    "출근룩", "데이트룩", "하객룩", "캠퍼스룩", "캐주얼데일리",
    "꾸안꾸", "미니멀룩", "스트릿룩", "고프코어", "비즈니스캐주얼",
    "운동/애슬레저", "여행룩", "홈웨어/편한옷", "겨울방한", "여름시원룩",
    "기타"
]

EXTRACTION_PROMPT = f"""당신은 한국 이커머스 패션 리뷰 분석 전문가입니다.
리뷰를 분석하여 아래 JSON을 반환하세요. 반드시 한국어로만 작성하세요.

규칙:
1. intent는 반드시 다음 목록 중 하나를 선택: {json.dumps(INTENT_LIST, ensure_ascii=False)}
2. 리뷰 내용이 여러 intent에 해당하면 가장 주된 것 하나만 선택
3. attributes의 각 값은 리뷰에서 직접 언급되거나 강하게 추론되는 경우에만 입력, 아니면 null
4. keywords는 고객이 사용한 감성적/구어적 표현을 그대로 추출 (3~5개)
5. 모든 값은 반드시 한국어로 작성

JSON 형식만 출력하세요:
```json
{{
  "intent": "목록 중 하나",
  "attributes": {{
    "material": "소재 또는 null",
    "fit": "핏/사이즈감 또는 null",
    "color": "색상 또는 null",
    "style": "스타일 특징 또는 null",
    "season": "계절 또는 null"
  }},
  "sentiment": "긍정/부정/중립",
  "keywords": ["표현1", "표현2", "표현3"]
}}
```"""

# 텍스트가 충분히 긴 의류 리뷰 20건 선택
test_reviews = clothing_df[clothing_df["text"].str.len() > 60].sample(20, random_state=123)

results = []
errors = 0
for i, (_, row) in enumerate(test_reviews.iterrows()):
    print(f"\n[{i+1}/20] [{row['rating']}점] {row['text'][:70]}...")

    try:
        content = call_llm(EXTRACTION_PROMPT, f"리뷰: {row['text']}", max_tokens=400)

        # JSON 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        parsed["review_id"] = row["id"]
        parsed["review_text"] = row["text"]
        parsed["rating"] = int(row["rating"])
        results.append(parsed)

        print(f"  intent: {parsed['intent']}")
        print(f"  attrs:  {json.dumps(parsed['attributes'], ensure_ascii=False)}")
        print(f"  sent:   {parsed.get('sentiment', '?')}")
        print(f"  keys:   {parsed.get('keywords', [])}")

    except json.JSONDecodeError as e:
        errors += 1
        print(f"  JSON 파싱 실패: {str(e)[:50]}")
        print(f"  Raw: {content[:150]}")
    except Exception as e:
        errors += 1
        print(f"  에러: {type(e).__name__}: {str(e)[:80]}")

    time.sleep(0.5)  # rate limit 방지

# 결과 저장 및 통계
print("\n" + "=" * 60)
print(f"추출 결과: {len(results)}건 성공, {errors}건 실패")

if results:
    with open(os.path.join(DATA_DIR, "extraction_results.jsonl"), "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Intent 분포
    intent_counts = {}
    for r in results:
        intent = r.get("intent", "unknown")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\nIntent 분포:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"  {intent}: {count}건")

    # Sentiment 분포
    sent_counts = {}
    for r in results:
        s = r.get("sentiment", "unknown")
        sent_counts[s] = sent_counts.get(s, 0) + 1
    print(f"\nSentiment 분포: {sent_counts}")

    print(f"\n저장: data/extraction_results.jsonl")

print("=" * 60)
