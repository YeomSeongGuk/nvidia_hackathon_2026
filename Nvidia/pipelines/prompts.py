"""Prompt templates for the analyzed-data pipeline.

Stage 1 (Extract) uses an English instruction block because the source text can
be Korean, English, or mixed; keeping raw_intent in the source language lets
Stage 2 perform cross-lingual merging later.

Stages 2, 2.5 and 2.75 use Korean prompts on purpose: this is a Korean
fashion-ecommerce domain, and we found that Korean-native instructions give
significantly better canonicalization, refinement, and cross-cluster merge
decisions when the examples themselves are Korean TPO terms ("하객룩",
"오피스룩", ...).

All examples in these prompts are literal cues for the LLM; do NOT translate
them to English or the output quality will drop.
"""

EXTRACT_SYSTEM = """You are a fashion product review analyst.
Given a clean text from a customer review, extract a JSON object.

STRICT RULES (follow every rule, do NOT negotiate with yourself):

R1. DO NOT hallucinate. Only extract values that are LITERALLY WRITTEN in
    the text. If a value is not explicitly written, output null.

R2. If the text is NOT about fashion/clothing (e.g. food, electronics,
    baby seat, toys, home appliance), then:
    - raw_intent = "general_wear"
    - every attribute MUST be null (this is non-negotiable)
    - still fill sentiment + extracted_keywords normally.

R3. Attributes MUST be fashion-specific. Do NOT force-fit non-fashion words:
    - material : fabric/textile word only (cotton, 린넨, tweed, denim, silk).
                 NEVER a taste, a size (13cm), an age (6세), a weight (20kg).
    - fit      : how the garment sits (slim, loose, 오버핏, tight, 슬림).
                 NEVER a number, a size code, or an age.
    - color    : color name only (black, navy, 연보라, 검정).
                 NEVER a weight, a size, or a number.
    - style    : garment style (캐주얼, formal, street, 빈티지).
                 NEVER a person's age or a product category like "아동화".
    - season   : spring / summer / fall / winter (봄/여름/가을/겨울) only.

R4. raw_intent is the customer's TPO/situational phrase (하객룩, 데일리 캐주얼,
    wedding guest look, 홈웨어, 데이트룩). Keep it in the ORIGINAL language
    of the text. 1-5 words. If no clear TPO, output exactly "general_wear".

R5. sentiment is one of "positive", "negative", "neutral".

R6. extracted_keywords: 3-5 short phrases literally present in the text.

R7. When in doubt, PREFER null. Silence is better than wrong data.

EXAMPLES:

Input: "많이 달아요. 근데 맛있어요. (Rating: 5)"
Output: {"raw_intent":"general_wear","attributes":{"material":null,"fit":null,"color":null,"style":null,"season":null},"sentiment":"positive","extracted_keywords":["많이 달아요","맛있어요","Rating 5"]}

Input: "하객룩으로 딱 좋음. 트위드 소재에 네이비 컬러."
Output: {"raw_intent":"하객룩","attributes":{"material":"트위드","fit":null,"color":"네이비","style":null,"season":null},"sentiment":"positive","extracted_keywords":["하객룩","트위드","네이비"]}

Input: "20킬로 6세 아이가 좋아해요 13센치 했어요 (Rating: 5)"
Output: {"raw_intent":"general_wear","attributes":{"material":null,"fit":null,"color":null,"style":null,"season":null},"sentiment":"positive","extracted_keywords":["20킬로 6세","13센치","좋아해요"]}

Output VALID JSON only. No prose, no comments, no reasoning in the content."""


EXTRACT_USER_TEMPLATE = """Text:
\"\"\"
{text}
\"\"\"

Return a JSON object with EXACTLY these keys:
- raw_intent (string, 1-5 words, in the text's original language, a TPO/style category or "general_wear")
- attributes (object with keys: material, fit, color, style, season - values are strings or null)
- sentiment (one of: "positive", "negative", "neutral")
- extracted_keywords (list of 3-5 strings)
"""


# ---------------------------------------------------------------------------
# Stage 2: canonicalize a cluster of customer-surface intents into one name.
# ---------------------------------------------------------------------------

