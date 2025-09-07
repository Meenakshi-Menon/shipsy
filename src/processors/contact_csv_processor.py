'''
import pandas as pd
import logging
from typing import List, Dict, Optional
from pathlib import Path
from src.agents.contact_agent import ContactEnrichmentAgent, ContactInfo

# Configure logging
logger = logging.getLogger(__name__)


class ContactCSVProcessor:
    """Processor for handling CSV files with contact data."""
    
    def __init__(self):
        """Initialize the contact CSV processor."""
        self.contact_agent = ContactEnrichmentAgent()
    
    def read_contacts_csv(self, file_path: str) -> List[Dict[str, str]]:
        """
        Read contacts from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of dictionaries with contact data
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Read {len(df)} contacts from {file_path}")
            
            # Validate required columns
            required_columns = ["contact_name", "company_name"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert to list of dictionaries
            contacts = df[required_columns].to_dict('records')
            
            # Clean the data
            cleaned_contacts = []
            for contact in contacts:
                cleaned_contact = {
                    "contact_name": str(contact["contact_name"]).strip(),
                    "company_name": str(contact["company_name"]).strip()
                }
                
                # Skip empty contacts
                if cleaned_contact["contact_name"] and cleaned_contact["company_name"]:
                    cleaned_contacts.append(cleaned_contact)
                else:
                    logger.warning(f"Skipping contact with empty fields: {contact}")
            
            logger.info(f"Processed {len(cleaned_contacts)} valid contacts")
            return cleaned_contacts
            
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise
    
    def enrich_contacts_from_csv(self, input_file_path: str, output_file_path: str) -> List[ContactInfo]:
        """
        Enrich contacts from a CSV file and save results.
        
        Args:
            input_file_path: Path to input CSV file
            output_file_path: Path to output CSV file
            
        Returns:
            List of enriched ContactInfo objects
        """
        try:
            # Read contacts from CSV
            contacts = self.read_contacts_csv(input_file_path)
            
            if not contacts:
                logger.warning("No contacts found in the input file")
                return []
            
            logger.info(f"Starting enrichment for {len(contacts)} contacts")
            
            # Enrich contacts using the agent
            enriched_contacts = self.contact_agent.process_contacts_batch(contacts)
            
            # Save results to CSV
            self.save_enriched_contacts_to_csv(enriched_contacts, output_file_path)
            
            # Also save to JSON for backup
            json_output_path = output_file_path.replace('.csv', '.json')
            self.save_enriched_contacts_to_json(enriched_contacts, json_output_path)
            
            logger.info(f"Enrichment completed. Results saved to {output_file_path}")
            return enriched_contacts
            
        except Exception as e:
            logger.error(f"Error enriching contacts from CSV: {str(e)}")
            raise
    
    def save_enriched_contacts_to_csv(self, contacts: List[ContactInfo], file_path: str) -> None:
        """
        Save enriched contacts to a CSV file.
        
        Args:
            contacts: List of ContactInfo objects
            file_path: Path to save the CSV file
        """
        try:
            # Convert ContactInfo objects to dictionaries
            data = []
            for contact in contacts:
                data.append({
                    "contact_name": contact.contact_name,
                    "company_name": contact.company_name,
                    "linkedin_url": contact.linkedin_url,
                    "current_job_title": contact.current_job_title,
                    "work_email": contact.work_email,
                    "citation_source": contact.citation_source
                })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            
            logger.info(f"Saved {len(contacts)} enriched contacts to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving contacts to CSV {file_path}: {str(e)}")
            raise
    
    def save_enriched_contacts_to_json(self, contacts: List[ContactInfo], file_path: str) -> None:
        """
        Save enriched contacts to a JSON file.
        
        Args:
            contacts: List of ContactInfo objects
            file_path: Path to save the JSON file
        """
        try:
            import json
            
            # Convert ContactInfo objects to dictionaries
            data = []
            for contact in contacts:
                data.append({
                    "contact_name": contact.contact_name,
                    "company_name": contact.company_name,
                    "linkedin_url": contact.linkedin_url,
                    "current_job_title": contact.current_job_title,
                    "work_email": contact.work_email,
                    "citation_source": contact.citation_source
                })
            
            # Save to JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(contacts)} enriched contacts to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving contacts to JSON {file_path}: {str(e)}")
            raise
    
    def create_sample_contacts_csv(self, file_path: str) -> None:
        """
        Create a sample CSV file with contact data for testing.
        
        Args:
            file_path: Path to save the sample CSV file
        """
        sample_contacts = [
            {"contact_name": "John Smith", "company_name": "Microsoft"},
            {"contact_name": "Sarah Johnson", "company_name": "Google"},
            {"contact_name": "Michael Brown", "company_name": "Apple"},
            {"contact_name": "Emily Davis", "company_name": "Amazon"},
            {"contact_name": "David Wilson", "company_name": "Meta"}
        ]
        
        df = pd.DataFrame(sample_contacts)
        df.to_csv(file_path, index=False)
        
        logger.info(f"Created sample contacts CSV at {file_path}")


if __name__ == "__main__":
    # Test the contact CSV processor
    processor = ContactCSVProcessor()
    
    # Create a sample CSV file
    sample_file = "sample_contacts.csv"
    processor.create_sample_contacts_csv(sample_file)
    
    print(f"Created sample CSV file: {sample_file}")
    print("You can now run the enrichment process on this file.")
'''

import pandas as pd
from src.agents.contact_agent import ContactEnrichmentAgent

class ExcelContactProcessor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.agent = ContactEnrichmentAgent()

    def process_contacts(self, input_sheet="Contacts", output_sheet="Contact Results"):
        # read contacts data from the Contacts sheet
        df = pd.read_excel(self.filepath, sheet_name=input_sheet)

        results = []
        for _, row in df.iterrows():
            contact_name = str(row.get("Contact Name", "")).strip()
            company_name = str(row.get("Company Name", "")).strip()
            company_domain = str(row.get("Company Domain", "")).strip()

            if not contact_name or not company_name:
                continue

            try:
                enriched = self.agent.enrich_contact(contact_name, company_name)

                results.append({
                    "Contact Name": enriched.contact_name,
                    "Company Name": enriched.company_name,
                    "LinkedIn URL": enriched.linkedin_url,
                    "Current Job Title": enriched.current_job_title,
                    "Work Email": enriched.work_email,
                    "Citation": enriched.citation_source,
                })
            except Exception as e:
                results.append({
                    "Contact Name": contact_name,
                    "Company Name": company_name,
                    "LinkedIn URL": "Error",
                    "Current Job Title": "Error",
                    "Work Email": "Error",
                    "Citation": str(e),
                })

        results_df = pd.DataFrame(results)

        # write results into a new sheet
        with pd.ExcelWriter(self.filepath, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            results_df.to_excel(writer, sheet_name=output_sheet, index=False)

        print(f"[INFO] Contact results written to sheet: {output_sheet}")

