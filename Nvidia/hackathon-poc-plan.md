# Hackathon PoC 계획서: Customer Driven Discovery Using NeMo Curator

## 1. 프로젝트 한 줄 요약

> 고객 리뷰/블로그의 감성적 표현("꾸안꾸", "하객룩")을 NeMo Curator로 큐레이션하고, LLM으로 상품 DB 속성({material, fit, color})에 매핑하는 **Semantic Bridge**를 구축하여, 기존에 검색 불가능했던 자연어 쿼리를 상품 추천으로 연결한다.

---

## 2. 구현 가능성 판정

PDF 설계의 3-Phase를 NeMo Curator 공식 문서/소스코드와 대조 분석한 결과:

### Phase 1: Data Curation — NeMo Curator 직접 지원

| 설계 항목 | NeMo Curator 지원 | 비고 |
|-----------|:-----------------:|------|
| Common Crawl/블로그 수집 | **O** | `CommonCrawlDownloadExtractStage` 내장. 커스텀 소스는 `DocumentDownloadExtractStage` 패턴 |
| 리뷰/Q&A 데이터 로딩 | **O** | JSONL, Parquet Reader 내장 |
| MinHash 중복제거 | **O** | Fuzzy MinHash LSH, GPU 가속 (8TB 데이터 16x 빠른 처리 실증) |
| 노이즈 필터링 | **O** | 30+ 휴리스틱 필터 + fastText/DeBERTa 품질 분류기 |
| 한국어 언어 감지 | **O** | FastText lid.176.bin (176개 언어, 한국어 포함) |
| Incremental/Delta Processing | **커스텀** | 파이프라인 입력단에서 타임스탬프 기반 필터링 직접 구현 필요 |

### Phase 2: Knowledge Extraction — 프레임워크 지원 + 커스텀 개발

| 설계 항목 | NeMo Curator 지원 | 비고 |
|-----------|:-----------------:|------|
| LLM 연동 | **O** | `LLMClient`/`AsyncOpenAIClient` — OpenAI 호환 API(NIM, vLLM 등) 지원 |
| 지식 추출 스테이지 | **O** | `ExtractKnowledgeStage`, `KnowledgeListStage` 내장 |
| 커스텀 추출 로직 | **O** | `BaseSyntheticStage` 상속으로 커스텀 프롬프트 스테이지 구현 가능 |
| 고객 언어→상품 속성 매핑 | **커스텀** | 핵심 차별점. 프롬프트 엔지니어링 + 도메인 설계 필요 |
| Semantic Deduplication | **O** | K-means 클러스터링 + pairwise similarity, GPU 가속 |

### Phase 3: Knowledge DB + 서빙 — NeMo Curator 범위 밖

| 설계 항목 | NeMo Curator 지원 | 비고 |
|-----------|:-----------------:|------|
| Semantic Bridge Dictionary | **범위 밖** | ES 등 별도 저장소에 인덱싱 |
| Query Expansion | **범위 밖** | 서빙 타임 로직, 별도 구현 |
| Chatbot | **범위 밖** | 별도 RAG 시스템 필요 |

### 판정 요약

- **Phase 1**: NeMo Curator 핵심 기능과 정확히 일치. 바로 구현 가능.
- **Phase 2**: 파이프라인 인프라(Pipeline, LLMClient, GPU 가속)는 지원됨. 핵심 매핑 로직은 커스텀 개발.
- **Phase 3**: NeMo Curator 범위 밖이지만, PoC에서는 ES 임베딩 검색으로 충분히 시연 가능.

---

## 3. PoC 범위 (해커톤용)

챗봇을 직접 만들지 않는다. 대신 Semantic Bridge의 **가치 증명**에 집중한다.

### 시연 시나리오 (Before/After)

```
[Before — 기존 검색]
  쿼리: "비 오는 날 데이트룩"
  결과: 키워드 매칭 실패 → 관련 없는 상품 노출

[After — Semantic Bridge]
  쿼리: "비 오는 날 데이트룩"
  → ES 임베딩 검색 → Intent 매칭 (score: 0.92)
  → 연관 속성:
      material: "나일론, 폴리에스터" (weight: 0.88)
      water_resistance: "발수가공" (weight: 0.85)
      style: "캐주얼, 시티보이" (weight: 0.79)
      color: "블랙, 네이비, 카키" (weight: 0.76)
  → 근거: "287건의 리뷰 분석 결과 방수 소재+레귤러핏 만족도 최고"
  → 이 속성으로 Shopping API 쿼리 가능
```

