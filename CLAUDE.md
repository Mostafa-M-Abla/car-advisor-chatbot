# Egyptian Car Market AI Chatbot - Claude Documentation

## Project Overview
An advanced AI-powered conversational assistant for the Egyptian automotive market. The system combines web scraping, intelligent data processing, and a sophisticated multi-component chatbot architecture to help users find the perfect vehicle based on their preferences. Features include natural language processing, conversation memory, external automotive knowledge integration, and intelligent query routing.

## Project Structure

```
car-selection-chatbot/
├── web_scrapper/                    # Web scraping module
│   ├── car_scraper.py              # Universal web scraper (62+ brands)
│   ├── features_mapping.csv        # Field mapping configuration
│   └── scrapped_data.csv           # Raw scraped car data
│
├── chatbot/                        # Core chatbot system components
│   ├── car_chatbot.py              # Main orchestrator with unified LLM handler
│   ├── query_processor.py          # Configuration holder (schema, synonyms)
│   ├── response_generator.py       # Database result formatting (pure functions)
│   ├── conversation_manager.py     # Conversation history and context tracking
│   └── chatbot_config.yaml         # Comprehensive chatbot configuration
│
├── database/                       # Database system
│   ├── database_creator.py         # SQLite database creation with indexing
│   ├── database_handler.py         # Database operations and result formatting
│   ├── database_tester.py          # Database validation and testing
│   ├── cars.db                     # SQLite database (937 cars with full specs)
│   ├── schema.yaml                 # Database schema definition
│   └── synonyms.yaml               # Natural language synonym mappings
│
├── evaluation/                     # Evaluation and testing module
│   └── run_evaluation.py           # Chatbot performance evaluation script (auto-updates dataset)
│
├── scrapped_data_postprocessing.py # AI-enhanced data processing pipeline
├── power_train.csv                 # Powertrain type classifications
├── processed_data.csv              # Clean, AI-enhanced car data
├── run_chatbot.py                  # Entry point and launcher script
├── .env                           # Environment variables (API keys)
├── requirements.txt               # Python dependencies
├── postprocessing_output.log      # Data processing logs
├── chatbot.log                    # Runtime logs and debugging
└── CLAUDE.md                      # This comprehensive documentation
```

## System Architecture

### Overview
The chatbot system uses **LangChain and LangGraph** for agentic architecture with function calling, enabling iterative query refinement and natural response generation. GPT-4.1 acts as an intelligent agent with access to database tools, allowing it to search, refine, and craft contextual responses.

### Core Architecture Flow (LANGCHAIN + LANGGRAPH)
```
User Input → CarChatbot (Orchestrator)
    ↓
    ├── ConversationManager (Memory & Context)
    └── LangGraph ReAct Agent (MULTI-TURN WITH TOOLS)
        ├── Input: SystemMessage(unified_prompt + schema + synonyms) + HumanMessage(user_input + context)
        ├── LangChain ChatOpenAI (GPT-4.1) decides: Use tool or provide knowledge?
        │
        ├─→ [ITERATION 1] Tool Call: execute_sql_query_bound(sql)
        │   └── LangChain Tool (@tool decorator) → DatabaseHandler → Returns results to agent
        │
        ├─→ [ITERATION 2] (Optional) Refine: execute_sql_query_bound(adjusted_sql)
        │   └── LangChain Tool → DatabaseHandler → Returns results to agent
        │
        ├─→ [ITERATION 3] (Optional) Final attempt: execute_sql_query_bound(final_sql)
        │   └── LangChain Tool → DatabaseHandler → Returns results to agent
        │
        └─→ Agent sees all results → Crafts natural, contextual response
    ↓
Conversational Response → User
```

### Component Interaction Model (LANGCHAIN + LANGGRAPH)
1. **CarChatbot** receives user input and orchestrates the LangGraph agent flow
2. **ConversationManager** provides conversation context from history
3. **LangGraph Agent** (`create_react_agent`) runs multi-turn agent loop:
   - **Tool Definition**: LangChain `@tool` decorator defines `execute_sql_query_bound`
   - **Agent Creation**: `create_react_agent(model, tools)` creates ReAct-style agent
   - **Decision Making**: Agent decides when to query database vs provide knowledge
   - **SQL Execution**: Agent calls tool with generated SQL → sees actual results
   - **Iterative Refinement**: Agent can adjust query if needed (up to recursion_limit=10)
   - **Natural Responses**: Agent crafts context-specific responses using database results
   - **Handles hybrid queries seamlessly** (e.g., "reliable SUVs under 2M" → queries database + adds reliability insights)
4. **SQL Tool** (`chatbot/tools.py`) wraps DatabaseHandler for LangChain integration
5. **DatabaseHandler** executes validated SQL queries and returns raw results
6. **QueryProcessor** provides LangChain ChatOpenAI model and configuration
7. **Configuration system** provides centralized `unified_prompt` in chatbot_config.yaml

