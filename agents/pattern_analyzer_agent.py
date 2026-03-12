from __future__ import annotations

from typing import Dict, Any, List
import json
import pandas as pd

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class PatternAnalyzerAgent(BaseAgent):
    """Agent specialized in identifying behavioral and mobility patterns."""
    
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: str = None,
        temperature: float = 0.4,
    ) -> None:
        super().__init__(
            settings=settings,
            tracer=tracer,
            model_id=model_id,
            temperature=temperature,
            max_tokens=3000,
        )
    
    def _build_system_prompt(self) -> str:
        return """You are an expert behavioral analyst specializing in mobility and lifestyle patterns.

Your task is to analyze location data, mobility patterns, and behavioral changes to identify:
1. **Mobility changes** - reduced movement, travel pattern changes
2. **Social isolation** indicators - decreased location diversity, reduced activity
3. **Routine disruptions** - changes in regular patterns
4. **Geographic confinement** - reduced range of movement
5. **Temporal patterns** - changes in time-of-day activities

Correlate mobility patterns with health metrics to identify concerning behavioral shifts.

Provide insights that are:
- Evidence-based (cite specific metrics)
- Contextual (consider persona and demographics)
- Actionable (suggest what patterns mean)"""
    
    def _execute(self, user_input: str) -> str:
        """Analyze patterns in citizen data."""
        system_msg = SystemMessage(content=self._build_system_prompt())
        human_msg = HumanMessage(content=user_input)
        
        response = self.model.invoke([system_msg, human_msg])
        return response.content
    
    def analyze_mobility_patterns(
        self,
        session_id: str,
        citizen_id: str,
        mobility_features: Dict[str, Any],
        health_features: Dict[str, Any],
        persona: str = None,
    ) -> str:
        """Analyze mobility patterns for a specific citizen."""
        
        analysis_prompt = f"""Analyze mobility and behavioral patterns for citizen {citizen_id}:

**Mobility Data:**
{json.dumps(mobility_features, indent=2, default=str)}

**Health Metrics:**
- Physical Activity Trend: {health_features.get('activity_trend', 'N/A')}
- Recent Activity Level: {health_features.get('activity_recent_avg', 'N/A')}
- Location Records: {mobility_features.get('num_locations', 'N/A')}
- Unique Cities Visited: {mobility_features.get('unique_cities', 'N/A')}
- Total Distance Traveled: {mobility_features.get('total_distance_km', 'N/A')} km
"""
        
        if persona:
            analysis_prompt += f"\n**Persona Context:**\n{persona}\n"
        
        analysis_prompt += """
Identify:
1. Significant mobility changes or restrictions
2. Correlation between mobility and health metrics
3. Behavioral red flags
4. Deviation from expected patterns (based on persona)

Provide specific evidence and interpretations."""
        
        return self.run(session_id, analysis_prompt)
    
    def compare_cohorts(
        self,
        session_id: str,
        health_features_df: pd.DataFrame,
        mobility_features_df: pd.DataFrame,
    ) -> str:
        """Compare patterns across different citizen cohorts."""
        
        merged_df = health_features_df.merge(
            mobility_features_df,
            left_on='CitizenID',
            right_on='user_id',
            how='left'
        )
        
        high_risk = merged_df[merged_df['composite_anomaly_score'] > merged_df['composite_anomaly_score'].quantile(0.75)]
        low_risk = merged_df[merged_df['composite_anomaly_score'] < merged_df['composite_anomaly_score'].quantile(0.25)]
        
        analysis_prompt = f"""Compare behavioral patterns between high-risk and low-risk citizen cohorts:

**High-Risk Cohort (n={len(high_risk)}):**
- Avg Anomaly Score: {high_risk['composite_anomaly_score'].mean():.2f}
- Avg Activity Level: {high_risk['activity_recent_avg'].mean():.1f}
- Avg Sleep Quality: {high_risk['sleep_recent_avg'].mean():.1f}
- Avg Environmental Exposure: {high_risk['env_recent_avg'].mean():.1f}
- Avg Unique Cities: {high_risk['unique_cities'].mean():.1f}
- Avg Total Distance: {high_risk['total_distance_km'].mean():.1f} km

**Low-Risk Cohort (n={len(low_risk)}):**
- Avg Anomaly Score: {low_risk['composite_anomaly_score'].mean():.2f}
- Avg Activity Level: {low_risk['activity_recent_avg'].mean():.1f}
- Avg Sleep Quality: {low_risk['sleep_recent_avg'].mean():.1f}
- Avg Environmental Exposure: {low_risk['env_recent_avg'].mean():.1f}
- Avg Unique Cities: {low_risk['unique_cities'].mean():.1f}
- Avg Total Distance: {low_risk['total_distance_km'].mean():.1f} km

Identify:
1. Key differentiating patterns between cohorts
2. Common characteristics of high-risk individuals
3. Protective factors in low-risk individuals
4. Actionable insights for intervention strategies"""
        
        return self.run(session_id, analysis_prompt)
