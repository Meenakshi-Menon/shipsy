#!/usr/bin/env python3
"""
Contact Enrichment Agent - Main Script

This script processes a CSV file with contact names and company names,
enriches the data by finding LinkedIn profiles, job titles, and work emails,
and outputs the results to CSV and JSON files.

Usage:
    python contact_enrichment.py input.csv output.csv

Requirements:
    - CSV file with columns: contact_name, company_name
    - Environment variables: OPENROUTER_API_KEY, BRAVE_API_KEY
"""

import sys
import logging
import argparse
from pathlib import Path
from src.config.settings import Config
from src.processors.contact_csv_processor import ContactCSVProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contact_enrichment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to run the contact enrichment process."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Enrich contact information from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python contact_enrichment.py contacts.csv enriched_contacts.csv
    python contact_enrichment.py --sample sample_contacts.csv
        """
    )
    
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input CSV file with contact data (columns: contact_name, company_name)"
    )
    
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output CSV file for enriched contact data"
    )
    
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Create a sample CSV file for testing"
    )
    
    parser.add_argument(
        "--sample-file",
        default="sample_contacts.csv",
        help="Name of the sample file to create (default: sample_contacts.csv)"
    )
    
    args = parser.parse_args()
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize the processor
        processor = ContactCSVProcessor()
        
        if args.sample:
            # Create sample file
            logger.info(f"Creating sample CSV file: {args.sample_file}")
            processor.create_sample_contacts_csv(args.sample_file)
            logger.info(f"Sample file created successfully: {args.sample_file}")
            print(f"\nSample CSV file created: {args.sample_file}")
            print("You can now run the enrichment process:")
            print(f"python contact_enrichment.py {args.sample_file} enriched_{args.sample_file}")
            return
        
        # Validate input arguments
        if not args.input_file or not args.output_file:
            parser.error("Both input_file and output_file are required when not using --sample")
        
        # Check if input file exists
        input_path = Path(args.input_file)
        if not input_path.exists():
            logger.error(f"Input file does not exist: {args.input_file}")
            sys.exit(1)
        
        # Check if output directory exists
        output_path = Path(args.output_file)
        output_dir = output_path.parent
        if not output_dir.exists():
            logger.info(f"Creating output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process the contacts
        logger.info(f"Starting contact enrichment process...")
        logger.info(f"Input file: {args.input_file}")
        logger.info(f"Output file: {args.output_file}")
        
        enriched_contacts = processor.enrich_contacts_from_csv(
            args.input_file,
            args.output_file
        )
        
        # Print summary
        total_contacts = len(enriched_contacts)
        successful_linkedin = sum(1 for c in enriched_contacts if c.linkedin_url not in ["NOT_FOUND", "ERROR"])
        successful_emails = sum(1 for c in enriched_contacts if c.work_email not in ["NOT_FOUND", "ERROR"])
        successful_titles = sum(1 for c in enriched_contacts if c.current_job_title not in ["NOT_FOUND", "ERROR"])
        
        print(f"\n{'='*60}")
        print(f"CONTACT ENRICHMENT SUMMARY")
        print(f"{'='*60}")
        print(f"Total contacts processed: {total_contacts}")
        print(f"LinkedIn profiles found: {successful_linkedin} ({successful_linkedin/total_contacts*100:.1f}%)")
        print(f"Job titles found: {successful_titles} ({successful_titles/total_contacts*100:.1f}%)")
        print(f"Work emails generated: {successful_emails} ({successful_emails/total_contacts*100:.1f}%)")
        print(f"\nResults saved to:")
        print(f"  CSV: {args.output_file}")
        print(f"  JSON: {args.output_file.replace('.csv', '.json')}")
        print(f"  Log: contact_enrichment.log")
        print(f"{'='*60}")
        
        logger.info("Contact enrichment process completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error during contact enrichment: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Check the log file for more details: contact_enrichment.log")
        sys.exit(1)


if __name__ == "__main__":
    main()