### ES에 인덱싱되는 데이터 구조

```json
{
  "intent_id": "wedding_guest_look_001",
  "intent_name": "결혼식 하객룩",
  "query_variations": [
    "결혼식 하객룩 추천", "하객 패션", "결혼식 뭐 입지", "하객 코디"
  ],
  "query_embedding": [0.12, -0.34, ...],
  "mapped_attributes": {
    "material": {"value": "tweed,chiffon", "weight": 0.85},
    "fit": {"value": "standard,slim", "weight": 0.78},
    "color": {"value": "pastel,navy,beige", "weight": 0.72},
    "style": {"value": "formal,semi_formal", "weight": 0.90}
  },
  "evidence": {
    "total_reviews_analyzed": 342,
    "source_categories": ["dress", "blazer", "skirt"],
    "sample_reviews": [
      "트위드 소재가 하객룩으로 딱이에요",
      "네이비 컬러 원피스 입고 갔는데 많이 칭찬받았어요"
    ]
  },
  "last_updated": "2026-04-18"
}
```

---

## 4. 데이터 확보 전략

생성 데이터 없이 **실제 데이터**로 진행한다.

### 확보 가능한 실제 데이터셋

| 우선순위 | 데이터 | 건수 | 확보 방법 | 시간 |
|:--------:|--------|------|-----------|------|
| **1 (필수)** | 네이버 쇼핑 리뷰 (bab2min/corpus) | **20만건** | `curl` 한 줄 (20MB) | 즉시 |
| 2 (권장) | Common Crawl 한국어 패션 블로그 | 수천건 | CC Index → byte-range fetch | 1~2h |
| 3 (선택) | 국립국어원 ABSA 쇼핑몰 리뷰 | 5,800건 | 모두의말뭉치 가입 후 다운로드 | 30분 |

### 네이버 쇼핑 리뷰 상세

- **출처**: https://github.com/bab2min/corpus/tree/master/sentiment
- **수집 기간**: 2020.06~2020.07, 네이버 쇼핑 실제 리뷰
- **구조**: `별점(1~5)\t리뷰텍스트` (긍정 10만 / 부정 10만)
- **라이선스**: Public Domain
- **패션 관련**: 의류, 신발, 액세서리 등 약 3,800건 이상 포함
- **다운로드**: `curl -sL https://raw.githubusercontent.com/bab2min/corpus/master/sentiment/naver_shopping.txt -o naver_shopping.txt`

### 실제 데이터 예시

```
5  아주좋아요 바지 정말 좋아서2개 더 구매했어요 이가격에 대박입니다.
   바느질이 조금 엉성하긴 하지만 편하고 가성비 최고예요.
2  넉넉한 길이로 주문했는데도 안 맞네요 별로예요
5  촉감도 좋고 무게감이나 핏도 편합니다
2  베이지 색 구매했는데 약간 살색에 가까워요
```

### Common Crawl 한국어 블로그 수집 방법

PDF 아키텍처에 "Common Crawl (Blogs)"가 별도 Data Source로 있으므로, 두 소스를 모두 사용하면 설계 충실도가 높아진다.

1. **CC Index에서 한국어 패션 도메인 필터링** (blog.naver.com, tistory.com, musinsa.com 등)
2. **byte-range fetch로 대상 WARC 레코드만 다운로드** (전체 WARC 파일을 받지 않음)
3. NeMo Curator의 `CommonCrawlHTMLExtractor`로 텍스트 추출 (한국어 jusText stoplist 지원)

> 시간 부족 시 네이버 쇼핑 리뷰만으로도 PoC 성립. Common Crawl은 보너스.

---

## 5. 환경 구성

### 이중 환경 전략

```
┌──────────────────────────────────┐     semantic_bridge.jsonl    ┌───────────────────────┐
│         GPU 머신 (Jupyter)        │        ───────────►         │     로컬 랩탑          │
│                                  │         파일 전송            │                       │
│  Phase 1: NeMo Curator 큐레이션   │                             │  Phase 3: ES 인덱싱    │
│  Phase 2: LLM Intent 추출        │                             │           + 데모       │
│                                  │                             │                       │
│  입력: naver_shopping.txt (20MB)  │                             │  입력: .jsonl 파일     │
│  출력: semantic_bridge.jsonl      │                             │  출력: 검색 데모       │
└──────────────────────────────────┘                             └───────────────────────┘
```