### Design Principles (LANGCHAIN + LANGGRAPH ARCHITECTURE)
- **LangChain Framework**: Industry-standard agent framework for reliability and maintainability
- **LangGraph ReAct Agent**: Reasoning + Acting pattern for intelligent tool usage
- **Tool-Based Interaction**: LangChain `@tool` decorator for clean SQL tool definition
- **Iterative Refinement**: Agent can make multiple tool calls (recursion_limit=10)
- **Natural Response Generation**: Agent sees actual database results and crafts tailored responses
- **Context-Aware Formatting**: Responses adapt to query type (not rigid templates)
- **Hybrid Query Support**: Database searches seamlessly include automotive knowledge
- **Centralized Configuration**: All LLM behavior controlled via `unified_prompt` in YAML
- **Conversation Memory**: Tracks conversation history for context continuity
- **Egyptian Market Focus**: Specialized for local automotive market needs
- **Observability**: LangSmith tracing for debugging and monitoring
- **Simplified Components**: Removed rigid formatting (~150 lines), agent does everything

### Major Architectural Changes (2025)

#### Phase 1: Unified Architecture (January 2025)
**Problem Identified:**
- Old architecture had 3 separate LLM prompts that didn't work together
- Binary routing failed on hybrid queries ("reliable SUVs under 2M" only routed to knowledge, never queried database)
- Config prompts were ignored (hardcoded prompts in query_processor and knowledge_handler)

**Solution Implemented:**
- **Unified single-prompt architecture**: One call handles everything
- **Removed knowledge_handler.py entirely** (~200 lines)
- **Simplified query_processor.py**: No SQL generation, just config holder (~140 lines removed)
- **Simplified response_generator.py**: No LLM calls, just formatting (~50 lines removed)
- **All prompts in config**: True centralized configuration
- **Hybrid queries now work correctly**: Database + knowledge in single response

#### Phase 2: Agentic Architecture with Function Calling (October 2025)
**Problem Identified:**
- LLM couldn't see database results (formatted with rigid templates before LLM saw them)
- No iterative refinement (single-shot SQL generation)
- Hybrid queries just concatenated LLM text + formatted results (not user-friendly)
- Rigid formatting didn't adapt to query context

**Solution Implemented:**
- **Function calling architecture**: LLM uses `execute_sql_query` tool to access database
- **Iterative refinement**: Up to 3 tool calls for query adjustment
- **LLM sees raw results**: Crafts natural, context-specific responses
- **Removed rigid templates**: response_generator.py reduced to utility function (~130 lines removed)
- **Better hybrid queries**: LLM naturally integrates database results with knowledge
- **Context-aware responses**: Different queries get different response styles

#### Phase 3: LangChain & LangGraph Integration (October 2025)
**Why LangChain?**
- **Industry standard**: Well-tested agent framework used by thousands of projects
- **Better observability**: Built-in LangSmith tracing for debugging
- **Consistency**: Same framework for chatbot and evaluation
- **Future-proof**: Easier to add streaming, memory, more tools
- **Cleaner code**: High-level abstractions vs manual loops

**Changes Made:**
- **Migrated to LangChain ChatOpenAI**: Replaced direct OpenAI API calls
- **LangGraph create_react_agent**: Replaced manual agent loop (~90 lines simplified)
- **LangChain @tool decorator**: Clean tool definition in `chatbot/tools.py`
- **Added dependencies**: `langgraph>=0.0.20`, `langchain-core>=0.1.0`
- **Same behavior**: All tests pass with identical functionality

## Key Features

### System Monitoring & Logging
**Comprehensive visibility into system behavior:**
- **AI Usage Tracking**: Logs when AI-generated SQL is successfully used
- **Fallback Monitoring**: Warning-level logs when non-AI fallback is triggered
  - Logs reason: No SQL generated vs. SQL failed validation
  - Includes user query and criteria used for fallback
  - Helps identify AI performance issues
- **Query Validation**: Tracks when generated SQL fails safety checks
- **Performance Insights**: Monitor which queries require fallback vs. AI handling
- **Debugging Support**: Detailed context for troubleshooting query processing issues

### 1. Advanced Conversational AI System
- **LLM-Integrated Clarification**: Intelligent decision-making for when clarification is needed
- **Context-Aware Responses**: Maintains conversation history for context continuity
- **Natural Language Processing**: Converts complex user queries to precise database searches
- **External Knowledge Integration**: Leverages GPT-4.1 for automotive knowledge beyond database

## Core Components

### 1. CarChatbot (`chatbot/car_chatbot.py`)
**Main orchestrator with agentic LLM handler**
- **Initialization**: Loads configuration, validates database, initializes all components
- **Agentic Processing**: Multi-turn agent loop with function calling (max 3 iterations)
- **Conversation Flow**: Manages interactive CLI interface with commands
- **Error Handling**: Comprehensive exception handling and graceful degradation
- **Session Management**: Tracks conversation statistics and interaction patterns

