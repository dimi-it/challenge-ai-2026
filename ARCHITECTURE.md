# System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                   run_health_analysis.py                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                                │
│  • Coordinates workflow                                              │
│  • Manages data flow                                                 │
│  • Generates reports                                                 │
└──┬────────────────┬────────────────┬────────────────┬───────────────┘
   │                │                │                │
   │ Phase 1        │ Phase 2        │ Phase 3        │ Phase 4
   │ Anomaly        │ Pattern        │ Risk           │ Prioritization
   │ Detection      │ Analysis       │ Assessment     │
   │                │                │                │
   ▼                ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Anomaly     │ │   Pattern    │ │     Risk     │ │     Risk     │
│  Detector    │ │   Analyzer   │ │   Assessor   │ │   Assessor   │
│   Agent      │ │    Agent     │ │    Agent     │ │    Agent     │
│              │ │              │ │              │ │              │
│ T=0.3        │ │ T=0.4        │ │ T=0.2        │ │ T=0.2        │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
   │                │                │                │
   └────────────────┴────────────────┴────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   LangChain    │
                    │   ChatOpenAI   │
                    └────────┬───────┘
                             │
                    ┌────────┴───────┐
                    │                │
                    ▼                ▼
            ┌──────────────┐  ┌──────────────┐
            │  OpenRouter  │  │   OpenAI     │
            │     API      │  │    API       │
            └──────────────┘  └──────────────┘
```

## Data Flow Pipeline

```
INPUT DATA
├── users.json
├── personas.md
├── status.csv
└── locations.json
        │
        ▼
┌─────────────────────────────────────────┐
│         DATA LOADER                      │
│  • Parse JSON/CSV/MD                     │
│  • Create UserProfile objects            │
│  • Build DataFrames                      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      FEATURE ENGINEER                    │
│  • Health trends (activity, sleep, env) │
│  • Mobility metrics (distance, cities)  │
│  • Anomaly scores (composite)           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      MULTI-AGENT ANALYSIS                │
│                                          │
│  Phase 1: Batch Anomaly Detection        │
│  Phase 2: Cohort Pattern Analysis        │
│  Phase 3: Individual Risk Assessment     │
│  Phase 4: Intervention Prioritization    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│       REPORT GENERATOR                   │
│  • Executive summary                     │
│  • Detailed findings                     │
│  • Intervention plan                     │
└────────────┬────────────────────────────┘
             │
             ▼
