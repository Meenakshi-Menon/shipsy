import pandas as pd
import csv
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from src.agents.revenue_agent import DeepSeekRevenueAgent
from src.tools.tier_assignment import analyze_company_tier


class CompanyRevenueProcessor:
    """Processes CSV files containing company information and determines revenue/tiers."""
    
    def __init__(self):
        self.revenue_agent = DeepSeekRevenueAgent()
        self.processed_companies = []
        self.failed_companies = []
    
    def load_csv(self, csv_path: str) -> List[Dict[str, str]]:
        """
        Load company data from CSV file.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of dictionaries containing company information
        """
        try:
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['Company Name', 'Company Region', 'Company Domain']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert to list of dictionaries
            companies = df.to_dict('records')
            
            print(f"Loaded {len(companies)} companies from {csv_path}")
            return companies
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        except Exception as e:
            raise Exception(f"Error loading CSV file: {str(e)}")
    
    def process_single_company(self, company_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Process a single company to determine revenue and tier.
        
        Args:
            company_data: Dictionary with company information
            
        Returns:
            Dictionary with analysis results
        """
        company_name = company_data.get('Company Name', '')
        company_domain = company_data.get('Company Domain', '')
        company_region = company_data.get('Company Region', '')
        
        print(f"\nProcessing: {company_name}")
        print(f"Domain: {company_domain}")
        print(f"Region: {company_region}")
        print("-" * 50)
        
        try:
            # Use revenue agent to analyze the company
            revenue_analysis = self.revenue_agent.analyze_company_revenue(
                company_name, company_domain
            )
            
            # Add region information
            revenue_analysis['company_region'] = company_region
            
            # Perform tier analysis
            tier_analysis = analyze_company_tier(revenue_analysis)
            
            print(f"✓ Revenue: {tier_analysis['revenue_display']}")
            print(f"✓ Tier: {tier_analysis['tier']}")
            print(f"✓ Citation: {tier_analysis['citation'][:100]}...")
            
            return tier_analysis
            
        except Exception as e:
            error_result = {
                "company_name": company_name,
                "company_domain": company_domain,
                "company_region": company_region,
                "estimated_revenue_usd": None,
                "revenue_display": "Error",
                "tier": "Error",
                "tier_description": f"Processing failed: {str(e)}",
                "citation": f"Error: {str(e)}"
            }
            
            print(f"✗ Error processing {company_name}: {str(e)}")
            return error_result
    
    def process_companies_batch(self, companies: List[Dict[str, str]], 
                              delay_between_companies: float = 2.0) -> List[Dict[str, Any]]:
        """
        Process multiple companies with delays between requests.
        
        Args:
            companies: List of company data dictionaries
            delay_between_companies: Delay in seconds between company processing
            
        Returns:
            List of analysis results
        """
        results = []
        total_companies = len(companies)
        
        print(f"\nStarting batch processing of {total_companies} companies...")
        print("=" * 60)
        
        for i, company_data in enumerate(companies, 1):
            print(f"\n[{i}/{total_companies}] Processing company...")
            
            result = self.process_single_company(company_data)
            results.append(result)
            
            # Add delay between companies to respect rate limits
            if i < total_companies:
                print(f"Waiting {delay_between_companies} seconds before next company...")
                time.sleep(delay_between_companies)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str):
        """
        Save analysis results to CSV and JSON files.
        
        Args:
            results: List of analysis results
            output_path: Base path for output files (without extension)
        """
        # Save as CSV
        csv_path = f"{output_path}.csv"
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        print(f"\nResults saved to CSV: {csv_path}")
        
        # Save as JSON for detailed analysis
        json_path = f"{output_path}.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Detailed results saved to JSON: {json_path}")
        
        # Save summary statistics
        summary_path = f"{output_path}_summary.txt"
        self._save_summary(results, summary_path)
        print(f"Summary saved to: {summary_path}")
    
    def _save_summary(self, results: List[Dict[str, Any]], summary_path: str):
        """Save a summary of the analysis results."""
        total_companies = len(results)
        
        # Count by tier
        tier_counts = {}
        revenue_found = 0
        
        for result in results:
            tier = result.get('tier', 'Unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            if result.get('estimated_revenue_usd') is not None:
                revenue_found += 1
        
        with open(summary_path, 'w') as f:
            f.write("COMPANY REVENUE ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Companies Processed: {total_companies}\n")
            f.write(f"Companies with Revenue Data: {revenue_found}\n")
            f.write(f"Success Rate: {(revenue_found/total_companies)*100:.1f}%\n\n")
            
            f.write("TIER DISTRIBUTION:\n")
            f.write("-" * 20 + "\n")
            for tier, count in sorted(tier_counts.items()):
                percentage = (count/total_companies)*100
                f.write(f"{tier}: {count} companies ({percentage:.1f}%)\n")
            
            f.write("\nTIER DEFINITIONS:\n")
            f.write("-" * 20 + "\n")
            f.write("Super Platinum: Annual revenue from operations > $1Bn\n")
            f.write("Platinum: Annual revenue from operations $500Mn to $1Bn\n")
            f.write("Diamond: Annual revenue from operations $100Mn to $500Mn\n")
            f.write("Gold: Annual revenue from operations below $100Mn\n")
            f.write("Unknown/Error: Revenue information not available\n")
    
    def process_csv_file(self, input_csv_path: str, output_base_path: str = None,
                        delay_between_companies: float = 2.0) -> List[Dict[str, Any]]:
        """
        Complete pipeline to process a CSV file.
        
        Args:
            input_csv_path: Path to input CSV file
            output_base_path: Base path for output files (defaults to input name)
            delay_between_companies: Delay between company processing
            
        Returns:
            List of analysis results
        """
        # Load companies from CSV
        companies = self.load_csv(input_csv_path)
        
        # Process companies
        results = self.process_companies_batch(companies, delay_between_companies)
        
        # Determine output path
        if output_base_path is None:
            input_path = Path(input_csv_path)
            output_base_path = input_path.parent / f"{input_path.stem}_analyzed"
        
        # Save results
        self.save_results(results, str(output_base_path))
        
        return results


if __name__ == "__main__":
    # Example usage
    processor = CompanyRevenueProcessor()
    
    # Create a sample CSV for testing
    sample_data = [
        {
            "Company Name": "Apple Inc",
            "Company Region": "North America",
            "Company Domain": "apple.com"
        },
        {
            "Company Name": "Microsoft Corporation",
            "Company Region": "North America", 
            "Company Domain": "microsoft.com"
        }
    ]
    
    # Save sample CSV
    sample_df = pd.DataFrame(sample_data)
    sample_csv_path = "sample_companies.csv"
    sample_df.to_csv(sample_csv_path, index=False)
    
    print("Created sample CSV file for testing")
    print("To process your own CSV file, use:")
    print("processor.process_csv_file('your_file.csv')")
