#!/usr/bin/env python3
"""
Optimization Analyzer - Phân tích kết quả test và đưa ra gợi ý cải thiện
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime

# Try to import pandas, fallback to datetime
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationRecommendation:
    """Gợi ý tối ưu hóa"""
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    current_score: float
    target_score: float
    improvement_potential: float
    action_items: List[str]
    expected_impact: str

class OptimizationAnalyzer:
    """Phân tích kết quả test và đưa ra gợi ý cải thiện"""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.recommendations: List[OptimizationRecommendation] = []
        
    def analyze_reports(self) -> Dict[str, Any]:
        """Phân tích tất cả báo cáo và tạo gợi ý tối ưu"""
        logger.info("🔍 Bắt đầu phân tích báo cáo...")
        
        # Load tất cả báo cáo
        reports = self._load_all_reports()
        
        # Phân tích từng loại
        analysis = {
            "overall_performance": self._analyze_overall_performance(reports),
            "persona_analysis": self._analyze_persona_performance(reports),
            "safety_analysis": self._analyze_safety_performance(reports),
            "translation_analysis": self._analyze_translation_performance(reports),
            "efficiency_analysis": self._analyze_efficiency_performance(reports),
            "agentdev_analysis": self._analyze_agentdev_performance(reports),
            "recommendations": self._generate_recommendations(reports)
        }
        
        # Tạo báo cáo tối ưu
        self._create_optimization_report(analysis)
        
        return analysis
    
    def _load_all_reports(self) -> Dict[str, Any]:
        """Load tất cả báo cáo từ thư mục reports"""
        reports = {}
        
        # Load JSON reports
        for json_file in self.reports_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports[json_file.stem] = data
                    logger.info(f"✅ Loaded {json_file.name}")
            except Exception as e:
                logger.error(f"❌ Error loading {json_file}: {e}")
        
        return reports
    
    def _analyze_overall_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích hiệu suất tổng thể"""
        overall_scores = []
        
        for report_name, report_data in reports.items():
            if 'overall_score' in report_data:
                overall_scores.append(report_data['overall_score'])
        
        if not overall_scores:
            return {"average_score": 0.0, "trend": "unknown"}
        
        avg_score = sum(overall_scores) / len(overall_scores)
        
        return {
            "average_score": avg_score,
            "min_score": min(overall_scores),
            "max_score": max(overall_scores),
            "trend": "improving" if len(overall_scores) > 1 and overall_scores[-1] > overall_scores[0] else "stable"
        }
    
    def _analyze_persona_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích hiệu suất persona"""
        persona_scores = []
        
        for report_name, report_data in reports.items():
            if 'evaluations' in report_data and 'persona' in report_data['evaluations']:
                persona_scores.append(report_data['evaluations']['persona']['average_score'])
        
        if not persona_scores:
            return {"average_score": 0.0, "issues": []}
        
        avg_score = sum(persona_scores) / len(persona_scores)
        
        # Phân tích các vấn đề thường gặp
        issues = []
        if avg_score < 0.7:
            issues.append("Persona không nhất quán")
        if avg_score < 0.8:
            issues.append("Thiếu tính cá nhân hóa")
        
        return {
            "average_score": avg_score,
            "issues": issues,
            "recommendation": "Cần cải thiện PersonaMorph module"
        }
    
    def _analyze_safety_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích hiệu suất safety"""
        safety_scores = []
        
        for report_name, report_data in reports.items():
            if 'evaluations' in report_data and 'safety' in report_data['evaluations']:
                safety_scores.append(report_data['evaluations']['safety']['average_score'])
        
        if not safety_scores:
            return {"average_score": 0.0, "critical_issues": []}
        
        avg_score = sum(safety_scores) / len(safety_scores)
        
        # Phân tích các vấn đề bảo mật
        critical_issues = []
        if avg_score < 0.9:
            critical_issues.append("Cần tăng cường EthicalCore")
        if avg_score < 0.95:
            critical_issues.append("Cần cải thiện ContentIntegrityFilter")
        
        return {
            "average_score": avg_score,
            "critical_issues": critical_issues,
            "recommendation": "Ưu tiên cao: Cải thiện hệ thống bảo mật"
        }
    
    def _analyze_translation_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích hiệu suất translation"""
        translation_scores = []
        
        for report_name, report_data in reports.items():
            if 'evaluations' in report_data and 'translation' in report_data['evaluations']:
                translation_scores.append(report_data['evaluations']['translation']['average_score'])
        
        if not translation_scores:
            return {"average_score": 0.0, "language_issues": []}
        
        avg_score = sum(translation_scores) / len(translation_scores)
        
        # Phân tích các vấn đề ngôn ngữ
        language_issues = []
        if avg_score < 0.8:
            language_issues.append("Cần cải thiện NLLB model")
        if avg_score < 0.9:
            language_issues.append("Cần tối ưu Gemma translation")
        
        return {
            "average_score": avg_score,
            "language_issues": language_issues,
            "recommendation": "Cần cải thiện hệ thống translation"
        }
    
    def _analyze_efficiency_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích hiệu suất efficiency"""
        efficiency_scores = []
        latencies = []
        token_costs = []
        
        for report_name, report_data in reports.items():
            if 'evaluations' in report_data and 'efficiency' in report_data['evaluations']:
                eff_data = report_data['evaluations']['efficiency']
                efficiency_scores.append(eff_data['average_score'])
                latencies.append(eff_data.get('average_latency', 0))
                token_costs.append(eff_data.get('average_token_cost', 0))
        
        if not efficiency_scores:
            return {"average_score": 0.0, "performance_issues": []}
        
        avg_score = sum(efficiency_scores) / len(efficiency_scores)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        avg_token_cost = sum(token_costs) / len(token_costs) if token_costs else 0
        
        # Phân tích các vấn đề hiệu suất
        performance_issues = []
        if avg_latency > 5.0:
            performance_issues.append("Latency quá cao")
        if avg_token_cost > 1000:
            performance_issues.append("Token cost quá cao")
        if avg_score < 0.8:
            performance_issues.append("Cần tối ưu TokenOptimizer")
        
        return {
            "average_score": avg_score,
            "average_latency": avg_latency,
            "average_token_cost": avg_token_cost,
            "performance_issues": performance_issues,
            "recommendation": "Cần tối ưu hiệu suất và chi phí"
        }
    
    def _analyze_agentdev_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích hiệu suất AgentDev"""
        agentdev_scores = []
        
        for report_name, report_data in reports.items():
            if 'evaluations' in report_data and 'agentdev' in report_data['evaluations']:
                agentdev_scores.append(report_data['evaluations']['agentdev']['average_score'])
        
        if not agentdev_scores:
            return {"average_score": 0.0, "integration_issues": []}
        
        avg_score = sum(agentdev_scores) / len(agentdev_scores)
        
        # Phân tích các vấn đề tích hợp
        integration_issues = []
        if avg_score < 0.7:
            integration_issues.append("AgentDev integration không ổn định")
        if avg_score < 0.8:
            integration_issues.append("Cần cải thiện Advanced Decision Making")
        
        return {
            "average_score": avg_score,
            "integration_issues": integration_issues,
            "recommendation": "Cần cải thiện AgentDev integration"
        }
    
    def _generate_recommendations(self, reports: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Tạo gợi ý tối ưu hóa"""
        recommendations = []
        
        # Phân tích từng loại và tạo gợi ý
        overall_analysis = self._analyze_overall_performance(reports)
        persona_analysis = self._analyze_persona_performance(reports)
        safety_analysis = self._analyze_safety_performance(reports)
        translation_analysis = self._analyze_translation_performance(reports)
        efficiency_analysis = self._analyze_efficiency_performance(reports)
        agentdev_analysis = self._analyze_agentdev_performance(reports)
        
        # Gợi ý Persona
        if persona_analysis['average_score'] < 0.8:
            recommendations.append(OptimizationRecommendation(
                category="Persona",
                priority="high",
                title="Cải thiện PersonaMorph Module",
                description="Persona không nhất quán, cần tăng cường tính cá nhân hóa",
                current_score=persona_analysis['average_score'],
                target_score=0.9,
                improvement_potential=0.9 - persona_analysis['average_score'],
                action_items=[
                    "Tăng cường PersonaMorph weight",
                    "Cải thiện user preference detection",
                    "Thêm persona templates"
                ],
                expected_impact="Tăng 20% user satisfaction"
            ))
        
        # Gợi ý Safety
        if safety_analysis['average_score'] < 0.95:
            recommendations.append(OptimizationRecommendation(
                category="Safety",
                priority="critical",
                title="Tăng cường EthicalCore",
                description="Cần cải thiện hệ thống bảo mật và lọc nội dung",
                current_score=safety_analysis['average_score'],
                target_score=0.98,
                improvement_potential=0.98 - safety_analysis['average_score'],
                action_items=[
                    "Tighten EthicalCore rules",
                    "Cải thiện ContentIntegrityFilter",
                    "Thêm real-time monitoring"
                ],
                expected_impact="Giảm 90% safety incidents"
            ))
        
        # Gợi ý Translation
        if translation_analysis['average_score'] < 0.85:
            recommendations.append(OptimizationRecommendation(
                category="Translation",
                priority="medium",
                title="Tối ưu Translation System",
                description="Cần cải thiện chất lượng translation",
                current_score=translation_analysis['average_score'],
                target_score=0.95,
                improvement_potential=0.95 - translation_analysis['average_score'],
                action_items=[
                    "Upgrade NLLB model to 1.3B",
                    "Tối ưu Gemma translation",
                    "Thêm language detection"
                ],
                expected_impact="Tăng 15% translation accuracy"
            ))
        
        # Gợi ý Efficiency
        if efficiency_analysis['average_score'] < 0.8:
            recommendations.append(OptimizationRecommendation(
                category="Efficiency",
                priority="high",
                title="Tối ưu Performance & Cost",
                description="Cần cải thiện hiệu suất và giảm chi phí",
                current_score=efficiency_analysis['average_score'],
                target_score=0.9,
                improvement_potential=0.9 - efficiency_analysis['average_score'],
                action_items=[
                    "Tối ưu TokenOptimizer",
                    "Implement caching",
                    "Reduce API calls"
                ],
                expected_impact="Giảm 30% cost, tăng 40% speed"
            ))
        
        # Gợi ý AgentDev
        if agentdev_analysis['average_score'] < 0.8:
            recommendations.append(OptimizationRecommendation(
                category="AgentDev",
                priority="medium",
                title="Cải thiện AgentDev Integration",
                description="Cần cải thiện tích hợp AgentDev",
                current_score=agentdev_analysis['average_score'],
                target_score=0.9,
                improvement_potential=0.9 - agentdev_analysis['average_score'],
                action_items=[
                    "Cải thiện Advanced Decision Making",
                    "Tối ưu Self-Learning Mechanism",
                    "Thêm error handling"
                ],
                expected_impact="Tăng 25% AgentDev reliability"
            ))
        
        return recommendations
    
    def _create_optimization_report(self, analysis: Dict[str, Any]) -> None:
        """Tạo báo cáo tối ưu hóa"""
        report_path = self.reports_dir / "optimization_report.json"
        
        # Convert recommendations to dict
        recommendations_dict = []
        for rec in analysis['recommendations']:
            recommendations_dict.append({
                "category": rec.category,
                "priority": rec.priority,
                "title": rec.title,
                "description": rec.description,
                "current_score": rec.current_score,
                "target_score": rec.target_score,
                "improvement_potential": rec.improvement_potential,
                "action_items": rec.action_items,
                "expected_impact": rec.expected_impact
            })
        
        # Tạo báo cáo chi tiết
        timestamp = pd.Timestamp.now().isoformat() if HAS_PANDAS else datetime.now().isoformat()
        report = {
            "timestamp": timestamp,
            "analysis": {
                "overall_performance": analysis['overall_performance'],
                "persona_analysis": analysis['persona_analysis'],
                "safety_analysis": analysis['safety_analysis'],
                "translation_analysis": analysis['translation_analysis'],
                "efficiency_analysis": analysis['efficiency_analysis'],
                "agentdev_analysis": analysis['agentdev_analysis'],
                "recommendations": recommendations_dict
            },
            "summary": {
                "total_recommendations": len(analysis['recommendations']),
                "high_priority": len([r for r in analysis['recommendations'] if r.priority == "high"]),
                "critical_priority": len([r for r in analysis['recommendations'] if r.priority == "critical"]),
                "overall_score": analysis['overall_performance']['average_score']
            }
        }
        
        # Save JSON report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Optimization report saved: {report_path}")
        
        # Tạo HTML report
        self._create_html_optimization_report(analysis)
    
    def _create_html_optimization_report(self, analysis: Dict[str, Any]) -> None:
        """Tạo báo cáo HTML tối ưu hóa"""
        html_path = self.reports_dir / "optimization_report.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StillMe AI - Optimization Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .section h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .recommendation {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
                .priority-high {{ border-left-color: #e74c3c; }}
                .priority-critical {{ border-left-color: #c0392b; background: #fdf2f2; }}
                .priority-medium {{ border-left-color: #f39c12; }}
                .score {{ font-weight: bold; color: #27ae60; }}
                .action-items {{ margin-top: 10px; }}
                .action-items li {{ margin: 5px 0; }}
                .summary {{ background: #ecf0f1; padding: 20px; border-radius: 5px; text-align: center; }}
                .metric {{ display: inline-block; margin: 0 20px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 StillMe AI - Optimization Report</h1>
                    <p>Phân tích hiệu suất và gợi ý cải thiện</p>
                </div>
                
                <div class="summary">
                    <div class="metric">
                        <div class="metric-value">{analysis['overall_performance']['average_score']:.2f}</div>
                        <div class="metric-label">Overall Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{len(analysis['recommendations'])}</div>
                        <div class="metric-label">Recommendations</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{len([r for r in analysis['recommendations'] if r.priority == "critical"])}</div>
                        <div class="metric-label">Critical Issues</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📊 Performance Analysis</h2>
                    <p><strong>Persona Score:</strong> <span class="score">{analysis['persona_analysis']['average_score']:.2f}</span></p>
                    <p><strong>Safety Score:</strong> <span class="score">{analysis['safety_analysis']['average_score']:.2f}</span></p>
                    <p><strong>Translation Score:</strong> <span class="score">{analysis['translation_analysis']['average_score']:.2f}</span></p>
                    <p><strong>Efficiency Score:</strong> <span class="score">{analysis['efficiency_analysis']['average_score']:.2f}</span></p>
                    <p><strong>AgentDev Score:</strong> <span class="score">{analysis['agentdev_analysis']['average_score']:.2f}</span></p>
                </div>
                
                <div class="section">
                    <h2>🎯 Optimization Recommendations</h2>
        """
        
        for rec in analysis['recommendations']:
            priority_class = f"priority-{rec.priority}"
            html_content += f"""
                    <div class="recommendation {priority_class}">
                        <h3>{rec.title} <span style="color: #e74c3c;">[{rec.priority.upper()}]</span></h3>
                        <p><strong>Mô tả:</strong> {rec.description}</p>
                        <p><strong>Current Score:</strong> <span class="score">{rec.current_score:.2f}</span> → <strong>Target:</strong> <span class="score">{rec.target_score:.2f}</span></p>
                        <p><strong>Improvement Potential:</strong> <span class="score">+{rec.improvement_potential:.2f}</span></p>
                        <p><strong>Expected Impact:</strong> {rec.expected_impact}</p>
                        <div class="action-items">
                            <strong>Action Items:</strong>
                            <ul>
            """
            for item in rec.action_items:
                html_content += f"<li>{item}</li>"
            html_content += """
                            </ul>
                        </div>
                    </div>
            """
        
        html_content += """
                </div>
                
                <div class="section">
                    <h2>📈 Next Steps</h2>
                    <ol>
                        <li>Ưu tiên các vấn đề <strong>CRITICAL</strong> và <strong>HIGH</strong></li>
                        <li>Implement các action items theo thứ tự ưu tiên</li>
                        <li>Chạy lại test suite sau mỗi cải thiện</li>
                        <li>Monitor performance metrics liên tục</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✅ HTML optimization report saved: {html_path}")

def main():
    """Demo optimization analyzer"""
    print("🚀 StillMe AI - Optimization Analyzer Demo")
    print("=" * 50)
    
    # Tạo analyzer
    analyzer = OptimizationAnalyzer()
    
    # Phân tích báo cáo
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
        print(f"  {i}. [{rec.priority.upper()}] {rec.title}")
        print(f"     Current: {rec.current_score:.2f} → Target: {rec.target_score:.2f}")
        print(f"     Impact: {rec.expected_impact}")
        print()
    
    print("✅ Optimization analysis completed!")
    print("📄 Check reports/optimization_report.html for detailed report")

if __name__ == "__main__":
    main()