**Key Methods:**
- `process_message()`: Main entry point, calls agentic LLM handler
- `_unified_llm_handler()`: **CORE METHOD** - Runs multi-turn agent loop:
  - Loads `unified_prompt` from config with tool usage guidelines
  - Injects schema, synonyms, user input, and context
  - Provides `execute_sql_query` tool via function calling
  - LLM decides: Call tool or provide knowledge?
  - Runs up to 3 iterations for query refinement
  - LLM sees raw database results and crafts natural responses
  - Returns final conversational response
- `_get_sql_tool_definition()`: Defines SQL execution tool for function calling
- `_execute_sql_tool()`: Executes SQL and returns results to LLM
- `start_conversation()`: Interactive CLI interface with help, stats, clear commands

**Removed Methods (simplified in agentic architecture):**
- ~~`_handle_database_query()`~~ → Replaced by tool calling
- ~~`_handle_external_knowledge_query()`~~ → LLM decides autonomously
- ~~`_extract_car_context_from_query()`~~ → No longer needed
- ~~`_format_results()`~~ → LLM formats responses naturally

### 2. QueryProcessor (`chatbot/query_processor.py`)
**Configuration holder for schema and synonyms (SIMPLIFIED)**

**Unified Architecture Role:**
- Serves as centralized source for database schema
- Provides synonym mappings for natural language
- Maintains OpenAI client instance
- **No longer generates SQL** (moved to unified prompt)

**Key Attributes:**
- `schema`: Database schema loaded from schema.yaml
- `synonyms`: Natural language mappings loaded from synonyms.yaml
- `openai_client`: Shared OpenAI client instance
- `config`: Chatbot configuration

**Removed Methods (moved to unified prompt):**
- ~~`generate_sql_with_gpt4()`~~ → SQL generation now in unified prompt
- ~~`parse_query()`~~ → Query parsing now in unified prompt

**Simplification Benefits:**
- Removed ~140 lines of SQL generation code
- Single responsibility: Configuration holder only
- More maintainable and focused
- Schema/synonyms accessible to unified handler

### 3. DatabaseHandler (`database/database_handler.py`)
**Simplified database operations and result management**

**Single Execution Path:**
- **AI-Generated SQL Only**: Executes GPT-4.1 generated queries
  - Validated for safety before execution
  - Parameterized queries prevent SQL injection
  - Logged for monitoring and debugging

**Key Features:**
- Egyptian Pound formatting with commas
- Feature categorization (safety, comfort, technology)
- Car comparison utilities
- Database validation and health checks
- Comprehensive query logging

**Simplification:**
- Removed `search_cars()` fallback method (~60 lines)
- Single responsibility: Execute validated SQL queries
- Clearer error handling when SQL generation fails

### 4. ResponseGenerator (`chatbot/response_generator.py`)
**Utility functions (FULLY SIMPLIFIED)**

**Agentic Architecture Role:**
- **Optional utility functions** - LLM can reference if needed
- **No rigid templates** - LLM crafts all responses naturally
- **Minimal code** - Just helper functions

**Available Utility:**
- `format_price()`: Egyptian Pound formatting with commas (e.g., "1,500,000 EGP")

**Removed in Agentic Architecture (~130 lines):**
- ~~`format_car_result()`~~ → LLM crafts car descriptions naturally
- ~~`format_results_summary()`~~ → LLM formats results based on context
- ~~`generate_response()`~~ → LLM generates all responses
- ~~ResponseGenerator class~~ → Now just standalone functions

**Benefits:**
- LLM crafts context-specific responses (not rigid templates)
- Different queries get different formatting styles
- More natural, conversational responses
- Simpler codebase (~130 lines removed)

### 5. ConversationManager (`chatbot/conversation_manager.py`)
**Conversation history and context management (SIMPLIFIED)**
- **Conversation History**: Maintains structured conversation turns with timestamps
- **Context Generation**: Provides recent conversation context for LLM interactions
- **Session Analytics**: Tracks success rates, query patterns, and interaction statistics
- **Export Functionality**: Can export conversation history to JSON for analysis

**Simplification Note:**
- Removed ~150 lines of dead preference tracking code
- User preference learning was never actually functional (criteria always None/empty)
- Focus on conversation context rather than structured preference extraction
- Cleaner, more maintainable design that leverages LLM's natural context understanding

### 6. ~~KnowledgeHandler~~ (DELETED - UNIFIED)
**This component has been removed entirely in the unified architecture.**

**Previous Functionality:**
- Query classification (database vs. knowledge)
- External automotive knowledge retrieval
- Separate LLM calls for knowledge queries

