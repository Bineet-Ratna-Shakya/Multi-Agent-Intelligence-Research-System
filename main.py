# Main application.

import os
import sys
import argparse
from typing import Dict, Any
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logger
from config import PRODUCT_CATEGORIES

def main():
    logger = setup_logger("Main", "logs/main.log")
    
    parser = argparse.ArgumentParser(description="Multi-Agent Competitive Intelligence System")
    parser.add_argument("--query", "-q", required=True, help="Search query for product updates")
    parser.add_argument("--category", "-c", required=True, 
                       choices=list(PRODUCT_CATEGORIES.keys()),
                       help="Product category")
    parser.add_argument("--output-format", "-f", default="json", 
                       choices=["json", "markdown"],
                       help="Output format for the report")
    parser.add_argument("--output-file", "-o", 
                       help="Output filename (without extension)")
    
    args = parser.parse_args()
    
    logger.info("Starting Multi-Agent Competitive Intelligence System")
    logger.info(f"Query: {args.query}")
    logger.info(f"Category: {args.category}")
    
    try:
        os.makedirs("reports", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        coordinator = CoordinatorAgent()
        
        task = {
            "query": args.query,
            "product_category": args.category
        }
        
        logger.info("Executing competitive intelligence pipeline...")
        result = coordinator.execute(task)
        
        if result["success"]:
            report = result["report"]
            stats = result["stats"]
            
            print("\n" + "="*60)
            print("COMPETITIVE INTELLIGENCE REPORT SUMMARY")
            print("="*60)
            print(f"Query: {args.query}")
            print(f"Category: {PRODUCT_CATEGORIES[args.category]}")
            print(f"Sources Found: {stats['sources_found']}")
            print(f"Summaries Generated: {stats['summaries_generated']}")
            print(f"Summaries Verified: {stats['summaries_verified']}")
            print(f"Summaries Filtered: {stats['summaries_filtered']}")
            print("\nTop Updates:")
            
            for i, update in enumerate(report["updates"][:3], 1):
                print(f"\n{i}. {update['product']}")
                print(f"   Summary: {update['summary'][:100]}...")
                print(f"   Date: {update['date']}")
                print(f"   Source: {update['source']}")
            
            filepath = coordinator.save_report(
                report, 
                format=args.output_format,
                filename=args.output_file
            )
            
            print(f"\nFull report saved to: {filepath}")
            logger.info(f"Pipeline completed successfully. Report saved to: {filepath}")
            
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"\nError: {error_msg}")
            logger.error(f"Pipeline failed: {error_msg}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        logger.info("Operation cancelled by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

