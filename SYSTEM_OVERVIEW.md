# Health Monitoring System - Technical Overview

## System Architecture

### Component Structure

```
ChallengeAI2026/
├── agents/                          # Multi-agent system
│   ├── base_agent.py               # Abstract base class
│   ├── anomaly_detector_agent.py   # Detects health anomalies
│   ├── pattern_analyzer_agent.py   # Analyzes behavioral patterns
│   ├── risk_assessor_agent.py      # Assesses risks and prioritizes
│   └── orchestrator_agent.py       # Coordinates all agents
│
├── utils/                           # Data processing utilities
│   ├── data_loader.py              # Loads JSON, CSV, MD files
│   └── feature_engineering.py      # Computes features & scores
│
├── scripts/                         # Utility scripts
│   ├── preprocess_data.py          # Data exploration & validation
│   └── test_system.py              # System verification tests
│
├── config/                          # Configuration
│   └── settings.py                 # Environment settings
│
├── tracing/                         # Observability
│   └── langfuse_tracer.py          # Langfuse integration
│
├── input_sandbox/                   # Challenge data
│   ├── public_lev_1/               # 5 citizens (testing)
│   ├── public_lev_2/               # Medium dataset
│   └── public_lev_3/               # Full dataset
│
├── output/                          # Generated reports
│
├── run_health_analysis.py          # Main execution script
├── HEALTH_ANALYSIS_README.md       # Detailed documentation
├── QUICKSTART.md                   # Quick start guide
└── SYSTEM_OVERVIEW.md              # This file
```

## Agent Capabilities

### 1. Anomaly Detector Agent
**Purpose**: Identify citizens with concerning health patterns

**Capabilities**:
- Batch analysis of all citizens
- Individual deep-dive analysis
- Anomaly score calculation
- Medical escalation detection

**Key Methods**:
- `analyze_citizen()`: Single citizen analysis
- `batch_analyze()`: Top N anomalies identification

**Temperature**: 0.3 (precise, consistent)

### 2. Pattern Analyzer Agent
**Purpose**: Identify behavioral and mobility changes

**Capabilities**:
- Mobility pattern analysis
- Cohort comparison (high-risk vs low-risk)
- Behavioral change detection
- Geographic confinement identification

**Key Methods**:
- `analyze_mobility_patterns()`: Individual mobility analysis
- `compare_cohorts()`: Population-level patterns

**Temperature**: 0.4 (balanced creativity/precision)

### 3. Risk Assessor Agent
**Purpose**: Comprehensive risk evaluation and prioritization

**Capabilities**:
- Multi-factor risk assessment
- Intervention prioritization
- Resource allocation recommendations
- Expected outcome projections

**Key Methods**:
- `assess_individual_risk()`: Detailed risk assessment
- `prioritize_interventions()`: Triage and resource allocation

**Temperature**: 0.2 (highly consistent, decisive)

### 4. Orchestrator Agent
**Purpose**: Coordinate workflow and data flow

**Capabilities**:
- Data pipeline management
- Agent coordination
- Report generation
- Session management

**Key Methods**:
- `load_data()`: Initialize data
- `engineer_features()`: Compute features
- `analyze_all_citizens()`: Run full analysis
- `generate_report()`: Create comprehensive report

## Data Processing Pipeline

### Stage 1: Data Loading
```python
DataLoader.load_all()
├── users.json → UserProfile objects
├── personas.md → Persona descriptions
├── status.csv → Health metrics DataFrame
└── locations.json → Location tracking DataFrame
```

### Stage 2: Feature Engineering
```python
FeatureEngineer
├── compute_health_trends()
│   ├── Activity metrics (mean, std, trend)
│   ├── Sleep metrics (mean, std, trend)
│   ├── Environmental metrics (mean, std, trend)
│   └── Medical escalation (specialist visits, follow-ups)
│
├── compute_mobility_features()
│   ├── Distance calculations (Haversine)
│   ├── Geographic diversity (unique cities)
│   └── Temporal patterns (time between records)
│
└── compute_anomaly_scores()
    ├── Activity decline score
    ├── Sleep decline score
    ├── Environmental increase score
    ├── Medical escalation score
    └── Composite anomaly score (weighted sum)
```

### Stage 3: Multi-Agent Analysis
```python
Orchestrator.analyze_all_citizens()
├── Phase 1: Anomaly Detection
│   └── AnomalyDetectorAgent.batch_analyze()
│
├── Phase 2: Pattern Analysis
│   └── PatternAnalyzerAgent.compare_cohorts()
│
├── Phase 3: Detailed Risk Assessment
│   ├── AnomalyDetectorAgent.analyze_citizen()
│   ├── PatternAnalyzerAgent.analyze_mobility_patterns()
│   └── RiskAssessorAgent.assess_individual_risk()
│
└── Phase 4: Intervention Prioritization
    └── RiskAssessorAgent.prioritize_interventions()
```

