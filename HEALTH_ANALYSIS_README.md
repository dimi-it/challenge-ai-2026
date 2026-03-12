# Health Monitoring System - Multi-Agent Analysis

An advanced agentic system for analyzing citizen health data, detecting anomalies, identifying behavioral patterns, and assessing health risks.

## System Architecture

### Multi-Agent Design

The system employs a **multi-agent architecture** with specialized agents coordinated by an orchestrator:

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  (Coordinates workflow, manages data flow between agents)    │
└────────────┬────────────────┬────────────────┬──────────────┘
             │                │                │
    ┌────────▼────────┐  ┌───▼────────┐  ┌───▼──────────┐
    │ Anomaly Detector│  │  Pattern   │  │     Risk     │
    │     Agent       │  │  Analyzer  │  │  Assessor    │
    │                 │  │   Agent    │  │    Agent     │
    └─────────────────┘  └────────────┘  └──────────────┘
```

### Agent Responsibilities

1. **Anomaly Detector Agent** (`anomaly_detector_agent.py`)
   - Detects declining health trends
   - Identifies medical escalation patterns
   - Flags sudden metric changes
   - Assigns anomaly scores

2. **Pattern Analyzer Agent** (`pattern_analyzer_agent.py`)
   - Analyzes mobility patterns
   - Identifies behavioral changes
   - Detects social isolation indicators
   - Correlates location data with health metrics

3. **Risk Assessor Agent** (`risk_assessor_agent.py`)
   - Performs comprehensive risk assessment
   - Prioritizes interventions
   - Recommends specific actions
   - Considers demographic and vulnerability factors

4. **Orchestrator Agent** (`orchestrator_agent.py`)
   - Coordinates all agents
   - Manages data pipeline
   - Generates comprehensive reports
   - Ensures proper workflow execution

## Data Pipeline

### Input Data Structure

```
input_sandbox/
├── public_lev_1/          # Level 1 dataset (5 citizens)
│   ├── users.json         # User demographics
│   ├── personas.md        # Detailed persona descriptions
│   ├── status.csv         # Health status events
│   └── locations.json     # GPS tracking data
├── public_lev_2/          # Level 2 dataset (larger)
└── public_lev_3/          # Level 3 dataset (largest)
```

### Data Files

**users.json** - Citizen profiles
```json
{
  "user_id": "WNACROYX",
  "first_name": "Craig",
  "last_name": "Connor",
  "birth_year": 1991,
  "job": "Ride-share Driver",
  "residence": {
    "city": "Bath",
    "lat": "51.3814",
    "lng": "-2.3597"
  }
}
```

**status.csv** - Health metrics over time
```csv
EventID,CitizenID,EventType,PhysicalActivityIndex,SleepQualityIndex,EnvironmentalExposureLevel,Timestamp
31,WNACROYX,routine check-up,53,58,45,2026-01-01T00:00:00
```

**locations.json** - GPS tracking
```json
{
  "user_id": "WNACROYX",
  "timestamp": "2026-01-01T17:36:58",
  "lat": 51.3814,
  "lng": -2.3597,
  "city": "Bath"
}
```

**personas.md** - Rich behavioral descriptions

## Feature Engineering

The system computes comprehensive features from raw data:

### Health Features
- **Trend Analysis**: Activity, sleep, environmental exposure trends
- **Statistical Metrics**: Mean, std, min, max for each health indicator
- **Temporal Patterns**: Early vs. recent averages
- **Medical Escalation**: Specialist consultations, follow-ups

### Mobility Features
- **Distance Metrics**: Total distance, average trip distance
- **Geographic Diversity**: Unique cities visited, coordinate ranges
- **Temporal Patterns**: Time between location records
- **Movement Patterns**: Haversine distance calculations

### Anomaly Scores
- **Activity Decline Score**: Measures decrease in physical activity
- **Sleep Decline Score**: Tracks sleep quality deterioration
- **Environmental Increase Score**: Monitors exposure level rises
- **Medical Escalation Score**: Weights specialist visits and follow-ups
- **Composite Anomaly Score**: Weighted combination of all factors

## Usage

### Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment** (copy `.env.example` to `.env`):
```env
PROVIDER=openrouter
OPENROUTER_API_KEY=your-key-here
DEFAULT_MODEL_ID=anthropic/claude-3.5-sonnet
LANGFUSE_PUBLIC_KEY=your-key
LANGFUSE_SECRET_KEY=your-key
```

3. **Explore the data**:
```bash
python scripts/preprocess_data.py input_sandbox/public_lev_1 --explore
```

4. **Run analysis**:
```bash
python run_health_analysis.py input_sandbox/public_lev_1
```

### Advanced Usage

**Analyze different dataset levels**:
```bash
# Level 1 (5 citizens)
python run_health_analysis.py input_sandbox/public_lev_1