**Problem:**
- Used hardcoded prompts that ignored config
- Binary routing failed on hybrid queries
- Created artificial separation between database and knowledge

**Solution:**
- **Deleted knowledge_handler.py (~200 lines removed)**
- Functionality moved to unified prompt
- Hybrid queries now work seamlessly
- All prompts centralized in config

**Unified Approach:**
- Replaced 5 specialized methods with one `get_knowledge_response()` method
- Handles all query types: reliability, reviews, comparisons, market insights, safety, history
- Leverages GPT-4.1's intelligence to provide appropriate response format
- Simpler, more maintainable, and more flexible for diverse user questions
- Automatically integrates database context when specific cars are mentioned

### 7. Data Processing Pipeline (`scrapped_data_postprocessing.py`)
- **Data Cleaning**: Removes invalid entries, normalizes columns
- **AI Enhancement**: Uses OpenAI GPT-4 for:
  - Body type classification (sedan, hatchback, crossover/suv, coupe, convertible, van)
  - Origin country completion for missing brands
- **Powertrain Classification**: Loads powertrain types from `power_train.csv` file
  - Categories: Internal_Combustion_Engine, Electric, Hybrid, Plug_in_Hybrid_PHEV, Mild_Hybrid_MHEV, Range_Extended_Electric_Vehicle_REEV_EREV
  - Manual adjustments applied for specific models (santa-fe, MG-4, x-Trail)
- **Warranty Parsing**: Splits warranty strings into km and years columns
- **Price Filtering**: Removes entries with invalid pricing
- **Year Filtering**: Keeps only recent model years based on current date
- **Column Standardization**: Renames and reorganizes columns
- **Transmission Type Normalization**: Standardizes transmission types (automatic → automatic_traditional, cvt → automatic_cvt, dsg → automatic_dsg)
- **Brand Name Normalization**: Fixes brand names (moris-garage → MG, CitroÃ«n → Citroen)
- **Duplicate Removal**: Eliminates duplicate entries based on car_trim

### 8. Evaluation Module (`evaluation/run_evaluation.py`)
**Chatbot performance evaluation and testing**
- **Automated Testing**: Runs predefined test cases to evaluate chatbot responses
- **Dataset**: 4 core test cases (expandable to 16 when uncommenting additional examples)
  - Cheapest car query
  - Brand origin knowledge (BMW)
  - Clarification handling ("I want to buy a good car")
  - Complex multi-filter query (non-Chinese, automatic, ESP)
- **Performance Metrics**: Correctness score (0.0-1.0) using GPT-4.1 as evaluator
- **Regression Testing**: Ensures updates don't break existing functionality
- **Query Validation**: Tests various query types (price ranges, features, complex filters, knowledge)
- **Output Analysis**: Per-example breakdown with ✅/❌ status and aggregate statistics
- **Dataset Management**: Automatically updates existing dataset, alphabetically sorted by question
- **LangSmith Integration**: Full experiment tracking with metadata
- **10-second delay**: Between evaluations to avoid rate limits

### 9. Hyperparameter Tuning (`evaluation/hyperparameter_tuning.py`)
**Automated grid search for optimal chatbot parameters**
- **Architecture**: Imports `rag_bot`, `correctness`, and `client` from run_evaluation.py (no code duplication)
- **Parameters Tuned**:
  - Temperature: Controls LLM randomness (default grid: [0.0, 0.1, 0.3, 0.5])
  - Max Tokens: Controls response length (default grid: [800, 1200, 1500, 2000])
- **Grid Search**: Configurable test matrix (default: 16 configurations)
- **Evaluation Metric**: Same correctness evaluator as run_evaluation.py
- **Results Tracking**:
  - Saves detailed JSON with all configurations tested
  - Identifies best configuration automatically
  - Provides aggregate analysis by parameter (temperature avg, max_tokens avg)
  - Shows top 5 performing configurations
- **Safe Operations**: Automatic config backup/restore, always runs in finally block
- **Usage**: `python evaluation/hyperparameter_tuning.py`
- **Customization**: Modify `TEMPERATURE_VALUES` and `MAX_TOKENS_VALUES` at lines 33-34
- **Output**: Saves to `evaluation/tuning_results_TIMESTAMP.json`

## Configuration System

### Centralized Configuration (`chatbot/chatbot_config.yaml`)
The entire chatbot behavior is controlled through a comprehensive YAML configuration file with the **unified_prompt** as the single source of truth for all LLM behavior.

#### OpenAI Configuration
```yaml
openai:
  model: "gpt-4.1"          # Centralized model selection
  temperature: 0.1          # Response randomness control
  max_tokens: 1500          # Increased for agentic responses
```

#### Conversation Settings
```yaml
conversation:
  max_history: 20           # Conversation memory depth
  greeting: |               # Custom welcome message
    Hi! I'm your AI car advisor for the Egyptian market...
```

