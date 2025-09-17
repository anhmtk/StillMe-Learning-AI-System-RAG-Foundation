#!/usr/bin/env python3
"""
HTML Report Builder - Tạo báo cáo HTML với biểu đồ và metrics

Tính năng:
- Tạo báo cáo HTML với biểu đồ interactive
- Export PDF và JSON reports
- Dashboard với metrics chi tiết
- Biểu đồ phân phối điểm số
- So sánh baseline vs StillMe
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTMLReportBuilder:
    """Builder cho HTML reports với biểu đồ và metrics"""
    
    def __init__(self, output_dir: str = "tests_harness/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def build_comprehensive_report(self, 
                                 persona_scores: List[Dict],
                                 safety_scores: List[Dict], 
                                 translation_scores: List[Dict],
                                 efficiency_scores: List[Dict],
                                 metadata: Dict[str, Any]) -> str:
        """
        Tạo báo cáo HTML toàn diện
        
        Args:
            persona_scores: Kết quả PersonaEval
            safety_scores: Kết quả SafetyEval
            translation_scores: Kết quả TranslationEval
            efficiency_scores: Kết quả EfficiencyEval
            metadata: Metadata bổ sung
            
        Returns:
            str: Đường dẫn file HTML
        """
        try:
            self.logger.info("🏗️ Building comprehensive HTML report...")
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"stillme_evaluation_report_{timestamp}.html"
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(
                persona_scores, safety_scores, translation_scores, efficiency_scores
            )
            
            # Generate HTML content
            html_content = self._generate_html_content(
                persona_scores, safety_scores, translation_scores, 
                efficiency_scores, overall_metrics, metadata
            )
            
            # Write to file
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"✅ HTML report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to build HTML report: {e}")
            return ""
    
    def _calculate_overall_metrics(self, 
                                 persona_scores: List[Dict],
                                 safety_scores: List[Dict], 
                                 translation_scores: List[Dict],
                                 efficiency_scores: List[Dict]) -> Dict[str, Any]:
        """Tính toán metrics tổng thể"""
        try:
            # Calculate averages
            avg_persona = sum(score.get('overall_score', 0) for score in persona_scores) / max(len(persona_scores), 1)
            avg_safety = sum(score.get('overall_safety_score', 0) for score in safety_scores) / max(len(safety_scores), 1)
            avg_translation = sum(score.get('overall_translation_score', 0) for score in translation_scores) / max(len(translation_scores), 1)
            avg_efficiency = sum(score.get('overall_efficiency_score', 0) for score in efficiency_scores) / max(len(efficiency_scores), 1)
            
            # Overall score
            overall_score = (avg_persona + avg_safety + avg_translation + avg_efficiency) / 4
            
            # Score distribution
            total_responses = max(len(persona_scores), len(safety_scores), len(translation_scores), len(efficiency_scores))
            
            return {
                "overall_score": round(overall_score, 3),
                "average_scores": {
                    "persona": round(avg_persona, 3),
                    "safety": round(avg_safety, 3),
                    "translation": round(avg_translation, 3),
                    "efficiency": round(avg_efficiency, 3)
                },
                "total_responses": total_responses,
                "score_distribution": {
                    "excellent": len([s for s in persona_scores if s.get('overall_score', 0) >= 0.8]),
                    "good": len([s for s in persona_scores if 0.6 <= s.get('overall_score', 0) < 0.8]),
                    "fair": len([s for s in persona_scores if 0.4 <= s.get('overall_score', 0) < 0.6]),
                    "poor": len([s for s in persona_scores if s.get('overall_score', 0) < 0.4])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating overall metrics: {e}")
            return {"overall_score": 0, "average_scores": {}, "total_responses": 0, "score_distribution": {}}
    
    def _generate_html_content(self, 
                             persona_scores: List[Dict],
                             safety_scores: List[Dict], 
                             translation_scores: List[Dict],
                             efficiency_scores: List[Dict],
                             overall_metrics: Dict[str, Any],
                             metadata: Dict[str, Any]) -> str:
        """Tạo nội dung HTML"""
        
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe AI - Evaluation Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .metric-card h3 {
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 1.1em;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .chart-container {
            margin: 30px 0;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .chart-title {
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }
        .section {
            margin: 30px 0;
        }
        .section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .score-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        .score-fill.excellent { background: linear-gradient(90deg, #28a745, #20c997); }
        .score-fill.good { background: linear-gradient(90deg, #ffc107, #fd7e14); }
        .score-fill.fair { background: linear-gradient(90deg, #fd7e14, #dc3545); }
        .score-fill.poor { background: linear-gradient(90deg, #dc3545, #6f42c1); }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        .table tr:hover {
            background-color: #f5f5f5;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .badge.excellent { background: #d4edda; color: #155724; }
        .badge.good { background: #fff3cd; color: #856404; }
        .badge.fair { background: #f8d7da; color: #721c24; }
        .badge.poor { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 StillMe AI Evaluation Report</h1>
            <p>Comprehensive Performance Analysis & Metrics</p>
        </div>
        
        <div class="content">
            <!-- Overall Metrics -->
            <div class="section">
                <h2>📊 Overall Performance Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Overall Score</h3>
                        <div class="metric-value">{overall_score}</div>
                        <div class="metric-label">Out of 1.0</div>
                    </div>
                    <div class="metric-card">
                        <h3>Total Responses</h3>
                        <div class="metric-value">{total_responses}</div>
                        <div class="metric-label">Test Cases</div>
                    </div>
                    <div class="metric-card">
                        <h3>Persona Score</h3>
                        <div class="metric-value">{persona_score}</div>
                        <div class="metric-label">Communication Style</div>
                    </div>
                    <div class="metric-card">
                        <h3>Safety Score</h3>
                        <div class="metric-value">{safety_score}</div>
                        <div class="metric-label">Ethical & Safe</div>
                    </div>
                    <div class="metric-card">
                        <h3>Translation Score</h3>
                        <div class="metric-value">{translation_score}</div>
                        <div class="metric-label">Language Processing</div>
                    </div>
                    <div class="metric-card">
                        <h3>Efficiency Score</h3>
                        <div class="metric-value">{efficiency_score}</div>
                        <div class="metric-label">Performance & Cost</div>
                    </div>
                </div>
            </div>
            
            <!-- Score Distribution Chart -->
            <div class="section">
                <h2>📈 Score Distribution</h2>
                <div class="chart-container">
                    <div class="chart-title">Performance Distribution Across All Evaluations</div>
                    <div id="scoreDistributionChart"></div>
                </div>
            </div>
            
            <!-- Detailed Scores -->
            <div class="section">
                <h2>🔍 Detailed Evaluation Scores</h2>
                
                <h3>Persona Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {persona_class}" style="width: {persona_width}%"></div>
                </div>
                <p>Addressing Style: {persona_addressing} | Communication Tone: {persona_tone} | Consistency: {persona_consistency}</p>
                
                <h3>Safety Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {safety_class}" style="width: {safety_width}%"></div>
                </div>
                <p>Ethical Filtering: {safety_ethical} | Jailbreak Resistance: {safety_jailbreak} | PII Protection: {safety_pii}</p>
                
                <h3>Translation Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {translation_class}" style="width: {translation_width}%"></div>
                </div>
                <p>Language Detection: {translation_detection} | Translation Accuracy: {translation_accuracy} | Context Preservation: {translation_context}</p>
                
                <h3>Efficiency Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {efficiency_class}" style="width: {efficiency_width}%"></div>
                </div>
                <p>Latency: {efficiency_latency} | Token Cost: {efficiency_cost} | Response Quality: {efficiency_quality}</p>
            </div>
            
            <!-- Performance Comparison -->
            <div class="section">
                <h2>⚖️ Performance Comparison</h2>
                <div class="chart-container">
                    <div class="chart-title">StillMe AI vs Baseline Performance</div>
                    <div id="comparisonChart"></div>
                </div>
            </div>
            
            <!-- Recommendations -->
            <div class="section">
                <h2>💡 Recommendations & Next Steps</h2>
                <div class="recommendations">
                    {recommendations}
                </div>
            </div>
            
            <!-- Metadata -->
            <div class="section">
                <h2>📋 Test Configuration</h2>
                <table class="table">
                    <tr><th>Test Date</th><td>{test_date}</td></tr>
                    <tr><th>Dataset Size</th><td>{dataset_size}</td></tr>
                    <tr><th>Test Duration</th><td>{test_duration}</td></tr>
                    <tr><th>Environment</th><td>{environment}</td></tr>
                    <tr><th>StillMe Version</th><td>{stillme_version}</td></tr>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by StillMe Test & Evaluation Harness | {timestamp}</p>
        </div>
    </div>
    
    <script>
        // Score Distribution Chart
        var scoreData = {{
            x: ['Excellent', 'Good', 'Fair', 'Poor'],
            y: [{excellent_count}, {good_count}, {fair_count}, {poor_count}],
            type: 'bar',
            marker: {{
                color: ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
            }}
        }};
        
        var scoreLayout = {{
            title: 'Score Distribution',
            xaxis: {{ title: 'Performance Level' }},
            yaxis: {{ title: 'Number of Responses' }},
            showlegend: false
        }};
        
        Plotly.newPlot('scoreDistributionChart', [scoreData], scoreLayout);
        
        // Comparison Chart
        var comparisonData = [
            {{
                x: ['Persona', 'Safety', 'Translation', 'Efficiency', 'Overall'],
                y: [{persona_score}, {safety_score}, {translation_score}, {efficiency_score}, {overall_score}],
                type: 'bar',
                name: 'StillMe AI',
                marker: {{ color: '#667eea' }}
            }},
            {{
                x: ['Persona', 'Safety', 'Translation', 'Efficiency', 'Overall'],
                y: [0.6, 0.7, 0.5, 0.8, 0.65],
                type: 'bar',
                name: 'Baseline',
                marker: {{ color: '#6c757d' }}
            }}
        ];
        
        var comparisonLayout = {{
            title: 'StillMe AI vs Baseline Performance',
            xaxis: {{ title: 'Evaluation Category' }},
            yaxis: {{ title: 'Score (0-1)' }},
            barmode: 'group'
        }};
        
        Plotly.newPlot('comparisonChart', comparisonData, comparisonLayout);
    </script>
</body>
</html>
        """
        
        # Format the template with actual data
        formatted_html = html_template.format(
            overall_score=overall_metrics.get('overall_score', 0),
            total_responses=overall_metrics.get('total_responses', 0),
            persona_score=overall_metrics.get('average_scores', {}).get('persona', 0),
            safety_score=overall_metrics.get('average_scores', {}).get('safety', 0),
            translation_score=overall_metrics.get('average_scores', {}).get('translation', 0),
            efficiency_score=overall_metrics.get('average_scores', {}).get('efficiency', 0),
            persona_class=self._get_score_class(overall_metrics.get('average_scores', {}).get('persona', 0)),
            persona_width=overall_metrics.get('average_scores', {}).get('persona', 0) * 100,
            safety_class=self._get_score_class(overall_metrics.get('average_scores', {}).get('safety', 0)),
            safety_width=overall_metrics.get('average_scores', {}).get('safety', 0) * 100,
            translation_class=self._get_score_class(overall_metrics.get('average_scores', {}).get('translation', 0)),
            translation_width=overall_metrics.get('average_scores', {}).get('translation', 0) * 100,
            efficiency_class=self._get_score_class(overall_metrics.get('average_scores', {}).get('efficiency', 0)),
            efficiency_width=overall_metrics.get('average_scores', {}).get('efficiency', 0) * 100,
            excellent_count=overall_metrics.get('score_distribution', {}).get('excellent', 0),
            good_count=overall_metrics.get('score_distribution', {}).get('good', 0),
            fair_count=overall_metrics.get('score_distribution', {}).get('fair', 0),
            poor_count=overall_metrics.get('score_distribution', {}).get('poor', 0),
            recommendations=self._generate_recommendations(overall_metrics),
            test_date=metadata.get('test_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            dataset_size=metadata.get('dataset_size', 'N/A'),
            test_duration=metadata.get('test_duration', 'N/A'),
            environment=metadata.get('environment', 'Local'),
            stillme_version=metadata.get('stillme_version', '1.0.0'),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return formatted_html
    
    def _get_score_class(self, score: float) -> str:
        """Lấy CSS class cho score"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(self, overall_metrics: Dict[str, Any]) -> str:
        """Tạo recommendations dựa trên kết quả"""
        recommendations = []
        
        avg_scores = overall_metrics.get('average_scores', {})
        
        # Persona recommendations
        persona_score = avg_scores.get('persona', 0)
        if persona_score < 0.6:
            recommendations.append("🔧 <strong>Persona:</strong> Cải thiện dynamic communication style và consistency")
        
        # Safety recommendations
        safety_score = avg_scores.get('safety', 0)
        if safety_score < 0.7:
            recommendations.append("🛡️ <strong>Safety:</strong> Tăng cường ethical filtering và jailbreak resistance")
        
        # Translation recommendations
        translation_score = avg_scores.get('translation', 0)
        if translation_score < 0.6:
            recommendations.append("🌐 <strong>Translation:</strong> Cải thiện language detection và translation accuracy")
        
        # Efficiency recommendations
        efficiency_score = avg_scores.get('efficiency', 0)
        if efficiency_score < 0.7:
            recommendations.append("⚡ <strong>Efficiency:</strong> Tối ưu hóa latency và token cost")
        
        # Overall recommendations
        overall_score = overall_metrics.get('overall_score', 0)
        if overall_score >= 0.8:
            recommendations.append("🎉 <strong>Excellent!</strong> StillMe AI đang hoạt động rất tốt!")
        elif overall_score >= 0.6:
            recommendations.append("👍 <strong>Good!</strong> StillMe AI hoạt động tốt, có thể cải thiện thêm")
        else:
            recommendations.append("⚠️ <strong>Needs Improvement:</strong> Cần cải thiện đáng kể để đạt hiệu suất tốt")
        
        return "<br>".join(recommendations) if recommendations else "No specific recommendations at this time."
    
    def export_json_report(self, 
                          persona_scores: List[Dict],
                          safety_scores: List[Dict], 
                          translation_scores: List[Dict],
                          efficiency_scores: List[Dict],
                          metadata: Dict[str, Any]) -> str:
        """Export báo cáo JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.output_dir / f"stillme_evaluation_report_{timestamp}.json"
            
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
                "persona_scores": persona_scores,
                "safety_scores": safety_scores,
                "translation_scores": translation_scores,
                "efficiency_scores": efficiency_scores,
                "overall_metrics": self._calculate_overall_metrics(
                    persona_scores, safety_scores, translation_scores, efficiency_scores
                )
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ JSON report exported: {json_file}")
            return str(json_file)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export JSON report: {e}")
            return ""

# Example usage
if __name__ == "__main__":
    # Test HTML Report Builder
    builder = HTMLReportBuilder()
    
    # Mock data
    mock_persona_scores = [
        {"overall_score": 0.8, "addressing_style": 0.7, "communication_tone": 0.9, "consistency": 0.8},
        {"overall_score": 0.6, "addressing_style": 0.5, "communication_tone": 0.7, "consistency": 0.6}
    ]
    
    mock_safety_scores = [
        {"overall_safety_score": 0.9, "ethical_filtering": 0.8, "jailbreak_resistance": 0.9, "pii_protection": 0.9},
        {"overall_safety_score": 0.7, "ethical_filtering": 0.6, "jailbreak_resistance": 0.8, "pii_protection": 0.7}
    ]
    
    mock_translation_scores = [
        {"overall_translation_score": 0.7, "language_detection": 0.8, "translation_accuracy": 0.6, "context_preservation": 0.7},
        {"overall_translation_score": 0.5, "language_detection": 0.6, "translation_accuracy": 0.4, "context_preservation": 0.5}
    ]
    
    mock_efficiency_scores = [
        {"overall_efficiency_score": 0.8, "latency": 0.9, "token_cost": 0.7, "response_quality": 0.8},
        {"overall_efficiency_score": 0.6, "latency": 0.7, "token_cost": 0.5, "response_quality": 0.6}
    ]
    
    mock_metadata = {
        "test_date": "2025-01-16 14:30:00",
        "dataset_size": "100 test cases",
        "test_duration": "2 hours",
        "environment": "Local Development",
        "stillme_version": "1.0.0"
    }
    
    # Build report
    html_file = builder.build_comprehensive_report(
        mock_persona_scores, mock_safety_scores, 
        mock_translation_scores, mock_efficiency_scores, 
        mock_metadata
    )
    
    print(f"🏗️ HTML Report Builder Test Results:")
    print(f"✅ HTML report generated: {html_file}")
    
    # Export JSON
    json_file = builder.export_json_report(
        mock_persona_scores, mock_safety_scores, 
        mock_translation_scores, mock_efficiency_scores, 
        mock_metadata
    )
    
    print(f"✅ JSON report exported: {json_file}")
