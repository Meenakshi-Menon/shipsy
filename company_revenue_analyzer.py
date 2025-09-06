#!/usr/bin/env python3
"""
Company Revenue Analysis Automation

This script processes a CSV file containing company information and automatically
determines each company's annual revenue from operations and assigns them to tiers.

Required CSV columns:
- Company Name
- Company Region  
- Company Domain

The script uses:
- Brave Search API for web searching
- DeepSeek model via OpenRouter for revenue extraction
- Static tier assignment based on revenue thresholds

Usage:
    python company_revenue_analyzer.py input.csv [output_prefix]
"""

import sys
import argparse
import time
from pathlib import Path
from src.processors.csv_processor import CompanyRevenueProcessor
from src.config.settings import Config


def validate_environment():
    """Validate that all required API keys are configured."""
    try:
        Config.validate()
        print("✓ Environment configuration validated")
        return True
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease ensure you have set the following environment variables:")
        print("- OPENROUTER_API_KEY (for DeepSeek model)")
        print("- BRAVE_API_KEY (for web search)")
        print("\nYou can set these in a .env file or as environment variables.")
        return False


def main():
    """Main function to run the company revenue analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze company revenue and assign tiers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python company_revenue_analyzer.py companies.csv
    python company_revenue_analyzer.py companies.csv results
    python company_revenue_analyzer.py companies.csv --delay 3.0
        """
    )
    
    parser.add_argument(
        "input_csv",
        help="Path to input CSV file with company data"
    )
    
    parser.add_argument(
        "output_prefix",
        nargs="?",
        help="Prefix for output files (default: input filename + '_analyzed')"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between company processing (default: 2.0)"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration and CSV format, don't process"
    )
    
    args = parser.parse_args()
    
    print("Company Revenue Analysis Automation")
    print("=" * 50)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Check if input file exists
    input_path = Path(args.input_csv)
    if not input_path.exists():
        print(f"✗ Input file not found: {args.input_csv}")
        sys.exit(1)
    
    print(f"✓ Input file found: {args.input_csv}")
    
    # Initialize processor
    processor = CompanyRevenueProcessor()
    
    try:
        # Load and validate CSV
        companies = processor.load_csv(args.input_csv)
        print(f"✓ CSV loaded successfully with {len(companies)} companies")
        
        # Validate CSV structure
        required_columns = ['Company Name', 'Company Region', 'Company Domain']
        sample_company = companies[0] if companies else {}
        missing_columns = [col for col in required_columns if col not in sample_company]
        
        if missing_columns:
            print(f"✗ CSV missing required columns: {missing_columns}")
            print("Required columns: Company Name, Company Region, Company Domain")
            sys.exit(1)
        
        print("✓ CSV structure validated")
        
        if args.validate_only:
            print("\nValidation complete. Use without --validate-only to process companies.")
            return
        
        # Determine output path
        if args.output_prefix:
            output_path = args.output_prefix
        else:
            output_path = input_path.parent / f"{input_path.stem}_analyzed"
        
        print(f"✓ Output will be saved with prefix: {output_path}")
        print(f"✓ Delay between companies: {args.delay} seconds")
        
        # Confirm before processing
        print(f"\nReady to process {len(companies)} companies.")
        print("This may take several minutes depending on the number of companies.")
        
        if len(companies) > 5:
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Processing cancelled.")
                return
        
        # Process companies
        print(f"\nStarting processing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        start_time = time.time()
        
        results = processor.process_companies_batch(companies, args.delay)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Save results
        processor.save_results(results, str(output_path))
        
        # Print summary
        print(f"\nProcessing completed in {processing_time:.1f} seconds")
        print("=" * 50)
        
        # Count results by tier
        tier_counts = {}
        revenue_found = 0
        
        for result in results:
            tier = result.get('tier', 'Unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            if result.get('estimated_revenue_usd') is not None:
                revenue_found += 1
        
        print(f"Total Companies: {len(results)}")
        print(f"Revenue Data Found: {revenue_found}")
        print(f"Success Rate: {(revenue_found/len(results))*100:.1f}%")
        
        print("\nTier Distribution:")
        for tier, count in sorted(tier_counts.items()):
            percentage = (count/len(results))*100
            print(f"  {tier}: {count} ({percentage:.1f}%)")
        
        print(f"\nResults saved to:")
        print(f"  - {output_path}.csv")
        print(f"  - {output_path}.json") 
        print(f"  - {output_path}_summary.txt")
        
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during processing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
