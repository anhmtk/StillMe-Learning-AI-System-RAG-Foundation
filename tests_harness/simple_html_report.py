#!/usr/bin/env python3
"""
Simple HTML Report Builder - Version đơn giản không có JavaScript

Tạo báo cáo HTML cơ bản với CSS styling, không có interactive charts
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleHTMLReportBuilder:
    """Simple HTML Report Builder"""
    
    def __init__(self, output_dir: str = "tests_harness/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def build_simple_report(self, 
                          persona_scores: List[Dict],
                          safety_scores: List[Dict], 
                          translation_scores: List[Dict],
                          efficiency_scores: List[Dict],
                          metadata: Dict[str, Any]) -> str:
        """Tạo báo cáo HTML đơn giản"""
        try:
            self.logger.info("🏗️ Building simple HTML report...")
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_dir / f"stillme_simple_report_{timestamp}.html"
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(
                persona_scores, safety_scores, translation_scores, efficiency_scores
            )
            
            # Generate HTML content
            html_content = self._generate_simple_html(
                persona_scores, safety_scores, translation_scores, 
                efficiency_scores, overall_metrics, metadata
            )
            
            # Write to file
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"✅ Simple HTML report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to build simple HTML report: {e}")
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
    
    def _generate_simple_html(self, 
                             persona_scores: List[Dict],
                             safety_scores: List[Dict], 
                             translation_scores: List[Dict],
                             efficiency_scores: List[Dict],
                             overall_metrics: Dict[str, Any],
                             metadata: Dict[str, Any]) -> str:
        """Tạo HTML đơn giản"""
        
        # Get values
        overall_score = overall_metrics.get('overall_score', 0)
        total_responses = overall_metrics.get('total_responses', 0)
        avg_scores = overall_metrics.get('average_scores', {})
        score_dist = overall_metrics.get('score_distribution', {})
        
        persona_score = avg_scores.get('persona', 0)
        safety_score = avg_scores.get('safety', 0)
        translation_score = avg_scores.get('translation', 0)
        efficiency_score = avg_scores.get('efficiency', 0)
        
        excellent_count = score_dist.get('excellent', 0)
        good_count = score_dist.get('good', 0)
        fair_count = score_dist.get('fair', 0)
        poor_count = score_dist.get('poor', 0)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_metrics)
        
        # Get metadata
        test_date = metadata.get('test_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        dataset_size = metadata.get('dataset_size', 'N/A')
        test_duration = metadata.get('test_duration', 'N/A')
        environment = metadata.get('environment', 'Local')
        stillme_version = metadata.get('stillme_version', '1.0.0')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe AI - Evaluation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 1.1em;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .score-bar {{
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .score-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        .score-fill.excellent {{ background: linear-gradient(90deg, #28a745, #20c997); }}
        .score-fill.good {{ background: linear-gradient(90deg, #ffc107, #fd7e14); }}
        .score-fill.fair {{ background: linear-gradient(90deg, #fd7e14, #dc3545); }}
        .score-fill.poor {{ background: linear-gradient(90deg, #dc3545, #6f42c1); }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .table th, .table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .table th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        .table tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .badge.excellent {{ background: #d4edda; color: #155724; }}
        .badge.good {{ background: #fff3cd; color: #856404; }}
        .badge.fair {{ background: #f8d7da; color: #721c24; }}
        .badge.poor {{ background: #d1ecf1; color: #0c5460; }}
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
            
            <!-- Score Distribution -->
            <div class="section">
                <h2>📈 Score Distribution</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>Excellent (≥0.8)</h3>
                        <div class="metric-value">{excellent_count}</div>
                        <div class="metric-label">Responses</div>
                    </div>
                    <div class="metric-card">
                        <h3>Good (0.6-0.8)</h3>
                        <div class="metric-value">{good_count}</div>
                        <div class="metric-label">Responses</div>
                    </div>
                    <div class="metric-card">
                        <h3>Fair (0.4-0.6)</h3>
                        <div class="metric-value">{fair_count}</div>
                        <div class="metric-label">Responses</div>
                    </div>
                    <div class="metric-card">
                        <h3>Poor (<0.4)</h3>
                        <div class="metric-value">{poor_count}</div>
                        <div class="metric-label">Responses</div>
                    </div>
                </div>
            </div>
            
            <!-- Detailed Scores -->
            <div class="section">
                <h2>🔍 Detailed Evaluation Scores</h2>
                
                <h3>Persona Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {self._get_score_class(persona_score)}" style="width: {persona_score * 100}%"></div>
                </div>
                <p>Score: {persona_score:.3f} | Communication style and addressing consistency</p>
                
                <h3>Safety Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {self._get_score_class(safety_score)}" style="width: {safety_score * 100}%"></div>
                </div>
                <p>Score: {safety_score:.3f} | Ethical filtering and safety measures</p>
                
                <h3>Translation Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {self._get_score_class(translation_score)}" style="width: {translation_score * 100}%"></div>
                </div>
                <p>Score: {translation_score:.3f} | Language detection and translation accuracy</p>
                
                <h3>Efficiency Evaluation</h3>
                <div class="score-bar">
                    <div class="score-fill {self._get_score_class(efficiency_score)}" style="width: {efficiency_score * 100}%"></div>
                </div>
                <p>Score: {efficiency_score:.3f} | Performance and cost optimization</p>
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
</body>
</html>
        """
        
        return html_content
    
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

# Example usage
if __name__ == "__main__":
    # Test Simple HTML Report Builder
    builder = SimpleHTMLReportBuilder()
    
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
    html_file = builder.build_simple_report(
        mock_persona_scores, mock_safety_scores, 
        mock_translation_scores, mock_efficiency_scores, 
        mock_metadata
    )
    
    print(f"🏗️ Simple HTML Report Builder Test Results:")
    print(f"✅ HTML report generated: {html_file}")
