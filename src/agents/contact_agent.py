import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config.settings import Config
from src.tools.web_search import BraveWebSearch
import re
from urllib.parse import urlparse


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Data class for contact information."""
    contact_name: str
    company_name: str
    linkedin_url: Optional[str] = None
    current_job_title: Optional[str] = None
    work_email: Optional[str] = None
    citation_source: Optional[str] = None


class ContactEnrichmentAgent:
    """Agent for enriching contact information using Brave Search and DeepSeek."""
    
    def __init__(self):
        """Initialize the contact enrichment agent."""
        self.brave_search = BraveWebSearch()
        self.llm = ChatOpenAI(
            model=Config.DEEPSEEK_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=Config.DEEPSEEK_TEMPERATURE,
            max_tokens=Config.DEEPSEEK_MAX_TOKENS,
            extra_headers={
                "HTTP-Referer": "https://github.com/vaishnav/langgraph-agent-project",
                "X-Title": "Contact Enrichment Agent"
            }
        )
        
        # System prompt for the agent
        self.system_prompt = """You are a professional contact enrichment specialist. Your task is to find LinkedIn profiles and current job titles for given contacts.

IMPORTANT INSTRUCTIONS:
1. You will receive a contact name and company name
2. Use the provided search results to find the person's LinkedIn profile URL
3. Extract their current job title at that company
4. Return ONLY the LinkedIn URL and job title - nothing else
5. If you cannot find the information, return "NOT_FOUND" for both fields

SEARCH STRATEGY:
- Look for LinkedIn profiles using site:linkedin.com/in/ searches
- Focus on the most recent and relevant results
- Verify the person works at the specified company
- Extract the exact job title from their LinkedIn profile

OUTPUT FORMAT:
Return a JSON object with exactly these fields:
{
    "linkedin_url": "https://linkedin.com/in/username" or "NOT_FOUND",
    "current_job_title": "Job Title" or "NOT_FOUND"
}

Do not include any other text or explanation."""

    def search_linkedin_profile(self, contact_name: str, company_name: str) -> Dict[str, Any]:
        """
        Search for LinkedIn profile using Brave Search with site filters.
        
        Args:
            contact_name: Name of the contact
            company_name: Name of the company
            
        Returns:
            Dictionary containing search results
        """
        # Construct LinkedIn-specific search query
        query_parts = [
            "site:linkedin.com",
            f'"{contact_name}"',
            f'"{company_name}"'
        ]
        
        query = " ".join(query_parts)
        logger.info(f"Searching LinkedIn for: {query}")
        
        results = self.brave_search.search(query, count=10)
        
        if "error" in results:
            logger.warning(f"LinkedIn search error: {results['error']}")
            return {"error": results["error"], "results": []}
        
        web_results = results.get("web", {}).get("results", [])
        logger.info(f"Found {len(web_results)} LinkedIn search results")
        
        return {"results": web_results}

    def search_additional_info(self, contact_name: str, company_name: str) -> Dict[str, Any]:
        """
        Search for additional information about the contact.
        
        Args:
            contact_name: Name of the contact
            company_name: Name of the company
            
        Returns:
            Dictionary containing search results
        """
        # Search for general information about the person
        query_parts = [
            f'"{contact_name}"',
            f'"{company_name}"',
            "profile",
            "bio",
            "about"
        ]
        
        query = " ".join(query_parts)
        logger.info(f"Searching additional info for: {query}")
        
        results = self.brave_search.search(query, count=10)
        
        if "error" in results:
            logger.warning(f"Additional search error: {results['error']}")
            return {"error": results["error"], "results": []}
        
        web_results = results.get("web", {}).get("results", [])
        logger.info(f"Found {len(web_results)} additional search results")
        
        return {"results": web_results}

    def extract_contact_info(self, contact_name: str, company_name: str) -> Dict[str, str]:
        """
        Extract LinkedIn URL and job title using the LLM.
        
        Args:
            contact_name: Name of the contact
            company_name: Name of the company
            
        Returns:
            Dictionary with linkedin_url and current_job_title
        """
        try:
            # Get LinkedIn search results
            linkedin_results = self.search_linkedin_profile(contact_name, company_name)
            
            # Get additional search results
            additional_results = self.search_additional_info(contact_name, company_name)
            
            # Combine all search results
            all_results = []
            
            if "results" in linkedin_results:
                all_results.extend(linkedin_results["results"])
            
            if "results" in additional_results:
                all_results.extend(additional_results["results"])
            
            if not all_results:
                logger.warning(f"No search results found for {contact_name} at {company_name}")
                return {
                    "linkedin_url": "NOT_FOUND",
                    "current_job_title": "NOT_FOUND"
                }
            
            # Format search results for the LLM
            formatted_results = []
            for i, result in enumerate(all_results[:10], 1):  # Limit to top 10 results
                formatted_results.append(
                    f"{i}. {result.get('title', 'No title')}\n"
                    f"   URL: {result.get('url', 'No URL')}\n"
                    f"   Description: {result.get('description', 'No description')}\n"
                )
            
            search_results_text = "\n".join(formatted_results)
            
            # Create the prompt for the LLM
            human_prompt = f"""Contact Name: {contact_name}
