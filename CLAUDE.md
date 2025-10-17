# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An AI-powered conversational assistant for the Egyptian automotive market using **LangChain/LangGraph agentic architecture**. The system combines web scraping, AI-enhanced data processing, and a GPT-4.1 powered agent that uses SQL tools to search 900+ cars in the Egyptian market.

**Key Tech Stack**: LangChain + LangGraph | GPT-4.1 | Gradio | SQLite | Python

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (required)
echo "OPENAI_API_KEY=your-key-here" > .env
echo "LANGSMITH_API_KEY=your-key-here" >> .env

# Run web interface (recommended)
python app.py  # Opens at http://localhost:7860

# Run CLI interface
python run_chatbot.py

# Run evaluation tests
python evaluation/run_evaluation.py

# Hyperparameter tuning
python evaluation/hyperparameter_tuning.py
```

## Data Pipeline (One-time Setup)

```bash
# 1. Process raw scraped data with AI enhancement
python postprocessing/scrapped_data_postprocessing.py

# 2. Create SQLite database from processed CSV
python database/database_creator.py

# 3. Validate database (optional)
python database/database_tester.py
```

## Architecture: LangGraph Agentic Flow

### Core Pattern (Multi-Turn Agent with Tools)

```
User Input → CarChatbot.process_message()
    ↓
    ├── ConversationManager (provides conversation context)
    └── LangGraph ReAct Agent (_unified_llm_handler)
        │
        ├── SystemMessage: unified_prompt + schema + synonyms (from chatbot_config.yaml)
        ├── HumanMessage: user query + conversation context
        │
        ├─→ [Agent Decision] Use SQL tool or provide knowledge?
        │
        ├─→ [ITERATION 1] Tool Call: execute_sql_query_bound(sql)
        │   └── chatbot/tools.py → DatabaseHandler → Returns results
        │
        ├─→ [ITERATION 2-3] (Optional) Refine SQL based on results
        │   └── Agent adjusts query if 0 results or too many results
        │
        └─→ [Final Response] Agent crafts natural response using all gathered data
    ↓