#### Agentic Prompt (CORE CONFIGURATION)
```yaml
prompts:
  unified_prompt: |
    You are an expert car advisor for the Egyptian automotive market with access to a comprehensive database and automotive knowledge.

    **DATABASE SCHEMA**:
    {schema}

    **SYNONYMS** (user terms → database values):
    {synonyms}

    ---

    ## YOUR CAPABILITIES

    1. **DATABASE ACCESS**: You have the `execute_sql_query` tool to search 900+ car trims
    2. **AUTOMOTIVE KNOWLEDGE**: You can provide reliability insights, reviews, comparisons
    3. **ITERATIVE REFINEMENT**: You can call `execute_sql_query` up to 3 times to refine searches

    ## TOOL USAGE GUIDELINES

    **When to use `execute_sql_query`**:
    - User asks for cars with specific criteria (price, body type, features, origin)
    - Hybrid queries: "reliable SUVs under 2M" (search database + add knowledge)

    **SQL Generation Rules**: [detailed SQL rules]

    **Iterative Refinement Examples**:
    - First query returns 0 results → Try relaxing budget by 10-20%
    - First query returns 100+ results → Add more filters to narrow down

    ## RESPONSE FORMATTING

    **After receiving database results**:
    - Craft natural, conversational responses tailored to the query
    - Format prices with commas: "1,500,000 EGP"
    - Highlight key features relevant to user's question
    - Use emojis sparingly for readability

    **Response Examples**: [context-specific examples]
```

**Key Features of Agentic Prompt:**
- **Tool-based interaction**: Guides LLM on when to use `execute_sql_query`
- **Iterative refinement**: Instructions for adjusting queries based on results
- **Natural response generation**: LLM crafts responses after seeing database results
- **Context-aware formatting**: Different queries get different response styles
- **Hybrid query support**: Seamlessly combines database + knowledge
- **Egyptian market focus**: Context-specific recommendations
- **Schema/synonym injection**: Dynamic integration of database structure

**Evolution from Previous Architecture:**
- ~~JSON output format~~ → Function calling replaces structured JSON
- ~~Rigid templates~~ → LLM crafts natural responses
- ~~Single-shot queries~~ → Iterative refinement (max 3 calls)

### Database System
#### Database Creator (`database/database_creator.py`)
- Creates SQLite database with comprehensive schema
- Imports processed CSV data with 886 vehicles
- Creates performance indexes on key columns:
  - car_brand, car_model, car_trim, body_type
  - Price_EGP, Transmission_Type, Origin_Country, Engine_Turbo

#### Database Tester (`database/database_tester.py`)
- Comprehensive test suite for database validation
- Sample queries for data exploration
- Performance testing for indexed columns

## Advanced Chatbot Capabilities

### Intelligent Query Processing
- **Natural Language Understanding**: Processes complex queries like "crossovers under 2M EGP, non-Chinese, automatic with ESP"
- **Flexible Input Handling**: Understands variations like "under 2 million", "below 2M", "max 2,000,000 EGP"
- **Feature Recognition**: Maps user terms to database columns (e.g., "auto" → "automatic", "ESP" → safety feature)
- **Smart Defaults**: Handles broad requests like "random car under 800k" without excessive clarification

### LLM-Integrated Clarification System
**Previous Problem**: Rule-based system was too rigid, asking unnecessary clarification for clear requests
**Solution**: GPT-4.1 now intelligently decides when clarification is genuinely needed

**Examples of Smart Handling:**
- ✅ "Pick a random car under 800k" → Proceeds with diverse selection
- ✅ "Any good SUV" → Shows variety of SUVs with explanations
- ✅ "Surprise me with a budget car" → Selects diverse affordable options
- ❓ "I need a car" (no criteria) → Asks for budget and type
- ❓ "Good car" (extremely vague) → Requests specific requirements

### External Knowledge Integration
**Simplified, Unified Approach:**
The system now uses a single, flexible method that automatically handles all types of automotive knowledge queries without rigid categorization. GPT-4.1 naturally adapts its response to match the question type.

**Example Queries Handled:**
- **Reliability**: "Is the Toyota Camry reliable?" → Natural reliability analysis
- **Comparisons**: "Honda Civic vs Toyota Corolla" → Adaptive side-by-side comparison
- **Market Insights**: "What cars are popular in Egypt?" → Market trends and analysis
- **Historical Data**: "When was the BMW X5 first introduced?" → Brand and model history
- **Maintenance**: "Cost to maintain a BMW?" → Ownership cost analysis
- **Reviews**: "What do people think of the Hyundai Elantra?" → Balanced review summary
- **Safety**: "Is the Volvo XC90 safe?" → Safety ratings and features analysis

**Key Improvement**: Removed rigid category routing and specialized prompts. The system now flows conversation context and database information naturally to GPT-4.1, which intelligently determines the appropriate response format.

