"""Evidence-bound model allocation benchmark for MODE:P.

This harness does not call models and does not infer creative quality from local
tool speed.  It evaluates fixed regression outputs against the active MODE:P
contracts, then combines those results with optional real model run records.

Director allocation remains quality-first.  DP can be moved to a faster model
only when real run records cover every fixed DP case, pass without regression,
and beat the current DP baseline on median elapsed time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from dp_contract import parse_dp_feedback, validate_dp_contract
from structural_precheck import run_precheck


SCHEMA_VERSION = "mode_p_model_allocation_benchmark_v1"
RUN_RECORD_SCHEMA_VERSION = "mode_p_model_run_record_v1"
CURRENT_DIRECTOR_POLICY = "retain_strongest_available_model"
CURRENT_DP_POLICY = "retain_current_dp_model_until_real_evidence"



_DIRECTOR_MASTER = """\
Master 版本：BENCH_S1/v2.0

## 1. 场景设计
场景前状态：Rico 坐在桌前听录音。
戏剧变化：Rico 从接收信息转为收起证据。
信息策略：先建立桌面证据，再把注意力转到手部动作。
场景后状态：Rico 握着录音笔转向门口。
场景空间：4m×5m 工作室，桌子居中，门在左后方。
关系线：Rico 与录音笔形成前后轴线。
人物路径：Rico 从椅子前起身并转向门口。
摄影可用区域：桌前和桌侧通道可放置机位。
视觉策略：固定机位与收紧景别突出证据，4300K台灯保持主光方向。
镜头拆分理由：右手停在录音笔旁时从关系镜切入动作镜。
场间关系：黑场进入，Rico 转向门口后离场。
场景蓝图：[D] 夜间工作室内，Rico 从桌前观察转为起身收起录音笔，台灯与门缝暖光给出明确空间方向。
声音基调：[D] 台灯电流声和远处街道低频声持续，录音笔按键声出现在第二镜。

## Boundary BENCH_S1-B0 | SCENE_ENTRY -> BENCH_S1-1
边界关系：[M] <scene_entry>
转场执行：[M] <post_production>
剪辑触发：[D] 黑场在台灯电流声建立后切入。
交接描述：[D] Rico 坐在桌前，录音笔位于桌面中央，台灯照亮桌面。
接入状态键：[M]
  - character:Rico position:desk_front facing:N screen_direction:static posture:sitting wardrobe:dark_jacket
  - prop:recorder held_by:none location:desk_center
  - light_main direction:desk_lamp color_temp:4300K ratio:1:4
  - action_phase:static

## Shot BENCH_S1-1 | 6s
叙事职责：[D] 建立 Rico 与桌面证据的关系。
剧本事实：[D] Rico watches the recorder on the desk.
原文定位：[M] BENCH_S1 L1-L3
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <investigation_object>
时间控制：[M] <event_nodes>
摄影设计：[D] 桌面高度固定机位，50mm中近景压缩桌面与人物距离。
构图设计：[D] 录音笔位于下方三分线，Rico面部居中，门缝暖光形成后景深度。
光影设计：[D] 4300K台灯从右侧照亮桌面，Rico面部一半进入阴影，光比1:4。
表演设计：[D] Rico视线固定在录音笔，右手缓慢稳定地靠近。
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无
视觉时间线：[D] [0.0s][SB] Rico坐在桌前，录音笔位于桌面中央，台灯照亮桌面。
  [3.0s][SB] Rico右手从桌边移动到录音笔旁，视线保持在录音笔上。
  [6.0s][SB] Rico右手停在录音笔右侧，录音笔保持在桌面中央。
声音设计：[D] 台灯电流声持续，远处街道低频声稳定。

## Boundary BENCH_S1-B1 | BENCH_S1-1 -> BENCH_S1-2
边界关系：[M] <continuous>
转场执行：[M] <post_production>
剪辑触发：[D] Rico右手停在录音笔右侧时硬切。
交接描述：[D] Rico坐在桌前，右手停在录音笔右侧，视线落在录音笔上。
交出状态键：[M]
  - character:Rico position:desk_front facing:N screen_direction:static posture:sitting wardrobe:dark_jacket
  - prop:recorder held_by:none location:desk_center
  - light_main direction:desk_lamp color_temp:4300K ratio:1:4
  - action_phase:prepare
接入状态键：[M] <same>

