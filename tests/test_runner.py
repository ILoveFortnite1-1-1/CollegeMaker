#!/usr/bin/env python3
"""
Standalone E2E Test Runner for College Portfolio Application.
Executes test suites across Tiers 1-4 with detailed reporting, tier selection,
filtering, timing, and proper process exit codes.
"""

import os
import sys
import time
import unittest
import argparse
import traceback
from typing import List, Dict, Any, Optional

# Ensure workspace root and tests/ dir are on python path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESTS_DIR = os.path.abspath(os.path.dirname(__file__))

for p in [WORKSPACE_ROOT, TESTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)


class TestColor:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DetailedTestResult(unittest.TestResult):
    """Custom TestResult collecting detailed execution stats."""
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.verbose = verbose
        self.successes: List[unittest.TestCase] = []
        self.test_timings: Dict[str, float] = {}
        self._start_time = 0.0

    def startTest(self, test: unittest.TestCase):
        super().startTest(test)
        self._start_time = time.time()
        if self.verbose:
            test_name = f"{test.__class__.__name__}.{test._testMethodName}"
            sys.stdout.write(f"  RUNNING: {test_name:<65} ")
            sys.stdout.flush()

    def addSuccess(self, test: unittest.TestCase):
        super().addSuccess(test)
        elapsed = time.time() - self._start_time
        test_id = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_timings[test_id] = elapsed
        self.successes.append(test)
        if self.verbose:
            sys.stdout.write(f"{TestColor.GREEN}[PASS]{TestColor.ENDC} ({elapsed:.3f}s)\n")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"{TestColor.GREEN}.{TestColor.ENDC}")
            sys.stdout.flush()

    def addFailure(self, test: unittest.TestCase, err):
        super().addFailure(test, err)
        elapsed = time.time() - self._start_time
        test_id = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_timings[test_id] = elapsed
        if self.verbose:
            sys.stdout.write(f"{TestColor.FAIL}[FAIL]{TestColor.ENDC} ({elapsed:.3f}s)\n")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"{TestColor.FAIL}F{TestColor.ENDC}")
            sys.stdout.flush()

    def addError(self, test: unittest.TestCase, err):
        super().addError(test, err)
        elapsed = time.time() - self._start_time
        test_id = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_timings[test_id] = elapsed
        if self.verbose:
            sys.stdout.write(f"{TestColor.FAIL}[ERROR]{TestColor.ENDC} ({elapsed:.3f}s)\n")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"{TestColor.FAIL}E{TestColor.ENDC}")
            sys.stdout.flush()

    def addSkip(self, test: unittest.TestCase, reason: str):
        super().addSkip(test, reason)
        elapsed = time.time() - self._start_time
        test_id = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_timings[test_id] = elapsed
        if self.verbose:
            sys.stdout.write(f"{TestColor.WARNING}[SKIP]{TestColor.ENDC} ({reason})\n")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"{TestColor.WARNING}s{TestColor.ENDC}")
            sys.stdout.flush()


def discover_suite(tier_filter: Optional[int] = None, keyword_filter: Optional[str] = None) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tier_files = {
        1: "test_tier1_features.py",
        2: "test_tier2_boundaries.py",
        3: "test_tier3_pairwise.py",
        4: "test_tier4_scenarios.py"
    }

    files_to_load = []
    if tier_filter and tier_filter in tier_files:
        files_to_load.append(tier_files[tier_filter])
    else:
        files_to_load = list(tier_files.values())

    for filename in files_to_load:
        filepath = os.path.join(TESTS_DIR, filename)
        if os.path.exists(filepath):
            module_name = filename[:-3]
            try:
                mod = __import__(module_name)
                discovered = loader.loadTestsFromModule(mod)
                for test_group in discovered:
                    for test in test_group:
                        if keyword_filter:
                            test_id = f"{test.__class__.__name__}.{test._testMethodName}"
                            if keyword_filter.lower() in test_id.lower():
                                suite.addTest(test)
                        else:
                            suite.addTest(test)
            except Exception as e:
                print(f"{TestColor.FAIL}Failed to import test module {module_name}: {e}{TestColor.ENDC}")
                traceback.print_exc()

    return suite


