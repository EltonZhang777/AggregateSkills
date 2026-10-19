import argparse
import json
import sys


def apply_candidate(source_path, expected_sha256, candidate, approved_root=None):
    # Preserve the current caller signature while local-path writes are unsupported.
    return {"status": "not_applied", "reason": "conditional_replace_unsupported"}


def main():
    parser = argparse.ArgumentParser(
        description="Conditional writes are unavailable; local-path application is rejected."
    )
    parser.add_argument("source")
    parser.add_argument("expected_sha256")
    parser.add_argument("--approved-root")
    args = parser.parse_args()

    result = apply_candidate(
        args.source,
        args.expected_sha256,
        candidate=sys.stdin.buffer.read(),
        approved_root=args.approved_root,
    )
    print(json.dumps(result))
    return 1


if __name__ == "__main__":
    sys.exit(main())