Company Name: {company_name}

Search Results:
{search_results_text}

Please find the LinkedIn profile URL and current job title for this person."""

            # Call the LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            logger.info(f"Calling LLM for contact: {contact_name} at {company_name}")
            response = self.llm.invoke(messages)
            
            # Parse the response
            response_text = response.content.strip()
            logger.info(f"LLM response: {response_text}")
            
            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                return {
                    "linkedin_url": result.get("linkedin_url", "NOT_FOUND"),
                    "current_job_title": result.get("current_job_title", "NOT_FOUND")
                }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {response_text}")
                return {
                    "linkedin_url": "NOT_FOUND",
                    "current_job_title": "NOT_FOUND"
                }
                
        except Exception as e:
            logger.error(f"Error extracting contact info for {contact_name}: {str(e)}")
            return {
                "linkedin_url": "NOT_FOUND",
                "current_job_title": "NOT_FOUND"
            }

    def generate_work_email(self, contact_name: str, company_domain: str) -> str:
        """
        Generate a likely work email address from contact name and company domain.
        
        Args:
            contact_name: Full name of the contact
            company_domain: Company domain (e.g., "company.com")
            
        Returns:
            Generated email address
 
        if not contact_name or not company_domain:
            return "NOT_FOUND"
        
        # Clean the domain
        domain = company_domain.lower().strip()
        if not domain.startswith('@'):
            domain = f"@{domain}"
        
        # Parse the name
        name_parts = contact_name.lower().strip().split()
        
        if len(name_parts) >= 2:
            # Try firstname.lastname@domain format
            first_name = name_parts[0]
            last_name = name_parts[-1]
            email = f"{first_name}.{last_name}{domain}"
        elif len(name_parts) == 1:
            # Single name - use firstname@domain
            email = f"{name_parts[0]}{domain}"
        else:
            return "NOT_FOUND"
        
        # Clean up the email
        email = re.sub(r'[^a-zA-Z0-9.@]', '', email)
        
        logger.info(f"Generated email for {contact_name}: {email}")
        return email
        """
        if not contact_name or not company_domain:
            return "NOT_FOUND"

    # Clean the domain
        if company_domain.startswith("http"):
            parsed = urlparse(company_domain)
            domain = parsed.netloc
        else:
            domain = company_domain
        if domain.startswith("www."):
            domain = domain[4:]
        domain = domain.lower().strip()
        if not domain:
            return "NOT_FOUND"

     # Parse the name
        name_parts = contact_name.lower().strip().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            email = f"{first_name}.{last_name}@{domain}"
        elif len(name_parts) == 1:
            email = f"{name_parts[0]}@{domain}"
        else:
            return "NOT_FOUND"

        # Clean up the email safely
        email = re.sub(r'[^a-z0-9.@\-]', '', email)
        return email

    def extract_company_domain(self, company_name: str) -> Optional[str]:
        """
        Extract company domain from company name using web search.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Company domain or None if not found
        """
        try:
            # Search for company website
            query = f'"{company_name}" official website'
            results = self.brave_search.search(query, count=5)
            
            if "error" in results:
                logger.warning(f"Domain search error: {results['error']}")
                return None
            
            web_results = results.get("web", {}).get("results", [])
            
            # Look for company website in results
            for result in web_results:
                url = result.get("url", "").lower()
                title = result.get("title", "").lower()
                
                # Skip LinkedIn, social media, and job sites
                skip_domains = ["linkedin.com", "facebook.com", "twitter.com", "instagram.com", 
                              "indeed.com", "glassdoor.com", "crunchbase.com"]
                
                if any(skip_domain in url for skip_domain in skip_domains):
                    continue
                
                # Extract domain from URL
                if url.startswith("http"):
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc
                        
                        # Remove www prefix
                        if domain.startswith("www."):
                            domain = domain[4:]
                        
                        if domain and "." in domain:
                            logger.info(f"Found domain for {company_name}: {domain}")
                            return domain
                    except Exception as e:
                        logger.warning(f"Error parsing URL {url}: {str(e)}")
                        continue
            
            logger.warning(f"Could not find domain for company: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting domain for {company_name}: {str(e)}")
            return None

    def enrich_contact(self, contact_name: str, company_name: str) -> ContactInfo:
        """
        Enrich contact information by finding LinkedIn profile, job title, and work email.
        
        Args:
            contact_name: Name of the contact
            company_name: Name of the company
            
        Returns:
            ContactInfo object with enriched data
        """
        logger.info(f"Starting enrichment for: {contact_name} at {company_name}")
        
        # Initialize contact info
        contact_info = ContactInfo(
            contact_name=contact_name,
            company_name=company_name
        )
        
        # Extract LinkedIn URL and job title using the agent
        agent_results = self.extract_contact_info(contact_name, company_name)
        contact_info.linkedin_url = agent_results["linkedin_url"]
        contact_info.current_job_title = agent_results["current_job_title"]
        
        # Set citation source
        if contact_info.linkedin_url != "NOT_FOUND":
            contact_info.citation_source = "LinkedIn Profile"
        else:
            contact_info.citation_source = "Web Search"
        
        # Extract company domain and generate work email
        company_domain = self.extract_company_domain(company_name)
        if company_domain:
            contact_info.work_email = self.generate_work_email(contact_name, company_domain)
        else:
            contact_info.work_email = "NOT_FOUND"
        
        logger.info(f"Enrichment completed for: {contact_name}")
        return contact_info

    def process_contacts_batch(self, contacts: List[Dict[str, str]]) -> List[ContactInfo]:
        """
        Process a batch of contacts for enrichment.
        
        Args:
            contacts: List of dictionaries with 'contact_name' and 'company_name' keys
            
        Returns:
            List of ContactInfo objects
        """
        enriched_contacts = []
        
        for i, contact in enumerate(contacts, 1):
            contact_name = contact.get("contact_name", "")
            company_name = contact.get("company_name", "")
            
            if not contact_name or not company_name:
                logger.warning(f"Skipping contact {i}: missing name or company")
                continue
            
            logger.info(f"Processing contact {i}/{len(contacts)}: {contact_name}")
            
            try:
                enriched_contact = self.enrich_contact(contact_name, company_name)
                enriched_contacts.append(enriched_contact)
                
                # Add a small delay to avoid rate limiting
                import time
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing contact {contact_name}: {str(e)}")
                # Add a failed contact with basic info
                failed_contact = ContactInfo(
                    contact_name=contact_name,
                    company_name=company_name,
                    linkedin_url="ERROR",
                    current_job_title="ERROR",
                    work_email="ERROR",
                    citation_source="ERROR"
                )
                enriched_contacts.append(failed_contact)
        
        return enriched_contacts
    
def run_contact_agent(contact_name: str, company_name: str, company_domain: str = ""):
    """
    Wrapper function to be used in excel_company_processor.
    Uses ContactEnrichmentAgent to enrich contact details.
    """
    agent = ContactEnrichmentAgent()
    result = agent.enrich_contact(contact_name, company_name)
    
    return (
        result.linkedin_url,
        result.current_job_title,
        result.work_email,
        result.citation_source
    )



if __name__ == "__main__":
    # Test the contact enrichment agent
    agent = ContactEnrichmentAgent()
    
    # Test with a sample contact
    test_contact = {
        "contact_name": "John Smith",
        "company_name": "Microsoft"
    }
    
    print("Testing contact enrichment agent...")
    result = agent.enrich_contact(test_contact["contact_name"], test_contact["company_name"])
    
    print(f"\nResults for {test_contact['contact_name']} at {test_contact['company_name']}:")
    print(f"LinkedIn URL: {result.linkedin_url}")
    print(f"Job Title: {result.current_job_title}")
    print(f"Work Email: {result.work_email}")
    print(f"Citation Source: {result.citation_source}")
