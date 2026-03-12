#!/usr/bin/env python3
"""
Health Monitoring System - Main Execution Script

This script orchestrates a multi-agent system to analyze citizen health data,
detect anomalies, identify behavioral patterns, and assess risks.
"""

import sys
from pathlib import Path

from config.settings import Settings
from tracing.langfuse_tracer import LangfuseTracer
from agents.orchestrator_agent import OrchestratorAgent


def main():
    """Run the health monitoring analysis system."""
    
    print("="*80)
    print("HEALTH MONITORING SYSTEM - MULTI-AGENT ANALYSIS")
    print("="*80)
    
    settings = Settings()
    tracer = LangfuseTracer(settings)
    
    session_id = tracer.generate_session_id()
    print(f"\nSession ID: {session_id}")
    print(f"Provider: {settings.provider}")
    print(f"Model: {settings.default_model_id}")
    
    orchestrator = OrchestratorAgent(settings, tracer)
    
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "input_sandbox/public_lev_1"
    
    print(f"\nData Directory: {data_dir}")
    
    try:
        print("\n" + "="*80)
        print("STEP 1: LOADING DATA")
        print("="*80)
        orchestrator.load_data(data_dir)
        
        print("\n" + "="*80)
        print("STEP 2: FEATURE ENGINEERING")
        print("="*80)
        orchestrator.engineer_features()
        
        print("\n" + "="*80)
        print("STEP 3: MULTI-AGENT ANALYSIS")
        print("="*80)
        
        results = orchestrator.analyze_all_citizens(
            session_id=session_id,
            top_n=5,
            detailed_analysis=True,
        )
        
        print("\n" + "="*80)
        print("STEP 4: GENERATING REPORT")
        print("="*80)
        
        report = orchestrator.generate_report(results)
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / f"health_analysis_report_{session_id}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nReport saved to: {report_file}")
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nView traces at: {settings.langfuse_host}")
        print(f"Session ID: {session_id}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        tracer.flush()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
