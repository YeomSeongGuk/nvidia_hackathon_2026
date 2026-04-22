# Semantic Bridge PoC — 해커톤 계획서

## 한 줄 요약

고객 리뷰의 감성 표현("꾸안꾸", "하객룩")을 NeMo Curator로 큐레이션 → LLM으로 상품 속성에 매핑 → ES 임베딩 검색으로 시연

---

## 아키텍처

```
[Phase 1: 큐레이션]          [Phase 2: 추출]              [Phase 3: 시연]
NeMo Curator                 vLLM + Nemotron 3            Elasticsearch

네이버쇼핑 리뷰 20만건        큐레이션된 리뷰               semantic_bridge.jsonl
  + CC 블로그(선택)             ↓                            ↓
      ↓                    LLM Intent-Attribute 추출     ES 임베딩 인덱싱
 패션 필터링                    ↓                            ↓
 MinHash 중복제거           query_variations 생성         자연어 쿼리 → 속성 반환
 노이즈 필터링                  ↓
 품질 스코어링              semantic_bridge.jsonl
```

---

## 사용 도구

| 도구 | 용도 | 환경 |
|------|------|------|
| **NeMo Curator** | 중복제거, 필터링, 품질 분류 | GPU Jupyter |
| **vLLM + Nemotron 3 Nano** | LLM 추론 (Intent-Attribute 추출) | GPU Jupyter |
| **NeMo Data Designer** (선택) | 구조화 출력 (Pydantic 스키마 강제) | GPU Jupyter |
| **NIM Cloud API** | Fallback LLM (GPU 안 될 때) | 어디서든 |
| **Elasticsearch** | 임베딩 검색 시연 | 로컬 랩탑 |

---

## 데이터

| 데이터 | 건수 | 확보 | 시간 |
|--------|------|------|------|
| **네이버 쇼핑 리뷰** (bab2min/corpus) | 20만건 | curl 한 줄 | 즉시 |
| CC 한국어 패션 블로그 (선택) | 수천건 | CC Index → byte-range fetch | 1~2h |

---

## 시연 시나리오

```
입력: "비 오는 날 데이트룩"

→ ES 임베딩 검색 결과:
  Intent: rainy_day_date_look (score: 0.92)
  속성: material=나일론|폴리에스터, style=캐주얼, color=블랙|네이비
  근거: "287건 리뷰 분석, 방수 소재+레귤러핏 만족도 최고"
  → Shopping API 쿼리 변환 가능
```

---

## 타임라인 (20h)

| 시간 | Phase | 작업 |
|:----:|:-----:|------|
| 5h | **1. 큐레이션** | 데이터 다운로드 → NeMo Curator (필터/중복제거/품질) → 통계 산출 |
| 8h | **2. 추출** | Intent 설계(20~30개) → LLM 추출 파이프라인 → 검증 |
| 5h | **3. 시연** | ES 인덱싱 → 임베딩 검색 데모 → 발표 자료 |
| 2h | 버퍼 | 이슈 대응 |

---

## 환경 구성

```
GPU 머신 (Jupyter)                        로컬 랩탑
├─ vLLM + Nemotron 3 Nano (port 5000)    ├─ ES Docker (port 9200)
├─ NeMo Curator                           └─ 데모 스크립트
├─ 노트북 01~04
└─ 출력: semantic_bridge.jsonl ──scp──→ 입력
```

---

## 멀티모달 확장 (시간 여유 시)

- Musinsa Snap 이미지(28K건) + CLIP 임베딩 → 비주얼 속성 추가
- 추가 시간: +5h / 텍스트 파이프라인 완성 후에만 착수
