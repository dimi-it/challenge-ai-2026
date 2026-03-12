from __future__ import annotations

from typing import Dict, Any
import json
import pandas as pd

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class AnomalyDetectorAgent(BaseAgent):
    """Agent specialized in detecting health anomalies from citizen data."""
    
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: str = None,
        temperature: float = 0.3,
    ) -> None:
        super().__init__(
            settings=settings,
            tracer=tracer,
            model_id=model_id,
            temperature=temperature,
            max_tokens=4000,
        )
    
    def _build_system_prompt(self) -> str:
        return """You are an expert health data analyst specializing in anomaly detection.

Your task is to analyze citizen health metrics and identify individuals showing concerning patterns.

Focus on:
1. **Declining trends** in PhysicalActivityIndex and SleepQualityIndex
2. **Increasing trends** in EnvironmentalExposureLevel
3. **Medical escalation** patterns (specialist consultations, follow-ups)
4. **Sudden changes** or deterioration in health metrics
5. **Combinations** of multiple negative indicators

For each citizen analyzed, provide:
- Risk level (LOW, MODERATE, HIGH, CRITICAL)
- Key concerning patterns identified
- Specific metric changes that triggered the alert
- Recommended actions

Be concise but thorough. Focus on actionable insights."""
    
    def _execute(self, user_input: str) -> str:
        """Analyze health data and detect anomalies."""
        system_msg = SystemMessage(content=self._build_system_prompt())
        human_msg = HumanMessage(content=user_input)
        
        response = self.model.invoke([system_msg, human_msg])
        return response.content
    
    def analyze_citizen(
        self,
        session_id: str,
        citizen_id: str,
        health_features: Dict[str, Any],
        persona: str = None,
    ) -> Dict[str, Any]:
        """Analyze a specific citizen for health anomalies."""
        
        analysis_prompt = f"""Analyze the following citizen's health data:

**Citizen ID:** {citizen_id}

**Health Metrics Summary:**
{json.dumps(health_features, indent=2, default=str)}
"""
        
        if persona:
            analysis_prompt += f"\n**Persona Context:**\n{persona}\n"
        
        analysis_prompt += """
Based on this data, provide:
1. Risk Level (LOW/MODERATE/HIGH/CRITICAL)
2. Key Concerns (bullet points)
3. Metric Analysis (specific numbers and trends)
4. Recommended Actions

Format your response as JSON with keys: risk_level, concerns, metrics_analysis, recommendations"""
        
        result = self.run(session_id, analysis_prompt)
        
        return {
            'citizen_id': citizen_id,
            'analysis': result,
            'features': health_features,
        }
    
    def batch_analyze(
        self,
        session_id: str,
        health_features_df: pd.DataFrame,
        personas: Dict[str, str] = None,
        top_n: int = 5,
    ) -> str:
        """Analyze multiple citizens and identify top anomalies."""
        
        sorted_df = health_features_df.sort_values('composite_anomaly_score', ascending=False)
        top_citizens = sorted_df.head(top_n)
        
        analysis_prompt = f"""Analyze the following {top_n} citizens with the highest anomaly scores:

"""
        
        for idx, row in top_citizens.iterrows():
            citizen_id = row['CitizenID']
            persona_text = personas.get(citizen_id, "No persona available") if personas else "No persona available"
            
            analysis_prompt += f"""
---
**Citizen {idx + 1}: {citizen_id}**

Anomaly Score: {row['composite_anomaly_score']:.2f}

Key Metrics:
- Physical Activity: {row['activity_early_avg']:.1f} → {row['activity_recent_avg']:.1f} (trend: {row['activity_trend']:.1f})
- Sleep Quality: {row['sleep_early_avg']:.1f} → {row['sleep_recent_avg']:.1f} (trend: {row['sleep_trend']:.1f})
- Environmental Exposure: {row['env_early_avg']:.1f} → {row['env_recent_avg']:.1f} (trend: {row['env_trend']:.1f})
- Specialist Consultations: {row['specialist_count']}
- Follow-up Assessments: {row['follow_up_count']}

Persona Context:
{persona_text[:500]}...

"""
        
        analysis_prompt += """
For each citizen, provide:
1. Risk assessment (CRITICAL/HIGH/MODERATE/LOW)
2. Primary concerns
3. Urgency level
4. Recommended interventions

Rank them by priority for immediate attention."""
        
        return self.run(session_id, analysis_prompt)