## Shot BENCH_S1-2 | 5s
叙事职责：[D] Rico收起录音笔并准备离开。
剧本事实：[D] Rico picks up the recorder and turns toward the door.
原文定位：[M] BENCH_S1 L4-L6
生成单元：[M] 一个独立 SD2.0 视频段，时长从 0 秒到本镜 duration。
场景表达：[M] <action_chase>
时间控制：[M] <second_nodes>
摄影设计：[D] 桌面近景固定机位，70mm，焦点从录音笔移动到Rico右手。
构图设计：[D] Rico右手占据右下三分区，录音笔居中偏下，门缝暖光保持左后景锚点。
光影设计：[D] 4300K台灯保持主光，门缝暖光标明门口方向，光比1:4。
表演设计：[D] Rico手指握紧录音笔，拇指按键，起身时头部先转向门口。
生成模式：[M] <text_only>
参考资产：[M] 无
参考职责：[D] 无
参考优先级：[D] 无
视觉时间线：[D] [0.0s][SB] Rico坐在桌前，右手停在录音笔右侧，视线落在录音笔上。
  [1.0s] Rico右手握住录音笔。
  [2.0s][SB] Rico拿起录音笔，桌面中央露出空位。
  [3.0s][SB] Rico拇指按下录音笔停止键。
  [4.0s] Rico从椅子前起身，头部先转向门口。
  [5.0s][SB] Rico站在桌侧，右手握着录音笔，身体朝向门口。
声音设计：[D] 2秒出现桌面轻响，3秒出现按键声，4秒出现椅子摩擦声。

## Boundary BENCH_S1-B2 | BENCH_S1-2 -> SCENE_EXIT
边界关系：[M] <scene_exit>
转场执行：[M] <post_production>
剪辑触发：[D] Rico身体转向门口并站稳后硬切离场。
交接描述：[D] Rico站在桌侧，右手握着录音笔，身体朝向门口。
交出状态键：[M]
  - character:Rico position:desk_side facing:W screen_direction:right_to_left posture:standing wardrobe:dark_jacket
  - prop:recorder held_by:Rico location:right_hand
  - light_main direction:desk_lamp color_temp:4300K ratio:1:4
  - action_phase:recover
