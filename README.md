# LangGraph Agent Project - Company Revenue Analysis

This project provides an automated system using LangGraph agents to determine the latest available Revenue from Operations of companies and assign them to tiers based on predefined criteria. Built with modern Python tooling including `uv` for fast dependency management.

## Features

- **Web Search Integration**: Uses Brave Search API to find company financial information
- **AI-Powered Analysis**: Leverages DeepSeek model via OpenRouter for revenue extraction
- **Automated Tier Assignment**: Static tier assignment based on revenue thresholds
- **CSV Processing**: Batch processing of company data from CSV files
- **Rate Limiting**: Built-in delays to respect API rate limits

## Tier Definitions

- **Super Platinum**: Annual revenue from operations > $1Bn
- **Platinum**: Annual revenue from operations $500Mn to $1Bn
- **Diamond**: Annual revenue from operations $100Mn to $500Mn
- **Gold**: Annual revenue from operations below $100Mn

## Prerequisites

1. **OpenRouter API Key**: For accessing DeepSeek model

   - Sign up at [OpenRouter](https://openrouter.ai/)
   - Get your API key from the dashboard

2. **Brave Search API Key**: For web searching
   - Sign up at [Brave Search API](https://brave.com/search/api/)
   - Get your API key from the dashboard

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd langgraph-agent-project
```

2. Install dependencies using `uv` (recommended):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

**Why use `uv`?**

- **Faster**: Up to 10-100x faster than pip for dependency resolution and installation
- **Reliable**: Better dependency resolution with lockfile support
- **Modern**: Built for modern Python projects with better tooling integration
- **Compatible**: Works seamlessly with existing `pyproject.toml` files

Alternatively, you can use pip:

```bash
pip install -e .
```

3. Set up environment variables:

```bash
cp env.example .env
```

4. Edit `.env` file with your API keys:

```bash
# OpenRouter API Configuration for DeepSeek
OPENROUTER_API_KEY=your_openrouter_api_key_here
DEEPSEEK_MODEL=deepseek/deepseek-chat-v3.1:free
DEEPSEEK_TEMPERATURE=0.3
DEEPSEEK_MAX_TOKENS=2000

# Brave Search API Configuration
BRAVE_API_KEY=your_brave_api_key_here
BRAVE_SEARCH_COUNT=10
```

## Usage

### Basic Usage

Process a CSV file with company data:

```bash
# Using uv (recommended)
uv run python company_revenue_analyzer.py companies.csv

# Or using python directly (if dependencies are installed globally)
python company_revenue_analyzer.py companies.csv
```

### Advanced Usage

```bash
# Specify custom output prefix
uv run python company_revenue_analyzer.py companies.csv results

# Adjust delay between companies (default: 2 seconds)
uv run python company_revenue_analyzer.py companies.csv --delay 3.0

# Validate CSV format without processing
uv run python company_revenue_analyzer.py companies.csv --validate-only
```

### CSV Format

Your input CSV must contain these columns:

- `Company Name`: The name of the company
- `Company Region`: Geographic region of the company
- `Company Domain`: Company's website domain

Example CSV:

```csv
Company Name,Company Region,Company Domain
Apple Inc,North America,apple.com
Microsoft Corporation,North America,microsoft.com
Tesla Inc,North America,tesla.com
```

## Output Files

The script generates three output files:

1. **`{prefix}.csv`**: Main results in CSV format
2. **`{prefix}.json`**: Detailed results in JSON format
3. **`{prefix}_summary.txt`**: Summary statistics and tier distribution

### Output Columns

- `company_name`: Company name
- `company_domain`: Company domain
- `company_region`: Company region
- `estimated_revenue_usd`: Revenue in USD (if found)
- `revenue_display`: Formatted revenue display
- `tier`: Assigned tier
- `tier_description`: Description of the tier
- `citation`: Source of the revenue information

## Architecture

### Components

1. **Web Search Tool** (`src/tools/web_search.py`)

   - Brave Search API integration
   - Company-specific financial search
   - Rate limiting with 1-second delays

2. **Revenue Agent** (`src/agents/revenue_agent.py`)

   - DeepSeek model integration via OpenRouter
   - Revenue extraction from search results
   - Citation tracking

3. **Tier Assignment** (`src/tools/tier_assignment.py`)

   - Static tier assignment logic
   - Revenue formatting utilities
   - Tier descriptions

4. **CSV Processor** (`src/processors/csv_processor.py`)

   - Batch processing pipeline
   - Error handling and retry logic
   - Results aggregation

5. **Main Script** (`company_revenue_analyzer.py`)
   - Command-line interface
   - Configuration validation
   - Progress tracking

### Data Flow

```
CSV Input → Load Companies → For Each Company:
  ↓
Web Search (Brave API) → Find Financial Sources
  ↓
AI Analysis (DeepSeek) → Extract Revenue
  ↓
Tier Assignment (Static) → Assign Tier
  ↓
Aggregate Results → Save Output Files
```

## Rate Limiting

The system includes built-in rate limiting:

- 1-second delay after each Brave Search API call
- Configurable delay between company processing (default: 2 seconds)
- Respects API quotas and prevents overuse

## Error Handling

- **API Failures**: Graceful handling of API timeouts and errors
- **Missing Data**: Companies without revenue data are marked appropriately
- **Invalid CSV**: Validation of required columns and format
- **Network Issues**: Retry logic and timeout handling

## Testing

Test with the provided sample file:

```bash
uv run python company_revenue_analyzer.py sample_companies.csv --validate-only
```

## Troubleshooting

### Common Issues

1. **API Key Errors**

   - Ensure `.env` file is properly configured
   - Verify API keys are valid and have sufficient credits

2. **CSV Format Errors**

   - Check that required columns are present
   - Ensure CSV is properly formatted (no special characters)

3. **Rate Limiting**

   - Increase `--delay` parameter if hitting rate limits
   - Check API quotas in your dashboard

4. **No Revenue Found**
   - Some companies may not have publicly available revenue data
   - Try different company names or check domain accuracy

### Debug Mode

For detailed logging, you can modify the script to include debug output or run individual components separately.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review API documentation for Brave Search and OpenRouter
3. Open an issue in the repository
