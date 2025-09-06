import requests
import json
import logging
import time
import re
from typing import Dict, List, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from src.config.settings import Config
from src.tools.web_search import BraveWebSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RevenueAgentError(Exception):
    """Base exception for revenue agent errors."""
    pass


class APIError(RevenueAgentError):
    """Exception raised for API-related errors."""
    pass


class ValidationError(RevenueAgentError):
    """Exception raised for input validation errors."""
    pass


class ConfigurationError(RevenueAgentError):
    """Exception raised for configuration errors."""
    pass


class DataProcessingError(RevenueAgentError):
    """Exception raised for data processing errors."""
    pass


class DeepSeekRevenueAgent:
    """Agent that uses DeepSeek model via OpenRouter to extract company revenue information."""
    
    def __init__(self):
        try:
            # Validate configuration
            if not Config.OPENROUTER_API_KEY:
                raise ConfigurationError("OPENROUTER_API_KEY is not configured")
            
            self.api_key = Config.OPENROUTER_API_KEY
            self.model = Config.DEEPSEEK_MODEL
            self.temperature = Config.DEEPSEEK_TEMPERATURE
            self.max_tokens = Config.DEEPSEEK_MAX_TOKENS
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.web_search = BraveWebSearch()
            
            logger.info("DeepSeekRevenueAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeekRevenueAgent: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    def _validate_input(self, company_name: str, company_domain: str = "") -> None:
        """Validate input parameters."""
        if not company_name or not isinstance(company_name, str):
            raise ValidationError("Company name must be a non-empty string")
        
        if len(company_name.strip()) < 2:
            raise ValidationError("Company name must be at least 2 characters long")
        
        # Sanitize inputs
        company_name = company_name.strip()
        if not isinstance(company_domain, str):
            company_domain = None

        if company_domain:
            company_domain = company_domain.strip()
        
        # Basic validation for domain format
        if company_domain and not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', company_domain):
            logger.warning(f"Company domain '{company_domain}' may not be in valid format")
    
    def _retry_api_call(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry API calls with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except (requests.exceptions.RequestException, APIError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"API call failed after {max_retries} attempts: {str(e)}")
                    raise APIError(f"API call failed after {max_retries} attempts: {str(e)}")
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {str(e)}")
                time.sleep(delay)
        
        raise APIError("Unexpected error in retry logic")
    
    def _call_deepseek(self, messages: List[Dict]) -> str:
        """Call DeepSeek model via OpenRouter API with comprehensive error handling."""
        if not messages or not isinstance(messages, list):
            raise ValidationError("Messages must be a non-empty list")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://langgraph-agent-project",
            "X-Title": "Company Revenue Analysis"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        def make_request():
            logger.info(f"Making API request to DeepSeek with model: {self.model}")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Log response status for debugging
            logger.info(f"API response status: {response.status_code}")
            
            if response.status_code == 401:
                raise APIError("Invalid API key or unauthorized access")
            elif response.status_code == 429:
                raise APIError("Rate limit exceeded. Please try again later.")
            elif response.status_code == 500:
                raise APIError("Internal server error from OpenRouter API")
            elif response.status_code >= 400:
                raise APIError(f"API request failed with status {response.status_code}: {response.text}")
            
            response.raise_for_status()
            return response
        
        try:
            response = self._retry_api_call(make_request)
            result = response.json()
            
            # Validate response structure
            if "choices" not in result:
                raise DataProcessingError("Invalid API response: missing 'choices' field")
            
            if not result["choices"] or len(result["choices"]) == 0:
                raise DataProcessingError("Invalid API response: empty choices array")
            
            if "message" not in result["choices"][0]:
                raise DataProcessingError("Invalid API response: missing 'message' field")
            
            if "content" not in result["choices"][0]["message"]:
                raise DataProcessingError("Invalid API response: missing 'content' field")
            
            content = result["choices"][0]["message"]["content"]
            logger.info("Successfully received response from DeepSeek API")
            return content
            
        except requests.exceptions.Timeout:
            raise APIError("Request timeout: The API call took too long to respond")
        except requests.exceptions.ConnectionError:
            raise APIError("Connection error: Unable to connect to the API")
        except json.JSONDecodeError as e:
            raise DataProcessingError(f"Failed to parse API response as JSON: {str(e)}")
        except Exception as e:
            if isinstance(e, (APIError, DataProcessingError)):
                raise
            raise APIError(f"Unexpected error calling DeepSeek API: {str(e)}")
    
    def search_company_financials(self, company_name: str, company_domain: str = "") -> str:
        """Search for company financial information with error handling."""
        try:
            # Validate inputs
            self._validate_input(company_name, company_domain)
            
            logger.info(f"Searching for financial information for: {company_name}")
            
            # Search for company revenue information
            results = self.web_search.search_company_revenue(company_name, company_domain)
            
            if not results:
                logger.warning(f"No financial information found for {company_name}")
                return f"No financial information found for {company_name}."
            
            # Format results safely
            formatted_results = []
            for i, result in enumerate(results[:5], 1):
                try:
                    title = result.get('title', 'No title') if result else 'No title'
                    url = result.get('url', 'No URL') if result else 'No URL'
                    description = result.get('description', 'No description') if result else 'No description'
                    published_date = result.get('published_date', 'Unknown') if result else 'Unknown'
                    
                    formatted_results.append(
                        f"{i}. {title}\n"
                        f"   URL: {url}\n"
                        f"   Description: {description}\n"
                        f"   Published: {published_date}\n"
                    )
                except Exception as e:
                    logger.warning(f"Error formatting result {i}: {str(e)}")
                    continue
            
            if not formatted_results:
                logger.warning(f"Failed to format any results for {company_name}")
                return f"Found results but failed to format them for {company_name}."
            
            logger.info(f"Successfully formatted {len(formatted_results)} results for {company_name}")
            return "\n".join(formatted_results)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error searching company financials for {company_name}: {str(e)}")
            raise DataProcessingError(f"Failed to search financial information: {str(e)}")
    
    def extract_revenue_from_sources(self, company_name: str, search_results: str) -> Tuple[Optional[float], str]:
        """
        Use DeepSeek to extract revenue information from search results with comprehensive error handling.
        
        Args:
            company_name: Name of the company
            search_results: Formatted search results from web search
            
        Returns:
            Tuple of (estimated_revenue_in_usd, citation_source)
        """
        try:
            # Validate inputs
            if not company_name or not isinstance(company_name, str):
                raise ValidationError("Company name must be a non-empty string")
            
            if not search_results or not isinstance(search_results, str):
                raise ValidationError("Search results must be a non-empty string")
            
            logger.info(f"Extracting revenue information for: {company_name}")
            
            prompt = f"""
You are a financial analyst tasked with extracting the most recent annual revenue for {company_name}.

Based on the following search results, please:
1. Find the most recent annual operating revenue. If not available, use an estimate.
2. Convert it to USD if it's in another currency
3. Provide the specific source URL where you found this information
4. If you cannot find reliable revenue from data, state that clearly

Search Results:
{search_results}

Please respond in the following JSON format:
{{
    "revenue_usd": <number in USD or null if not found>,
    "source_url": "<URL of the source or empty string if not found>",
    "confidence": "<high/medium/low>",
    "reasoning": "<brief explanation of how you arrived at this conclusion>"
}}

Important notes:
- Prefer official financial reports, SEC filings, or investor relations pages
- Use the most recent data available
- If multiple sources conflict, choose the most authoritative one
- Convert currencies using approximate exchange rates if needed
- Use estimates from relevant sources if needed
"""

            messages = [
                {"role": "user", "content": prompt}
            ]
            
            response = self._call_deepseek(messages)
            
            if not response or not isinstance(response, str):
                logger.error("Received empty or invalid response from DeepSeek API")
                return None, "Failed to get response from AI model"
            
            # Try to parse JSON response with multiple strategies
            try:
                # Strategy 1: Look for JSON block in response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    data = json.loads(json_str)
                    
                    # Validate required fields
                    revenue = data.get("revenue_usd")
                    source = data.get("source_url", "")
                    confidence = data.get("confidence", "low")
                    reasoning = data.get("reasoning", "")
                    
                    # Validate revenue value if present
                    if revenue is not None:
                        try:
                            revenue = float(revenue)
                            if revenue < 0:
                                logger.warning(f"Negative revenue value detected: {revenue}")
                                revenue = None
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid revenue value: {revenue}")
                            revenue = None
                    
                    logger.info(f"Successfully extracted revenue data for {company_name}")
                    return revenue, f"{source} (Confidence: {confidence}) - {reasoning}"
                
                # Strategy 2: Try to parse entire response as JSON
                try:
                    data = json.loads(response)
                    revenue = data.get("revenue_usd")
                    source = data.get("source_url", "")
                    confidence = data.get("confidence", "low")
                    reasoning = data.get("reasoning", "")
                    
                    if revenue is not None:
                        revenue = float(revenue)
                    
                    return revenue, f"{source} (Confidence: {confidence}) - {reasoning}"
                except json.JSONDecodeError:
                    pass
                
                # Strategy 3: Fallback - return raw response
                logger.warning(f"Could not parse JSON from response for {company_name}")
                return None, f"Could not parse structured response: {response[:200]}..."
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for {company_name}: {str(e)}")
                return None, f"Invalid JSON response: {str(e)}"
            except Exception as e:
                logger.error(f"Error processing response for {company_name}: {str(e)}")
                return None, f"Error processing AI response: {str(e)}"
                
        except ValidationError:
            raise
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting revenue for {company_name}: {str(e)}")
            raise DataProcessingError(f"Failed to extract revenue information: {str(e)}")
    
    def analyze_company_revenue(self, company_name: str, company_domain: str = "") -> Dict:
        """
        Complete analysis of company revenue with comprehensive error handling.
        
        Args:
            company_name: Name of the company
            company_domain: Optional company domain
            
        Returns:
            Dictionary with revenue analysis results
        """
        try:
            # Validate inputs
            self._validate_input(company_name, company_domain)
            
            logger.info(f"Starting revenue analysis for: {company_name}")
            
            # Step 1: Search for financial information
            try:
                search_results = self.search_company_financials(company_name, company_domain)
                logger.info(f"Search completed for {company_name}")
            except Exception as e:
                logger.error(f"Search failed for {company_name}: {str(e)}")
                search_results = f"Search failed: {str(e)}"
            
            # Step 2: Extract revenue using DeepSeek
            try:
                revenue, citation = self.extract_revenue_from_sources(company_name, search_results)
                logger.info(f"Revenue extraction completed for {company_name}")
            except Exception as e:
                logger.error(f"Revenue extraction failed for {company_name}: {str(e)}")
                revenue = None
                citation = f"Revenue extraction failed: {str(e)}"
            
            result = {
                "company_name": company_name,
                "company_domain": company_domain,
                "estimated_revenue_usd": revenue,
                "citation": citation,
                "search_results": search_results,
                "status": "success" if revenue is not None else "partial",
                "timestamp": time.time()
            }
            
            logger.info(f"Analysis completed for {company_name} with status: {result['status']}")
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Complete analysis failed for {company_name}: {str(e)}")
            # Return partial results even if analysis fails
            return {
                "company_name": company_name,
                "company_domain": company_domain,
                "estimated_revenue_usd": None,
                "citation": f"Analysis failed: {str(e)}",
                "search_results": "",
                "status": "failed",
                "timestamp": time.time(),
                "error": str(e)
            }


def create_revenue_agent_tools():
    """Create LangChain tools for the revenue agent with error handling."""
    try:
        agent = DeepSeekRevenueAgent()
    except Exception as e:
        logger.error(f"Failed to create revenue agent: {str(e)}")
        raise ConfigurationError(f"Failed to initialize revenue agent: {str(e)}")
    
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
        try:
            return agent.search_company_financials(company_name, company_domain)
        except ValidationError as e:
            return f"Validation error: {str(e)}"
        except Exception as e:
            logger.error(f"Error in search_company_financials tool: {str(e)}")
            return f"Search failed: {str(e)}"
    
    @tool
    def extract_revenue_from_sources(company_name: str, search_results: str) -> str:
        """
        Extract revenue information from search results using DeepSeek.
        
        Args:
            company_name: Name of the company
            search_results: Formatted search results
            
        Returns:
            JSON string with revenue analysis
        """
        try:
            revenue, citation = agent.extract_revenue_from_sources(company_name, search_results)
            
            result = {
                "revenue_usd": revenue,
                "citation": citation,
                "company_name": company_name,
                "status": "success" if revenue is not None else "partial"
            }
            
            return json.dumps(result, indent=2)
            
        except ValidationError as e:
            error_result = {
                "revenue_usd": None,
                "citation": f"Validation error: {str(e)}",
                "company_name": company_name,
                "status": "failed",
                "error": str(e)
            }
            return json.dumps(error_result, indent=2)
        except Exception as e:
            logger.error(f"Error in extract_revenue_from_sources tool: {str(e)}")
            error_result = {
                "revenue_usd": None,
                "citation": f"Extraction failed: {str(e)}",
                "company_name": company_name,
                "status": "failed",
                "error": str(e)
            }
            return json.dumps(error_result, indent=2)
    
    return [search_company_financials, extract_revenue_from_sources]


if __name__ == "__main__":
    # Test the revenue agent with error handling
    try:
        print("Initializing DeepSeek Revenue Agent...")
        agent = DeepSeekRevenueAgent()
        print("✓ Agent initialized successfully")
        
        # Test with a well-known company
        test_company = "Apple Inc"
        test_domain = "apple.com"
        
        print(f"\nAnalyzing revenue for: {test_company}")
        print("=" * 50)
        
        result = agent.analyze_company_revenue(test_company, test_domain)
        
        print(f"Company: {result['company_name']}")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result['estimated_revenue_usd']:
            print(f"Estimated Revenue (USD): ${result['estimated_revenue_usd']:,.2f}")
        else:
            print("Revenue not found")
        
        print(f"Citation: {result['citation']}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
        
        print("\nSearch Results:")
        print(result['search_results'])
        
    except ConfigurationError as e:
        print(f"Configuration Error: {str(e)}")
        print("Please check your environment variables and configuration.")
    except ValidationError as e:
        print(f"Validation Error: {str(e)}")
    except APIError as e:
        print(f"API Error: {str(e)}")
    except DataProcessingError as e:
        print(f"Data Processing Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        logger.error(f"Unexpected error in main: {str(e)}")
