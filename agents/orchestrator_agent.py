from __future__ import annotations

from typing import Dict, Any, List
import pandas as pd

from agents.base_agent import BaseAgent
from agents.anomaly_detector_agent import AnomalyDetectorAgent
from agents.pattern_analyzer_agent import PatternAnalyzerAgent
from agents.risk_assessor_agent import RiskAssessorAgent
from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer
from utils.data_loader import DataLoader, UserProfile
from utils.feature_engineering import FeatureEngineer


class OrchestratorAgent:
    """Orchestrates multiple specialized agents to perform comprehensive health analysis."""
    
    def __init__(
        self,
        settings: Settings,
        tracer: LangfuseTracer,
    ) -> None:
        self.settings = settings
        self.tracer = tracer
        
        self.anomaly_detector = AnomalyDetectorAgent(settings, tracer)
        self.pattern_analyzer = PatternAnalyzerAgent(settings, tracer)
        self.risk_assessor = RiskAssessorAgent(settings, tracer)
        
        self.data_loader = None
        self.feature_engineer = FeatureEngineer()
        
        self.users = None
        self.personas = None
        self.status_df = None
        self.locations_df = None
        self.health_features = None
        self.mobility_features = None
    
    def load_data(self, data_dir: str) -> None:
        """Load all data from the specified directory."""
        self.data_loader = DataLoader(data_dir)
        self.users, self.personas, self.status_df, self.locations_df = self.data_loader.load_all()
        
        print(f"Loaded {len(self.users)} users")
        print(f"Loaded {len(self.personas)} personas")
        print(f"Loaded {len(self.status_df)} status records")
        print(f"Loaded {len(self.locations_df)} location records")
    
    def engineer_features(self) -> None:
        """Compute features from raw data."""
        print("\nEngineering features...")
        
        self.health_features = self.feature_engineer.compute_health_trends(self.status_df)
        self.health_features = self.feature_engineer.compute_anomaly_scores(self.health_features)
        
        self.mobility_features = self.feature_engineer.compute_mobility_features(self.locations_df)
        
        print(f"Computed health features for {len(self.health_features)} citizens")
        print(f"Computed mobility features for {len(self.mobility_features)} citizens")
    
    def analyze_all_citizens(
        self,
        session_id: str,
        top_n: int = 5,
        detailed_analysis: bool = True,
    ) -> Dict[str, Any]:
        """Run comprehensive analysis on all citizens."""
        
        if self.health_features is None or self.mobility_features is None:
            raise ValueError("Features not computed. Call engineer_features() first.")
        
        print(f"\n{'='*60}")
        print("PHASE 1: ANOMALY DETECTION")
        print(f"{'='*60}")
        
        batch_anomaly_analysis = self.anomaly_detector.batch_analyze(
            session_id=session_id,
            health_features_df=self.health_features,
            personas=self.personas,
            top_n=top_n,
        )
        
        print(batch_anomaly_analysis)
        
        print(f"\n{'='*60}")
        print("PHASE 2: PATTERN ANALYSIS")
        print(f"{'='*60}")
        
        cohort_analysis = self.pattern_analyzer.compare_cohorts(
            session_id=session_id,
            health_features_df=self.health_features,
            mobility_features_df=self.mobility_features,
        )
        
        print(cohort_analysis)
        
        results = {
            'batch_anomaly_analysis': batch_anomaly_analysis,
            'cohort_pattern_analysis': cohort_analysis,
            'detailed_assessments': [],
        }
        
        if detailed_analysis:
            print(f"\n{'='*60}")
            print("PHASE 3: DETAILED RISK ASSESSMENT")
            print(f"{'='*60}")
            
            top_citizens = self.health_features.nlargest(top_n, 'composite_anomaly_score')
            
            for idx, row in top_citizens.iterrows():
                citizen_id = row['CitizenID']
                print(f"\n--- Analyzing {citizen_id} ---")
                
                health_dict = row.to_dict()
                
                mobility_row = self.mobility_features[
                    self.mobility_features['user_id'] == citizen_id
                ]
                mobility_dict = mobility_row.iloc[0].to_dict() if len(mobility_row) > 0 else {}
                
                persona = self.personas.get(citizen_id, "No persona available")
                user_profile = self.users.get(citizen_id)
                user_dict = {
                    'birth_year': user_profile.birth_year,
                    'job': user_profile.job,
                    'city': user_profile.city,
                } if user_profile else {}
                
                anomaly_analysis = self.anomaly_detector.analyze_citizen(
                    session_id=session_id,
                    citizen_id=citizen_id,
                    health_features=health_dict,
                    persona=persona,
                )
                
                pattern_analysis = self.pattern_analyzer.analyze_mobility_patterns(
                    session_id=session_id,
                    citizen_id=citizen_id,
                    mobility_features=mobility_dict,
                    health_features=health_dict,
                    persona=persona,
                )
                
                risk_assessment = self.risk_assessor.assess_individual_risk(
                    session_id=session_id,
                    citizen_id=citizen_id,
                    anomaly_analysis=anomaly_analysis['analysis'],
                    pattern_analysis=pattern_analysis,
                    persona=persona,
                    user_profile=user_dict,
                )
                
                print(f"\n**RISK ASSESSMENT FOR {citizen_id}:**")
                print(risk_assessment)
                
                results['detailed_assessments'].append({
                    'citizen_id': citizen_id,
                    'anomaly_score': row['composite_anomaly_score'],
                    'anomaly_analysis': anomaly_analysis,
                    'pattern_analysis': pattern_analysis,
                    'risk_assessment': risk_assessment,
                })
        
        print(f"\n{'='*60}")
        print("PHASE 4: INTERVENTION PRIORITIZATION")
        print(f"{'='*60}")
        
        citizen_summaries = []
        for assessment in results['detailed_assessments']:
            citizen_summaries.append({
                'citizen_id': assessment['citizen_id'],
                'anomaly_score': f"{assessment['anomaly_score']:.2f}",
                'key_issues': assessment['risk_assessment'][:200],
            })
        
        prioritization = self.risk_assessor.prioritize_interventions(
            session_id=session_id,
            citizen_assessments=citizen_summaries,
        )
        
        print(prioritization)
        results['intervention_prioritization'] = prioritization
        
        return results
    
    def generate_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a comprehensive report from analysis results."""
        
        report = f"""
{'='*80}
HEALTH MONITORING SYSTEM - COMPREHENSIVE ANALYSIS REPORT
{'='*80}