Conversational Response → User
```

### Key Design Principle: Tool-Based Interaction

The agent **does NOT generate responses directly from SQL**. Instead:

1. **Agent calls `execute_sql_query_bound` tool** (defined in `chatbot/tools.py`)
2. **Tool returns raw database results** to agent
3. **Agent sees results and crafts natural, context-specific responses**
4. **Agent can iterate** up to 3 times (adjusting SQL based on results)

This allows the agent to:
- Handle hybrid queries (database + automotive knowledge)
- Refine searches when results are empty or too broad
- Adapt response formatting based on query context

## Critical Architecture Files

### 1. `chatbot/car_chatbot.py` - Main Orchestrator
- **`_create_agent()`**: Creates LangGraph ReAct agent with SQL tool
- **`_unified_llm_handler()`**: **CORE METHOD** - Invokes agent with system prompt
- **`process_message()`**: Entry point for all user queries

### 2. `chatbot/tools.py` - LangChain Tool Definition
- **`create_sql_tool_with_db(db_handler)`**: Creates tool bound to DatabaseHandler
- **`execute_sql_query_bound()`**: LangChain `@tool` that wraps SQL execution
- Returns: `{"success": bool, "results_count": int, "results": List[Dict]}`

### 3. `chatbot/chatbot_config.yaml` - Single Source of Truth
- **`prompts.unified_prompt`**: **ALL agent behavior controlled here**
  - Defines when to use SQL tool vs provide knowledge
  - SQL generation rules and iterative refinement instructions
  - Response formatting guidelines and examples
  - Schema and synonyms injected dynamically via `.format()`
- **`openai`**: Model selection (gpt-4.1), temperature, max_tokens
- **`conversation.greeting`**: Used by both CLI and Gradio interfaces

### 4. `chatbot/query_processor.py` - Configuration Holder
- Loads schema from `database/schema.yaml`
- Loads synonyms from `database/synonyms.yaml`
- Provides LangChain ChatOpenAI model instance
- **No SQL generation logic** (agent handles this via tool calling)

### 5. `database/database_handler.py` - SQL Execution
- Executes validated SQL queries
- Returns raw results (no formatting, agent handles this)
- Query validation (only SELECT from cars table)

### 6. `chatbot/conversation_manager.py` - Memory
- Tracks conversation history with timestamps
- Provides context for agent (last N turns)
- Session analytics (success rate, query patterns)

## Configuration System

### All Behavior Controlled via `chatbot_config.yaml`

**Critical**: The `unified_prompt` in `chatbot_config.yaml` is the **single source of truth** for all agent behavior. It defines:

1. **When to use SQL tool**: "User asks for cars with specific criteria..."
2. **SQL generation rules**: "Use exact column names from schema..."
3. **Iterative refinement**: "First query returns 0 results → Try relaxing budget..."
4. **Response formatting**: "Craft natural, conversational responses..."
5. **Egyptian market context**: "Consider local roads, climate, service networks..."

**Schema and synonyms are injected dynamically**:
```python
unified_prompt.format(
    schema=yaml.dump(self.query_processor.schema),
    synonyms=yaml.dump(self.query_processor.synonyms)
)
```

### Why This Matters

When modifying agent behavior:
- ✅ **DO**: Edit `chatbot_config.yaml` → `prompts.unified_prompt`
- ❌ **DON'T**: Hardcode logic in Python files

## Important Conventions

### 1. Greeting Management
Both `app.py` (Gradio) and `run_chatbot.py` (CLI) load greeting from `chatbot_config.yaml`:
```python
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    greeting = config.get('conversation', {}).get('greeting', 'Welcome!')
```
**Never duplicate the greeting text** in multiple files.

### 2. Path Resolution
All modules use absolute paths relative to project root:
```python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, "database", "cars.db")
```

### 3. Agent Recursion Limit
Set to 10 steps in `_unified_llm_handler()` (allows ~3 tool iterations):
```python
result = self.agent.invoke(
    {"messages": [SystemMessage(...), HumanMessage(...)]},
    config={"recursion_limit": 10}
)
```

### 4. Gradio Interface Responsiveness
`app.py` uses viewport-based heights for responsive design:
```python
chatbot=gr.Chatbot(height="65vh")  # Dynamic sizing
```
CSS ensures input box is always visible via `min-height` and responsive breakpoints.

## Database Schema Quick Reference

### Key Tables & Columns
- **Table**: `cars` (937 vehicles after deduplication)
- **Price**: `Price_EGP` (Egyptian Pounds)
- **Body Types**: sedan, hatchback, crossover/suv, coupe, convertible, van
- **Transmission**: automatic_traditional, automatic_cvt, automatic_dsg, manual
- **Powertrain**: Internal_Combustion_Engine, Electric, Hybrid, Plug_in_Hybrid_PHEV, etc.
- **Features**: Boolean columns (ABS, ESP, Sunroof, etc.)

### Indexed Columns (for performance)
car_brand, car_model, car_trim, body_type, Price_EGP, Transmission_Type, Origin_Country, Engine_Turbo

## Testing & Evaluation

### Evaluation System (`evaluation/run_evaluation.py`)
- Uses GPT-4.1 as correctness evaluator (0.0-1.0 score)
- Tests: cheapest car, brand knowledge, clarification handling, complex filters
- LangSmith integration for experiment tracking
- 10-second delay between evaluations to avoid rate limits
- **Requires both OPENAI_API_KEY and LANGSMITH_API_KEY in .env file**
- Uses `python-dotenv` to load environment variables (validates keys on startup)

### Hyperparameter Tuning (`evaluation/hyperparameter_tuning.py`)
- Grid search over temperature and max_tokens
- Modifies `chatbot_config.yaml` temporarily
- Auto backup/restore in finally block
- Default grid: temperature [0.0, 0.1, 0.3, 0.5], max_tokens [800, 1200, 1500, 2000]
- Customize by editing `TEMPERATURE_VALUES` and `MAX_TOKENS_VALUES` at lines 33-34

## Data Processing Pipeline

### AI-Enhanced Data Processing (`postprocessing/scrapped_data_postprocessing.py`)

GPT-4 is used for **one-time data enhancement**:
1. **Body type classification**: Batch 50 brand-model combinations → 6 categories
2. **Origin country completion**: AI fills missing brand origins
3. **Powertrain loading**: Loads from `postprocessing/power_train.csv` with manual adjustments
4. **Brand normalization**: moris-garage → MG, CitroÃ«n → Citroen
5. **Transmission standardization**: automatic → automatic_traditional, etc.
6. **Duplicate removal**: Based on car_trim column

**Output**: `processed_data.csv` (used by `database/database_creator.py`)

## Troubleshooting

### Database Issues
```bash
# Check if database exists and has data
python -c "import sqlite3; conn = sqlite3.connect('database/cars.db'); print(conn.execute('SELECT COUNT(*) FROM cars').fetchone())"
```

### OpenAI API Issues
- Ensure `OPENAI_API_KEY` is set in `.env` file
- Check logs in `chatbot.log` for rate limit errors
- Agent has built-in error handling with graceful degradation

### Gradio Not Opening
- Check port 7860 is available
- Try: `python app.py` with `share=True` for public link
- Verify Gradio version: `pip show gradio` (should be >=4.0.0)

## Web Scraper (`web_scrapper/car_scraper.py`)

Scrapes 62+ automotive brands from Egyptian market websites:
```bash
# Test scraper on specific brand
python web_scrapper/car_scraper.py --test-brands hyundai
```

## Important Notes

1. **Never modify SQL in Python code** - Agent generates SQL dynamically via tool calling
2. **All agent behavior controlled via YAML** - Edit `chatbot_config.yaml` for changes
3. **Greeting is centralized** - Always load from config, never duplicate
4. **Agent can iterate** - Up to 3 SQL tool calls per query for refinement
5. **Database is read-only** - Only SELECT queries allowed for safety
6. **Egyptian market focus** - Prices in EGP, local climate/road considerations