### Conversation Memory & Context
- **Context Tracking**: Maintains conversation history for continuity across multiple queries
- **Context Awareness**: References previous queries and maintains conversation flow
- **Session Statistics**: Tracks success rate, query patterns, and interaction quality

### Egyptian Market Specialization
- **Local Currency**: All prices formatted in Egyptian Pounds with proper comma separation
- **Market Context**: Recommendations consider local market conditions, availability, and service networks
- **Origin Awareness**: Understands local bias for/against certain countries of origin
- **Feature Prioritization**: Emphasizes features important in Egyptian climate and roads

## Data Schema

### Core Vehicle Information
- `id`: Primary key (auto-increment)
- `car_brand`: Vehicle manufacturer (normalized: MG, Citroen)
- `car_model`: Model name
- `car_trim`: Specific variant/trim level (deduplicated)
- `Price_EGP`: Price in Egyptian Pounds
- `body_type`: AI-classified body style (sedan, hatchback, crossover/suv, coupe, convertible, van)

### Engine & Performance
- `Engine_CC`: Engine displacement (cleaned numeric)
- `Engine_Turbo`: Boolean for turbocharger presence
- `Horsepower_HP`: Power output
- `Max_Speed_kmh`: Maximum speed
- `Acceleration_0_100_sec`: 0-100 km/h acceleration time
- `Torque_Newton_Meter`: Engine torque
- `Fuel_Type`: Type of fuel (petrol, diesel, etc.)
- `Number_of_Cylinders`: Number of engine cylinders
- `Fuel_Consumption_l_100_km`: Fuel efficiency

### Powertrain & Electrification
- `powertrain_type`: Powertrain classification loaded from power_train.csv with manual adjustments
  - Categories: Internal_Combustion_Engine, Electric, Hybrid, Plug_in_Hybrid_PHEV, Mild_Hybrid_MHEV, Range_Extended_Electric_Vehicle_REEV_EREV
  - Special cases: santa-fe (Plug_in_Hybrid_PHEV), MG-4 (Internal_Combustion_Engine), x-Trail (Plug_in_Hybrid_PHEV)
- `Battery_Capacity_kWh`: Battery capacity for electric/hybrid vehicles
- `Battery_Range_km`: Electric range for electric/hybrid vehicles

### Transmission & Drivetrain
- `Transmission_Type`: Type of transmission (standardized: automatic_traditional, automatic_cvt, automatic_dsg, manual)
- `Number_transmission_Speeds`: Number of gears
- `Traction_Type`: Drive type (FWD, RWD, AWD)

### Dimensions & Capacity
- `Length_mm`, `Width_mm`, `Height_mm`: Vehicle dimensions
- `Wheelbase_mm`: Distance between axles
- `Ground_Clearance_mm`: Ground clearance
- `Trunk_Size_L`: Cargo capacity
- `Number_of_Seats`: Seating capacity (validated ≤9)
- `Fuel_Tank_L`: Fuel tank capacity

### Features & Safety
- Multiple boolean columns for features:
  - Safety: `ABS`, `EBD`, `ESP`, `Driver_Airbag`, `Passenger_Airbag`
  - Comfort: `Air_Conditioning`, `Power_Steering`, `Cruise_Control`
  - Technology: `Bluetooth`, `GPS`, `Multimedia_Touch_Screen`
  - Convenience: `Remote_Keyless`, `Central_Locking`, `Sunroof`

### Warranty & Pricing
- `Warranty_km`: Warranty distance coverage (extracted from text)
- `Warranty_years`: Warranty time coverage (extracted from text)
- `Minimum_Installment`: Minimum monthly payment
- `Minimum_Deposit`: Required down payment

### Origin & Assembly
- `Origin_Country`: Country where brand originated (AI-completed)
- `Assembly_Country`: Manufacturing location
- `Year`: Model year (filtered for recency)

## AI Integration & Architecture

### Agentic AI Integration
The system leverages OpenAI GPT models across two distinct layers:

#### 1. Data Processing Layer (`scrapped_data_postprocessing.py`)
**GPT-4 for Data Enhancement:**
- **Body Type Classification**: Batch processing of brand-model combinations into 6 standard categories
- **Origin Country Completion**: AI-powered brand origin identification using automotive knowledge
- **Batch Processing**: 50 combinations per API call with intelligent error handling
- **Duplicate Detection**: Removes duplicate entries based on car_trim
- **Powertrain Loading**: Loads pre-classified powertrain types from power_train.csv with model-specific adjustments

