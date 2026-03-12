from __future__ import annotations

from typing import Dict, Any, List
import json

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent
from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer


class RiskAssessorAgent(BaseAgent):
    """Agent specialized in comprehensive risk assessment and prioritization."""
    
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
        model_id: str = None,
        temperature: float = 0.2,
    ) -> None:
        super().__init__(
            settings=settings,
            tracer=tracer,
            model_id=model_id,
            temperature=temperature,
            max_tokens=4000,
        )
    
    def _build_system_prompt(self) -> str:
        return """You are a senior healthcare risk assessment specialist.

Your role is to synthesize multiple data sources and provide comprehensive risk assessments:

**Assessment Criteria:**
1. **Medical urgency** - immediate health risks requiring intervention
2. **Trend severity** - rate and magnitude of health deterioration
3. **Vulnerability factors** - age, social support, existing conditions
4. **Intervention feasibility** - likelihood of successful intervention
5. **Resource prioritization** - optimal allocation of limited resources

**Risk Levels:**
- CRITICAL: Immediate intervention required, high risk of adverse outcome
- HIGH: Urgent attention needed, significant deterioration observed
- MODERATE: Monitoring and preventive action recommended
- LOW: Stable, routine monitoring sufficient

Provide evidence-based assessments with:
- Clear risk categorization
- Specific intervention recommendations
- Priority ranking
- Resource allocation guidance
- Expected outcomes if intervention occurs vs. no action

Be decisive but nuanced. Consider both individual and population-level factors."""
    
    def _execute(self, user_input: str) -> str:
        """Perform risk assessment."""
        system_msg = SystemMessage(content=self._build_system_prompt())
        human_msg = HumanMessage(content=user_input)
        
        response = self.model.invoke([system_msg, human_msg])
        return response.content
    
    def assess_individual_risk(
        self,
        session_id: str,
        citizen_id: str,
        anomaly_analysis: str,
        pattern_analysis: str,
        persona: str,
        user_profile: Dict[str, Any],
    ) -> str:
        """Comprehensive risk assessment for an individual citizen."""
        
        age = 2026 - user_profile.get('birth_year', 2000)
        
        assessment_prompt = f"""Conduct a comprehensive risk assessment for citizen {citizen_id}:

**Demographic Information:**
- Age: {age}
- Occupation: {user_profile.get('job', 'Unknown')}
- Location: {user_profile.get('city', 'Unknown')}

**Persona Profile:**
{persona}

**Anomaly Detection Analysis:**
{anomaly_analysis}

**Behavioral Pattern Analysis:**
{pattern_analysis}

Provide a structured risk assessment including:

1. **RISK LEVEL**: (CRITICAL/HIGH/MODERATE/LOW)

2. **PRIMARY CONCERNS**: Top 3 health/behavioral risks identified

3. **VULNERABILITY ASSESSMENT**: 
   - Age-related factors
   - Social support adequacy
   - Environmental risks

4. **INTERVENTION RECOMMENDATIONS**:
   - Immediate actions (within 24-48 hours)
   - Short-term interventions (1-2 weeks)
   - Long-term monitoring plan

5. **EXPECTED OUTCOMES**:
   - If intervention occurs
   - If no action taken

6. **RESOURCE REQUIREMENTS**: What resources/specialists are needed

7. **PRIORITY SCORE** (1-10, where 10 is most urgent)

Be specific and actionable."""
        
        return self.run(session_id, assessment_prompt)
    
    def prioritize_interventions(
        self,
        session_id: str,
        citizen_assessments: List[Dict[str, Any]],
        available_resources: str = "Standard healthcare resources",
    ) -> str:
        """Prioritize interventions across multiple citizens given resource constraints."""
        
        assessment_summary = "**Citizens Requiring Assessment:**\n\n"
        
        for idx, assessment in enumerate(citizen_assessments, 1):
            assessment_summary += f"{idx}. {assessment['citizen_id']}\n"
            assessment_summary += f"   Anomaly Score: {assessment.get('anomaly_score', 'N/A')}\n"
            assessment_summary += f"   Key Issues: {assessment.get('key_issues', 'N/A')}\n\n"
        
        prioritization_prompt = f"""Given the following citizens requiring intervention:

{assessment_summary}

**Available Resources:**
{available_resources}

Provide a prioritized intervention plan:

1. **TIER 1 - IMMEDIATE ACTION** (next 24-48 hours)
   - List citizens requiring immediate intervention
   - Specific actions for each
   - Resources needed

2. **TIER 2 - URGENT** (within 1 week)
   - Citizens needing prompt attention
   - Recommended interventions
   - Timeline

3. **TIER 3 - MONITORING** (ongoing)
   - Citizens for enhanced monitoring
   - Monitoring protocols
   - Escalation triggers

4. **RESOURCE ALLOCATION STRATEGY**
   - How to optimally distribute available resources
   - Trade-offs and justifications

5. **RISK MITIGATION**
   - What happens if we can't address all cases
   - Contingency plans

Justify your prioritization with specific evidence."""
        
        return self.run(session_id, prioritization_prompt)