def run_tests(tier: Optional[int] = None, keyword: Optional[str] = None, verbose: bool = False, base_url: Optional[str] = None) -> int:
    if base_url:
        os.environ["TEST_BASE_URL"] = base_url

    suite = discover_suite(tier_filter=tier, keyword_filter=keyword)
    total_tests = suite.countTestCases()

    tier_label = f"Tier {tier}" if tier else "All Tiers (1-4)"
    print(f"\n{TestColor.BOLD}======================================================================{TestColor.ENDC}")
    print(f"{TestColor.HEADER}{TestColor.BOLD}COLLEGE PORTFOLIO E2E TEST RUNNER{TestColor.ENDC}")
    print(f"Target Scope : {tier_label}")
    print(f"Test Count   : {total_tests} test cases discovered")
    print(f"Server Target: {os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')}")
    print(f"{TestColor.BOLD}======================================================================{TestColor.ENDC}\n")

    if total_tests == 0:
        print(f"{TestColor.WARNING}No tests found matching the specified criteria.{TestColor.ENDC}")
        return 0

    result = DetailedTestResult(verbose=verbose)
    start_time = time.time()
    suite.run(result)
    duration = time.time() - start_time

    if not verbose:
        print()

    # Print failure / error details
    if result.failures:
        print(f"\n{TestColor.FAIL}{TestColor.BOLD}FAILURES ({len(result.failures)}):{TestColor.ENDC}")
        for test, err in result.failures:
            print(f"{TestColor.FAIL}----------------------------------------------------------------------{TestColor.ENDC}")
            print(f"FAIL: {test.__class__.__name__}.{test._testMethodName}")
            print(f"{TestColor.FAIL}{err}{TestColor.ENDC}")

    if result.errors:
        print(f"\n{TestColor.FAIL}{TestColor.BOLD}ERRORS ({len(result.errors)}):{TestColor.ENDC}")
        for test, err in result.errors:
            print(f"{TestColor.FAIL}----------------------------------------------------------------------{TestColor.ENDC}")
            print(f"ERROR: {test.__class__.__name__}.{test._testMethodName}")
            print(f"{TestColor.FAIL}{err}{TestColor.ENDC}")

    # Print summary box
    passed_count = len(result.successes)
    failed_count = len(result.failures)
    error_count = len(result.errors)
    skipped_count = len(result.skipped)

    print(f"\n{TestColor.BOLD}======================================================================{TestColor.ENDC}")
    print(f"{TestColor.BOLD}TEST SUMMARY{TestColor.ENDC}")
    print(f"  Total Run : {result.testsRun}")
    print(f"  Passed    : {TestColor.GREEN}{passed_count}{TestColor.ENDC}")
    print(f"  Failed    : {TestColor.FAIL}{failed_count}{TestColor.ENDC}")
    print(f"  Errors    : {TestColor.FAIL}{error_count}{TestColor.ENDC}")
    print(f"  Skipped   : {TestColor.WARNING}{skipped_count}{TestColor.ENDC}")
    print(f"  Duration  : {duration:.3f} seconds")
    print(f"{TestColor.BOLD}======================================================================{TestColor.ENDC}")

    if failed_count == 0 and error_count == 0:
        print(f"\n{TestColor.GREEN}{TestColor.BOLD}OVERALL RESULT: SUCCESS (100% PASS){TestColor.ENDC}\n")
        return 0
    else:
        print(f"\n{TestColor.FAIL}{TestColor.BOLD}OVERALL RESULT: FAILURE ({failed_count + error_count} defective test cases){TestColor.ENDC}\n")
        return 1


def main():
    parser = argparse.ArgumentParser(description="College Portfolio E2E Test Suite Runner")
    parser.add_argument("-t", "--tier", type=int, choices=[1, 2, 3, 4], help="Execute only a specific test tier")
    parser.add_argument("-k", "--filter", type=str, help="Filter tests by method or class name substring")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose per-test execution details")
    parser.add_argument("--base-url", type=str, help="Backend base URL target (default: http://127.0.0.1:8000)")

    args = parser.parse_args()
    exit_code = run_tests(tier=args.tier, keyword=args.filter, verbose=args.verbose, base_url=args.base_url)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