### Stage 4: Report Generation
```python
Orchestrator.generate_report()
├── Executive Summary
├── Methodology
├── Findings (all phases)
├── Detailed Assessments
└── Intervention Plan
```

## Key Algorithms

### Anomaly Score Calculation

```python
composite_anomaly_score = (
    activity_decline_score * 1.5 +      # Weight: High
    sleep_decline_score * 1.2 +         # Weight: Medium-High
    env_increase_score * 1.3 +          # Weight: High
    medical_escalation_score * 0.5      # Weight: Medium
)

where:
    activity_decline_score = clip(-activity_trend / 50, 0, 2)
    sleep_decline_score = clip(-sleep_trend / 50, 0, 2)
    env_increase_score = clip(env_trend / 50, 0, 2)
    medical_escalation_score = specialist_count * 2 + follow_up_count * 1.5
```

### Haversine Distance (Mobility)

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    Δlat = radians(lat2 - lat1)
    Δlon = radians(lon2 - lon1)
    
    a = sin(Δlat/2)² + cos(lat1) * cos(lat2) * sin(Δlon/2)²
    c = 2 * arctan2(√a, √(1-a))
    
    return R * c
```

## Test Results (Level 1)

**Data Loaded**:
- 5 users
- 5 personas
- 50 status records
- 958 location records

**Top Anomaly**: WNACROYX (Craig Connor)
- Anomaly Score: **8.44** (significantly higher than others)
- Activity Trend: **-36.0** (severe decline)
- Sleep Trend: **-38.0** (critical deterioration)
- Environmental Exposure: **+46.0** (alarming increase)
- Specialist Visits: **3** (medical escalation)

**Interpretation**: System correctly identifies Craig Connor as the highest-risk individual, matching the persona description of declining health and behavioral changes.

## Performance Characteristics

### Scalability
- **Level 1** (5 citizens): ~2-3 minutes
- **Level 2** (estimated): ~5-10 minutes
- **Level 3** (estimated): ~15-30 minutes

*Times vary based on model speed and API latency*

### Token Usage (per citizen, detailed analysis)
- Anomaly Detection: ~1,500 tokens
- Pattern Analysis: ~1,200 tokens
- Risk Assessment: ~2,000 tokens
- **Total per citizen**: ~4,700 tokens

### Cost Optimization
- Use batch analysis for initial screening
- Detailed analysis only for top N anomalies
- Adjust `top_n` parameter based on budget
- Consider faster/cheaper models for pattern analysis

## Extension Points

### Adding New Features
```python
# In utils/feature_engineering.py
@staticmethod
def compute_custom_feature(df: pd.DataFrame) -> pd.DataFrame:
    # Your feature logic
    return features_df
```

### Adding New Agents
```python
# Create agents/custom_agent.py
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def _build_system_prompt(self) -> str:
        return "Your prompt"
    
    def _execute(self, user_input: str) -> str:
        # Your logic
        return result
```

### Custom Analysis Workflows
```python
# Modify orchestrator_agent.py
def custom_analysis_workflow(self, session_id: str):
    # Your custom workflow
    pass
```

## Monitoring & Debugging

### Langfuse Tracing
All LLM calls are automatically traced:
- View at: https://cloud.langfuse.com
- Session ID groups all related calls
- Track: tokens, latency, cost, errors

### Logging
Console output shows:
- Data loading progress
- Feature engineering stats
- Real-time agent analysis
- Phase completion status

### Error Handling
- Data validation before processing
- Graceful degradation if data missing
- Detailed error messages with stack traces

## Best Practices

1. **Start Small**: Test on Level 1 before scaling
2. **Validate Data**: Run preprocessing script first
3. **Monitor Costs**: Check Langfuse for token usage
4. **Review Outputs**: AI insights need human validation
5. **Adjust Parameters**: Tune `top_n`, temperature, max_tokens
6. **Version Control**: Track changes to prompts and features

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -r requirements.txt` |
| API key errors | Check `.env` configuration |
| Data not found | Verify `input_sandbox/` structure |
| Slow performance | Reduce `top_n`, use faster model |
| High costs | Use batch analysis only, cheaper model |
| Poor results | Adjust prompts, temperature, or features |

## Future Enhancements

- [ ] Real-time monitoring dashboard
- [ ] Automated intervention scheduling
- [ ] Integration with healthcare systems
- [ ] Predictive modeling (ML/DL)
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Alert notifications
- [ ] Historical trend visualization

## References

- **LangChain**: https://python.langchain.com/
- **Langfuse**: https://langfuse.com/docs
- **Pandas**: https://pandas.pydata.org/
- **OpenRouter**: https://openrouter.ai/

---

**System Status**: ✅ Fully Operational

**Last Updated**: 2026-03-12

**Version**: 1.0.0
