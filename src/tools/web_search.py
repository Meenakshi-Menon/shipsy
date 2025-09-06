import requests
import json
import time
import logging
from typing import Dict, List, Optional
from src.config.settings import Config

# Configure logging
logger = logging.getLogger(__name__)


class BraveWebSearch:
    """Web search tool using Brave Search API."""
    
    def __init__(self):
        self.api_key = Config.BRAVE_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
    
    def search(self, query: str, count: int = None) -> Dict:
        """
        Perform a web search using Brave Search API with enhanced error handling.
        
        Args:
            query: Search query string
            count: Number of results to return (default from config)
            
        Returns:
            Dictionary containing search results
        """
        if not query or not isinstance(query, str):
            logger.error("Invalid query provided to search method")
            return {
                "error": "Invalid query: must be a non-empty string",
                "web": {"results": []}
            }
        
        if count is None:
            count = Config.BRAVE_SEARCH_COUNT
            
        logger.info(f"Performing search for query: {query[:100]}...")
        
        params = {
            "q": query,
            "count": count,
            "offset": 0,
            "mkt": "en-US",
            "safesearch": "moderate"
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            logger.info(f"Search response status: {response.status_code}")
            
            if response.status_code == 401:
                logger.error("Unauthorized access to Brave Search API")
                return {
                    "error": "Unauthorized access to search API. Check API key.",
                    "web": {"results": []}
                }
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded for Brave Search API")
                return {
                    "error": "Rate limit exceeded. Please try again later.",
                    "web": {"results": []}
                }
            
            response.raise_for_status()
            
            # Wait 1 second after each search call for rate limiting
            time.sleep(1)
            
            result = response.json()
            logger.info(f"Search completed successfully, found {len(result.get('web', {}).get('results', []))} results")
            return result
            
        except requests.exceptions.Timeout:
            logger.error("Search request timed out")
            return {
                "error": "Search request timed out. Please try again.",
                "web": {"results": []}
            }
        except requests.exceptions.ConnectionError:
            logger.error("Connection error during search")
            return {
                "error": "Connection error. Please check your internet connection.",
                "web": {"results": []}
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Search request failed: {str(e)}")
            return {
                "error": f"Search request failed: {str(e)}",
                "web": {"results": []}
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse search response: {str(e)}")
            return {
                "error": f"Failed to parse search response: {str(e)}",
                "web": {"results": []}
            }
    
    def search_company_revenue(self, company_name: str, company_domain: str = None) -> List[Dict]:
        """
        Search for company revenue information with enhanced error handling.
        Prioritizes professional sites like RocketReach, Apollo.io, Hunter.io before generic search.
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain
            
        Returns:
            List of search results with relevant information
        """
        if not company_name or not isinstance(company_name, str):
            logger.error("Invalid company name provided")
            return []
        
        logger.info(f"Searching for revenue information for company: {company_name}")
        
        # First, try professional sites for company data
        professional_results = self._search_professional_sites(company_name, company_domain)
        if professional_results:
            logger.info(f"Found {len(professional_results)} results from professional sites")
            return professional_results
        
        # If no results from professional sites, fall back to generic search
        logger.info("No results from professional sites, falling back to generic search")
        return self._search_generic_revenue(company_name, company_domain)
    
    def _search_professional_sites(self, company_name: str, company_domain: str = None) -> List[Dict]:
        """
        Search professional sites like RocketReach, Apollo.io, Hunter.io for company data.
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain
            
        Returns:
            List of search results from professional sites
        """
        professional_sites = [
            "site:rocketreach.co",
            "site:apollo.io", 
            "site:hunter.io",
            "site:zoominfo.com",
            "site:clearbit.com",
            "site:crunchbase.com"
        ]
        
        all_results = []
        
        for site_filter in professional_sites:
            # Construct site-specific query
            query_parts = [
                site_filter,
                f'"{company_name}"',
                "revenue",
                "financial",
                "company data"
            ]
            
            if company_domain:
                query_parts.append(f'({company_domain})')
            
            query = " ".join(query_parts)
            logger.info(f"Searching professional site with query: {query}")
            
            results = self.search(query, count=10)
            
            if "error" in results:
                logger.warning(f"Search error for {site_filter}: {results['error']}")
                continue
            
            web_results = results.get("web", {}).get("results", [])
            
            # Process results from this professional site
            for result in web_results:
                try:
                    all_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", ""),
                        "published_date": result.get("published_date", ""),
                        "age": result.get("age", ""),
                        "source_type": "professional_site"
                    })
                except Exception as e:
                    logger.warning(f"Error processing professional site result: {str(e)}")
                    continue
            
            # If we found results from this site, we can break early
            if web_results:
                logger.info(f"Found {len(web_results)} results from {site_filter}")
                break
        
        return all_results[:10]  # Return top 10 professional site results
    
    def _search_generic_revenue(self, company_name: str, company_domain: str = None) -> List[Dict]:
        """
        Perform generic search for company revenue information.
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain
            
        Returns:
            List of search results from generic search
        """
        # Construct search query for revenue information
        query_parts = [
            f'"{company_name}"',
            "annual revenue",
            "revenue",
            "financial results",
            "earnings report"
        ]
        
        if company_domain:
            query_parts.append(f'({company_domain})')
        
        query = " ".join(query_parts)
        logger.info(f"Constructed generic search query: {query}")
        
        results = self.search(query, count=15)
        
        if "error" in results:
            logger.warning(f"Generic search error for {company_name}: {results['error']}")
            return []
        
        # Extract relevant results
        search_results = []
        web_results = results.get("web", {}).get("results", [])
        
        logger.info(f"Processing {len(web_results)} generic search results for {company_name}")
        
        for i, result in enumerate(web_results):
            try:
                search_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                    "published_date": result.get("published_date", ""),
                    "age": result.get("age", ""),
                    "source_type": "generic_search"
                })
            except Exception as e:
                logger.warning(f"Error processing generic search result {i}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(search_results)} generic results for {company_name}")
        return search_results
    
    def get_revenue_sources(self, company_name: str, company_domain: str = None) -> List[str]:
        """
        Get URLs of sources that likely contain revenue information.
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain
            
        Returns:
            List of URLs that likely contain revenue information
        """
        results = self.search_company_revenue(company_name, company_domain)
        
        # Filter for likely revenue sources
        revenue_sources = []
        for result in results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            description = result.get("description", "").lower()
            
            # Look for financial reports, earnings, SEC filings, etc.
            financial_keywords = [
                "annual report", "quarterly report", "earnings", "financial results",
                "sec filing", "10-k", "10-q", "revenue", "income statement",
                "financial statement", "investor relations", "ir.", "investor"
            ]
            
            if any(keyword in url or keyword in title or keyword in description 
                   for keyword in financial_keywords):
                revenue_sources.append(result.get("url", ""))
        
        return revenue_sources[:5]  # Return top 5 most relevant sources