#### 2. Agentic Chatbot Layer (`chatbot/car_chatbot.py`)
**GPT-4.1 as Intelligent Agent with Tools:**
- **Function Calling Architecture**: LLM uses `execute_sql_query` tool to access database
- **Iterative Refinement**: Up to 3 tool calls for query adjustment based on results
- **SQL Generation**: Converts user queries to validated SQL in real-time
- **Result-Aware Responses**: LLM sees raw database results and crafts natural, context-specific responses
- **Automotive Knowledge**: Provides expertise on reliability, comparisons, market trends
- **Hybrid Query Handling**: Seamlessly integrates database results with knowledge insights
- **Smart Clarification**: Intelligently decides when user input is too vague
- **Adaptive Formatting**: Response style adapts to query context (not rigid templates)

**Tool Definition:**
```python
execute_sql_query(sql_query: str) -> Dict[str, Any]
# Returns: {"success": bool, "results_count": int, "results": List[Dict]}
```

**Agent Loop (Max 3 Iterations):**
1. LLM decides: Need database or just knowledge?
2. If database needed: Call `execute_sql_query` with generated SQL
3. See results: 0 results? Too many? Refine query
4. Optional: Call tool again with adjusted SQL
5. Craft natural response using all gathered information

**Supporting Components (No LLM Calls):**
- **QueryProcessor**: Configuration holder (schema, synonyms, OpenAI client)
- **ResponseGenerator**: Optional utility functions (price formatting)
- **DatabaseHandler**: SQL execution and result retrieval
- **ConversationManager**: Conversation history and context tracking

### Centralized Model Management
- **Single Configuration Point**: All LLM behavior controlled via `unified_prompt` in `chatbot/chatbot_config.yaml`
- **GPT-4 for Data Processing**: One-time data enhancement during preprocessing
- **GPT-4.1 for Chatbot**: All runtime chatbot intelligence (tool usage, SQL generation, responses, knowledge)
- **Fallback Handling**: Graceful degradation if AI services are unavailable
- **Performance Optimization**: Multi-turn agent with max 3 iterations balances flexibility and cost

## Database Performance

### Indexes
Performance-optimized with indexes on frequently queried columns:
```sql
CREATE INDEX idx_car_brand ON cars (car_brand);
CREATE INDEX idx_car_model ON cars (car_model);
CREATE INDEX idx_car_trim ON cars (car_trim);
CREATE INDEX idx_Price_EGP ON cars (Price_EGP);
CREATE INDEX idx_body_type ON cars (body_type);
CREATE INDEX idx_Transmission_Type ON cars (Transmission_Type);
CREATE INDEX idx_Origin_Country ON cars (Origin_Country);
CREATE INDEX idx_Engine_Turbo ON cars (Engine_Turbo);
```

### Sample Queries
```sql
-- Find budget crossovers with safety features
SELECT car_brand, car_model, Price_EGP, body_type
FROM cars
WHERE body_type = 'crossover/suv'
AND Price_EGP < 2000000
AND ABS = 1 AND ESP = 1
ORDER BY Price_EGP ASC;

-- Count cars by body type
SELECT body_type, COUNT(*) as count
FROM cars
GROUP BY body_type
ORDER BY count DESC;

-- Premium German cars with advanced features
SELECT car_brand, car_model, Price_EGP, Engine_Turbo, Transmission_Type
FROM cars
WHERE Origin_Country = 'germany'
AND Price_EGP > 2000000
AND Engine_Turbo = 1;

-- Non-Chinese automatic cars under budget
SELECT car_brand, car_model, Price_EGP, Origin_Country
FROM cars
WHERE Origin_Country != 'china'
AND Transmission_Type = 'automatic'
AND Price_EGP < 1500000
ORDER BY Price_EGP ASC
LIMIT 10;
```

## Usage Instructions

### Prerequisites
```bash
# Install required dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with:
OPENAI_API_KEY=your-openai-api-key-here
```

### Data Pipeline (One-time Setup)
```bash
# 1. Process raw scraped data with AI enhancement
python scrapped_data_postprocessing.py

# 2. Create SQLite database from processed data
python database/database_creator.py

# 3. Validate database integrity (optional)
python database/database_tester.py
```

### Running the Chatbot
```bash
# Start the advanced AI car chatbot
python run_chatbot.py

# Alternative: Direct module execution
python chatbot/car_chatbot.py
```

### Running Evaluation Tests
```bash
# Run chatbot evaluation tests
python evaluation/run_evaluation.py

# This will test various query types and report on:
# - Query understanding accuracy
# - Response quality and format
# - Feature extraction correctness
# - Edge case handling
```

### Interactive Commands
Once the chatbot starts, you have access to these commands:
- **help**: Show available commands and example queries
- **stats**: Display session statistics and database information
- **clear**: Reset conversation history and start fresh
- **quit/exit**: End the conversation and show session summary

