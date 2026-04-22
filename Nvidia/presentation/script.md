# 해커톤 피치 스크립트 — 5분

**목표 시간**: 300초  ·  **슬라이드**: 9장  ·  **언어**: 발화 한국어 / 슬라이드 영어

기호: `(click)` = 다음 슬라이드로, `(pause)` = 반박자 쉼, `(point …)` = 슬라이드 특정 영역 지시.

중점 슬라이드: **2, 3, 5, 9**.  1, 4, 6, 7, 8 은 가볍게 통과.

---

## Slide 1 — Title  `(10 s)`

> 안녕하세요, Coupang Catalog Enrichment 팀의 ***[이름]*** 입니다.
> 지금부터 5분간 **Customer Driven Discovery** — 한국 패션 리뷰에서
> 제품 카탈로그로 이어지는 **semantic bridge** 를 NeMo Curator 와
> Nemotron-Super 120B 로 구축한 결과를 공유드리겠습니다.  `(click)`

---

## Slide 2 — Problem → Solution  `(50 s)`  **★ 중점**

> 문제부터 짚겠습니다.  `(pause)`
>
> 한국 쇼핑 유저가 **"내일 결혼식 갈 때 입을 옷"** 같은 쿼리를 입력하면,
> 기존 키워드 검색은 매칭할 게 없습니다. 카탈로그는 **소재, 핏, 색상** 정보만
> 가지고 있고, 고객은 **상황, TPO, 감정**으로 이야기합니다.
> 이 두 언어 사이의 간극이 문제입니다.
>
> `(click — arrow)`
>
> 그런데 리뷰 데이터는 이미 이 두 언어를 **모두** 담고 있습니다.
> "데일리 오피스룩으로 입었어요" 같은 리뷰에는 상황과 속성이 함께 들어있죠.
> 그래서 저희의 접근은, 이 다리를 명시적으로 발굴하자는 것입니다.
> 리뷰를 LLM 으로 curate 해서 카탈로그 속성과 매핑되는
> **canonical TPO intent** 를 만듭니다.
>
> `(point to bottom strip)`
>
> 결과는 1만 건의 한국어 리뷰에서 **260 개의 canonical intent**.
> 상위 빈도인 *일상용, 출근룩* 부터 long-tail 인
> **스크린골프, 필라테스 레이어** 까지 — 카탈로그가 아직 인덱스하지 않은
> **실제 고객 수요 신호** 입니다.  `(click)`

---

## Slide 3 — The NVIDIA + NeMo Stack  `(50 s)`  **★ 중점**

> 여섯 가지 요소입니다. 데이터 쪽 세 개, 컴퓨트·평가 쪽 세 개.
>
> `(gesture top row)`
>
> **NeMo Curator** 가 파이프라인의 기반입니다. Stage 1 의 synth, dedup,
> filter 가 Curator 의 idiom 을 따릅니다. **NeMo Data Designer** 는
> 합성 리뷰 생성 자체를 담당합니다 — seed 와 row-level LLM prompt 방식.
>
> 그리고 핵심, **Korean Personalized Persona** 입니다.  `(pause)`
> 연령, 성별, 직업, 시도, 시군구, 성격, 취미 — 일곱 가지 필드.
> **모든 합성 리뷰가 고유한 한국 쇼핑객에 anchor 됩니다.** 막연한 "user"
> 가 아니라, 예를 들면 부산 거주 28세 오피스 워커, 등산 취미처럼요.
> 이 persona diversity 덕분에 long-tail 까지 커버 폭을 확보했습니다.
>
> `(gesture bottom row)`
>
> 추론 쪽은 **Nemotron-Super 120B FP8** 을 Brev H100 에서 vLLM 으로
> 서빙합니다. 한국어 TPO 뉘앙스 — 존댓말, 반말, 은어 — 를 fine-tuning
> 없이 처리합니다. 평가 쪽은 **Friendli serverless** 에 GLM, DeepSeek,
> Qwen3 세 개의 foreign judge. 그리고 **BGE-M3** 가 semantic clustering
> 과 dedup 을 담당합니다.  `(click)`

