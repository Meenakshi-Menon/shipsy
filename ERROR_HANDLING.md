# Error Handling in Revenue Agent

This document describes the comprehensive error handling system implemented in the revenue agent to ensure robust operation and graceful failure handling.

## Overview

The revenue agent now includes extensive error handling capabilities that provide:

- **Input validation** and sanitization
- **API error handling** with retry logic
- **Graceful degradation** when services are unavailable
- **Comprehensive logging** for debugging and monitoring
- **Custom exception classes** for better error categorization
- **Tool-level error handling** for LangChain integration

## Custom Exception Classes

### RevenueAgentError

Base exception class for all revenue agent errors.

### APIError

Raised for API-related errors such as:

- Invalid API keys
- Rate limiting
- Network timeouts
- Server errors

### ValidationError

Raised for input validation errors such as:

- Empty or invalid company names
- Invalid domain formats (only when domain is provided)
- Missing required parameters

**Note:** Company domain is optional and can be `None`, empty string, blank string (from CSV empty cells), or a valid domain string. Blank strings and whitespace-only strings are treated as empty.

### ConfigurationError

Raised for configuration-related errors such as:

- Missing environment variables
- Invalid configuration values

### DataProcessingError

Raised for data processing errors such as:

- JSON parsing failures
- Invalid response formats
- Data extraction errors

## Error Handling Features

### 1. Input Validation and Sanitization

All methods now validate inputs before processing:

```python
def _validate_input(self, company_name: str, company_domain: str = "") -> None:
    """Validate input parameters."""
    if not company_name or not isinstance(company_name, str):
        raise ValidationError("Company name must be a non-empty string")
    
    if len(company_name.strip()) < 2:
        raise ValidationError("Company name must be at least 2 characters long")
    
    # Company domain is optional - handle None, empty string, blank string, or valid domain
    if company_domain is not None and not isinstance(company_domain, str):
        raise ValidationError("Company domain must be a string when provided")
    
    # Sanitize inputs
    company_name = company_name.strip()
    if company_domain and isinstance(company_domain, str):
        company_domain = company_domain.strip()
    
    # Basic validation for domain format (only if domain is provided and not empty/blank)
    if (company_domain and isinstance(company_domain, str) and 
        company_domain.strip() and company_domain.strip() != ""):
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', company_domain.strip()):
            logger.warning(f"Company domain '{company_domain}' may not be in valid format")
```

### 2. Retry Logic with Exponential Backoff

API calls include automatic retry logic:

```python
def _retry_api_call(self, func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry API calls with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.RequestException, APIError) as e:
            if attempt == max_retries - 1:
                raise APIError(f"API call failed after {max_retries} attempts: {str(e)}")

            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

### 3. Comprehensive Logging

All operations are logged with appropriate levels:

```python
logger.info(f"Starting revenue analysis for: {company_name}")
logger.warning(f"No financial information found for {company_name}")
logger.error(f"API call failed: {str(e)}")
```

### 4. Graceful Degradation

The agent continues operation even when some components fail:

```python
def analyze_company_revenue(self, company_name: str, company_domain: str = "") -> Dict:
    try:
        # Step 1: Search for financial information
        try:
            search_results = self.search_company_financials(company_name, company_domain)
        except Exception as e:
            search_results = f"Search failed: {str(e)}"

        # Step 2: Extract revenue using DeepSeek
        try:
            revenue, citation = self.extract_revenue_from_sources(company_name, search_results)
        except Exception as e:
            revenue = None
            citation = f"Revenue extraction failed: {str(e)}"

        return {
            "status": "success" if revenue is not None else "partial",
            # ... other fields
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
            # ... other fields
        }
```

### 5. API Error Handling

Specific handling for different HTTP status codes:

```python
if response.status_code == 401:
    raise APIError("Invalid API key or unauthorized access")
elif response.status_code == 429:
    raise APIError("Rate limit exceeded. Please try again later.")