EXECUTIVE SUMMARY
-----------------
This report presents findings from a multi-agent analysis system that evaluated
citizen health data using anomaly detection, behavioral pattern analysis, and
risk assessment methodologies.

METHODOLOGY
-----------
1. Data Loading: User profiles, health status, location tracking
2. Feature Engineering: Trend analysis, mobility metrics, anomaly scoring
3. Anomaly Detection: AI-powered identification of concerning patterns
4. Pattern Analysis: Behavioral and mobility pattern recognition
5. Risk Assessment: Comprehensive risk evaluation and prioritization

FINDINGS
--------

{analysis_results.get('batch_anomaly_analysis', 'N/A')}

COHORT ANALYSIS
---------------

{analysis_results.get('cohort_pattern_analysis', 'N/A')}

DETAILED ASSESSMENTS
--------------------
"""
        
        for idx, assessment in enumerate(analysis_results.get('detailed_assessments', []), 1):
            report += f"""
Citizen {idx}: {assessment['citizen_id']}
Anomaly Score: {assessment['anomaly_score']:.2f}

{assessment['risk_assessment']}

{'-'*80}
"""
        
        report += f"""

INTERVENTION PRIORITIZATION
---------------------------

{analysis_results.get('intervention_prioritization', 'N/A')}

{'='*80}
END OF REPORT
{'='*80}
"""
        
        return report