---

## Slide 4 — Why This Stack  `(20 s)`  *가볍게*

> 왜 이 스택인가, 네 가지만 짧게.  `(pause)` 한국어 네이티브 추론,
> 해커톤 스케일의 FP8 throughput, NeMo Curator 의 깔끔한 파이프라인
> 추상화. 그리고 아주 중요한 **독립적 평가** — 자기가 만든 출력을
> 자기가 채점하는 건 알려진 실패 패턴이라, 다른 연구소의 judge 셋이
> 서로의 blind spot 을 잡게 했습니다.  `(click)`

---

## Slide 5 — Our Approach  `(50 s)`  **★ 중점**

> 저희가 실제로 어떻게 일했는지 보여드리겠습니다.
> **세 단계 — whole build, eval infrastructure, iterate.**
>
> `(point phase 1)`
>
> **1단계, end-to-end 먼저.** 단일 stage 를 튜닝하기 전에 파이프라인
> 전체가 먼저 돌아가야 합니다. 1만 건 입력 → 260 canonical → 1.3천
> 자연어 쿼리. 여기서 NeMo Curator 와 Data Designer 의 진가가 나왔습니다.
>
> `(point phase 2)`
>
> **2단계, eval infrastructure.** 각 stage 마다 전용 judge 모듈 —
> 총 5개. 모두 tri-judge ensemble 에 연결됩니다. 거기에 LLM 이 놓칠
> deterministic probe — reasoning leak regex, Hangul 순도,
> diversity ratio — 를 더했습니다.
>
> `(point phase 3)`
>
> **3단계, iterate.** 이터당 가설 하나, sealed subagent 하나, 완전한
> judge report, git commit. Regress 면 롤백, win 이면 eager stack 으로
> 다음 이터 baseline 에 쌓습니다. Stage 1 에서만 **23번** 돌렸고,
> 한 이터당 약 13분 걸립니다.  `(click)`

---

## Slide 6 — Quality Engine  `(25 s)`  *가볍게*

> 저희 quality engine 은 세 가지를 하나로 엮은 구조입니다.  `(pause)`
>
> **LLM-as-Judge × 독립 judge 3개** — 이것이 **Wisdom of the Crowd**
> 입니다. mean 으로 promote 결정, high variance 는 block, agreement
> rate 로 confidence 가중. 거기에 judge 가 놓치는 지점을 위한
> deterministic probe — regex, count, ratio. Promote 결정은 단 하나 —
> **crowd 가 합의하고, probe 가 확증할 때.**  `(click)`

---

## Slide 7 — Results  `(35 s)`  *가볍게*

> 왼쪽이 **Stage 1**, 오른쪽이 **Stage 2**. 두 축으로 함께 봐 주시면
> 됩니다.  `(pause)`
>
> `(point left)`
>
> Stage 1 은 **23 이터 돌려서 10 gate 중 8 개 통과** — baseline 에선
> 1 개였습니다. Attribute grounding **0.47 → 0.99**, title reasoning
> leak 은 **0.47 → 0.01**, 47 % 에서 1 % 로. Persona reflection
> 3.6 → 4.7.
>
> `(point right)`
>
> Stage 2 는 시연 직전까지 **6 이터 진행해서 12 / 16 gate 통과** —
> baseline 9/16 에서 3 gate 추가. 주역은 **iter_04 C1
> canonical_suffix_enforce** — 단 한 장의 prompt patch 로 Stage 2.2
> 세 개 gate 를 한 번에 넘겼습니다. Stage 2.3 usefulness 는 trade-off
> 로 오히려 떨어졌어요 — 솔직한 숫자로 함께 보여드립니다.  `(click)`