CANONICAL_SYSTEM = """당신은 한국 패션 이커머스의 상품 기획자입니다.
고객이 리뷰/블로그에서 사용하는 다양한 표현들 중, 같은 의미 그룹(cluster)에 속한 표현들이 주어집니다.
이 그룹을 대표하는 한국어 canonical 이름을 1개 정하세요.

규칙:
- 한국어 단어 1-6글자 이내. 예: "하객룩", "데일리캐주얼", "오피스룩", "운동복", "홈웨어", "데이트룩".
- 해당 그룹이 영어 표현만 포함해도, 캐논컬 이름은 반드시 한국어로 출력.
- 불필요한 수식어 제거. 고객이 검색/클릭할만한 실제 표현 형태로.
- 출력은 JSON. 커멘터리 금지."""


CANONICAL_USER_TEMPLATE = """같은 의미 그룹에 속한 고객 표현들:
{members}

JSON 형식으로 응답하세요:
{{"canonical_name": "..."}}
"""


# ---------------------------------------------------------------------------
# Stage 2.5: refine a cluster that may contain multiple semantic sub-groups.
# ---------------------------------------------------------------------------

REFINE_SYSTEM = """당신은 한국 패션 이커머스의 상품 기획자입니다.
임베딩 기반 1차 클러스터링으로 묶인 고객 표현들이 주어집니다.
이 중 **의미상 서로 다른 TPO/스타일 그룹**이 섞여 있는지 판단하고, 반드시 필요한 경우 subgroup으로 분리합니다.

중요 원칙:
- 임베딩은 단어 형태 유사성 때문에 전혀 다른 TPO를 묶어버리는 경우가 많습니다.
- 같은 TPO(시간/장소/상황) 또는 거의 동일한 스타일 카테고리인 것끼리만 같은 subgroup으로 유지.
- 예시 ← 반드시 따르세요:
  * ["교복", "오피스룩"]  → 다른 subgroup (학생 교복 vs 사무실 착장)
  * ["홈웨어", "운동복"]  → 다른 subgroup (집 내부 vs 운동 활동)
  * ["캐주얼", "데일리 캐주얼", "스트리트 캐주얼", "일상캐주얼"] → 같은 subgroup (모두 일상 캐주얼)
  * ["데이트룩", "하객룩"] → 다른 subgroup
  * ["여름 캐주얼"] 단독은 ["데일리 캐주얼", "일상캐주얼"]와 묶어도 OK (모두 캐주얼)
- 확신이 없으면 분리하세요 (과소병합보다 과병합이 더 나쁨).
- 모든 입력 표현이 정확히 한 subgroup에 포함되어야 합니다 (누락/중복 금지).
- 출력은 JSON, 커멘터리 금지."""


REFINE_USER_TEMPLATE = """다음은 1차 클러스터링된 고객 표현들입니다:
{members}

JSON 형식으로 응답하세요:
{{"subgroups": [["표현1", "표현2"], ["표현3"], ...]}}
"""


# ---------------------------------------------------------------------------
# Stage 2.75: cross-cluster merge - detect canonical intents that mean the
# same thing (e.g. "운동룩" vs "운동복", "데일리룩" vs "캐주얼").
# ---------------------------------------------------------------------------

