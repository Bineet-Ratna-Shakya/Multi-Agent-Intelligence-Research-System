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

    parser = argparse.ArgumentParser(description="AI Bookkeeping Agent - Multi-Agent Financial Analysis")
    parser.add_argument("--query", "-q", required=True,
                        help="Financial question (e.g., \"What's my biggest expense category?\")")
    parser.add_argument("--csv", "-c", default=DEFAULT_CSV_PATH,
                        help="Path to transactions CSV file")
    parser.add_argument("--output-format", "-f", default="json",
                        choices=["json", "markdown"],
                        help="Output format for the report")
    parser.add_argument("--output-file", "-o",
                        help="Output filename (without extension)")

    args = parser.parse_args()

    logger.info("Starting AI Bookkeeping Agent")
    logger.info(f"Query: {args.query}")
    logger.info(f"CSV: {args.csv}")

    try:
        coordinator = CoordinatorAgent()

        task = {
            "query": args.query,
            "csv_path": args.csv
        }

        logger.info("Executing financial analysis pipeline...")
        result = coordinator.execute(task)

        if result["success"]:
            report = result["report"]
            stats = result["stats"]
            financial = report.get("financial_stats", {})

            print("\n" + "=" * 60)
            print("FINANCIAL ANALYSIS REPORT")
            print("=" * 60)
            print(f"Query: {args.query}")
            print(f"Period: {report['metadata'].get('period', 'N/A')}")
            print(f"Transactions Analyzed: {stats['transactions_loaded']}")
            print(f"\nTotal Income:   ${financial.get('total_income', 0):,.2f}")
            print(f"Total Expenses: ${financial.get('total_expenses', 0):,.2f}")
            net = financial.get("net", 0)
            print(f"Net {'Profit' if net > 0 else 'Loss'}:     ${abs(net):,.2f}")

            print("\n--- Expense Breakdown ---")
            for cat, amt in financial.get("expense_by_category", {}).items():
                print(f"  {cat:.<30} ${amt:>10,.2f}")

            print("\n--- Insights ---")
            for insight in report.get("insights", []):
                print(f"\n  [{insight['title']}]")
                print(f"  {insight['summary']}")

            filepath = coordinator.save_report(
                report,
                format=args.output_format,
                filename=args.output_file
            )

            print(f"\nFull report saved to: {filepath}")
            logger.info(f"Pipeline completed. Report: {filepath}")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"\nError: {error_msg}")
            logger.error(f"Pipeline failed: {error_msg}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
