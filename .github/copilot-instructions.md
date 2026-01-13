# Copilot Instructions for OData LLM Chatbot

This is a **Logistics Chatbot System** that converts natural language questions into OData API queries and performs calculations on transport order data. The project is built as a university assignment (THWS Business Analytics 2 course).

## Architecture Overview

The system follows a **4-stage pipeline** architecture with clear separation of concerns:

```
User Input (Natural Language)
    ↓
LLM Parser (GPT-4) → Converts to structured JSON with OData params + calculations
    ↓
OAuth Handler → Token management for API authentication
    ↓
OData Client → Executes API requests, returns raw data
    ↓
Calculation Engine → Applies aggregations/groupings via Registry pattern
    ↓
Response Generator → Converts results back to natural language
    ↓
Output (Formatted German response)
```

### Key Components

1. **[src/llm_parser.py](src/llm_parser.py)** - Accepts user input, uses GPT-4 to parse into:
   - `odata_params`: Filter, select, top, count parameters
   - `calculation`: Type (count, sum, aggregation) + configuration
   - Returns conversation history tracking for multi-turn support

2. **[src/odata_client.py](src/odata_client.py)** - Executes queries:
   - Manages OAuth token lifecycle via `OAuthTokenHandler`
   - Builds URLs with OData parameters ($filter, $select, $top, $count)
   - Returns `{value: [], count: N, query_metadata: {...}}`

3. **[src/calculation_engine.py](src/calculation_engine.py)** - Orchestrates calculations:
   - Takes raw OData response + calculation config
   - Delegates to appropriate calculator via Registry
   - Returns enhanced results with computation metadata

4. **[calculations/](calculations/)** - Plugin-based calculation system:
   - [base.py](calculations/base.py): `BaseCalculation` abstract class (all calculations inherit)
   - [registry.py](calculations/registry.py): `CalculationRegistry` manages available calculations
   - [count.py](calculations/count.py), [sum.py](calculations/sum.py): Built-in implementations
   - **Adding new calculation**: Create class inheriting `BaseCalculation`, implement `calculate()` + `validate_config()`, register in `_register_default_calculations()`

5. **[src/response_generator.py](src/response_generator.py)** - Natural language output in German

6. **[config/settings.py](config/settings.py)** - Centralized environment-based config with validation

## Critical Data Structures

### Parser Output Format (LLM → OData Client)
```python
{
    "odata_params": {
        "$filter": "createdAt ge 2025-12-17T00:00:00Z",
        "$select": "ID,group,amount",
        "$top": 100,
        "$count": "true"  # optional
    },
    "calculation": {  # optional
        "type": "count",  # "count", "sum", "aggregation"
        "grouping_field": "group",
        "time_field": "createdAt"
    }
}
```

### OData Client Response → Calculation Engine Input
```python
{
    "value": [{"ID": 1, "group": "A", "amount": 100}, ...],
    "count": 42,
    "total_count": 1000,  # if $count=true
    "query_metadata": {
        "timestamp": "ISO8601",
        "odata_params": {...},
        "request_count": N
    }
}
```

## Development Patterns

### Pattern 1: Adding New Calculations
The Registry pattern enables plugin-style extensibility without modifying engine:
1. Create `calculations/my_calc.py` with class inheriting `BaseCalculation`
2. Implement abstract methods: `calculate(data, config)` + `validate_config(config)`
3. Use helper `_group_data(data, field)` from base class for grouping
4. Register in `CalculationRegistry._register_default_calculations()`

**Example**: See [calculations/sum.py](calculations/sum.py) for sum/aggregation pattern.

### Pattern 2: Environment Configuration
- All configs centralized in [config/settings.py](config/settings.py)
- Loaded from `.env` file via `python-dotenv`
- Call `Config.validate()` on startup to check required vars
- Required: OPENAI_API_KEY, OAUTH_TOKEN_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, ODATA_BASE_URL

### Pattern 3: Conversation History
- `LLMQueryParser.conversation_history` maintains last 3 exchanges
- Passes context to subsequent queries for multi-turn support
- Structure: `[{"user_input": str, "parsed_output": dict, "timestamp": str}, ...]`

### Pattern 4: Error Handling
- Components catch exceptions and return fallback responses (don't crash pipeline)
- `ODataClient._execute_request()` handles OAuth token refresh automatically
- `LLMQueryParser._get_fallback_response()` returns safe defaults if GPT fails

## Testing & Demo Scripts

- **[demo_chatbot.py](demo_chatbot.py)** - Complete pipeline example, run with: `python demo_chatbot.py`
- **[demo_parser.py](demo_parser.py)** - LLM parser alone
- **[demo_odata.py](demo_odata.py)** - OData client alone
- **[demo_pipeline.py](demo_pipeline.py)** - Full pipeline (without response generator)
- **[demo_app.py](demo_app.py)** - Flask web interface (WIP)

## Setup & Validation

1. **Install dependencies**: `pip install -r requirements.txt` (Python 3.10+)
2. **Configure environment**: Copy `env.template` to `.env`, fill OAuth/API keys
3. **Validate setup**: `python3 -c "from config.settings import Config; Config.validate()"`
4. **Run demo**: `python demo_chatbot.py`

## Language & Localization

- Project language is **German** (comments, messages, response generation)
- Response generator outputs German by default (set `ResponseGenerator(language="de")`)
- OData API field names are in English (ID, createdAt, group, amount)

## Important Technical Constraints

- **LLM Parser**: Uses GPT-4 with `response_format={"type": "json_object"}` to force structured output, temperature=0.1 for consistency
- **OData Parameters**: Supports $filter, $select, $top (limited to MAX_TOP_LIMIT=1000), $count
- **Calculations**: All calculations group data in memory with `_group_data()` helper - not database-level grouping
- **OAuth**: Token caching with automatic refresh - no need to manually manage tokens in client code

## Code Style

- Type hints required for function signatures (use `Optional`, `Dict`, `List` from typing)
- Docstrings in German with "Args", "Returns" sections
- Classes use snake_case for methods
- Comments explain "why", not "what" (code is readable)
