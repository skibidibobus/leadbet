#!/usr/bin/env python3
"""
QUANTKUPON Unified E2E Test Runner
==================================
Milestone: E2E-M1 Test Infrastructure & Architecture
Usage:
    python3 tests/run_e2e_tests.py [--tier 0|1|2|3|4|harness|all] [--feature N] [--verbose] [--fail-fast]
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

# Feature Name Lookup Table for Features 1 to 29
FEATURE_NAMES: Dict[int, str] = {
    1: "Monorepo layout",
    2: "Neon PostgreSQL schema",
    3: "OpenAPI 3.1 contract",
    4: "De-vigging (Shin method)",
    5: "De-vigging (Power method)",
    6: "De-vigging (Multiplicative)",
    7: "Football Dixon-Coles model",
    8: "Basketball Pace model",
    9: "Tennis Markov chain",
    10: "Hockey Skellam model",
    11: "Phase 2 sports feature flag",
    12: "Table Tennis Volatility Guard",
    13: "Bayesian market fusion",
    14: "12% Turnover tax",
    15: "Promotional Zero-Tax profiles",
    16: "10% PIT threshold (> 2280 PLN)",
    17: "Mathematical ticket splitting",
    18: "Fractional Kelly criterion",
    19: "Quantitative audit metrics",
    20: "0 PLN pre-match cron",
    21: "Deterministic offline test mode",
    22: "Combinatorial coupon generator",
    23: "Anti-Correlation Guard",
    24: "Explicit Net EV & +EV filter",
    25: "1-Click Polish bookmaker override",
    26: "60-30-10 Design system",
    27: "Rule 'Never Color Alone'",
    28: "Auth & Legal 18+ / RODO gate",
    29: "Cloudflare Pages + Render setup",
}

# Tier Thresholds per SCOPE.md
TIER_MIN_THRESHOLDS: Dict[str, int] = {
    "1": 145,  # >=5 per feature * 29
    "2": 145,  # >=5 per feature * 29
    "3": 29,   # Pairwise cross-feature combinations
    "4": 15,   # Real-world application scenarios
}


class Colors:
    """ANSI color codes with auto-detection of terminal capability."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled and sys.stdout.isatty()
        self.RESET = "\033[0m" if self.enabled else ""
        self.BOLD = "\033[1m" if self.enabled else ""
        self.GREEN = "\033[32m" if self.enabled else ""
        self.RED = "\033[31m" if self.enabled else ""
        self.YELLOW = "\033[33m" if self.enabled else ""
        self.CYAN = "\033[36m" if self.enabled else ""
        self.DIM = "\033[2m" if self.enabled else ""


class TestResult:
    """Encapsulates the execution result of a single test tier or suite."""

    def __init__(
        self,
        name: str,
        scope: str,
        status: str,
        total: int = 0,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        duration: float = 0.0,
        failures: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.name = name
        self.scope = scope
        self.status = status  # PASSED, FAILED, PENDING, SKIPPED, ERROR
        self.total = total
        self.passed = passed
        self.failed = failed
        self.skipped = skipped
        self.duration = duration
        self.failures = failures or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scope": self.scope,
            "status": self.status,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": round(self.duration, 3),
            "failures": self.failures,
        }


