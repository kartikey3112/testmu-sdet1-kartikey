"""CLI: generate test cases for one module and prompt version.

  python -m scripts.generate_tests --module login --version v1
  python -m scripts.generate_tests --revalidate generated/raw/login.v1.<timestamp>.json
"""

import argparse
import sys
from pathlib import Path

from ai.llm_client import LLMConfigError, LLMError
from ai.testgen.runner import ROOT, generate, prompt_path, revalidate
from ai.testgen.schema import COVERAGE_AREAS


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--module", choices=sorted(COVERAGE_AREAS))
    parser.add_argument("--version", help="prompt version, e.g. v1")
    parser.add_argument("--revalidate", type=Path, help="validate a saved raw response again")
    args = parser.parse_args()

    if args.revalidate:
        result = revalidate(args.revalidate)
    else:
        if not (args.module and args.version):
            parser.error("--module and --version are required unless --revalidate is used")
        if not prompt_path(args.module, args.version).exists():
            parser.error(f"No prompt file {prompt_path(args.module, args.version)}")
        try:
            result = generate(args.module, args.version)
        except LLMConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except LLMError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3

    print(result.report_path.read_text(encoding="utf-8"))
    print(f"Raw response: {result.raw_path.resolve().relative_to(ROOT)}")
    print(f"Report:       {result.report_path.resolve().relative_to(ROOT)}")
    return 0 if result.report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
