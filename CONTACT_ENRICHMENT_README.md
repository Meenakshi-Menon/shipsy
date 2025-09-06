# Contact Enrichment Agent

A powerful agent for enriching contact information by finding LinkedIn profiles, job titles, and work emails using Brave Search API and DeepSeek AI.

## Features

- **LinkedIn Profile Discovery**: Uses Brave Search with site filters to find LinkedIn profiles
- **Job Title Extraction**: Extracts current job titles from LinkedIn profiles and web search results
- **Work Email Generation**: Generates likely work email addresses from contact names and company domains
- **Company Domain Detection**: Automatically finds company domains from web search
- **Batch Processing**: Processes multiple contacts from CSV files efficiently
- **Multiple Output Formats**: Saves results in both CSV and JSON formats
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Architecture

The contact enrichment agent consists of several key components:

### 1. Contact Enrichment Agent (`src/agents/contact_agent.py`)

- Main agent that orchestrates the enrichment process
- Uses DeepSeek AI via OpenRouter for intelligent data extraction
- Integrates with Brave Search API for web searches
- Handles LinkedIn profile discovery and job title extraction

### 2. CSV Processor (`src/processors/contact_csv_processor.py`)

- Handles reading and writing CSV files
- Manages batch processing of contacts
- Converts data between different formats

### 3. Main Script (`contact_enrichment.py`)

- Command-line interface for running the enrichment process
- Handles argument parsing and error handling
- Provides progress reporting and summary statistics

## Installation

1. **Install Dependencies**:

   ```bash
   uv sync
   ```

2. **Set up Environment Variables**:
   Create a `.env` file with the following variables:

   ```env
   # OpenRouter API Configuration for DeepSeek
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   DEEPSEEK_MODEL=deepseek/deepseek-chat-v3.1:free
   DEEPSEEK_TEMPERATURE=0.3
   DEEPSEEK_MAX_TOKENS=2000

   # Brave Search API Configuration
   BRAVE_API_KEY=your_brave_api_key_here
   BRAVE_SEARCH_COUNT=10
   ```

3. **Get API Keys**:
   - **OpenRouter API Key**: Sign up at [OpenRouter](https://openrouter.ai/) to get access to DeepSeek models
   - **Brave Search API Key**: Get your API key from [Brave Search API](https://brave.com/search/api/)

## Usage

### Basic Usage

1. **Create a Sample CSV File**:

   ```bash
   uv run python contact_enrichment.py --sample
   ```

2. **Run Contact Enrichment**:
   ```bash
   uv run python contact_enrichment.py input.csv output.csv
   ```

### Input CSV Format

Your input CSV file should have the following columns:

- `contact_name`: Full name of the contact
- `company_name`: Name of the company

Example:

```csv
contact_name,company_name
John Smith,Microsoft
Sarah Johnson,Google
Michael Brown,Apple
```

### Output Format

The enriched output will contain:

- `contact_name`: Original contact name
- `company_name`: Original company name
- `linkedin_url`: LinkedIn profile URL (or "NOT_FOUND")
- `current_job_title`: Current job title (or "NOT_FOUND")
- `work_email`: Generated work email (or "NOT_FOUND")
- `citation_source`: Source of the information

Example output:

```csv
contact_name,company_name,linkedin_url,current_job_title,work_email,citation_source
John Smith,Microsoft,https://linkedin.com/in/johnsmith,Software Engineer,john.smith@microsoft.com,LinkedIn Profile
```

## How It Works

### 1. LinkedIn Profile Discovery

- Uses Brave Search with `site:linkedin.com/in/` filters
- Searches for the contact name and company name
- Prioritizes LinkedIn profiles over other results

### 2. Job Title Extraction

- Uses DeepSeek AI to analyze search results
- Extracts current job title from LinkedIn profiles
- Handles various job title formats and variations

### 3. Work Email Generation

- Automatically detects company domain from web search
- Generates likely email formats (e.g., `firstname.lastname@domain.com`)
- Uses common email patterns for different companies

### 4. Data Processing Flow

```
CSV Input → Contact Agent → Brave Search → DeepSeek AI → Email Generation → CSV/JSON Output
```

## Testing

Run the test suite to verify everything is working:

```bash
uv run python test_contact_agent.py
```

This will test:

- CSV processing functionality
- ContactInfo data structure
- Email generation logic

## Error Handling

The agent includes comprehensive error handling:

- **API Rate Limiting**: Built-in delays and retry logic
- **Invalid Data**: Skips contacts with missing information
- **Search Failures**: Gracefully handles search API errors
- **LLM Errors**: Handles AI model failures with fallback responses

## Logging

All operations are logged to both console and `contact_enrichment.log` file:

- Search queries and results
- AI model interactions
- Processing progress
- Error messages and stack traces

## Performance Considerations

- **Rate Limiting**: 2-second delay between contact processing
- **Batch Processing**: Processes contacts sequentially to avoid API limits
- **Result Caching**: Search results are processed efficiently
- **Memory Usage**: Processes contacts in batches to manage memory

## Troubleshooting

### Common Issues

1. **API Key Errors**:

   - Verify your API keys are correctly set in `.env`
   - Check that your OpenRouter and Brave Search accounts are active

2. **No Results Found**:

   - Some contacts may not have public LinkedIn profiles
   - Try different name variations or company spellings

3. **Rate Limiting**:
   - The agent includes built-in delays
   - For large batches, consider processing in smaller chunks

### Debug Mode

Enable debug logging by modifying the logging level in `contact_enrichment.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Examples

### Process Sample Data

```bash
# Create sample file
uv run python contact_enrichment.py --sample

# Process the sample
uv run python contact_enrichment.py sample_contacts.csv enriched_sample_contacts.csv
```

### Process Your Own Data

```bash
# Your CSV should have contact_name and company_name columns
uv run python contact_enrichment.py my_contacts.csv enriched_my_contacts.csv
```

## Output Files

The enrichment process creates multiple output files:

- **CSV File**: `enriched_contacts.csv` - Main results in CSV format
- **JSON File**: `enriched_contacts.json` - Backup results in JSON format
- **Log File**: `contact_enrichment.log` - Detailed processing logs

## Contributing

To extend the contact enrichment agent:

1. **Add New Search Sources**: Modify `ContactEnrichmentAgent.search_linkedin_profile()`
2. **Improve Email Generation**: Enhance `generate_work_email()` method
3. **Add New Output Formats**: Extend `ContactCSVProcessor` class
4. **Enhance AI Prompts**: Modify the system prompt in `ContactEnrichmentAgent`

## License

This project is part of the LangGraph Agent Project. See the main project README for license information.