### GPU 머신 (NVIDIA 제공 Jupyter 예상)

```bash
pip install "nemo-curator[text_cuda12]"
# 노트북 01~04 순서대로 실행
```

### 로컬 랩탑

```bash
docker run -d -p 9200:9200 elasticsearch:8.x
pip install elasticsearch sentence-transformers
# 노트북 05 실행
```

### 노트북 구성

```
01_data_download_and_explore.ipynb    # 데이터 다운로드 + EDA
02_nemo_curator_pipeline.ipynb        # NeMo Curator 큐레이션 (필터, 중복제거)
03_intent_attribute_extraction.ipynb  # LLM 기반 Intent-Attribute 추출
04_export_semantic_bridge.ipynb       # 최종 JSONL 내보내기
05_es_index_and_demo.ipynb            # ES 인덱싱 + 검색 시연 (로컬)
```

---

## 6. 타임라인 (20시간)

```
[Phase 1: 데이터 확보 + 큐레이션] ────────────── 5h
│
├─ (0.5h) 네이버 쇼핑 리뷰 다운로드 + JSONL 변환
├─ (1.5h) Common Crawl: CC Index → 한국어 패션 블로그 fetch (선택)
├─ (2h)   NeMo Curator 파이프라인:
│         ① 패션 카테고리 필터링 (LLM 또는 MultilingualDomainClassifier)
│         ② MinHash 중복제거
│         ③ 노이즈 필터링 (짧은 리뷰, 의미없는 텍스트 제거)
│         ④ 품질 스코어링
└─ (1h)   큐레이션 전/후 통계 비교 산출 (발표용)

[Phase 2: Intent-Attribute 추출] ────────────── 8h
│
├─ (1h)   Intent 체계 설계 (20~30개)
│         예: wedding_guest_look, rainy_day_commute,
│             effortlessly_chic(꾸안꾸), gorpcore, office_casual 등
├─ (4h)   커스텀 BaseSyntheticStage로 LLM 추출 파이프라인 구축
│         리뷰 → { intent, mapped_attributes, confidence, evidence }
├─ (2h)   각 Intent별 query_variations 생성 (LLM)
│         "하객룩" → ["결혼식 뭐 입지", "하객 패션 추천", ...]
└─ (1h)   추출 결과 검증 + 정제

[Phase 3: ES 인덱싱 + 시연] ─────────────────── 5h
│
├─ (1h)   ES 인덱스 설계 (dense_vector + keyword 하이브리드)
├─ (1.5h) 임베딩 생성 + bulk 인덱싱
├─ (1.5h) 데모 스크립트:
│         자연어 쿼리 → 임베딩 검색 → Intent + 속성 반환 + 근거 리뷰
└─ (1h)   발표 자료 정리 + Before/After 시나리오

[버퍼] ──────────────────────────────────────── 2h
```

---

## 7. NeMo Curator 핵심 기능 매핑

프로젝트에서 사용하는 NeMo Curator 기능과 해당 API:

| 프로젝트 기능 | NeMo Curator API | GPU 사용 |
|--------------|-----------------|:--------:|
| 데이터 로딩 | `JsonlReader`, `DocumentDownloadExtractStage` | - |
| 한국어 필터링 | FastText `lid.176.bin` (언어 감지) | - |
| 패션 도메인 분류 | `MultilingualDomainClassifier` (한국어 포함 52개 언어) | **GPU** |
| 중복 제거 | `FuzzyDuplicates` (MinHash LSH) | **GPU** |
| 시맨틱 중복 제거 | `SemanticDeduplication` (K-means + pairwise) | **GPU** |
| 노이즈 필터링 | 30+ 휴리스틱 필터 (`ScoreFilter`, `DocumentFilter`) | - |
| LLM 연동 | `AsyncOpenAIClient` (OpenAI 호환 API) | - |
| 지식 추출 | `ExtractKnowledgeStage`, `BaseSyntheticStage` 커스텀 | - |
| Common Crawl | `CommonCrawlWARCReader` + `CommonCrawlHTMLExtractor` | - |
| PII 제거 | `GlinerPiiRedactor` (55+ 엔터티 타입) | **GPU** |

