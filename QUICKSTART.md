# Quick Start Guide - Health Monitoring System

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- API key for OpenRouter or OpenAI
- (Optional) Langfuse account for tracing

## Step 1: Environment Setup

```bash
# Navigate to project directory
cd C:\Users\d.masetta\Documents\work\ChallengeAI2026

# Activate virtual environment (if not already active)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Keys

Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` and add your keys:
```env
PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEFAULT_MODEL_ID=anthropic/claude-3.5-sonnet

# Optional: Langfuse tracing
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Step 3: Explore the Data (Optional)

```bash
python scripts/preprocess_data.py input_sandbox/public_lev_1 --explore
```

This will show you:
- Number of users
- Available data files
- Health metric ranges
- Data quality summary

## Step 4: Run the Analysis

```bash
python run_health_analysis.py input_sandbox/public_lev_1
```

This will:
1. Load all data files
2. Engineer features from raw data
3. Run multi-agent analysis
4. Generate a comprehensive report
5. Save results to `output/` folder

## Step 5: Review Results

The analysis will:
- Print findings to console in real-time
- Save a detailed report to `output/health_analysis_report_[session_id].txt`
- Provide a Langfuse trace URL for detailed inspection

## What to Expect

### Console Output

You'll see 4 phases:

```
================================================================================
PHASE 1: ANOMALY DETECTION
================================================================================
[AI analysis of top anomalies]

================================================================================
PHASE 2: PATTERN ANALYSIS
================================================================================
[Cohort comparison and behavioral patterns]

================================================================================
PHASE 3: DETAILED RISK ASSESSMENT
================================================================================
--- Analyzing WNACROYX ---
[Individual risk assessment]

================================================================================
PHASE 4: INTERVENTION PRIORITIZATION
================================================================================
[Prioritized intervention plan]
```

### Expected Findings (Level 1)

The system should identify **Craig Connor (WNACROYX)** as high-risk due to:
- Severe physical activity decline (53 → 17)
- Critical sleep quality drop (58 → 20)
- Alarming environmental exposure increase (45 → 91)
- Multiple specialist consultations

## Next Steps

### Analyze Larger Datasets

```bash
# Level 2 (more citizens)
python run_health_analysis.py input_sandbox/public_lev_2

# Level 3 (full dataset)
python run_health_analysis.py input_sandbox/public_lev_3
```

### Customize Analysis

Edit `run_health_analysis.py` to adjust:
- `top_n`: Number of citizens to analyze in detail (default: 5)
- `detailed_analysis`: Set to `False` for faster batch-only analysis

### View Traces

If you configured Langfuse, visit the trace URL printed at the end to see:
- All LLM calls
- Token usage
- Latency metrics
- Cost tracking

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "API key not found"
Check your `.env` file has the correct keys and provider setting.

### "File not found"
Ensure you're running from the project root directory and the data files exist in `input_sandbox/`.

### Analysis takes too long
- Reduce `top_n` parameter
- Use a faster model
- Set `detailed_analysis=False`

## Tips

1. **Start small**: Test with Level 1 before running larger datasets
2. **Monitor costs**: Check Langfuse for token usage
3. **Validate data**: Run preprocessing script first
4. **Review outputs**: AI insights should be validated by domain experts

## Support

For issues or questions:
1. Check `HEALTH_ANALYSIS_README.md` for detailed documentation
2. Review Langfuse traces for debugging
3. Examine the generated report in `output/`

---

**Ready to analyze health data? Run:**
```bash
python run_health_analysis.py input_sandbox/public_lev_1
```