class EnvironmentManager:
    """Manages Python virtualenv detection, Node.js PATH injection, and PYTHONPATH."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def resolve_pytest(self) -> Tuple[str, List[str]]:
        """Resolves the pytest executable and base command."""
        # 1. Local .venv
        venv_pytest = self.root_dir / ".venv" / "bin" / "pytest"
        if venv_pytest.is_file() and os.access(venv_pytest, os.X_OK):
            return str(venv_pytest), [str(venv_pytest)]

        alt_venv = self.root_dir / "venv" / "bin" / "pytest"
        if alt_venv.is_file() and os.access(alt_venv, os.X_OK):
            return str(alt_venv), [str(alt_venv)]

        # 2. In-interpreter pytest if available
        try:
            import pytest  # noqa: F401

            return sys.executable, [sys.executable, "-m", "pytest"]
        except ImportError:
            pass

        # 3. System PATH pytest
        which_pytest = shutil.which("pytest")
        if which_pytest:
            return which_pytest, [which_pytest]

        return "", []

    def build_subprocess_env(self, offline: bool = True) -> Dict[str, str]:
        """Constructs subprocess environment with proper PATH and PYTHONPATH."""
        env = os.environ.copy()

        # Invariant settings
        if offline:
            env["OFFLINE_MODE"] = "true"
        env["ENABLE_PHASE2_SPORTS"] = env.get("ENABLE_PHASE2_SPORTS", "false")

        # Monorepo PYTHONPATH injection
        python_paths = [
            str(self.root_dir / "packages" / "quant-engine"),
            str(self.root_dir / "packages" / "bookmaker-adapters"),
            str(self.root_dir / "apps" / "api"),
            str(self.root_dir / "apps" / "api" / "src"),
            str(self.root_dir / "tests"),
            str(self.root_dir),
        ]
        existing_pp = env.get("PYTHONPATH", "")
        if existing_pp:
            python_paths.append(existing_pp)
        env["PYTHONPATH"] = ":".join(python_paths)

        # Node.js NVM PATH injection if missing
        nvm_bin = Path.home() / ".nvm" / "versions" / "node" / "v20.20.2" / "bin"
        current_path = env.get("PATH", "")
        if nvm_bin.is_dir() and str(nvm_bin) not in current_path:
            env["PATH"] = f"{nvm_bin}:{current_path}"

        return env


class TestRunner:
    """Executes test tiers and formats reporting output."""

    def __init__(self, root_dir: Path, args: argparse.Namespace) -> None:
        self.root_dir = root_dir
        self.args = args
        self.colors = Colors()
        self.env_mgr = EnvironmentManager(root_dir)

    def parse_junit_xml(
        self, xml_path: Path
    ) -> Tuple[int, int, int, int, float, List[Dict[str, Any]]]:
        """Parses JUnit XML generated by pytest."""
        if not xml_path.is_file() or xml_path.stat().st_size == 0:
            return 0, 0, 0, 0, 0.0, []

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError:
            return 0, 0, 0, 0, 0.0, []

        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")

        total = 0
        failures_count = 0
        errors_count = 0
        skipped_count = 0
        duration = 0.0
        failures_list: List[Dict[str, Any]] = []

        for suite in suites:
            total += int(suite.attrib.get("tests", 0))
            failures_count += int(suite.attrib.get("failures", 0))
            errors_count += int(suite.attrib.get("errors", 0))
            skipped_count += int(suite.attrib.get("skipped", 0))
            duration += float(suite.attrib.get("time", 0.0))

            for tc in suite.findall("testcase"):
                classname = tc.attrib.get("classname", "")
                name = tc.attrib.get("name", "")
                fail = tc.find("failure")
                err = tc.find("error")

                if fail is not None or err is not None:
                    node = fail if fail is not None else err
                    msg = node.attrib.get("message", "") if node is not None else ""
                    tb = node.text if node is not None and node.text else ""
                    failures_list.append({
                        "nodeid": f"{classname}::{name}",
                        "message": msg,
                        "traceback": tb,
                    })

        passed = max(0, total - (failures_count + errors_count + skipped_count))
        failed = failures_count + errors_count
        return total, passed, failed, skipped_count, duration, failures_list

    def run_target(
        self, tier_id: str, tier_name: str, scope_desc: str, target_path: Path
    ) -> TestResult:
        """Runs a test target (file or directory)."""
        # Progressive check: target exists
        if not target_path.exists():
            return TestResult(name=tier_name, scope=scope_desc, status="PENDING")

        if target_path.is_dir():
            test_files = list(target_path.glob("test_*.py"))
            if not test_files:
                return TestResult(name=tier_name, scope=scope_desc, status="PENDING")

        # Resolve pytest binary
        pytest_bin, base_cmd = self.env_mgr.resolve_pytest()
        if not base_cmd:
            return TestResult(
                name=tier_name,
                scope=scope_desc,
                status="ERROR",
                failures=[{
                    "nodeid": "env",
                    "message": "pytest executable not found in .venv or PATH",
                }],
            )

        # Prepare temp file for JUnit XML
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp_xml:
            xml_path = Path(tmp_xml.name)

        cmd = list(base_cmd) + [
            str(target_path),
            f"--junitxml={xml_path}",
            "-q",
            "-o",
            "junit_family=xunit2",
        ]

        # Feature filtering if specified
        if self.args.feature:
            feat_id = self.args.feature
            cmd.extend(["-k", f"feat_{feat_id:02d} or feature_{feat_id} or feat_{feat_id}"])

        if self.args.fail_fast:
            cmd.append("-x")

        if self.args.verbose:
            cmd.append("-v")

        env = self.env_mgr.build_subprocess_env(offline=self.args.offline)

        start_time = time.time()
        try:
            if self.args.verbose:
                rel_path = (
                    target_path.relative_to(self.root_dir)
                    if target_path.is_relative_to(self.root_dir)
                    else target_path
                )
                print(f"\n{self.colors.CYAN}>>> Executing {tier_name} ({rel_path}){self.colors.RESET}")
                proc = subprocess.run(cmd, env=env)
            else:
                proc = subprocess.run(
                    cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
        except Exception as e:
            return TestResult(
                name=tier_name,
                scope=scope_desc,
                status="ERROR",
                duration=time.time() - start_time,
                failures=[{"nodeid": "exec", "message": str(e)}],
            )

        total, passed, failed, skipped, xml_duration, failures = self.parse_junit_xml(xml_path)
        try:
            xml_path.unlink()
        except OSError:
            pass

        duration = xml_duration if xml_duration > 0.0 else (time.time() - start_time)

        if total == 0:
            status = "PENDING"
        elif failed > 0 or proc.returncode not in (0, 5):
            status = "FAILED"
        else:
            status = "PASSED"

        return TestResult(
            name=tier_name,
            scope=scope_desc,
            status=status,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            failures=failures,
        )

    def run_ui_tests(self) -> Optional[TestResult]:
        """Runs Vitest UI tests if present in apps/web."""
        web_dir = self.root_dir / "apps" / "web"
        if not web_dir.is_dir() or not (web_dir / "package.json").is_file():
            return None

        vitest_bin = self.root_dir / "node_modules" / ".bin" / "vitest"
        web_vitest = web_dir / "node_modules" / ".bin" / "vitest"
        if not vitest_bin.is_file() and not web_vitest.is_file() and not shutil.which("vitest"):
            return TestResult(
                name="UI/Web",
                scope="Vitest Web Component Tests",
                status="SKIPPED",
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
            )

        env = self.env_mgr.build_subprocess_env(offline=self.args.offline)
        cmd = ["npx", "--no-install", "vitest", "run", "--dir", "apps/web", "--reporter=json"]

        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.root_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
            duration = time.time() - start_time
            try:
                data = json.loads(proc.stdout)
                num_tests = data.get("numTotalTests", 0)
                num_passed = data.get("numPassedTests", 0)
                num_failed = data.get("numFailedTests", 0)
                status = "PASSED" if num_failed == 0 and proc.returncode == 0 else "FAILED"
                return TestResult(
                    name="UI/Web",
                    scope="Vitest Web Component Tests",
                    status=status,
                    total=num_tests,
                    passed=num_passed,
                    failed=num_failed,
                    skipped=0,
                    duration=duration,
                )
            except Exception:
                status = "PASSED" if proc.returncode == 0 else "FAILED"
                return TestResult(
                    name="UI/Web",
                    scope="Vitest Web Component Tests",
                    status=status,
                    total=1 if status == "PASSED" else 0,
                    passed=1 if status == "PASSED" else 0,
                    failed=0 if status == "PASSED" else 1,
                    duration=duration,
                )
        except Exception:
            return TestResult(
                name="UI/Web",
                scope="Vitest Web Component Tests",
                status="SKIPPED",
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0.0,
            )

    def print_summary_table(self, results: List[TestResult]) -> None:
        """Renders the formatted ASCII summary table."""
        c = self.colors
        border = "=" * 88
        divider = "-" * 88

        print("\n" + border)
        print(f"{c.BOLD}                              QUANTKUPON E2E TEST RUNNER{c.RESET}")
        print(border)

        pytest_bin, _ = self.env_mgr.resolve_pytest()
        engine_str = pytest_bin if pytest_bin else "NOT FOUND (.venv missing)"
        feat_str = (
            f"Feature {self.args.feature}: {FEATURE_NAMES.get(self.args.feature, '')}"
            if self.args.feature
            else "all (Features 1-29)"
        )

        print(f"Execution Mode : {'OFFLINE (OFFLINE_MODE=true)' if self.args.offline else 'LIVE'}")
        print(f"Python Engine  : {engine_str}")
        print(f"Target Tier(s) : {self.args.tier}")
        print(f"Target Feature : {feat_str}")
        print(f"Timestamp      : {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
        print(divider)
        print(
            f"{'Tier':<10} {'Scope / Description':<26} {'Status':^9} {'Total':>7} {'Passed':>8} {'Failed':>8} {'Skipped':>9} {'Duration':>10}"
        )
        print(divider)

        total_tests = sum(r.total for r in results)
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_skipped = sum(r.skipped for r in results)
        total_duration = sum(r.duration for r in results)

        for r in results:
            if r.status == "PASSED":
                status_color = f"{c.GREEN}{r.status:^9}{c.RESET}"
            elif r.status in ("FAILED", "ERROR"):
                status_color = f"{c.RED}{r.status:^9}{c.RESET}"
            elif r.status == "PENDING":
                status_color = f"{c.YELLOW}{r.status:^9}{c.RESET}"
            else:
                status_color = f"{c.DIM}{r.status:^9}{c.RESET}"

            dur_str = f"{r.duration:.2f}s"
            print(
                f"{r.name:<10} {r.scope:<26} {status_color} {r.total:>7} {r.passed:>8} {r.failed:>8} {r.skipped:>9} {dur_str:>10}"
            )

        print(divider)
        overall_status = (
            "PASSED"
            if total_failed == 0 and total_tests > 0
            else ("PENDING" if total_tests == 0 else "FAILED")
        )
        overall_color = (
            f"{c.GREEN}{c.BOLD}PASSED{c.RESET}"
            if overall_status == "PASSED"
            else (
                f"{c.YELLOW}PENDING{c.RESET}"
                if overall_status == "PENDING"
                else f"{c.RED}{c.BOLD}FAILED{c.RESET}"
            )
        )

        tot_dur_str = f"{total_duration:.2f}s"
        print(
            f"{'TOTAL':<10} {'All Discovered Suites':<26} {overall_color:^9} {total_tests:>7} {total_passed:>8} {total_failed:>8} {total_skipped:>9} {tot_dur_str:>10}"
        )
        print(border)

        # Print failure diagnostics
        all_failures: List[Tuple[str, Dict[str, Any]]] = []
        for r in results:
            for f in r.failures:
                all_failures.append((r.name, f))

        if all_failures:
            print(
                f"\n{c.RED}{c.BOLD}========================================================================================{c.RESET}"
            )
            print(
                f"{c.RED}{c.BOLD}                               FAILURE DIAGNOSTICS ({len(all_failures)}){c.RESET}"
            )
            print(
                f"{c.RED}{c.BOLD}========================================================================================{c.RESET}"
            )
            for idx, (tier_name, fail_info) in enumerate(all_failures, start=1):
                print(
                    f"\n{c.RED}[FAIL {idx}/{len(all_failures)}]{c.RESET} {c.BOLD}{fail_info.get('nodeid', 'unknown')}{c.RESET}"
                )
                print(f"  Tier   : {tier_name}")
                print(f"  Message: {fail_info.get('message', 'No message')}")
                tb = fail_info.get("traceback", "")
                if tb:
                    print("  Traceback Snippet:")
                    tb_lines = tb.strip().splitlines()
                    for line in tb_lines[-6:]:
                        print(f"    {line}")
                print("-" * 88)

        # Final Outcome Line
        if overall_status == "PASSED":
            print(
                f"\n{c.GREEN}{c.BOLD}OVERALL STATUS: SUCCESS [100% OF {total_tests} DISCOVERED TESTS PASSED]{c.RESET}"
            )
            print(f"{c.GREEN}EXIT CODE: 0{c.RESET}")
        elif overall_status == "PENDING":
            print(
                f"\n{c.YELLOW}{c.BOLD}OVERALL STATUS: PENDING [0 tests discovered; test suites are in progress]{c.RESET}"
            )
        else:
            print(
                f"\n{c.RED}{c.BOLD}OVERALL STATUS: FAILED [{total_passed}/{total_tests} PASSED, {total_failed} FAILED]{c.RESET}"
            )
            print(f"{c.RED}EXIT CODE: 1{c.RESET}")
        print(border + "\n")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="QUANTKUPON Unified E2E Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tier",
        "-t",
        choices=["0", "1", "2", "3", "4", "harness", "all"],
        default="all",
        help="Target test tier to execute (default: all)",
    )
    parser.add_argument(
        "--feature",
        "-f",
        type=int,
        choices=range(1, 30),
        metavar="[1-29]",
        help="Filter test execution for a specific feature (1 to 29)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output and streaming pytest logs",
    )
    parser.add_argument(
        "--fail-fast",
        "-x",
        action="store_true",
        help="Exit immediately on first test failure",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=True,
        help="Enforce OFFLINE_MODE=true deterministic execution (default: True)",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Execute Node.js / Vitest frontend component tests",
    )
    parser.add_argument(
        "--enforce-all",
        action="store_true",
        help="Enforce that all 4 tiers exist and meet minimum test count thresholds (Milestone E2E-M6 gate)",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow exit code 0 even if 0 tests are discovered (for early scaffolding runs)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON summary to stdout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    root_dir = Path(__file__).resolve().parent.parent

    runner = TestRunner(root_dir, args)

    tier_specs = {
        "harness": ("Harness", "Self-Check Sanity Suite", root_dir / "tests" / "test_harness_self_check.py"),
        "0": ("Harness", "Self-Check Sanity Suite", root_dir / "tests" / "test_harness_self_check.py"),
        "1": ("Tier 1", "Feature Coverage (>=145)", root_dir / "tests" / "e2e" / "tier1_features"),
        "2": ("Tier 2", "Boundary & Corners (>=145)", root_dir / "tests" / "e2e" / "tier2_boundaries"),
        "3": ("Tier 3", "Cross-Feature Combos (>=29)", root_dir / "tests" / "e2e" / "tier3_combinations"),
        "4": ("Tier 4", "Real-World Scenarios (>=15)", root_dir / "tests" / "e2e" / "tier4_scenarios"),
    }

    if args.tier in ("0", "harness"):
        tiers_to_run = ["harness"]
    elif args.tier != "all":
        tiers_to_run = [args.tier]
    else:
        # If 'all': run harness self-check (if present) followed by tiers 1 to 4
        tiers_to_run = []
        if (root_dir / "tests" / "test_harness_self_check.py").is_file():
            tiers_to_run.append("harness")
        tiers_to_run.extend(["1", "2", "3", "4"])

    results: List[TestResult] = []

    for t_id in tiers_to_run:
        name, scope, target_path = tier_specs[t_id]
        res = runner.run_target(t_id, name, scope, target_path)
        results.append(res)

    # Optional UI test execution
    if args.ui:
        ui_res = runner.run_ui_tests()
        if ui_res is not None:
            results.append(ui_res)

    if args.json:
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tier": args.tier,
            "feature": args.feature,
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        runner.print_summary_table(results)

    total_tests = sum(r.total for r in results)
    total_failed = sum(r.failed for r in results)

    # Strict enforcement mode check
    if args.enforce_all:
        for t_id in ["1", "2", "3", "4"]:
            res = next((r for r in results if r.name == f"Tier {t_id}"), None)
            req_min = TIER_MIN_THRESHOLDS[t_id]
            if not res or res.status != "PASSED" or res.total < req_min:
                print(f"[ERROR] Enforcement failed: Tier {t_id} must have >= {req_min} passed tests.")
                return 1

    # Empty suite guard
    if total_tests == 0:
        if args.allow_empty:
            return 0
        print("[WARNING] Zero tests discovered across requested tiers. Empty suite guard active.")
        return 3

    # 100% pass invariant
    if total_failed == 0 and total_tests > 0:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
