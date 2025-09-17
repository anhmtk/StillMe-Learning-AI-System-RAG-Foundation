#!/usr/bin/env python3
"""
Demo Optimization Analyzer - Chạy phân tích tối ưu hóa
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from optimization.optimization_analyzer import OptimizationAnalyzer

def main():
    """Demo optimization analyzer"""
    print("🚀 StillMe AI - Optimization Analyzer Demo")
    print("=" * 50)
    
    # Tạo analyzer
    analyzer = OptimizationAnalyzer()
    
    # Phân tích báo cáo
    print("🔍 Analyzing reports...")
    analysis = analyzer.analyze_reports()
    
    # Hiển thị kết quả
    print(f"\n📊 Overall Performance: {analysis['overall_performance']['average_score']:.2f}")
    print(f"🎯 Total Recommendations: {len(analysis['recommendations'])}")
    
    print(f"\n🔍 Performance Breakdown:")
    print(f"  Persona: {analysis['persona_analysis']['average_score']:.2f}")
    print(f"  Safety: {analysis['safety_analysis']['average_score']:.2f}")
    print(f"  Translation: {analysis['translation_analysis']['average_score']:.2f}")
    print(f"  Efficiency: {analysis['efficiency_analysis']['average_score']:.2f}")
    print(f"  AgentDev: {analysis['agentdev_analysis']['average_score']:.2f}")
    
    print(f"\n🎯 Top Recommendations:")
    for i, rec in enumerate(analysis['recommendations'][:3], 1):
        if isinstance(rec, dict):
            print(f"  {i}. [{rec.get('priority', 'MEDIUM').upper()}] {rec.get('title', 'Unknown')}")
            print(f"     Current: {rec.get('current_score', 0):.2f} → Target: {rec.get('target_score', 0):.2f}")
            print(f"     Impact: {rec.get('expected_impact', 'No impact specified')}")
        else:
            print(f"  {i}. [{rec.priority.upper()}] {rec.title}")
            print(f"     Current: {rec.current_score:.2f} → Target: {rec.target_score:.2f}")
            print(f"     Impact: {rec.expected_impact}")
        print()
    
    print("✅ Optimization analysis completed!")
    print("📄 Check reports/optimization_report.html for detailed report")

if __name__ == "__main__":
    main()