---

## 8. 한국어 지원 현황

| 기능 | 한국어 지원 | 비고 |
|------|:-----------:|------|
| 언어 감지 | **O** | FastText lid.176.bin, 한국어 = `ko` |
| 도메인 분류 | **O** | `MultilingualDomainClassifier`, 52개 언어에 한국어 포함 |
| 중복 제거 (Exact/Fuzzy/Semantic) | **O** | 언어 무관 (language-agnostic) |
| 휴리스틱 필터 | **부분** | 대부분 언어 무관이나 일부(CommonEnglishWordsFilter)는 영어 전용 |
| 품질 분류기 (DeBERTa) | **X** | 영어 중심 학습. 한국어는 커스텀 필터 또는 fastText 모델 필요 |
| LLM 기반 추출 | **O** | 한국어 지원 LLM 사용 시 문제 없음 |
| Common Crawl 텍스트 추출 | **O** | jusText 한국어 stoplist 내장 |

---

## 9. 멀티모달 확장 (시간 여유 시 보조적 추가)

GPU 활용도를 높이고 데모 임팩트를 강화하기 위한 선택 사항.

### 추가 내용

- NeMo Curator의 Image curation 파이프라인 활용
- **Musinsa Snap 데이터셋** (28,727건 코디 이미지, HuggingFace)
- CLIP 임베딩으로 시각적 스타일 속성 추출 (색감, 패턴, 실루엣)
- 텍스트 속성 + 비주얼 속성을 Semantic Bridge에 통합

### 추가 시간: +5시간

| 항목 | 시간 |
|------|------|
| 이미지 데이터 준비 (Musinsa Snap) | +1h |
| CLIP 임베딩 생성 | +1.5h |
| 이미지 클러스터링 (스타일 그룹핑) | +1h |
| 텍스트+이미지 통합 | +1.5h |

### 멀티모달 시연 예시

```
[텍스트만]
  쿼리: "꾸안꾸" → {fit: relaxed, color: neutral, style: casual}

[멀티모달]
  쿼리: "꾸안꾸"
  → 텍스트 속성: {fit: relaxed, color: neutral, style: casual}
  → 비주얼 속성: 무채색 톤, 오버핏, 레이어드 (CLIP 클러스터 기반)
  → 대표 스타일 이미지 함께 제공
```

### 판단 기준

- Phase 1~3가 예정보다 빨리 끝나면 추가
- 텍스트 파이프라인이 완성되지 않은 상태에서 멀티모달 착수하지 않음
- 멀티모달 없이도 PoC는 충분히 성립

---

## 10. 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 |
|--------|:----:|:----:|------|
| GPU 환경 세팅 지연 | 중 | 높 | NeMo Curator CPU 모드(`text_cpu`)로 우선 진행, 소규모 데이터로 검증 |
| LLM API 응답 지연/할당량 | 중 | 중 | Intent 20개에서 10개로 축소, 배치 크기 조절 |
| 패션 리뷰 필터링 정확도 낮음 | 중 | 중 | 키워드 기반 사전 필터링 + LLM 분류 이중 적용 |
| Common Crawl 블로그 수집 시간 초과 | 높 | 낮 | 스킵. 네이버 쇼핑 리뷰 20만건만으로 충분 |
| Intent-Attribute 추출 품질 | 중 | 높 | 소량(100건)으로 먼저 검증 후 전체 실행 |

---

## 11. 발표 시 핵심 어필 포인트

1. **실제 데이터**: 네이버 쇼핑 리뷰 20만건 기반 (생성 데이터 아님)
2. **NeMo Curator 활용**: MinHash 중복제거, 시맨틱 중복제거, 품질 필터링, LLM 추출 스테이지 → GPU 가속 파이프라인
3. **Before/After 대비**: 키워드 매칭 실패 → Semantic Bridge로 자연어 쿼리가 상품 속성으로 변환되는 것을 실시간 시연
4. **근거 기반**: "342건의 리뷰 분석 결과..." → 할루시네이션 방지, 데이터 리니지 제공
5. **확장성**: 일일 신규 리뷰에 대한 incremental 처리 가능 설계 (Delta Processing)