---

## Slide 8 — Hypotheses: Wins & Losses  `(35 s)`  *가볍게*

> Stage 1 은 가설 **9 개 채택 11 개 롤백**, Stage 2 는 iter_04 C1
> 한 개 채택 SD-series 세 개 롤백.  `(pause)`
>
> **falsification 도 승리만큼 의미가 있었습니다.** H4 는 rating 분포를
> seed 쪽에서 고치려 했는데 코퍼스에 rating=3 리뷰가 literally
> zero — 원천적으로 불가능. H14 pure-Python dedup 은 0 건 제거로
> no-op.
>
> Stage 2 쪽도 같은 원리입니다. SD1 / SD2 는 retention 을 낮추면서
> downstream Stage 2.3 usefulness 가 깨졌고, **SD3 가 특히 흥미로웠는데** —
> keywords 를 signature 에서 빼면 구별력이 오히려 떨어졌습니다.
> keywords 는 noise 가 아니라 **signal** 이었다는 교훈.
> 모든 실패가 git 에 commit 된 **negative signal** — 13 분 이터라
> falsifiability 의 비용이 쌉니다.  `(click)`

---

## Slide 9 — Data, Use Cases, Q&A  `(45 s)`  **★ 중점**

> 마지막 조각입니다.  `(point left box)`
>
> **취득 데이터.** 1만 건의 한국 패션 리뷰 — 무신사, 네이버 쇼핑,
> 유튜브 출처. 합성 확장으로 5.5천 건의 curated 데이터. Stage 2
> clustering 결과 **260 canonical TPO**. 그리고 long-tail 은 noise 가
> 아닙니다 — **스크린골프, 필라테스 레이어, 분식룩** — 반복적으로
> 등장하는 실제 한국 쇼핑객 컨텍스트입니다.
>
> `(point right box)`
>
> **네 가지 적용처.** 첫째, **semantic search** — 출발점이었던
> 유스케이스로, 자연어 쿼리에서 canonical TPO 로, 다시 속성 필터로.
> 둘째, **추천** — 제품이 아닌 고객의 상황 단위로 intent bundle 을
> 랭킹합니다. 셋째, **광고·SEO 카피** — canonical 하나에 자연어
> variant 쿼리가 5개씩 따라옵니다. 넷째, **카탈로그 확장** —
> long-tail TPO 는 수요 신호입니다. "스크린골프" 가 리뷰에 반복
> 등장한다면, 인덱스할 가치가 있는 제품 라인이라는 뜻이죠.
>
> `(pause)`
>
> 감사합니다. 질문 받겠습니다.

---

## Delivery 체크리스트

- **페이스**: 한국어 발표 페이스 유지. 중점 슬라이드에서도 서두르지 말고.
  dry-run 으로 한 번 돌려서 **4:45 – 5:00** 에 랜딩하도록 — 10–15초 쿠션을
  남기는 게 이상적.
- **중점 슬라이드 (2, 3, 5, 9) 에서는 청중과 아이컨택.** 슬라이드가
  디테일을 담당하고, 발표자는 내러티브 flow 를 이끕니다.
- **`(pause)` 는 필수** — 5분 발표가 쫓기지 않고 여유 있게 보이게 하는
  유일한 장치입니다.
- 중간에 judge 가 질문으로 끊으면, 그 슬라이드 남은 스크립트는 스킵하고
  바로 진행 — 덱을 읽어주지 않습니다.
- Q&A fallback 라인:
  - *"judge bias 는 어떻게 방지하나요?"* → Slide 6, WoC + 다른 연구소 세 모델.
  - *"왜 fine-tuning 은 안 했나요?"* → Persona + prompt 로 충분했고,
    해커톤 시간 내에 수렴했습니다.
  - *"다음 계획은?"* → Stage 2 이터레이션 루프 (지금 돌고 있고, 결과는
    덱에 추가 예정).
