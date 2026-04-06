# CLI entry point for AI Bookkeeping Agent

import os
import sys
import argparse
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logger
from config import DEFAULT_CSV_PATH


def main():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    logger = setup_logger("Main", "logs/main.log")

    parser = argparse.ArgumentParser(description="AI Bookkeeping Agent")
    parser.add_argument("--query", "-q", required=True, help="Financial question")
    parser.add_argument("--csv", "-c", default=DEFAULT_CSV_PATH, help="Path to CSV")
    parser.add_argument("--output-format", "-f", default="json", choices=["json", "markdown"])
    parser.add_argument("--output-file", "-o", help="Output filename")
    args = parser.parse_args()

    logger.info(f"Query: {args.query} | CSV: {args.csv}")

    try:
        coordinator = CoordinatorAgent()
        result = coordinator.execute({"query": args.query, "csv_path": args.csv})

        if result["success"]:
            report = result["report"]

            print(f"\n{'='*60}")
            print(f"Query: {args.query}")
            print(f"Intent: {result['stats'].get('intent', '?')}")
            print(f"{'='*60}")

            for insight in report.get("insights", []):
                itype = insight.get("type", "")
                if itype == "warnings":
                    print(f"\n  [Note] {insight.get('answer', '')}")
                    continue

                print(f"\n  [{insight.get('title', '')}]")
                print(f"  {insight.get('answer', '')}")
                if insight.get("detail"):
                    print(f"\n{insight['detail']}")

            filepath = coordinator.save_report(report, format=args.output_format, filename=args.output_file)
            print(f"\nReport saved: {filepath}")
        else:
            print(f"\nError: {result.get('error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
