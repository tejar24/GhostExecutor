"""
Ghost QC - Autonomous Test Execution Entry Point

Usage:
    python -m app.run_tests <feature_file> [options]

Examples:
    python -m app.run_tests login.feature
    python -m app.run_tests login.feature --headed --slow-mo 500
    python -m app.run_tests features/*.feature --output-dir results
"""

import argparse
import sys
from pathlib import Path
from glob import glob

from app.executor.runner import AutonomousTestRunner


def main():
    parser = argparse.ArgumentParser(
        description="Ghost QC - Autonomous Test Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.run_tests login.feature
  python -m app.run_tests login.feature --headed
  python -m app.run_tests features/*.feature --output-dir results
  python -m app.run_tests compliance.feature --slow-mo 500 --stop-on-failure
        """
    )

    parser.add_argument(
        "features",
        nargs="+",
        help="Feature file(s) to execute (supports glob patterns)"
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible)"
    )

    parser.add_argument(
        "--slow-mo",
        type=int,
        default=100,
        help="Slow down browser actions by milliseconds (default: 100)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports)"
    )

    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Stop execution on first failure"
    )

    args = parser.parse_args()

    # Expand glob patterns and collect feature files
    feature_files = []
    for pattern in args.features:
        matches = glob(pattern)
        if matches:
            feature_files.extend(matches)
        elif Path(pattern).exists():
            feature_files.append(pattern)
        else:
            print(f"Warning: No files found matching '{pattern}'")

    if not feature_files:
        print("Error: No feature files found")
        sys.exit(1)

    # Remove duplicates while preserving order
    feature_files = list(dict.fromkeys(feature_files))

    print("=" * 60)
    print("GHOST QC - AUTONOMOUS TEST EXECUTOR")
    print("=" * 60)
    print(f"Feature files: {len(feature_files)}")
    for f in feature_files:
        print(f"  - {f}")
    print(f"Headless: {not args.headed}")
    print(f"Slow-mo: {args.slow_mo}ms")
    print(f"Output: {args.output_dir}")
    print("=" * 60)

    # Create and run
    runner = AutonomousTestRunner(
        headless=not args.headed,
        slow_mo=args.slow_mo,
        output_dir=args.output_dir,
        stop_on_failure=args.stop_on_failure
    )

    result = runner.run_feature_files(feature_files)

    # Exit with appropriate code
    if result.failed_scenarios > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
