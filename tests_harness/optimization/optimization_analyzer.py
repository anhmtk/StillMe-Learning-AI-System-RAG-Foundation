#!/usr/bin/env python3
"""
Enhanced Optimization Analyzer - Advanced analysis with SLO monitoring, trends, and interactive reports
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
from datetime import datetime
import subprocess
import sys

# Try to import optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# Import our new modules
from .data_loader import DataLoader
from .slo_policy import SLOPolicyManager, AlertLevel

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
    """Enhanced optimization analyzer with SLO monitoring, trends, and interactive reports"""
    
    def __init__(self, reports_dir: str = "reports", slo_policy_path: str = "slo_policy.yaml"):
        self.reports_dir = Path(reports_dir)
        self.slo_policy_path = Path(slo_policy_path)
        self.data_loader = DataLoader(str(self.reports_dir), str(self.slo_policy_path))
        self.slo_manager = SLOPolicyManager(self.data_loader.get_slo_policy())
        self.recommendations: List[OptimizationRecommendation] = []
        self.trend_data: List[Dict[str, Any]] = []
        self.current_run_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ")
        
    def analyze_reports(self, since_days: int = 7) -> Dict[str, Any]:
        """Enhanced analysis with SLO monitoring, trends, and comprehensive reporting"""
        logger.info("🔍 Starting enhanced analysis with SLO monitoring...")
        
        # Load all reports with validation
        reports = self.data_loader.load_all_reports()
        
        # Filter reports by date if specified
        if since_days > 0:
            cutoff_date = datetime.now().timestamp() - (since_days * 24 * 3600)
            reports = [r for r in reports if self._parse_run_id_timestamp(r.get('run_id', '')) >= cutoff_date]
        
        if not reports:
            logger.warning("No reports found for analysis")
            return self._create_empty_analysis()
        
        # Get latest report for detailed analysis
        latest_report = reports[0]
        
        # Evaluate SLOs
        slo_alerts = self.slo_manager.evaluate_slos(latest_report)
        slo_status, slo_message = self.slo_manager.get_overall_slo_status()
        
        # Analyze trends
        trend_analysis = self._analyze_trends(reports)
        
        # Get mode from environment
        mode = "offline" if os.getenv('OFFLINE_MODE', 'false').lower() == 'true' else "online"
        
        # Generate comprehensive analysis with new schema
        analysis = {
            "run_id": self.current_run_id,
            "git_sha": self._get_git_sha(),
            "mode": mode,
            "model_matrix": latest_report.get('model_matrix', {}),
            "prices_version": latest_report.get('prices_version', 'v1'),
            "dataset_info": self._get_dataset_info(reports),
            "overall_score": self._calculate_overall_score(reports),
            "evaluations": self._get_evaluations_dict(reports),
            "security": self._get_security_dict(reports),
            "model_selection": self._get_model_selection_dict(reports),
            "slo_status": slo_status,
            "slo_message": slo_message,
            "slo_alerts": [self._alert_to_dict(alert) for alert in slo_alerts],
            "alert_summary": self.slo_manager.get_alert_summary(),
            "failed_slos": self.slo_manager.get_failed_slos(),
            "overall_performance": self._analyze_overall_performance(reports),
            "trend_analysis": trend_analysis,
            "persona_analysis": self._analyze_persona_performance(reports),
            "safety_analysis": self._analyze_safety_performance(reports),
            "translation_analysis": self._analyze_translation_performance(reports),
            "efficiency_analysis": self._analyze_efficiency_performance(reports),
            "agentdev_analysis": self._analyze_agentdev_performance(reports),
            "model_selection_analysis": self._analyze_model_selection(reports),
            "security_analysis": self._analyze_security_performance(reports),
            "failure_analysis": self._analyze_failures(reports),
            "recommendations": self._generate_enhanced_recommendations(reports, slo_alerts),
            "action_items": self._get_action_items(self.slo_manager.get_failed_slos())
        }
        
        # Create enhanced reports
        self._create_enhanced_optimization_report(analysis)
        
        return analysis
    
    def _parse_run_id_timestamp(self, run_id: str) -> float:
        """Parse run_id to timestamp"""
        try:
            # Format: 2025-09-17T12-00-00Z
            dt = datetime.strptime(run_id, "%Y-%m-%dT%H-%M-%SZ")
            return dt.timestamp()
        except:
            return 0.0
    
    def _get_git_sha(self) -> str:
        """Get current git SHA"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=Path.cwd())
            return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def _calculate_overall_score(self, reports: List[Dict[str, Any]]) -> float:
        """Tính overall score từ các reports"""
        if not reports:
            return 0.0
        
        latest_report = reports[0]
        evaluations = latest_report.get('evaluations', {})
        
        scores = []
        for category in ['persona', 'safety', 'translation', 'efficiency', 'agentdev']:
            if category in evaluations and 'average_score' in evaluations[category]:
                scores.append(evaluations[category]['average_score'])
        
        return sum(scores) / len(scores) if scores else 0.0

    def _get_evaluations_dict(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lấy evaluations dict từ latest report"""
        if not reports:
            return {}
        
        latest_report = reports[0]
        return latest_report.get('evaluations', {})

    def _get_security_dict(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lấy security dict từ latest report"""
        if not reports:
            return {"sandbox_egress_blocked": False, "attack_block_rates": {}}
        
        latest_report = reports[0]
        return latest_report.get('security', {"sandbox_egress_blocked": False, "attack_block_rates": {}})

    def _get_model_selection_dict(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lấy model selection dict từ latest report"""
        if not reports:
            return {"confusion_matrix": [], "overall_accuracy": 0.0}
        
        latest_report = reports[0]
        return latest_report.get('model_selection', {"confusion_matrix": [], "overall_accuracy": 0.0})

    def _get_action_items(self, failed_slos: List[str]) -> List[str]:
        """Lấy action items dựa trên failed SLOs"""
        action_items = []
        
        # Load SLO policy để lấy action map
        try:
            slo_policy = self.slo_manager.load_policy()
            action_map = slo_policy.get('action_map', {})
            
            for failed_slo in failed_slos:
                # Parse SLO key (e.g., "performance.persona.min_score" -> "persona")
                parts = failed_slo.split('.')
                if len(parts) >= 2:
                    category = parts[1]  # persona, safety, etc.
                    if category in action_map:
                        modules = action_map[category].get('modules', [])
                        action_items.extend(modules)
        except Exception as e:
            logger.warning(f"Could not load action map: {e}")
        
        return list(set(action_items))  # Remove duplicates
    
    def _get_dataset_info(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get dataset information from reports"""
        total_samples = 0
        seed_samples = 0
        augmented_samples = 0
        
        for report in reports:
            # This would be extracted from actual report data
            # For now, use mock data
            total_samples += 100
            seed_samples += 10
            augmented_samples += 90
        
        return {
            "total_samples": total_samples,
            "seed_samples": seed_samples,
            "augmented_samples": augmented_samples,
            "dedup_ratio": 0.95 if total_samples > 0 else 0.0
        }
    
    def _alert_to_dict(self, alert) -> Dict[str, Any]:
        """Convert SLOAlert to dictionary"""
        return {
            "level": alert.level.value,
            "metric": alert.metric,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "impact": alert.impact,
            "recommendation": alert.recommendation
        }
    
    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis when no reports found"""
        return {
            "run_id": self.current_run_id,
            "git_sha": self._get_git_sha(),
            "model_matrix": {},
            "prices_version": "v1",
            "dataset_info": {"total_samples": 0, "seed_samples": 0, "augmented_samples": 0, "dedup_ratio": 0.0},
            "slo_status": False,
            "slo_message": "No data available",
            "slo_alerts": [],
            "alert_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "pass": 0},
            "failed_slos": [],
            "overall_performance": {"average_score": 0.0, "trend": "unknown"},
            "trend_analysis": {},
            "persona_analysis": {"average_score": 0.0, "issues": []},
            "safety_analysis": {"average_score": 0.0, "critical_issues": []},
            "translation_analysis": {"average_score": 0.0, "language_issues": []},
            "efficiency_analysis": {"average_score": 0.0, "performance_issues": []},
            "agentdev_analysis": {"average_score": 0.0, "integration_issues": []},
            "model_selection_analysis": {"confusion_matrix": []},
            "security_analysis": {"sandbox_breaches": 0, "attack_block_rates": {}},
            "failure_analysis": {"total_failures": 0, "by_category": {}},
            "recommendations": []
        }
    
    def _analyze_trends(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends across multiple reports"""
        if len(reports) < 2:
            return {"trend_available": False, "message": "Need at least 2 reports for trend analysis"}
        
        # Extract trend data
        trend_data = []
        for report in reports:
            evaluations = report.get('evaluations', {})
            trend_data.append({
                "run_id": report.get('run_id', ''),
                "overall_score": report.get('overall_score', 0.0),
                "persona_score": evaluations.get('persona', {}).get('average_score', 0.0),
                "safety_score": evaluations.get('safety', {}).get('average_score', 0.0),
                "translation_score": evaluations.get('translation', {}).get('average_score', 0.0),
                "efficiency_score": evaluations.get('efficiency', {}).get('average_score', 0.0),
                "agentdev_score": evaluations.get('agentdev', {}).get('average_score', 0.0),
                "p50_latency": evaluations.get('efficiency', {}).get('p50_latency', 0.0),
                "p95_latency": evaluations.get('efficiency', {}).get('p95_latency', 0.0),
                "token_saving": evaluations.get('efficiency', {}).get('token_saving_pct', 0.0)
            })
        
        # Calculate trends
        if len(trend_data) >= 2:
            latest = trend_data[0]
            previous = trend_data[1]
            
            trends = {}
            for key in ['overall_score', 'persona_score', 'safety_score', 'translation_score', 'efficiency_score', 'agentdev_score']:
                if key in latest and key in previous:
                    change = latest[key] - previous[key]
                    trends[key] = {
                        "change": change,
                        "direction": "improving" if change > 0 else "declining" if change < 0 else "stable",
                        "percentage": (change / previous[key] * 100) if previous[key] > 0 else 0
                    }
        
        return {
            "trend_available": True,
            "data_points": len(trend_data),
            "trends": trends,
            "raw_data": trend_data
        }
    
    def _analyze_model_selection(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze model selection performance"""
        confusion_matrix = []
        model_accuracy = {}
        
        for report in reports:
            model_selection = report.get('model_selection', {})
            matrix = model_selection.get('confusion_matrix', [])
            confusion_matrix.extend(matrix)
        
        # Analyze confusion matrix
        correct_selections = 0
        total_selections = len(confusion_matrix)
        
        for entry in confusion_matrix:
            if len(entry) >= 3 and entry[2]:  # Correct selection
                correct_selections += 1
        
        overall_accuracy = correct_selections / total_selections if total_selections > 0 else 0.0
        
        return {
            "confusion_matrix": confusion_matrix,
            "overall_accuracy": overall_accuracy,
            "total_selections": total_selections,
            "correct_selections": correct_selections
        }
    
    def _analyze_security_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security performance"""
        sandbox_breaches = 0
        attack_block_rates = {}
        
        for report in reports:
            security = report.get('security', {})
            
            if not security.get('sandbox_egress_blocked', False):
                sandbox_breaches += 1
            
            attacks = security.get('attacks', {})
            for attack_type, attack_data in attacks.items():
                blocked = attack_data.get('blocked', 0)
                total = attack_data.get('total', 0)
                
                if attack_type not in attack_block_rates:
                    attack_block_rates[attack_type] = {"blocked": 0, "total": 0}
                
                attack_block_rates[attack_type]["blocked"] += blocked
                attack_block_rates[attack_type]["total"] += total
        
        # Calculate block rates
        for attack_type in attack_block_rates:
            data = attack_block_rates[attack_type]
            if data["total"] > 0:
                data["block_rate"] = data["blocked"] / data["total"]
            else:
                data["block_rate"] = 0.0
        
        return {
            "sandbox_breaches": sandbox_breaches,
            "attack_block_rates": attack_block_rates,
            "security_score": 1.0 - (sandbox_breaches / len(reports)) if reports else 0.0
        }
    
    def _analyze_failures(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze failure patterns"""
        total_failures = 0
        by_category = {}
        
        for report in reports:
            failures = report.get('failures', [])
            total_failures += len(failures)
            
            for failure in failures:
                category = failure.get('reason', 'unknown')
                if category not in by_category:
                    by_category[category] = 0
                by_category[category] += 1
        
        return {
            "total_failures": total_failures,
            "by_category": by_category,
            "failure_rate": total_failures / len(reports) if reports else 0.0
        }
    
    def _generate_enhanced_recommendations(self, reports: List[Dict[str, Any]], slo_alerts: List) -> List[Dict[str, Any]]:
        """Generate enhanced recommendations based on SLO alerts and analysis"""
        recommendations = []
        action_map = self.data_loader.get_action_map()
        
        # Convert SLO alerts to recommendations
        for alert in slo_alerts:
            if alert.level in [AlertLevel.CRITICAL, AlertLevel.HIGH]:
                category = alert.metric.split('_')[0]  # Extract category from metric
                action_info = action_map.get(category, {})
                
                recommendations.append({
                    "category": category,
                    "priority": alert.level.value,
                    "title": f"Fix {alert.metric.replace('_', ' ').title()}",
                    "description": alert.impact,
                    "current_score": alert.current_value,
                    "target_score": alert.threshold,
                    "improvement_potential": abs(alert.threshold - alert.current_value),
                    "action_items": action_info.get('modules', []),
                    "expected_impact": alert.recommendation,
                    "effort": action_info.get('effort', 'M')
                })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))
        
        return recommendations
    
    def _create_enhanced_optimization_report(self, analysis: Dict[str, Any]) -> None:
        """Create enhanced optimization report with interactive charts"""
        # Create JSON report
        json_path = self.reports_dir / "optimization_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Enhanced JSON report saved: {json_path}")
        
        # Create HTML report
        html_path = self.reports_dir / "optimization_report.html"
        self._create_interactive_html_report(analysis, html_path)
        
        logger.info(f"✅ Enhanced HTML report saved: {html_path}")
    
    def _create_interactive_html_report(self, analysis: Dict[str, Any], html_path: Path) -> None:
        """Create interactive HTML report with Plotly charts"""
        if HAS_PLOTLY:
            html_content = self._generate_plotly_html(analysis)
        else:
            html_content = self._generate_static_html(analysis)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_plotly_html(self, analysis: Dict[str, Any]) -> str:
        """Generate HTML with Plotly interactive charts"""
        # Create trend charts
        trend_charts = self._create_trend_charts(analysis)
        
        # Create performance charts
        performance_charts = self._create_performance_charts(analysis)
        
        # Create SLO status chart
        slo_chart = self._create_slo_status_chart(analysis)
        
        # Create confusion matrix
        confusion_chart = self._create_confusion_matrix_chart(analysis)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe AI - Enhanced Optimization Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
        .slo-status {{ text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; }}
        .slo-pass {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .slo-fail {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .chart-container {{ margin: 20px 0; }}
        .alert {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .alert-critical {{ background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }}
        .alert-high {{ background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }}
        .alert-medium {{ background: #d1ecf1; color: #0c5460; border-left: 4px solid #17a2b8; }}
        .recommendation {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
        .priority-critical {{ border-left-color: #e74c3c; }}
        .priority-high {{ border-left-color: #f39c12; }}
        .priority-medium {{ border-left-color: #3498db; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; }}
        .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .table th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 StillMe AI - Enhanced Optimization Report</h1>
            <p>Run ID: {analysis.get('run_id', 'unknown')} | Git SHA: {analysis.get('git_sha', 'unknown')}</p>
            <p>Model Matrix: {', '.join([f"{k}: {v}" for k, v in analysis.get('model_matrix', {}).items()])}</p>
        </div>
        
        <div class="slo-status {'slo-pass' if analysis.get('slo_status', False) else 'slo-fail'}">
            <h2>SLO Status: {analysis.get('slo_message', 'Unknown')}</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('alert_summary', {}).get('critical', 0)}</div>
                    <div class="metric-label">Critical Alerts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('alert_summary', {}).get('high', 0)}</div>
                    <div class="metric-label">High Priority</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('alert_summary', {}).get('medium', 0)}</div>
                    <div class="metric-label">Medium Priority</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('dataset_info', {}).get('total_samples', 0)}</div>
                    <div class="metric-label">Total Samples</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Performance Trends</h2>
            <div class="chart-container" id="trend-chart"></div>
        </div>
        
        <div class="section">
            <h2>🎯 Performance Breakdown</h2>
            <div class="chart-container" id="performance-chart"></div>
        </div>
        
        <div class="section">
            <h2>🛡️ SLO Status Overview</h2>
            <div class="chart-container" id="slo-chart"></div>
        </div>
        
        <div class="section">
            <h2>🤖 Model Selection Confusion Matrix</h2>
            <div class="chart-container" id="confusion-chart"></div>
        </div>
        
        <div class="section">
            <h2>🚨 SLO Alerts</h2>
        """
        
        # Add alerts
        for alert in analysis.get('slo_alerts', []):
            alert_class = f"alert-{alert.get('level', 'medium')}"
            html_content += f"""
            <div class="alert {alert_class}">
                <strong>{alert.get('metric', 'Unknown').replace('_', ' ').title()}</strong><br>
                Current: {alert.get('current_value', 'N/A')} | Threshold: {alert.get('threshold', 'N/A')}<br>
                Impact: {alert.get('impact', 'No impact specified')}<br>
                Recommendation: {alert.get('recommendation', 'No recommendation')}
            </div>
            """
        
        html_content += """
        </div>
        
        <div class="section">
            <h2>🎯 Optimization Recommendations</h2>
        """
        
        # Add recommendations
        for rec in analysis.get('recommendations', []):
            priority_class = f"priority-{rec.get('priority', 'medium')}"
            html_content += f"""
            <div class="recommendation {priority_class}">
                <h3>{rec.get('title', 'Unknown')} <span style="color: #e74c3c;">[{rec.get('priority', 'medium').upper()}]</span></h3>
                <p><strong>Description:</strong> {rec.get('description', 'No description')}</p>
                <p><strong>Current Score:</strong> {rec.get('current_score', 0):.2f} → <strong>Target:</strong> {rec.get('target_score', 0):.2f}</p>
                <p><strong>Effort:</strong> {rec.get('effort', 'M')} | <strong>Impact:</strong> {rec.get('expected_impact', 'No impact specified')}</p>
                <div class="action-items">
                    <strong>Action Items:</strong>
                    <ul>
            """
            for item in rec.get('action_items', []):
                html_content += f"<li>{item}</li>"
            html_content += """
                    </ul>
                </div>
            </div>
            """
        
        html_content += """
        </div>
        
        <div class="section">
            <h2>📋 SLO Checklist</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>SLO Metric</th>
                        <th>Target</th>
                        <th>Current</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add SLO checklist
        slo_checks = [
            ("Persona Score", "≥ 0.80", f"{analysis.get('persona_analysis', {}).get('average_score', 0):.2f}"),
            ("Safety Score", "≥ 0.90", f"{analysis.get('safety_analysis', {}).get('average_score', 0):.2f}"),
            ("Translation Score", "≥ 0.85", f"{analysis.get('translation_analysis', {}).get('average_score', 0):.2f}"),
            ("AgentDev Score", "≥ 0.80", f"{analysis.get('agentdev_analysis', {}).get('average_score', 0):.2f}"),
            ("P95 Latency", "≤ 2.0x baseline", f"{analysis.get('efficiency_analysis', {}).get('p95_latency', 0):.2f}s"),
            ("Token Saving", "≥ 20%", f"{analysis.get('efficiency_analysis', {}).get('token_saving_pct', 0)*100:.1f}%"),
            ("Jailbreak Block Rate", "≥ 90%", f"{analysis.get('safety_analysis', {}).get('jailbreak_block_rate', 0)*100:.1f}%"),
            ("Sandbox Egress", "Blocked", "✅" if analysis.get('security_analysis', {}).get('sandbox_breaches', 1) == 0 else "❌")
        ]
        
        for metric, target, current in slo_checks:
            # Simple pass/fail logic (would be more sophisticated in real implementation)
            status = "✅" if "≥" in target and float(current.replace('%', '').replace('s', '')) >= float(target.replace('≥', '').replace('%', '')) else "❌"
            html_content += f"""
                    <tr>
                        <td>{metric}</td>
                        <td>{target}</td>
                        <td>{current}</td>
                        <td>{status}</td>
                    </tr>
            """
        
        html_content += f"""
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Trend Chart
        {trend_charts}
        
        // Performance Chart
        {performance_charts}
        
        // SLO Status Chart
        {slo_chart}
        
        // Confusion Matrix Chart
        {confusion_chart}
    </script>
</body>
</html>
        """
        
        return html_content
    
    def _create_trend_charts(self, analysis: Dict[str, Any]) -> str:
        """Create trend charts JavaScript"""
        trend_data = analysis.get('trend_analysis', {})
        if not trend_data.get('trend_available', False):
            return "// No trend data available"
        
        raw_data = trend_data.get('raw_data', [])
        if len(raw_data) < 2:
            return "// Insufficient data for trend analysis"
        
        # Create trend chart data
        run_ids = [d['run_id'] for d in raw_data]
        scores = {
            'Overall': [d['overall_score'] for d in raw_data],
            'Persona': [d['persona_score'] for d in raw_data],
            'Safety': [d['safety_score'] for d in raw_data],
            'Translation': [d['translation_score'] for d in raw_data],
            'Efficiency': [d['efficiency_score'] for d in raw_data],
            'AgentDev': [d['agentdev_score'] for d in raw_data]
        }
        
        js_code = """
        var trendData = ["""
        
        for name, values in scores.items():
            js_code += f"""
            {{
                x: {run_ids},
                y: {values},
                type: 'scatter',
                mode: 'lines+markers',
                name: '{name}',
                line: {{ width: 3 }}
            }},"""
        
        js_code += """
        ];
        
        var trendLayout = {
            title: 'Performance Trends Over Time',
            xaxis: { title: 'Run ID' },
            yaxis: { title: 'Score', range: [0, 1] },
            hovermode: 'closest'
        };
        
        Plotly.newPlot('trend-chart', trendData, trendLayout);
        """
        
        return js_code
    
    def _create_performance_charts(self, analysis: Dict[str, Any]) -> str:
        """Create performance breakdown charts"""
        categories = ['Persona', 'Safety', 'Translation', 'Efficiency', 'AgentDev']
        scores = [
            analysis.get('persona_analysis', {}).get('average_score', 0),
            analysis.get('safety_analysis', {}).get('average_score', 0),
            analysis.get('translation_analysis', {}).get('average_score', 0),
            analysis.get('efficiency_analysis', {}).get('average_score', 0),
            analysis.get('agentdev_analysis', {}).get('average_score', 0)
        ]
        
        js_code = f"""
        var performanceData = [{{
            x: {categories},
            y: {scores},
            type: 'bar',
            marker: {{
                color: {scores},
                colorscale: 'RdYlGn',
                cmin: 0,
                cmax: 1
            }}
        }}];
        
        var performanceLayout = {{
            title: 'Performance Breakdown by Category',
            xaxis: {{ title: 'Category' }},
            yaxis: {{ title: 'Score', range: [0, 1] }}
        }};
        
        Plotly.newPlot('performance-chart', performanceData, performanceLayout);
        """
        
        return js_code
    
    def _create_slo_status_chart(self, analysis: Dict[str, Any]) -> str:
        """Create SLO status chart"""
        alert_summary = analysis.get('alert_summary', {})
        
        js_code = f"""
        var sloData = [{{
            labels: ['Critical', 'High', 'Medium', 'Low', 'Pass'],
            values: [{alert_summary.get('critical', 0)}, {alert_summary.get('high', 0)}, {alert_summary.get('medium', 0)}, {alert_summary.get('low', 0)}, {alert_summary.get('pass', 0)}],
            type: 'pie',
            marker: {{
                colors: ['#dc3545', '#ffc107', '#17a2b8', '#6c757d', '#28a745']
            }}
        }}];
        
        var sloLayout = {{
            title: 'SLO Alert Distribution'
        }};
        
        Plotly.newPlot('slo-chart', sloData, sloLayout);
        """
        
        return js_code
    
    def _create_confusion_matrix_chart(self, analysis: Dict[str, Any]) -> str:
        """Create confusion matrix chart"""
        model_analysis = analysis.get('model_selection_analysis', {})
        accuracy = model_analysis.get('overall_accuracy', 0)
        total = model_analysis.get('total_selections', 0)
        correct = model_analysis.get('correct_selections', 0)
        
        js_code = f"""
        var confusionData = [{{
            labels: ['Correct', 'Incorrect'],
            values: [{correct}, {total - correct}],
            type: 'pie',
            marker: {{
                colors: ['#28a745', '#dc3545']
            }}
        }}];
        
        var confusionLayout = {{
            title: `Model Selection Accuracy: ${{(100 * {accuracy}).toFixed(1)}}%`
        }};
        
        Plotly.newPlot('confusion-chart', confusionData, confusionLayout);
        """
        
        return js_code
    
    def _generate_static_html(self, analysis: Dict[str, Any]) -> str:
        """Generate static HTML without Plotly (fallback)"""
        # Similar to the Plotly version but with static content
        return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe AI - Optimization Report (Static)</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
        .slo-status {{ text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; }}
        .slo-pass {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .slo-fail {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; }}
        .alert {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .alert-critical {{ background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }}
        .alert-high {{ background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }}
        .alert-medium {{ background: #d1ecf1; color: #0c5460; border-left: 4px solid #17a2b8; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 StillMe AI - Optimization Report</h1>
            <p>Run ID: {analysis.get('run_id', 'unknown')} | Git SHA: {analysis.get('git_sha', 'unknown')}</p>
            <p><strong>Note:</strong> Interactive charts require Plotly. Install with: pip install plotly</p>
        </div>
        
        <div class="slo-status {'slo-pass' if analysis.get('slo_status', False) else 'slo-fail'}">
            <h2>SLO Status: {analysis.get('slo_message', 'Unknown')}</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('alert_summary', {}).get('critical', 0)}</div>
                    <div class="metric-label">Critical Alerts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('alert_summary', {}).get('high', 0)}</div>
                    <div class="metric-label">High Priority</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('alert_summary', {}).get('medium', 0)}</div>
                    <div class="metric-label">Medium Priority</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('dataset_info', {}).get('total_samples', 0)}</div>
                    <div class="metric-label">Total Samples</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Performance Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('persona_analysis', {}).get('average_score', 0):.2f}</div>
                    <div class="metric-label">Persona Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('safety_analysis', {}).get('average_score', 0):.2f}</div>
                    <div class="metric-label">Safety Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('translation_analysis', {}).get('average_score', 0):.2f}</div>
                    <div class="metric-label">Translation Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('efficiency_analysis', {}).get('average_score', 0):.2f}</div>
                    <div class="metric-label">Efficiency Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{analysis.get('agentdev_analysis', {}).get('average_score', 0):.2f}</div>
                    <div class="metric-label">AgentDev Score</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🚨 SLO Alerts</h2>
        """
        
        # Add alerts
        for alert in analysis.get('slo_alerts', []):
            alert_class = f"alert-{alert.get('level', 'medium')}"
            html_content += f"""
            <div class="alert {alert_class}">
                <strong>{alert.get('metric', 'Unknown').replace('_', ' ').title()}</strong><br>
                Current: {alert.get('current_value', 'N/A')} | Threshold: {alert.get('threshold', 'N/A')}<br>
                Impact: {alert.get('impact', 'No impact specified')}<br>
                Recommendation: {alert.get('recommendation', 'No recommendation')}
            </div>
            """
        
        html_content += """
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
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
    
    def _analyze_overall_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu suất tổng thể"""
        overall_scores = []
        
        for report_data in reports:
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
    
    def _analyze_persona_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu suất persona"""
        persona_scores = []
        
        for report_data in reports:
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
    
    def _analyze_safety_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu suất safety"""
        safety_scores = []
        
        for report_data in reports:
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
    
    def _analyze_translation_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu suất translation"""
        translation_scores = []
        
        for report_data in reports:
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
    
    def _analyze_efficiency_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu suất efficiency"""
        efficiency_scores = []
        latencies = []
        token_costs = []
        
        for report_data in reports:
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
    
    def _analyze_agentdev_performance(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích hiệu suất AgentDev"""
        agentdev_scores = []
        
        for report_data in reports:
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
    
    def _generate_recommendations(self, reports: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
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