def create_web_search_tool():
    """Create a LangChain tool for web search."""
    from langchain_core.tools import tool
    
    brave_search = BraveWebSearch()
    
    @tool
    def search_web(query: str) -> str:
        """
        Search the web for information using Brave Search API.
        
        Args:
            query: The search query
            
        Returns:
            Formatted search results as a string
        """
        results = brave_search.search(query)
        
        if "error" in results:
            return f"Search error: {results['error']}"
        
        web_results = results.get("web", {}).get("results", [])
        
        if not web_results:
            return "No search results found."
        
        formatted_results = []
        for i, result in enumerate(web_results[:5], 1):
            formatted_results.append(
                f"{i}. {result.get('title', 'No title')}\n"
                f"   URL: {result.get('url', 'No URL')}\n"
                f"   Description: {result.get('description', 'No description')}\n"
            )
        
        return "\n".join(formatted_results)
    
    @tool
    def search_company_financials(company_name: str, company_domain: str = "") -> str:
        """
        Search for company financial information including revenue.
        
        Args:
            company_name: Name of the company to search for
            company_domain: Optional company domain
            
        Returns:
            Formatted search results focused on financial information
        """
        results = brave_search.search_company_revenue(company_name, company_domain)
        
        if not results:
            return f"No financial information found for {company_name}."
        
        formatted_results = []
        for i, result in enumerate(results[:5], 1):
            formatted_results.append(
                f"{i}. {result.get('title', 'No title')}\n"
                f"   URL: {result.get('url', 'No URL')}\n"
                f"   Description: {result.get('description', 'No description')}\n"
                f"   Published: {result.get('published_date', 'Unknown')}\n"
            )
        
        return "\n".join(formatted_results)
    
    return [search_web, search_company_financials]


if __name__ == "__main__":
    # Test the web search functionality
    search_tool = BraveWebSearch()
    
    # Test search
    test_query = "Apple Inc annual revenue 2024"
    print(f"Testing search for: {test_query}")
    results = search_tool.search(test_query)
    
    if "error" in results:
        print(f"Error: {results['error']}")
    else:
        web_results = results.get("web", {}).get("results", [])
        print(f"Found {len(web_results)} results")
        for i, result in enumerate(web_results[:3], 1):
            print(f"{i}. {result.get('title', 'No title')}")
            print(f"   {result.get('url', 'No URL')}")
            print()
