from __future__ import annotations

import argparse

from .strands_app import build_agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Strands Recovery Agent")
    parser.add_argument("--owr-root", required=True, help="OWR state root containing data/owrp.sqlite")
    parser.add_argument("--repo", required=True, help="Git repository whose next action may be queued")
    parser.add_argument("--prompt", default="Recover the strongest repeated-work finding and prepare one bounded next action.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    agent = build_agent(ask="stdio")
    prompt = (
        f"OWR root: {args.owr_root}\n"
        f"Repository: {args.repo}\n"
        f"Task: {args.prompt}\n"
        "Run the full recovery workflow. Use at most one finding and at most one proposed side effect."
    )
    result = agent(prompt)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