# Level 2 (more citizens)
python run_health_analysis.py input_sandbox/public_lev_2

# Level 3 (full dataset)
python run_health_analysis.py input_sandbox/public_lev_3
```

**Data validation**:
```bash
python scripts/preprocess_data.py input_sandbox/public_lev_1 --validate
```

**Export data summary**:
```bash
python scripts/preprocess_data.py input_sandbox/public_lev_1 --export summary.txt
```

## Analysis Workflow

The system executes a **4-phase analysis**:

### Phase 1: Anomaly Detection
- Batch analysis of all citizens
- Identification of top anomalies
- Anomaly score ranking

### Phase 2: Pattern Analysis
- Cohort comparison (high-risk vs. low-risk)
- Mobility pattern identification
- Behavioral change detection

### Phase 3: Detailed Risk Assessment
- Individual deep-dive analysis
- Multi-factor risk evaluation
- Intervention recommendations

### Phase 4: Intervention Prioritization
- Resource allocation strategy
- Tiered intervention plan (Immediate/Urgent/Monitoring)
- Expected outcome projections

## Output

### Report Structure

The system generates comprehensive reports saved to `output/`:

```
health_analysis_report_[session_id].txt
```

**Report Sections**:
1. Executive Summary
2. Methodology
3. Anomaly Detection Findings
4. Cohort Analysis
5. Detailed Individual Assessments
6. Intervention Prioritization
7. Resource Allocation Recommendations

### Langfuse Tracing

All agent interactions are traced in Langfuse for:
- Performance monitoring
- Cost tracking
- Debugging
- Audit trails

Access traces via the URL printed at the end of execution.

## Utilities

### Data Loader (`utils/data_loader.py`)
- Loads JSON, CSV, and Markdown files
- Parses user profiles and personas
- Converts to structured formats

### Feature Engineer (`utils/feature_engineering.py`)
- Computes health trends
- Calculates mobility metrics
- Generates anomaly scores
- Haversine distance calculations

## Key Insights from Level 1 Data

Based on initial analysis, **Craig Connor (WNACROYX)** shows critical patterns:

- **Physical Activity**: 53 → 17 (severe decline)
- **Sleep Quality**: 58 → 20 (critical deterioration)
- **Environmental Exposure**: 45 → 91 (alarming increase)
- **Medical Escalation**: Multiple specialist consultations + follow-ups
- **Behavioral Changes**: Cancelling social plans, irregular work schedule

This demonstrates the system's ability to identify high-risk individuals requiring immediate intervention.

## Extending the System

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `_build_system_prompt()` and `_execute()`
3. Add to orchestrator workflow
4. Update `agents/__init__.py`

### Custom Features

Add new feature engineering methods to `FeatureEngineer` class:
```python
@staticmethod
def compute_custom_feature(data: pd.DataFrame) -> pd.DataFrame:
    # Your feature logic
    return features_df
```

### Different Data Sources

Extend `DataLoader` to support additional formats:
```python
def load_custom_data(self) -> pd.DataFrame:
    # Your loading logic
    return df
```

## Technical Stack

- **LangChain**: Agent framework and LLM integration
- **Langfuse**: Observability and tracing
- **Pandas/NumPy**: Data processing and feature engineering
- **OpenAI/OpenRouter**: LLM providers
- **Python 3.8+**: Runtime environment

## Best Practices

1. **Always validate data** before running analysis
2. **Monitor Langfuse traces** for debugging
3. **Adjust temperature** per agent (lower for risk assessment, higher for pattern analysis)
4. **Scale gradually** - test on Level 1 before running Level 3
5. **Review reports** - AI insights require human validation

## Troubleshooting

**Issue**: Missing dependencies
```bash
pip install -r requirements.txt --upgrade
```

**Issue**: API key errors
- Check `.env` file configuration
- Verify API keys are valid
- Ensure correct provider is set

**Issue**: Data loading errors
- Validate data files exist
- Check file formats match expected structure
- Run preprocessing script with `--validate`

## License & Attribution

This system was developed for the ChallengeAI2026 health monitoring challenge.