### Example Queries
```
# Price-based searches
"Show me cars under 2 million EGP"
"Between 1.5 and 3 million EGP"

# Feature-specific requests
"Crossovers with automatic transmission and ESP"
"Non-Chinese cars with ABS and sunroof"

# Broad requests (handled intelligently)
"Pick a random car under 800k"
"Any good sedan for a family"
"Surprise me with a budget car"

# Knowledge queries
"Is the Toyota Camry reliable?"
"Compare Honda Civic vs Toyota Corolla"
"What cars are popular in Egypt?"
```

## Configuration

### Environment Variables (`.env`)
```
OPENAI_API_KEY=your-openai-api-key-here
```

### Schema Configuration (`database/schema.yaml`)
Defines the complete database structure with column types and constraints.

### Synonym Configuration (`database/synonyms.yaml`)
Maps user input variations to standardized terms for better chatbot understanding.

## Data Quality Metrics

### Processing Results
- **Total Records**: 937 vehicles with comprehensive specifications (after deduplication)
- **Data Completeness**: 100% for all AI-enhanced columns
- **Body Type Coverage**: 100% classification into 6 standardized categories
- **Origin Country**: 100% completion using GPT-4 automotive knowledge
- **Powertrain Classification**: 100% coverage from power_train.csv with manual adjustments
- **Brand Normalization**: All brand names standardized (MG, Citroen)
- **Schema Consistency**: All boolean features standardized and validated

### Quality Assurance
- **Price Validation**: Removes entries < 1,000 EGP
- **Year Filtering**: Dynamic filtering based on current date
- **Seat Count Validation**: Removes invalid counts > 9
- **Boolean Standardization**: Consistent True/False values
- **Unicode Handling**: Proper encoding for international text

## Performance Considerations

### Chatbot System Optimization
- **Modular Architecture**: Components can be optimized independently
- **Centralized Configuration**: Single point for model and behavior tuning
- **Intelligent Query Routing**: Reduces unnecessary processing through smart categorization
- **Conversation Memory**: Efficient context management without redundant storage

### GPT-4 API Optimization
- **Unified Model Usage**: Data processing uses GPT-4, chatbot uses GPT-4.1
- **Smart Prompt Engineering**: Optimized prompts for faster, more accurate responses
- **Context Management**: Selective context inclusion to minimize token usage
- **Fallback Handling**: Graceful degradation when API limits reached
- **Batch Processing**: Efficient batch processing for body type and origin country classification

### Database Optimization
- **Strategic Indexing**: 8 optimized indexes on frequently queried columns
- **Parameterized Queries**: Prevents SQL injection and improves performance
- **Result Formatting**: Efficient conversion from database rows to user-friendly summaries
- **Query Validation**: Pre-execution validation prevents problematic queries

## Troubleshooting

### Common Issues

1. **Chatbot Won't Start**:
   - Check OPENAI_API_KEY in `.env` file
   - Ensure `database/cars.db` exists (run `python database/database_creator.py`)
   - Verify all dependencies installed (`pip install -r requirements.txt`)

2. **Unicode/Encoding Errors**:
   - Fixed in current version (removed problematic emojis)
   - Windows console now supports the chatbot interface

3. **Database Issues**:
   - Permission denied: Close any database viewers
   - Missing table: Recreate database with `python database/database_creator.py`
   - No results: Check if processed_data.csv contains valid data

4. **GPT-4.1 API Issues**:
   - Rate limits: Built-in error handling with graceful fallbacks
   - Invalid API key: Update `.env` file with valid OpenAI API key
   - Token limits: System optimized to stay within reasonable token usage

### Debugging Commands
```bash
# Check database contents
python -c "import sqlite3; conn = sqlite3.connect('database/cars.db'); print(conn.execute('SELECT COUNT(*) FROM cars').fetchone())"

# Verify processed data
python -c "import pandas as pd; print(pd.read_csv('processed_data.csv').info())"

# Test web scraper
python web_scrapper/car_scraper.py --test-brands hyundai
```

## Future Enhancements

### Potential Improvements
- **Multi-language Support**: Extend AI processing for Arabic text
- **Image Recognition**: Add vehicle image classification
- **Price Prediction**: ML models for price forecasting
- **Conversation Context**: Enhanced understanding through conversation history
- **Real-time Updates**: Automated scraping and processing

### Scalability Considerations
- **Database Migration**: PostgreSQL for larger datasets
- **API Management**: Rate limiting and quota management
- **Caching Layer**: Redis for frequent queries
- **Microservices**: Separate scraping, processing, and chatbot services

## Contributing

### Code Standards
- **Python Style**: Follow PEP 8 guidelines
- **Error Handling**: Comprehensive exception handling
- **Logging**: Detailed progress and error logging
- **Documentation**: Clear docstrings and comments

### Testing
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline validation
- **Performance Tests**: Database query optimization
- **Data Quality Tests**: Validation of AI-enhanced data

---

*This documentation provides a comprehensive guide to the car selection chatbot system. For technical support or contributions, refer to the individual module documentation and code comments.*