CROSS_MERGE_SYSTEM = """당신은 한국 패션 이커머스의 상품 기획자입니다.
1차 semantic dedup 결과, 다수의 canonical intent가 얻어졌습니다. 그중 **서로 의미상 중복**되는 intent들을 찾아 병합 그룹을 제안합니다.

판단 규칙:
- 같은 TPO(Time/Place/Occasion) 또는 같은 스타일 카테고리를 가리키면 병합 그룹으로 묶기.
- 서로 다른 의미이면 유지(목록에 넣지 않음).
- 영어/한국어 동의어는 같은 의미로 간주.
- 확신이 없으면 병합하지 마세요 (잘못된 병합이 더 나쁨).
- 반드시 지킬 예시:
  * "운동룩" ≈ "운동복" → 병합
  * "데일리룩" ≈ "캐주얼" ≈ "일상복" → 병합 (모두 일상 캐주얼 착장)
  * "하객룩" ≠ "오피스룩" → 절대 병합 금지 (서로 다른 TPO)
  * "교복" ≠ "홈웨어" → 절대 병합 금지
  * "캐주얼" ≠ "오피스룩" → 절대 병합 금지 (오피스는 격식)
  * "캐주얼" ≠ "하객룩" → 절대 병합 금지
  * "여름룩" ≠ "겨울룩" → 절대 병합 금지

규칙:
- 입력 intent 이름을 한 글자도 바꾸지 말고 그대로 사용.
- 한 intent는 최대 한 병합 그룹에만 속함.
- 병합 그룹이 없으면 빈 리스트 반환.
- JSON만 출력, 커멘터리 금지."""


CROSS_MERGE_USER_TEMPLATE = """현재 canonical intent 목록 (evidence count와 고객 원문 표현 포함):
{intent_list}

서로 의미상 중복되는 intent들을 찾아 병합 그룹으로 묶어주세요.

JSON 형식:
{{"merge_groups": [["intent1", "intent2"], ["intent3", "intent4", "intent5"]]}}

주의: 병합이 필요 없으면 merge_groups=[].
"""


# ---------------------------------------------------------------------------
# Stage 2.4: expand one canonical intent into N natural-language chatbot
# queries (what a real user would TYPE into the shopping chatbot, not the
# terse TPO keyword we have in `intent_keyword`).
# ---------------------------------------------------------------------------

EXPAND_SYSTEM = """당신은 한국 이커머스 쇼핑 챗봇의 사용자 쿼리 생성 전문가입니다.
주어진 canonical intent와 그 속성들에 대해, 실제 사용자가 챗봇에 입력할 만한
자연어 질문/요청을 N개 생성합니다.

규칙:
- 각 쿼리는 자연스러운 한국어 1-2 문장. 챗봇 말 거는 친근한 어투.
- 반말/존댓말/명령문/질문문을 섞어 다양화. 줄임말 허용.
- canonical 이름(예: "하객룩")을 그대로 반복하지 말고, 사용자가 실제로
  말할 법한 상황 표현을 사용 ("결혼식 갈 때 뭐 입지?", "친구 결혼식 코디 추천").
- mapped_attributes에서 1-2개 속성은 자연스럽게 문장에 녹여도 OK,
  하지만 모든 속성을 나열하지 말 것 (너무 상세하면 자연스럽지 않음).
- 속성이 없는 intent("general_wear", "일반")면 범용 질문 ("편한 옷 추천해줘") 느낌.
- 모든 쿼리는 서로 다른 표현이어야 함 (단순 재구성 금지).

출력: JSON {"queries": [str, str, ...]}.
커멘터리 금지, JSON만."""


EXPAND_USER_TEMPLATE = """canonical intent: {intent_keyword}
mapped_attributes:
{attrs_block}

위 intent를 실제 쇼핑 챗봇 사용자가 입력할 만한 자연어 쿼리로 {n} 개 생성해주세요.

JSON 형식:
{{"queries": ["...", "...", ...]}}
"""


EXPAND_FEW_SHOTS = [
    {
        "intent_keyword": "하객룩",
        "attrs_block": "- material: 트위드 (0.67)\n- color: 네이비 (0.67)",
        "queries": [
            "결혼식 하객으로 갈 때 뭐 입지?",
            "하객룩 추천해줘, 너무 튀지 않게",
            "친구 결혼식에 트위드 원피스 어때?",
            "웨딩 게스트로 갈 때 네이비 컬러 코디 알려줘",
            "하객으로 갈 때 실례 안 되는 옷",
        ],
    },
    {
        "intent_keyword": "일반",
        "attrs_block": "(없음)",
        "queries": [
            "편하게 입을 만한 옷 추천",
            "아무거나 괜찮은 데일리 옷 알려줘",
            "뭐 입을지 모르겠을 때 무난한 거",
            "기본템 하나 추천해줘",
            "평범한 일상복",
        ],
    },
]
