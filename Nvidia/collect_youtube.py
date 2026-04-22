# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
한국 패션 유튜버 영상 자막 추출 (curl + 직접 파싱)
"""
import subprocess
import re
import json
import html
import os
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def fetch_youtube_page(video_id: str) -> str:
    """curl로 YouTube 페이지 HTML 가져오기"""
    result = subprocess.run(
        ["curl", "-sk", f"https://www.youtube.com/watch?v={video_id}",
         "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
         "-H", "Accept-Language: ko-KR,ko;q=0.9"],
        capture_output=True, text=True, timeout=20
    )
    return result.stdout


def extract_transcript(page: str, prefer_lang="ko") -> tuple[str | None, str]:
    """HTML에서 자막 추출"""
    # captionTracks 찾기
    m = re.search(r'"captionTracks":\s*(\[.*?\])', page)
    if not m:
        return None, "자막 없음"

    tracks = json.loads(m.group(1))
    if not tracks:
        return None, "자막 트랙 비어있음"

    # 한국어 자막 우선 탐색
    target_track = None
    for track in tracks:
        lang = track.get("languageCode", "")
        if lang.startswith(prefer_lang):
            target_track = track
            break

    # 없으면 자동생성 한국어
    if not target_track:
        for track in tracks:
            if track.get("kind") == "asr" and prefer_lang in track.get("languageCode", ""):
                target_track = track
                break

    # 그래도 없으면 첫 번째 (보통 원본 언어)
    if not target_track:
        target_track = tracks[0]

    caption_url = target_track.get("baseUrl", "")
    if not caption_url:
        return None, "자막 URL 없음"

    lang = target_track.get("languageCode", "?")
    kind = "자동생성" if target_track.get("kind") == "asr" else "수동"

    # 자막 XML 다운로드
    result = subprocess.run(
        ["curl", "-sk", caption_url], capture_output=True, text=True, timeout=15
    )
    xml_text = result.stdout

    # XML에서 텍스트 추출
    segments = re.findall(r'<text[^>]*>(.*?)</text>', xml_text)
    texts = [html.unescape(s).replace('\n', ' ').strip() for s in segments if s.strip()]

    if not texts:
        return None, f"자막 세그먼트 없음 ({lang})"

    full_text = " ".join(texts)
    return full_text, f"{lang}/{kind}/{len(texts)}세그먼트"


def get_video_title(page: str) -> str:
    m = re.search(r'"title":"(.*?)"', page)
    return m.group(1) if m else "unknown"


# ═══════════════════════════════════════════════════════════
# 한국 패션 유튜버 영상 목록
# 실제 유튜브에서 "하객룩" "남자 코디" "꾸안꾸" 등 검색 후 인기 영상 선별
# ═══════════════════════════════════════════════════════════

# 먼저 유튜브 검색으로 실제 패션 영상 ID를 확보
SEARCH_QUERIES = [
    "하객룩 코디 추천",
    "꾸안꾸 데일리룩 코디",
    "남자 봄 코디 추천",
    "여름 데이트룩 코디",
    "출근룩 직장인 코디",
    "고프코어 코디 남자",
    "캠퍼스룩 대학생",
    "겨울 코트 코디",
    "트위드 자켓 코디",
    "비즈니스캐주얼 남자",
]

print("=" * 60)
print("Step 1: 유튜브 검색으로 패션 영상 ID 수집")
print("=" * 60)

video_candidates = []

for query in SEARCH_QUERIES:
    try:
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        result = subprocess.run(
            ["curl", "-sk", search_url,
             "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
             "-H", "Accept-Language: ko-KR,ko;q=0.9"],
            capture_output=True, text=True, timeout=20
        )
        page = result.stdout

        # 영상 ID 추출
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', page)
        # 중복 제거하면서 순서 유지
        seen = set()
        unique_ids = []
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                unique_ids.append(vid)

        # 상위 2개만
        for vid in unique_ids[:2]:
            video_candidates.append({"id": vid, "query": query})

        print(f"  '{query}': {len(unique_ids)}개 발견, 상위 2개 선택")

    except Exception as e:
        print(f"  '{query}': {type(e).__name__}")

    time.sleep(1)

# 중복 영상 제거
seen_ids = set()
unique_candidates = []
for v in video_candidates:
    if v["id"] not in seen_ids:
        seen_ids.add(v["id"])
        unique_candidates.append(v)

print(f"\n총 후보 영상: {len(unique_candidates)}개")


# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Step 2: 자막 추출 (상위 10개)")
print("=" * 60)

results = []

for v in unique_candidates[:15]:  # 최대 15개 시도, 10개 목표
    if len(results) >= 10:
        break

    try:
        page = fetch_youtube_page(v["id"])
        title = get_video_title(page)
        text, info = extract_transcript(page, prefer_lang="ko")

        if text and len(text) > 100:
            results.append({
                "id": f"yt_{v['id']}",
                "source": "youtube_transcript",
                "video_id": v["id"],
                "title": title,
                "query": v["query"],
                "text": text,
                "text_length": len(text),
                "caption_info": info,
            })
            print(f"  ✓ {title[:50]}... ({len(text)}자, {info})")
            print(f"    → {text[:120]}...")
        else:
            print(f"  ✗ {title[:50]}... - {info}")

    except Exception as e:
        print(f"  ✗ {v['id']}: {type(e).__name__}")

    time.sleep(1)

# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"결과: {len(results)}건 자막 추출 성공")
print("=" * 60)

if results:
    out_path = os.path.join(DATA_DIR, "youtube_transcripts.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"저장: {out_path}")

    total_chars = sum(r["text_length"] for r in results)
    print(f"총 텍스트: {total_chars:,}자")

    for r in results:
        print(f"\n  [{r['query']}] {r['title'][:60]}")
        print(f"    {r['text'][:150]}...")