elif response.status_code == 500:
    raise APIError("Internal server error from OpenRouter API")
```

### 6. JSON Response Parsing

Multiple strategies for parsing AI responses:

```python
# Strategy 1: Look for JSON block in response
json_match = re.search(r'\{.*\}', response, re.DOTALL)
if json_match:
    json_str = json_match.group()
    data = json.loads(json_str)
    # Process data...

# Strategy 2: Try to parse entire response as JSON
try:
    data = json.loads(response)
    # Process data...
except json.JSONDecodeError:
    pass

# Strategy 3: Fallback - return raw response
return None, f"Could not parse structured response: {response[:200]}..."
```

## Tool-Level Error Handling

LangChain tools include error handling to prevent crashes:

```python
@tool
def search_company_financials(company_name: str, company_domain: str = "") -> str:
    try:
        return agent.search_company_financials(company_name, company_domain)
    except ValidationError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        logger.error(f"Error in search_company_financials tool: {str(e)}")
        return f"Search failed: {str(e)}"
```

## Web Search Error Handling

Enhanced error handling in the web search component:

```python
def search(self, query: str, count: int = None) -> Dict:
    if not query or not isinstance(query, str):
        return {
            "error": "Invalid query: must be a non-empty string",
            "web": {"results": []}
        }

    try:
        response = requests.get(self.base_url, headers=self.headers, params=params, timeout=30)

        if response.status_code == 401:
            return {"error": "Unauthorized access to search API. Check API key.", "web": {"results": []}}
        elif response.status_code == 429:
            return {"error": "Rate limit exceeded. Please try again later.", "web": {"results": []}}

        # ... process response
    except requests.exceptions.Timeout:
        return {"error": "Search request timed out. Please try again.", "web": {"results": []}}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error. Please check your internet connection.", "web": {"results": []}}
```

## Testing Error Handling

A comprehensive test suite is provided in `test_error_handling.py` that demonstrates:

1. **Input validation errors** - Testing with empty, None, and invalid inputs
2. **API error handling** - Testing with malformed requests and responses
3. **Graceful degradation** - Testing behavior when services fail
4. **Web search errors** - Testing search API error conditions
5. **Tool error handling** - Testing LangChain tool error handling

Run the test suite with:

```bash
python test_error_handling.py
```

## Best Practices

### For Developers

1. **Always catch specific exceptions** first, then general ones
2. **Log errors with appropriate levels** (ERROR for failures, WARNING for recoverable issues)
3. **Provide meaningful error messages** that help with debugging
4. **Return partial results** when possible instead of complete failure
5. **Use custom exceptions** for better error categorization

### For Users

1. **Check the status field** in results to understand success level
2. **Review error messages** in citations when revenue is not found
3. **Monitor logs** for detailed debugging information
4. **Handle ValidationError** by providing valid inputs
5. **Retry operations** when encountering temporary API errors

## Configuration

Ensure proper configuration by setting required environment variables:

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key
BRAVE_API_KEY=your_brave_search_api_key

# Optional (with defaults)
DEEPSEEK_MODEL=deepseek/deepseek-chat-v3.1:free
DEEPSEEK_TEMPERATURE=0.3
DEEPSEEK_MAX_TOKENS=2000
BRAVE_SEARCH_COUNT=10
```

## Monitoring and Debugging

### Log Levels

- **INFO**: Normal operation flow
- **WARNING**: Recoverable issues (e.g., no results found)
- **ERROR**: Failures that prevent operation

### Key Metrics to Monitor

1. **API call success rates**
2. **Response parsing success rates**
3. **Search result availability**
4. **Error frequency by type**

### Common Issues and Solutions

1. **API Key Errors**: Check environment variables
2. **Rate Limiting**: Implement backoff or reduce request frequency
3. **Network Issues**: Check internet connectivity and firewall settings
4. **Parsing Errors**: Review AI model responses for format changes

This comprehensive error handling system ensures the revenue agent operates reliably in production environments while providing clear feedback about any issues that occur.
