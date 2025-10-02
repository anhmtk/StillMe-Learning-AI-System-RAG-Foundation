"""
🔮 PREDICTIVE CAPABILITIES - SUB-PHASE 3.2
===========================================

Enterprise-grade predictive analytics system cho StillMe AI Framework.
Usage trend forecasting, performance prediction, và anomaly prediction.

Author: StillMe Phase 3 Development Team
Version: 3.2.0
Phase: 3.2 - Advanced Analytics Engine
Quality Standard: Enterprise-Grade (99.95% accuracy target)

FEATURES:
- Usage trend forecasting
- Performance prediction
- Anomaly prediction
- Capacity planning tools
- Predictive modeling
- Forecasting accuracy validation
"""

import json
import logging
import sqlite3
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Forecast result structure"""

    metric_name: str
    forecast_type: str
    predicted_values: list[float]
    confidence_intervals: list[tuple[float, float]]
    forecast_horizon: int
    accuracy_score: float
    model_used: str
    timestamp: datetime


@dataclass
class PerformancePrediction:
    """Performance prediction result"""

    component: str
    predicted_metric: str
    current_value: float
    predicted_value: float
    prediction_confidence: float
    time_horizon_hours: int
    recommendations: list[str]
    timestamp: datetime


@dataclass
class AnomalyPrediction:
    """Anomaly prediction result"""

    anomaly_type: str
    predicted_probability: float
    expected_timeframe: str
    severity_level: str
    affected_components: list[str]
    prevention_actions: list[str]
    confidence_score: float
    timestamp: datetime


class PredictiveCapabilities:
    """
    Enterprise-grade predictive analytics system
    """

    def __init__(self, metrics_db_path: str, config: Optional[dict[str, Any]] = None):
        self.metrics_db_path = Path(metrics_db_path)
        self.config = config or self._get_default_config()

        # Prediction models
        self._forecast_models = {}
        self._performance_models = {}
        self._anomaly_models = {}

        # Prediction cache
        self._prediction_cache = {}

        # Threading
        self._executor = ThreadPoolExecutor(max_workers=self.config["max_workers"])
        self._lock = threading.RLock()

        logger.info(
            "✅ PredictiveCapabilities initialized với enterprise-grade configuration"
        )

    def _get_default_config(self) -> dict[str, Any]:
        """Default configuration với predictive focus"""
        return {
            "accuracy_threshold": 0.9995,  # 99.95% accuracy requirement
            "max_workers": 4,
            "forecast_horizon_hours": 24,
            "prediction_confidence_threshold": 0.8,
            "model_retrain_interval_hours": 24,
            "cache_ttl_seconds": 1800,  # 30 minutes
            "enable_forecasting": True,
            "enable_performance_prediction": True,
            "enable_anomaly_prediction": True,
        }

    def forecast_usage_trends(
        self, metric_name: str, forecast_horizon_hours: int = 24
    ) -> ForecastResult:
        """
        Forecast usage trends using time series analysis

        Args:
            metric_name: Metric to forecast (usage_count, response_time, etc.)
            forecast_horizon_hours: Hours to forecast ahead

        Returns:
            ForecastResult object
        """
        try:
            start_time = time.time()

            # Get historical data
            historical_data = self._get_historical_data(
                metric_name, 168
            )  # 1 week of data

            if len(historical_data) < 24:  # Need at least 24 hours of data
                return ForecastResult(
                    metric_name=metric_name,
                    forecast_type="insufficient_data",
                    predicted_values=[],
                    confidence_intervals=[],
                    forecast_horizon=forecast_horizon_hours,
                    accuracy_score=0.0,
                    model_used="none",
                    timestamp=datetime.now(),
                )

            # Perform forecasting
            predicted_values, confidence_intervals = self._perform_forecasting(
                historical_data, forecast_horizon_hours
            )

            # Calculate accuracy score
            accuracy_score = self._calculate_forecast_accuracy(historical_data)

            # Create forecast result
            result = ForecastResult(
                metric_name=metric_name,
                forecast_type="usage_trend",
                predicted_values=predicted_values,
                confidence_intervals=confidence_intervals,
                forecast_horizon=forecast_horizon_hours,
                accuracy_score=accuracy_score,
                model_used="linear_regression",
                timestamp=datetime.now(),
            )

            # Cache result
            cache_key = f"forecast_{metric_name}_{forecast_horizon_hours}"
            self._prediction_cache[cache_key] = (time.time(), result)

            logger.debug(
                f"🔮 Usage trend forecast completed for {metric_name} in {(time.time() - start_time) * 1000:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Usage trend forecasting failed: {e}")
            return ForecastResult(
                metric_name=metric_name,
                forecast_type="error",
                predicted_values=[],
                confidence_intervals=[],
                forecast_horizon=forecast_horizon_hours,
                accuracy_score=0.0,
                model_used="error",
                timestamp=datetime.now(),
            )

    def predict_performance(
        self, component: str, metric: str, time_horizon_hours: int = 1
    ) -> PerformancePrediction:
        """
        Predict performance metrics for a component

        Args:
            component: Component to predict (module_name, feature_name, etc.)
            metric: Metric to predict (response_time, success_rate, etc.)
            time_horizon_hours: Hours ahead to predict

        Returns:
            PerformancePrediction object
        """
        try:
            start_time = time.time()

            # Get current performance data
            current_value = self._get_current_performance(component, metric)

            # Get historical performance data
            historical_data = self._get_performance_history(
                component, metric, 24
            )  # 24 hours

            if len(historical_data) < 12:  # Need at least 12 hours of data
                return PerformancePrediction(
                    component=component,
                    predicted_metric=metric,
                    current_value=current_value,
                    predicted_value=current_value,
                    prediction_confidence=0.0,
                    time_horizon_hours=time_horizon_hours,
                    recommendations=["Insufficient data for prediction"],
                    timestamp=datetime.now(),
                )

            # Predict future performance
            predicted_value, confidence = self._predict_performance_value(
                historical_data, time_horizon_hours
            )

            # Generate recommendations
            recommendations = self._generate_performance_recommendations(
                current_value, predicted_value, metric
            )

            # Create performance prediction
            result = PerformancePrediction(
                component=component,
                predicted_metric=metric,
                current_value=current_value,
                predicted_value=predicted_value,
                prediction_confidence=confidence,
                time_horizon_hours=time_horizon_hours,
                recommendations=recommendations,
                timestamp=datetime.now(),
            )

            logger.debug(
                f"🔮 Performance prediction completed for {component}.{metric} in {(time.time() - start_time) * 1000:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Performance prediction failed: {e}")
            return PerformancePrediction(
                component=component,
                predicted_metric=metric,
                current_value=0.0,
                predicted_value=0.0,
                prediction_confidence=0.0,
                time_horizon_hours=time_horizon_hours,
                recommendations=[f"Prediction failed: {e!s}"],
                timestamp=datetime.now(),
            )

    def predict_anomalies(
        self, time_horizon_hours: int = 24
    ) -> list[AnomalyPrediction]:
        """
        Predict potential anomalies

        Args:
            time_horizon_hours: Hours ahead to predict anomalies

        Returns:
            List of AnomalyPrediction objects
        """
        try:
            start_time = time.time()

            # Get historical anomaly data
            self._get_historical_anomalies(168)  # 1 week

            # Get current system metrics
            current_metrics = self._get_current_system_metrics()

            # Predict potential anomalies
            anomaly_predictions = []

            # Performance anomaly prediction
            perf_anomaly = self._predict_performance_anomaly(
                current_metrics, time_horizon_hours
            )
            if perf_anomaly:
                anomaly_predictions.append(perf_anomaly)

            # Resource anomaly prediction
            resource_anomaly = self._predict_resource_anomaly(
                current_metrics, time_horizon_hours
            )
            if resource_anomaly:
                anomaly_predictions.append(resource_anomaly)

            # Usage anomaly prediction
            usage_anomaly = self._predict_usage_anomaly(
                current_metrics, time_horizon_hours
            )
            if usage_anomaly:
                anomaly_predictions.append(usage_anomaly)

            logger.debug(
                f"🔮 Anomaly prediction completed: {len(anomaly_predictions)} anomalies predicted in {(time.time() - start_time) * 1000:.1f}ms"
            )

            return anomaly_predictions

        except Exception as e:
            logger.error(f"❌ Anomaly prediction failed: {e}")
            return []

    def _get_historical_data(self, metric_name: str, hours: int) -> list[float]:
        """Get historical data for forecasting"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=hours)

                if metric_name == "usage_count":
                    cursor = conn.execute(
                        """
                        SELECT COUNT(*) as value
                        FROM usage_events
                        WHERE timestamp >= ?
                        GROUP BY strftime('%H', timestamp)
                        ORDER BY timestamp
                    """,
                        [since_time.isoformat()],
                    )
                elif metric_name == "response_time":
                    cursor = conn.execute(
                        """
                        SELECT AVG(duration_ms) as value
                        FROM usage_events
                        WHERE timestamp >= ?
                        GROUP BY strftime('%H', timestamp)
                        ORDER BY timestamp
                    """,
                        [since_time.isoformat()],
                    )
                else:
                    return []

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"❌ Error getting historical data: {e}")
            return []

    def _perform_forecasting(
        self, historical_data: list[float], forecast_horizon: int
    ) -> tuple[list[float], list[tuple[float, float]]]:
        """Perform forecasting using simple linear regression"""
        try:
            if len(historical_data) < 2:
                return [], []

            # Simple linear regression
            n = len(historical_data)
            x = list(range(n))
            y = historical_data

            # Calculate regression coefficients
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            intercept = (sum_y - slope * sum_x) / n

            # Generate predictions
            predicted_values = []
            confidence_intervals = []

            for i in range(forecast_horizon):
                future_x = n + i
                predicted_value = slope * future_x + intercept
                predicted_values.append(predicted_value)

                # Simple confidence interval (95%)
                std_error = statistics.stdev(y) if len(y) > 1 else 0
                margin = 1.96 * std_error  # 95% confidence
                confidence_intervals.append(
                    (predicted_value - margin, predicted_value + margin)
                )

            return predicted_values, confidence_intervals

        except Exception as e:
            logger.error(f"❌ Forecasting failed: {e}")
            return [], []

    def _calculate_forecast_accuracy(self, historical_data: list[float]) -> float:
        """Calculate forecast accuracy based on historical data"""
        try:
            if len(historical_data) < 10:
                return 0.0

            # Use last 25% of data for validation
            validation_size = max(1, len(historical_data) // 4)
            train_data = historical_data[:-validation_size]
            validation_data = historical_data[-validation_size:]

            # Train model on training data
            if len(train_data) < 2:
                return 0.0

            n = len(train_data)
            x = list(range(n))
            y = train_data

            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            intercept = (sum_y - slope * sum_x) / n

            # Predict validation data
            predictions = []
            for i in range(len(validation_data)):
                predicted = slope * (n + i) + intercept
                predictions.append(predicted)

            # Calculate accuracy (1 - MAPE)
            mape = 0.0
            for i in range(len(validation_data)):
                if validation_data[i] != 0:
                    mape += (
                        abs(validation_data[i] - predictions[i]) / validation_data[i]
                    )

            mape /= len(validation_data)
            accuracy = max(0.0, 1.0 - mape)

            return accuracy

        except Exception as e:
            logger.error(f"❌ Forecast accuracy calculation failed: {e}")
            return 0.0

    def _get_current_performance(self, component: str, metric: str) -> float:
        """Get current performance value"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=1)

                if metric == "response_time":
                    cursor = conn.execute(
                        """
                        SELECT AVG(duration_ms)
                        FROM usage_events
                        WHERE timestamp >= ? AND module_name = ?
                    """,
                        [since_time.isoformat(), component],
                    )
                elif metric == "success_rate":
                    cursor = conn.execute(
                        """
                        SELECT AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END)
                        FROM usage_events
                        WHERE timestamp >= ? AND module_name = ?
                    """,
                        [since_time.isoformat(), component],
                    )
                else:
                    return 0.0

                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0.0

        except Exception as e:
            logger.error(f"❌ Error getting current performance: {e}")
            return 0.0

    def _get_performance_history(
        self, component: str, metric: str, hours: int
    ) -> list[float]:
        """Get performance history"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=hours)

                if metric == "response_time":
                    cursor = conn.execute(
                        """
                        SELECT AVG(duration_ms)
                        FROM usage_events
                        WHERE timestamp >= ? AND module_name = ?
                        GROUP BY strftime('%H', timestamp)
                        ORDER BY timestamp
                    """,
                        [since_time.isoformat(), component],
                    )
                elif metric == "success_rate":
                    cursor = conn.execute(
                        """
                        SELECT AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END)
                        FROM usage_events
                        WHERE timestamp >= ? AND module_name = ?
                        GROUP BY strftime('%H', timestamp)
                        ORDER BY timestamp
                    """,
                        [since_time.isoformat(), component],
                    )
                else:
                    return []

                return [row[0] for row in cursor.fetchall() if row[0] is not None]

        except Exception as e:
            logger.error(f"❌ Error getting performance history: {e}")
            return []

    def _predict_performance_value(
        self, historical_data: list[float], time_horizon: int
    ) -> tuple[float, float]:
        """Predict future performance value"""
        try:
            if len(historical_data) < 2:
                return 0.0, 0.0

            # Simple trend-based prediction
            recent_values = historical_data[-6:]  # Last 6 hours
            trend = statistics.mean(recent_values[-3:]) - statistics.mean(
                recent_values[:3]
            )

            current_value = historical_data[-1]
            predicted_value = current_value + (trend * time_horizon)

            # Calculate confidence based on data consistency
            std_dev = (
                statistics.stdev(historical_data) if len(historical_data) > 1 else 0
            )
            mean_value = statistics.mean(historical_data)
            confidence = max(0.0, 1.0 - (std_dev / max(0.001, mean_value)))

            return predicted_value, confidence

        except Exception as e:
            logger.error(f"❌ Performance value prediction failed: {e}")
            return 0.0, 0.0

    def _generate_performance_recommendations(
        self, current: float, predicted: float, metric: str
    ) -> list[str]:
        """Generate performance recommendations"""
        recommendations = []

        try:
            if metric == "response_time":
                if predicted > current * 1.2:  # 20% increase
                    recommendations.append("Consider performance optimization")
                if predicted > 5000:  # 5 seconds
                    recommendations.append("Response time may exceed acceptable limits")
            elif metric == "success_rate":
                if predicted < current * 0.9:  # 10% decrease
                    recommendations.append("Investigate potential issues")
                if predicted < 0.95:  # 95% success rate
                    recommendations.append("Success rate may fall below target")

            if not recommendations:
                recommendations.append("Performance is expected to remain stable")

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}")
            recommendations.append("Error generating recommendations")

        return recommendations

    def _get_historical_anomalies(self, hours: int) -> list[dict[str, Any]]:
        """Get historical anomaly data"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=hours)

                cursor = conn.execute(
                    """
                    SELECT
                        timestamp,
                        module_name,
                        feature_name,
                        duration_ms,
                        success,
                        error_code
                    FROM usage_events
                    WHERE timestamp >= ? AND (success = 0 OR duration_ms > 10000)
                    ORDER BY timestamp
                """,
                    [since_time.isoformat()],
                )

                anomalies = []
                for row in cursor.fetchall():
                    anomalies.append(
                        {
                            "timestamp": row[0],
                            "module_name": row[1],
                            "feature_name": row[2],
                            "duration_ms": row[3],
                            "success": row[4],
                            "error_code": row[5],
                        }
                    )

                return anomalies

        except Exception as e:
            logger.error(f"❌ Error getting historical anomalies: {e}")
            return []

    def _get_current_system_metrics(self) -> dict[str, Any]:
        """Get current system metrics"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=1)

                # Get current metrics
                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_events,
                        AVG(duration_ms) as avg_response_time,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                        COUNT(DISTINCT module_name) as active_modules
                    FROM usage_events
                    WHERE timestamp >= ?
                """,
                    [since_time.isoformat()],
                )

                result = cursor.fetchone()

                return {
                    "total_events": result[0] or 0,
                    "avg_response_time": result[1] or 0.0,
                    "success_rate": result[2] or 0.0,
                    "active_modules": result[3] or 0,
                }

        except Exception as e:
            logger.error(f"❌ Error getting current system metrics: {e}")
            return {}

    def _predict_performance_anomaly(
        self, current_metrics: dict[str, Any], time_horizon: int
    ) -> Optional[AnomalyPrediction]:
        """Predict performance anomalies"""
        try:
            if not current_metrics:
                return None

            # Check for performance degradation indicators
            avg_response_time = current_metrics.get("avg_response_time", 0)
            success_rate = current_metrics.get("success_rate", 0)

            # Calculate anomaly probability
            anomaly_probability = 0.0

            if avg_response_time > 5000:  # 5 seconds
                anomaly_probability += 0.3

            if success_rate < 0.95:  # 95% success rate
                anomaly_probability += 0.4

            if anomaly_probability > 0.5:  # 50% threshold
                return AnomalyPrediction(
                    anomaly_type="performance_degradation",
                    predicted_probability=anomaly_probability,
                    expected_timeframe=f"within {time_horizon} hours",
                    severity_level="high" if anomaly_probability > 0.7 else "medium",
                    affected_components=["system_performance"],
                    prevention_actions=[
                        "Monitor system resources",
                        "Check for bottlenecks",
                        "Review recent deployments",
                    ],
                    confidence_score=anomaly_probability,
                    timestamp=datetime.now(),
                )

            return None

        except Exception as e:
            logger.error(f"❌ Performance anomaly prediction failed: {e}")
            return None

    def _predict_resource_anomaly(
        self, current_metrics: dict[str, Any], time_horizon: int
    ) -> Optional[AnomalyPrediction]:
        """Predict resource anomalies"""
        try:
            if not current_metrics:
                return None

            # Check for resource usage indicators
            total_events = current_metrics.get("total_events", 0)
            active_modules = current_metrics.get("active_modules", 0)

            # Calculate anomaly probability
            anomaly_probability = 0.0

            if total_events > 10000:  # High load
                anomaly_probability += 0.2

            if active_modules < 5:  # Low module activity
                anomaly_probability += 0.3

            if anomaly_probability > 0.4:  # 40% threshold
                return AnomalyPrediction(
                    anomaly_type="resource_anomaly",
                    predicted_probability=anomaly_probability,
                    expected_timeframe=f"within {time_horizon} hours",
                    severity_level="medium",
                    affected_components=["resource_usage"],
                    prevention_actions=[
                        "Monitor resource usage",
                        "Check system capacity",
                        "Review load balancing",
                    ],
                    confidence_score=anomaly_probability,
                    timestamp=datetime.now(),
                )

            return None

        except Exception as e:
            logger.error(f"❌ Resource anomaly prediction failed: {e}")
            return None

    def _predict_usage_anomaly(
        self, current_metrics: dict[str, Any], time_horizon: int
    ) -> Optional[AnomalyPrediction]:
        """Predict usage anomalies"""
        try:
            if not current_metrics:
                return None

            # Check for usage pattern indicators
            total_events = current_metrics.get("total_events", 0)

            # Calculate anomaly probability
            anomaly_probability = 0.0

            if total_events < 100:  # Very low usage
                anomaly_probability += 0.4

            if total_events > 50000:  # Very high usage
                anomaly_probability += 0.3

            if anomaly_probability > 0.3:  # 30% threshold
                return AnomalyPrediction(
                    anomaly_type="usage_anomaly",
                    predicted_probability=anomaly_probability,
                    expected_timeframe=f"within {time_horizon} hours",
                    severity_level="low",
                    affected_components=["usage_patterns"],
                    prevention_actions=[
                        "Monitor usage patterns",
                        "Check user engagement",
                        "Review feature adoption",
                    ],
                    confidence_score=anomaly_probability,
                    timestamp=datetime.now(),
                )

            return None

        except Exception as e:
            logger.error(f"❌ Usage anomaly prediction failed: {e}")
            return None

    def get_prediction_summary(self) -> dict[str, Any]:
        """Get prediction summary"""
        try:
            return {
                "prediction_types": [
                    "usage_forecast",
                    "performance_prediction",
                    "anomaly_prediction",
                ],
                "cache_status": {"prediction_cache_size": len(self._prediction_cache)},
                "model_status": {
                    "forecast_models": len(self._forecast_models),
                    "performance_models": len(self._performance_models),
                    "anomaly_models": len(self._anomaly_models),
                },
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error getting prediction summary: {e}")
            return {"error": str(e)}


# Factory function
def create_predictive_capabilities(
    metrics_db_path: str, config: Optional[dict[str, Any]] = None
) -> PredictiveCapabilities:
    """Factory function để create predictive capabilities"""
    return PredictiveCapabilities(metrics_db_path, config)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Predictive Capabilities")
    parser.add_argument("--metrics-db", required=True, help="Metrics database path")
    parser.add_argument("--forecast", help="Forecast usage trends for metric")
    parser.add_argument(
        "--predict-performance", help="Predict performance for component"
    )
    parser.add_argument(
        "--predict-anomalies", action="store_true", help="Predict anomalies"
    )
    parser.add_argument(
        "--time-horizon", type=int, default=24, help="Time horizon in hours"
    )
    parser.add_argument("--summary", action="store_true", help="Get prediction summary")

    args = parser.parse_args()

    # Create predictive capabilities
    predictive = create_predictive_capabilities(args.metrics_db)

    if args.forecast:
        result = predictive.forecast_usage_trends(args.forecast, args.time_horizon)
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.predict_performance:
        result = predictive.predict_performance(
            args.predict_performance, "response_time", args.time_horizon
        )
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.predict_anomalies:
        results = predictive.predict_anomalies(args.time_horizon)
        print(json.dumps([asdict(r) for r in results], indent=2, default=str))
    elif args.summary:
        summary = predictive.get_prediction_summary()
        print(json.dumps(summary, indent=2, default=str))
    else:
        print("Use --help for usage information")