"""


@dataclass(frozen=True)
class RegressionResult:
    role: str
    case_id: str
    passed: bool
    elapsed_s: float
    iterations: int
    input_hash: str
    output_hash: str
    checks: dict[str, bool] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelRunRecord:
    schema_version: str
    role: str
    model: str
    case_id: str
    input_hash: str
    output_hash: str
    elapsed_s: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkReport:
    schema_version: str = SCHEMA_VERSION
    results: list[RegressionResult] = field(default_factory=list)
    total_elapsed_s: float = 0.0

    @property
    def ok(self) -> bool:
        return all(item.passed for item in self.results)

    def case_ids(self, role: str | None = None) -> set[str]:
        return {
            item.case_id
            for item in self.results
            if role is None or item.role == role
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "results": [item.to_dict() for item in self.results],
            "total_elapsed_s": self.total_elapsed_s,
        }


def run_benchmarks(iterations: int = 1) -> BenchmarkReport:
    """Run fixed local regressions used by model-allocation decisions."""
    if iterations < 1:
        raise ValueError("iterations must be >= 1")

    results = [
        _repeat_case("director", "director_structural_regression", iterations,
                     _run_director_structural_case, _DIRECTOR_MASTER),
        *[
            _repeat_case("dp", case["case_id"], iterations,
                         lambda current=case: _run_dp_case(current),
                         case["feedback"])
            for case in _dp_cases()
        ],
    ]
    return BenchmarkReport(
        results=results,
        total_elapsed_s=sum(item.elapsed_s for item in results),
    )


def allocation_advice(
    report: BenchmarkReport,
    run_records: Iterable[ModelRunRecord] | None = None,
    current_dp_model: str | None = None,
) -> dict[str, Any]:
    """Return model allocation advice from regression and real-run evidence."""
    current_dp_model = current_dp_model or CURRENT_DP_POLICY
    records = list(run_records or [])
    dp_case_ids = report.case_ids("dp")

    advice: dict[str, Any] = {
        "director_model": CURRENT_DIRECTOR_POLICY,
        "dp_model": current_dp_model,
        "status": "retain",
        "rationale": (
            "Director stays on the strongest available model because local "
            "structure checks do not measure creative directing quality."
        ),
        "eligible_dp_candidates": [],
        "missing_evidence": [],
    }

    if not report.ok:
        advice.update({
            "status": "blocked",
            "rationale": "Fixed local regressions are failing; model allocation evidence is invalid.",
        })
        return advice

    if not records:
        advice.update({
            "status": "insufficient_evidence",
            "rationale": (
                "No real model run records were supplied. DP cannot be moved "
                "to a faster model without fixed-case outputs and elapsed time."
            ),
        })
        return advice

    by_model: dict[str, list[ModelRunRecord]] = {}
    for record in records:
        if record.role == "dp":
            by_model.setdefault(record.model, []).append(record)

    complete: dict[str, list[ModelRunRecord]] = {}
    missing: dict[str, list[str]] = {}
    for model, model_records in by_model.items():
        covered = {record.case_id for record in model_records if record.passed}
        absent = sorted(dp_case_ids - covered)
        failed = sorted({record.case_id for record in model_records if not record.passed})
        if absent or failed:
            missing[model] = absent + [f"{case_id}:failed" for case_id in failed]
            continue
        complete[model] = model_records

    baseline_model = current_dp_model if current_dp_model in complete else None
    if baseline_model is None:
        advice.update({
            "status": "insufficient_evidence",
            "missing_evidence": missing or {current_dp_model: sorted(dp_case_ids)},
            "rationale": (
                "No complete passing real-run baseline exists for the current DP model; "
                "speed comparisons would be ungrounded."
            ),
        })
        return advice

    baseline_median = _median_elapsed(complete[baseline_model])
    candidates: list[tuple[str, float]] = []
    for model, model_records in complete.items():
        if model == baseline_model:
            continue
        median = _median_elapsed(model_records)
        if median < baseline_median:
            candidates.append((model, median))

    candidates.sort(key=lambda item: item[1])
    advice["eligible_dp_candidates"] = [
        {"model": model, "median_elapsed_s": elapsed}
        for model, elapsed in candidates
    ]
    if candidates:
        chosen, median = candidates[0]
        advice.update({
            "status": "eligible",
            "dp_model": chosen,
            "rationale": (
                f"{chosen} passed every fixed DP regression and median elapsed "
                f"{median:.3f}s is below current baseline {baseline_model} "
                f"({baseline_median:.3f}s)."
            ),
        })
    else:
        advice.update({
            "status": "retain",
            "missing_evidence": missing,
            "rationale": (
                "No alternative DP model both passed every fixed regression and "
                "beat the current baseline median elapsed time."
            ),
        })
    return advice


def load_model_run_records(runs_dir: Path) -> list[ModelRunRecord]:
    """Load real model run records from a directory of JSON files."""
    if not runs_dir.exists():
        raise FileNotFoundError(runs_dir)
    records: list[ModelRunRecord] = []
    for path in sorted(runs_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != RUN_RECORD_SCHEMA_VERSION:
            continue
        records.append(ModelRunRecord(
            schema_version=data["schema_version"],
            role=data["role"],
            model=data["model"],
            case_id=data["case_id"],
            input_hash=data["input_hash"],
            output_hash=data["output_hash"],
            elapsed_s=float(data["elapsed_s"]),
            passed=bool(data["passed"]),
        ))
    return records


def _repeat_case(
    role: str,
    case_id: str,
    iterations: int,
    runner,
    input_text: str,
) -> RegressionResult:
    elapsed: list[float] = []
    last: RegressionResult | None = None
    for _ in range(iterations):
        started = time.monotonic()
        current = runner()
        elapsed.append(time.monotonic() - started)
        last = current
    assert last is not None
    return RegressionResult(
        role=role,
        case_id=case_id,
        passed=last.passed,
        elapsed_s=sum(elapsed) / len(elapsed),
        iterations=iterations,
        input_hash=_sha256_text(input_text),
        output_hash=last.output_hash,
        checks=last.checks,
        problems=last.problems,
    )


def _run_director_structural_case() -> RegressionResult:
    with tempfile.TemporaryDirectory(prefix="mode_p_director_bench_") as temp:
        root = Path(temp)
        session = root / "session"
        session.mkdir()
        master_path = session / "DIRECTOR_MASTER.md"
        master_path.write_text(_DIRECTOR_MASTER, encoding="utf-8")

        report = run_precheck(master_path, session)
        checks = {item.name: item.passed for item in report.results}
        problems = [
            f"{item.name}: {item.output.strip()}"
            for item in report.results
            if not item.passed
        ]
        output_payload = {
            "checks": checks,
            "manifest": _read_if_exists(session / "working" / "SHOT_MANIFEST.json"),
            "storyboard": _read_if_exists(session / "working" / "STORYBOARD.md"),
            "video": _read_if_exists(session / "working" / "VIDEO_PROMPT.md"),
        }
        return RegressionResult(
            role="director",
            case_id="director_structural_regression",
            passed=report.ok,
            elapsed_s=0.0,
            iterations=1,
            input_hash=_sha256_text(_DIRECTOR_MASTER),
            output_hash=_sha256_json(output_payload),
            checks=checks,
            problems=problems,
        )


def _run_dp_case(case: dict[str, Any]) -> RegressionResult:
    feedback = parse_dp_feedback(case["feedback"])
    valid, problems = validate_dp_contract(feedback, set(case["valid_shot_ids"]))
    identities = sorted(
        (issue.shot_id, issue.field)
        for issue in feedback.issues
    )
    expected_identities = sorted(tuple(item) for item in case["expected_issues"])
    passed = (
        valid == case["expected_valid"]
        and feedback.status == case["expected_status"]
        and identities == expected_identities
    )
    if not passed:
        problems = list(problems) + [
            f"expected_valid={case['expected_valid']} got={valid}",
            f"expected_status={case['expected_status']} got={feedback.status}",
            f"expected_issues={expected_identities} got={identities}",
        ]
    output_payload = {
        "valid": valid,
        "status": feedback.status,
        "issues": identities,
        "problems": problems,
    }
    return RegressionResult(
        role="dp",
        case_id=case["case_id"],
        passed=passed,
        elapsed_s=0.0,
        iterations=1,
        input_hash=_sha256_text(case["feedback"]),
        output_hash=_sha256_json(output_payload),
        checks={
            "parse": feedback.status != "invalid" or not case["expected_valid"],
            "contract": valid == case["expected_valid"],
            "issue_identity": identities == expected_identities,
        },
        problems=list(problems),
    )


def _dp_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "dp_ready_clean",
            "feedback": (
                "READY BENCH_S1: Shot BENCH_S1-1 与 Shot BENCH_S1-2 的共享边界"
                "保持右手位置和主光方向一致。"
            ),
            "valid_shot_ids": ["BENCH_S1-1", "BENCH_S1-2"],
            "expected_valid": True,
            "expected_status": "ready",
            "expected_issues": [],
        },
        {
            "case_id": "dp_expected_issues",
            "feedback": (
                "BENCH_S1-1: camera_path — 桌面高度固定机位需要避开台灯底座。\n"
                "BENCH_S1-2: light_source — 门缝暖光需要在空间描述中保持同一方向。"
            ),
            "valid_shot_ids": ["BENCH_S1-1", "BENCH_S1-2"],
            "expected_valid": True,
            "expected_status": "issues",
            "expected_issues": [
                ("BENCH_S1-1", "camera_path"),
                ("BENCH_S1-2", "light_source"),
            ],
        },
        {
            "case_id": "dp_rejects_unknown_shot",
            "feedback": "BENCH_S1-9: camera_path — 这个镜头不在当前 Manifest 中。",
            "valid_shot_ids": ["BENCH_S1-1", "BENCH_S1-2"],
            "expected_valid": False,
            "expected_status": "issues",
            "expected_issues": [("BENCH_S1-9", "camera_path")],
        },
    ]


def _median_elapsed(records: list[ModelRunRecord]) -> float:
    return float(statistics.median(record.elapsed_s for record in records))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(data: Any) -> str:
    payload = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return _sha256_text(payload)


def _read_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _print_text_report(report: BenchmarkReport, advice: dict[str, Any] | None) -> None:
    print(f"MODE:P model-allocation benchmark ({report.schema_version})")
    for item in report.results:
        status = "PASS" if item.passed else "FAIL"
        print(f"  [{status}] {item.role}:{item.case_id} {item.elapsed_s:.4f}s")
        for problem in item.problems[:3]:
            print(f"    {problem}")
    print(f"  Total local elapsed: {report.total_elapsed_s:.4f}s")
    if advice is not None:
        print("Allocation evidence:")
        print(f"  Director: {advice['director_model']}")
        print(f"  DP: {advice['dp_model']}")
        print(f"  Status: {advice['status']}")
        print(f"  Rationale: {advice['rationale']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate MODE:P model allocation with fixed regressions."
    )
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--advice", action="store_true")
    parser.add_argument("--runs-dir", type=Path,
                        help="Directory containing real model run record JSON files")
    parser.add_argument("--current-dp-model", default=CURRENT_DP_POLICY)
    args = parser.parse_args()

    report = run_benchmarks(iterations=args.iterations)
    records = load_model_run_records(args.runs_dir) if args.runs_dir else []
    advice = (
        allocation_advice(report, records, args.current_dp_model)
        if args.advice else None
    )

    if args.json:
        data = report.to_dict()
        if args.advice:
            data["allocation_advice"] = advice
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _print_text_report(report, advice)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
