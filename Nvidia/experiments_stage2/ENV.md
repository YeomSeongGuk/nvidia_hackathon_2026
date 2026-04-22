# Stage 2 Environment — coupang + coupang2 topology

Records the coupang2 instance spec, network reachability, and which
routing option (PLAN §3b: A / B / C) the iter_run_stage2 driver uses.
Fill in as the two-instance bootstrap progresses.

> Status legend: `[ ]` pending, `[x]` confirmed, `[~]` partially done.

---

## 1. Instance identity

| field | value |
|---|---|
| Brev alias (`brev list` first column) | `coupang2` |
| Brev instance type / region | _TBD_ |
| Provisioned by | _sgyeom_ |
| First-boot date | _TBD_ |

## 2. Hardware — `brev exec coupang2 "nvidia-smi \| head -20 && free -h"`

| field | value |
|---|---|
| GPU count | _TBD_ |
| GPU model | _TBD_ |
| VRAM / GPU | _TBD_ |
| CPU cores | _TBD_ |
| Host RAM total | _TBD_ |

## 3. Python env — `brev exec coupang2 "python3 --version && which python3"`

- [ ] Python ≥ 3.10  on `coupang2`.
- [ ] venv path on `coupang2`: `~/.venv` (expected — matches `coupang`).
- [ ] Installed packages sanity:
  - `sentence-transformers` (BGE-M3 path)
  - `scikit-learn`, `scipy`, `numpy`, `pandas`
  - `pydantic`, `python-dotenv`
  - `FlagEmbedding` (optional, for BGE-M3 optimised path)
  - **NO vLLM client** on coupang2 (stays on coupang)

Quick smoke:

```bash
brev exec coupang2 "source ~/.venv/bin/activate && \\
  python -c 'import sentence_transformers, numpy, sklearn, scipy, pandas, pydantic; \\
  print(\"stage2-lite deps OK\")'"
```

## 4. Network reachability — coupang2 → coupang:5000

One-shot test from `coupang2`:

```bash
brev exec coupang2 "curl -sS -m 3 http://<coupang-internal-ip>:5000/v1/models | head -c 200"
```

| result | routing decision |
|---|---|
| `200 OK` with Nemotron listed | **Option A** — run Stage 2.2 (embed + LLM) end-to-end on `coupang2` |
| connection refused / timeout | **Option B** (default) — phase split: embed on `coupang2`, LLM on `coupang` |
| network unavailable | **Option C** — local broker (rarely needed) |

- [ ] Internal IP of `coupang` (noted here after `brev exec coupang "hostname -I"`): `_TBD_`
- [ ] Chosen routing option: `Option B (default)` until A is verified.

## 5. Brev copy round-trip (RTT) budget

Each Option B iter round-trips the Stage 2.2 cluster file between local,
coupang, and coupang2 up to 4 times. If one copy > 30 s, the phase-split
becomes the main wall-clock cost and Option A should be preferred.

Ping test: copy a 1 MB JSONL local → coupang2 → back, record wall time.

```bash
time brev copy /tmp/1mb.jsonl coupang2:/tmp/1mb_up.jsonl
time brev copy coupang2:/tmp/1mb_up.jsonl /tmp/1mb_down.jsonl
```

| direction | measured wall time |
|---|---|
| local → coupang2 | _TBD_ |
| coupang2 → local | _TBD_ |
| coupang → coupang2 (via local) | _TBD_ |

## 6. iter_run_stage2 environment overrides

Driver reads these from `os.environ` if set (see `scripts/iter_run_stage2.py`):

| env var | default | purpose |
|---|---|---|
| `COUPANG_HOST` | `coupang` | Brev alias for vLLM host |
| `COUPANG2_HOST` | `coupang2` | Brev alias for embedding host |
| `COUPANG_STAGE2_ROOT` | `/home/nvidia/experiments_data_stage2` | per-iter $STAGE_DATA_ROOT base on coupang |
| `COUPANG2_STAGE2_ROOT` | `/home/nvidia/experiments_data_stage2` | same on coupang2 |
| `COUPANG_VENV_PY` | `/home/nvidia/coupang/.venv/bin/python` | python interpreter on coupang |
| `COUPANG2_VENV_PY` | `/home/nvidia/coupang2/.venv/bin/python` | python interpreter on coupang2 |
| `COUPANG_PIPELINES_DIR` | `/home/nvidia/stage2_work` | pipelines/ deploy on coupang |
| `COUPANG2_PIPELINES_DIR` | `/home/nvidia/stage2_work` | pipelines/ deploy on coupang2 |

## 7. Running log

### 2026-04-22

- `experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl` pinned at
  `sha256:5e513bc75b3e3133546abfc72529f59850812e9fc133708610916b846fb640b6`
  (42 rows, from iter_21_dedup_v2).
- User confirmed `coupang2` is running and actively executing
  iter_26/iter_27 Stage 1 H10-realized experiments. Exact spec TBD.
- Stage 2 infra (stage_2_1_5_semdedup, stage_2_2 phase-split,
  iter_run_stage2, tri_judge_run_stage2, quant_stage2_report) all in
  tree as of commit `<pending>`. iter_run_stage2 defaults to
  `--stage22-mode full` (Option A) for iter_00_baseline; SD iters will
  enable phase_split once coupang2 details land here.