OUTPUT
├── Console output (real-time)
├── Report file (output/*.txt)
└── Langfuse traces (cloud)
```

## Agent Interaction Flow

```
Session Start
     │
     ▼
┌─────────────────────────────────────────┐
│  Orchestrator: Load & Engineer Features │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Anomaly Detector: Batch Analysis       │
│  Input: health_features_df               │
│  Output: Top N anomalies + analysis      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Pattern Analyzer: Cohort Comparison    │
│  Input: health + mobility features       │
│  Output: High-risk vs low-risk patterns  │
└────────────┬────────────────────────────┘
             │
             ▼
     For each top anomaly:
     │
     ├─► Anomaly Detector: Individual analysis
     │        │
     ├─► Pattern Analyzer: Mobility patterns
     │        │
     └─► Risk Assessor: Comprehensive assessment
             │
             ▼
┌─────────────────────────────────────────┐
│  Risk Assessor: Prioritize Interventions│
│  Input: All individual assessments       │
│  Output: Tiered intervention plan        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Orchestrator: Generate Final Report    │
└────────────┬────────────────────────────┘
             │
             ▼
        Session End
```

## Feature Engineering Pipeline

```
STATUS.CSV (Health Events)
     │
     ▼
┌─────────────────────────────────────────┐
│  Group by CitizenID                      │
│  Sort by Timestamp                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Compute Trends                          │
│  • activity_trend = last - first         │
│  • sleep_trend = last - first            │
│  • env_trend = last - first              │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Compute Statistics                      │
│  • mean, std, min, max                   │
│  • early_avg (first 3)                   │
│  • recent_avg (last 3)                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Medical Escalation                      │
│  • specialist_count                      │
│  • follow_up_count                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Anomaly Scores                          │
│  • activity_decline_score                │
│  • sleep_decline_score                   │
│  • env_increase_score                    │
│  • medical_escalation_score              │
│  • composite_anomaly_score (weighted)    │
└─────────────────────────────────────────┘

LOCATIONS.JSON (GPS Tracking)
     │
     ▼
┌─────────────────────────────────────────┐
│  Group by user_id                        │
│  Sort by timestamp                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Distance Calculations                   │
│  • Haversine distance between points     │
│  • total_distance_km                     │
│  • avg_distance_km                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Geographic Diversity                    │
│  • unique_cities                         │
│  • lat_range, lng_range                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Temporal Patterns                       │
│  • avg_time_between_records              │
│  • first/last location dates             │
└─────────────────────────────────────────┘
```

## Tracing Architecture

```
┌─────────────────────────────────────────┐
│         Application Layer                │
│  run_health_analysis.py                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      LangfuseTracer                      │
│  • generate_session_id()                 │
│  • get_langfuse_handler()                │
│  • flush()                               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      BaseAgent (@observe)                │
│  • run() method decorated                │
│  • propagate_attributes()                │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      LangChain Integration               │
│  • CallbackHandler                       │
│  • Automatic span creation               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      Langfuse Cloud                      │
│  • Trace storage                         │
│  • Analytics dashboard                   │
│  • Cost tracking                         │
└─────────────────────────────────────────┘
```

## Class Hierarchy

```
BaseAgent (Abstract)
├── model: ChatOpenAI
├── tracer: LangfuseTracer
├── _build_system_prompt() [abstract]
├── _execute() [abstract]
└── run() [@observe]
    │
    ├─► AnomalyDetectorAgent
    │   ├── analyze_citizen()
    │   └── batch_analyze()
    │
    ├─► PatternAnalyzerAgent
    │   ├── analyze_mobility_patterns()
    │   └── compare_cohorts()
    │
    └─► RiskAssessorAgent
        ├── assess_individual_risk()
        └── prioritize_interventions()

OrchestratorAgent (Standalone)
├── anomaly_detector: AnomalyDetectorAgent
├── pattern_analyzer: PatternAnalyzerAgent
├── risk_assessor: RiskAssessorAgent
├── data_loader: DataLoader
├── feature_engineer: FeatureEngineer
├── load_data()
├── engineer_features()
├── analyze_all_citizens()
└── generate_report()
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Development Environment                 │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Python Virtual Environment (.venv)             │    │
│  │  • LangChain                                    │    │
│  │  • Langfuse                                     │    │
│  │  • Pandas/NumPy                                 │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Configuration (.env)                           │    │
│  │  • API Keys                                     │    │
│  │  • Model Selection                              │    │
│  │  • Tracing Settings                             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Data Files (input_sandbox/)                    │    │
│  │  • Level 1: 5 citizens                          │    │
│  │  • Level 2: Medium dataset                      │    │
│  │  • Level 3: Full dataset                        │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  External Services                       │
│                                                          │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │   OpenRouter     │         │   Langfuse       │     │
│  │   (LLM API)      │         │   (Tracing)      │     │
│  └──────────────────┘         └──────────────────┘     │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Output Artifacts                        │
│                                                          │
│  • Console logs (real-time)                             │
│  • Report files (output/*.txt)                          │
│  • Trace URLs (Langfuse cloud)                          │
└─────────────────────────────────────────────────────────┘
```

## Security & Privacy Considerations

```
┌─────────────────────────────────────────┐
│         API Key Management               │
│  • Stored in .env (gitignored)           │
│  • Never hardcoded                       │
│  • Loaded via pydantic-settings          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         Data Privacy                     │
│  • Anonymized user IDs                   │
│  • No PII in traces                      │
│  • Local data processing                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         Access Control                   │
│  • Langfuse project-based isolation      │
│  • API key rotation support              │
│  • Session-based trace grouping          │
└─────────────────────────────────────────┘
```

## Scalability Considerations

```
Current: Single-threaded sequential processing
└─► Suitable for: 5-50 citizens

Future: Parallel processing
├─► Batch analysis: Concurrent API calls
├─► Feature engineering: Pandas vectorization
└─► Agent execution: ThreadPoolExecutor
    └─► Suitable for: 100+ citizens

Future: Distributed processing
├─► Data partitioning
├─► Agent pool management
└─► Result aggregation
    └─► Suitable for: 1000+ citizens
```
