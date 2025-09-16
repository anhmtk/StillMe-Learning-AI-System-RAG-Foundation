"""
📊 MULTI-DIMENSIONAL ANALYSIS - SUB-PHASE 3.2
==============================================

Enterprise-grade multi-dimensional analytics system cho StillMe AI Framework.
Time-series analysis, user behavior analytics, và feature usage patterns.

Author: StillMe Phase 3 Development Team
Version: 3.2.0
Phase: 3.2 - Advanced Analytics Engine
Quality Standard: Enterprise-Grade (99.95% accuracy target)

FEATURES:
- Time-series analysis capabilities
- User behavior analytics
- Feature usage patterns
- Resource optimization insights
- Multi-dimensional data aggregation
- Advanced statistical analysis
"""

import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TimeSeriesData:
    """Time series data structure"""

    timestamp: datetime
    value: float
    dimension: str
    metadata: Dict[str, Any]


@dataclass
class UserBehaviorMetrics:
    """User behavior analysis results"""

    user_id: str
    session_count: int
    avg_session_duration: float
    feature_usage_frequency: Dict[str, int]
    usage_patterns: Dict[str, Any]
    engagement_score: float
    retention_rate: float


@dataclass
class FeatureUsagePattern:
    """Feature usage pattern analysis"""

    feature_name: str
    usage_frequency: int
    user_adoption_rate: float
    usage_trend: str  # "increasing", "stable", "decreasing"
    peak_usage_hours: List[int]
    correlation_with_other_features: Dict[str, float]
    business_impact_score: float


@dataclass
class MultiDimensionalResult:
    """Multi-dimensional analysis result"""

    analysis_type: str
    dimensions: List[str]
    time_range: Tuple[datetime, datetime]
    aggregated_data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    confidence_score: float
    timestamp: datetime


class MultiDimensionalAnalysis:
    """
    Enterprise-grade multi-dimensional analytics system
    """

    def __init__(self, metrics_db_path: str, config: Optional[Dict[str, Any]] = None):
        self.metrics_db_path = Path(metrics_db_path)
        self.config = config or self._get_default_config()

        # Analysis cache
        self._analysis_cache = {}
        self._time_series_cache = {}

        # Threading
        self._executor = ThreadPoolExecutor(max_workers=self.config["max_workers"])
        self._lock = threading.RLock()

        # Performance monitoring
        self._analysis_times = deque(maxlen=1000)

        logger.info(
            "✅ MultiDimensionalAnalysis initialized với enterprise-grade configuration"
        )

    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration với analytics focus"""
        return {
            "accuracy_threshold": 0.9995,  # 99.95% accuracy requirement
            "max_workers": 4,
            "cache_ttl_seconds": 600,  # 10 minutes
            "time_series_granularity": "hour",  # hour, day, week
            "max_dimensions": 10,
            "statistical_confidence": 0.95,
            "trend_analysis_window": 30,  # days
            "memory_limit_mb": 4096,  # 4GB constraint
            "enable_real_time": True,
            "enable_predictive": True,
        }

    def analyze_time_series(
        self, dimension: str, time_range_hours: int = 24, granularity: str = "hour"
    ) -> MultiDimensionalResult:
        """
        Analyze time series data for a specific dimension

        Args:
            dimension: Dimension to analyze (module_name, feature_name, user_id, etc.)
            time_range_hours: Time range for analysis
            granularity: Time granularity (hour, day, week)

        Returns:
            MultiDimensionalResult object
        """
        try:
            start_time = time.time()

            # Get time series data
            time_series_data = self._get_time_series_data(
                dimension, time_range_hours, granularity
            )

            # Perform statistical analysis
            statistical_analysis = self._perform_statistical_analysis(time_series_data)

            # Generate insights
            insights = self._generate_time_series_insights(
                time_series_data, statistical_analysis
            )

            # Generate recommendations
            recommendations = self._generate_time_series_recommendations(
                statistical_analysis
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                time_series_data, statistical_analysis
            )

            # Create result
            result = MultiDimensionalResult(
                analysis_type="time_series",
                dimensions=[dimension],
                time_range=(
                    datetime.now() - timedelta(hours=time_range_hours),
                    datetime.now(),
                ),
                aggregated_data=statistical_analysis,
                insights=insights,
                recommendations=recommendations,
                confidence_score=confidence_score,
                timestamp=datetime.now(),
            )

            # Cache result
            cache_key = f"timeseries_{dimension}_{time_range_hours}_{granularity}"
            self._time_series_cache[cache_key] = (time.time(), result)

            # Update performance metrics
            analysis_duration = (time.time() - start_time) * 1000
            self._analysis_times.append(analysis_duration)

            logger.debug(
                f"📊 Time series analysis completed for {dimension} in {analysis_duration:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Time series analysis failed: {e}")
            return MultiDimensionalResult(
                analysis_type="time_series",
                dimensions=[dimension],
                time_range=(datetime.now(), datetime.now()),
                aggregated_data={},
                insights=[f"Analysis failed: {e!s}"],
                recommendations=[],
                confidence_score=0.0,
                timestamp=datetime.now(),
            )

    def analyze_user_behavior(
        self, time_range_hours: int = 168
    ) -> Dict[str, UserBehaviorMetrics]:
        """
        Analyze user behavior patterns

        Args:
            time_range_hours: Time range for analysis (default 1 week)

        Returns:
            Dictionary of UserBehaviorMetrics by user_id
        """
        try:
            start_time = time.time()

            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                # Get user behavior data
                cursor = conn.execute(
                    """
                    SELECT 
                        user_id,
                        session_id,
                        COUNT(*) as event_count,
                        AVG(duration_ms) as avg_duration,
                        MIN(timestamp) as first_event,
                        MAX(timestamp) as last_event,
                        COUNT(DISTINCT feature_name) as unique_features
                    FROM usage_events
                    WHERE timestamp >= ? AND user_id IS NOT NULL
                    GROUP BY user_id, session_id
                """,
                    [since_time.isoformat()],
                )

                user_sessions = cursor.fetchall()

                # Get feature usage by user
                cursor = conn.execute(
                    """
                    SELECT 
                        user_id,
                        feature_name,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ? AND user_id IS NOT NULL
                    GROUP BY user_id, feature_name
                """,
                    [since_time.isoformat()],
                )

                feature_usage = cursor.fetchall()

            # Process user behavior data
            user_metrics = {}
            user_sessions_dict = defaultdict(list)

            for (
                user_id,
                session_id,
                event_count,
                avg_duration,
                first_event,
                last_event,
                unique_features,
            ) in user_sessions:
                user_sessions_dict[user_id].append(
                    {
                        "session_id": session_id,
                        "event_count": event_count,
                        "avg_duration": avg_duration,
                        "first_event": first_event,
                        "last_event": last_event,
                        "unique_features": unique_features,
                    }
                )

            # Calculate metrics for each user
            for user_id, sessions in user_sessions_dict.items():
                # Calculate session metrics
                session_count = len(sessions)
                avg_session_duration = statistics.mean(
                    [s["avg_duration"] for s in sessions]
                )

                # Calculate feature usage frequency
                feature_usage_frequency = {}
                for user_id_feat, feature_name, usage_count in feature_usage:
                    if user_id_feat == user_id:
                        feature_usage_frequency[feature_name] = usage_count

                # Calculate usage patterns
                usage_patterns = self._calculate_usage_patterns(sessions)

                # Calculate engagement score
                engagement_score = self._calculate_engagement_score(
                    sessions, feature_usage_frequency
                )

                # Calculate retention rate
                retention_rate = self._calculate_retention_rate(
                    sessions, time_range_hours
                )

                # Create user behavior metrics
                user_metrics[user_id] = UserBehaviorMetrics(
                    user_id=user_id,
                    session_count=session_count,
                    avg_session_duration=avg_session_duration,
                    feature_usage_frequency=feature_usage_frequency,
                    usage_patterns=usage_patterns,
                    engagement_score=engagement_score,
                    retention_rate=retention_rate,
                )

            analysis_duration = (time.time() - start_time) * 1000
            self._analysis_times.append(analysis_duration)

            logger.debug(
                f"📊 User behavior analysis completed for {len(user_metrics)} users in {analysis_duration:.1f}ms"
            )

            return user_metrics

        except Exception as e:
            logger.error(f"❌ User behavior analysis failed: {e}")
            return {}

    def analyze_feature_usage_patterns(
        self, time_range_hours: int = 168
    ) -> Dict[str, FeatureUsagePattern]:
        """
        Analyze feature usage patterns

        Args:
            time_range_hours: Time range for analysis

        Returns:
            Dictionary of FeatureUsagePattern by feature_name
        """
        try:
            start_time = time.time()

            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                # Get feature usage data
                cursor = conn.execute(
                    """
                    SELECT 
                        feature_name,
                        COUNT(*) as usage_count,
                        COUNT(DISTINCT user_id) as unique_users,
                        AVG(duration_ms) as avg_duration,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM usage_events
                    WHERE timestamp >= ? AND feature_name IS NOT NULL
                    GROUP BY feature_name
                """,
                    [since_time.isoformat()],
                )

                feature_data = cursor.fetchall()

                # Get hourly usage patterns
                cursor = conn.execute(
                    """
                    SELECT 
                        feature_name,
                        strftime('%H', timestamp) as hour,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ? AND feature_name IS NOT NULL
                    GROUP BY feature_name, hour
                    ORDER BY feature_name, hour
                """,
                    [since_time.isoformat()],
                )

                hourly_data = cursor.fetchall()

            # Process feature usage patterns
            feature_patterns = {}
            hourly_usage_dict = defaultdict(lambda: defaultdict(int))

            # Process hourly data
            for feature_name, hour, usage_count in hourly_data:
                hourly_usage_dict[feature_name][int(hour)] = usage_count

            # Calculate patterns for each feature
            for (
                feature_name,
                usage_count,
                unique_users,
                avg_duration,
                success_rate,
            ) in feature_data:
                # Calculate user adoption rate
                total_users = self._get_total_users(since_time)
                user_adoption_rate = unique_users / max(1, total_users)

                # Calculate usage trend
                usage_trend = self._calculate_usage_trend(
                    feature_name, time_range_hours
                )

                # Get peak usage hours
                peak_usage_hours = self._get_peak_usage_hours(
                    hourly_usage_dict[feature_name]
                )

                # Calculate correlation with other features
                correlation_with_other_features = self._calculate_feature_correlation(
                    feature_name, time_range_hours
                )

                # Calculate business impact score
                business_impact_score = self._calculate_business_impact_score(
                    usage_count, user_adoption_rate, success_rate, avg_duration
                )

                # Create feature usage pattern
                feature_patterns[feature_name] = FeatureUsagePattern(
                    feature_name=feature_name,
                    usage_frequency=usage_count,
                    user_adoption_rate=user_adoption_rate,
                    usage_trend=usage_trend,
                    peak_usage_hours=peak_usage_hours,
                    correlation_with_other_features=correlation_with_other_features,
                    business_impact_score=business_impact_score,
                )

            analysis_duration = (time.time() - start_time) * 1000
            self._analysis_times.append(analysis_duration)

            logger.debug(
                f"📊 Feature usage pattern analysis completed for {len(feature_patterns)} features in {analysis_duration:.1f}ms"
            )

            return feature_patterns

        except Exception as e:
            logger.error(f"❌ Feature usage pattern analysis failed: {e}")
            return {}

    def _get_time_series_data(
        self, dimension: str, time_range_hours: int, granularity: str
    ) -> List[TimeSeriesData]:
        """Get time series data for analysis"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                # Build query based on granularity
                if granularity == "hour":
                    time_format = "strftime('%Y-%m-%d %H:00:00', timestamp)"
                elif granularity == "day":
                    time_format = "strftime('%Y-%m-%d 00:00:00', timestamp)"
                elif granularity == "week":
                    time_format = "strftime('%Y-%m-%d 00:00:00', date(timestamp, 'weekday 0', '-6 days'))"
                else:
                    time_format = "strftime('%Y-%m-%d %H:00:00', timestamp)"

                cursor = conn.execute(
                    f"""
                    SELECT 
                        {time_format} as time_bucket,
                        COUNT(*) as event_count,
                        AVG(duration_ms) as avg_duration,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM usage_events
                    WHERE timestamp >= ? AND {dimension} IS NOT NULL
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """,
                    [since_time.isoformat()],
                )

                time_series_data = []
                for row in cursor.fetchall():
                    time_series_data.append(
                        TimeSeriesData(
                            timestamp=datetime.fromisoformat(row[0]),
                            value=row[1],  # event_count
                            dimension=dimension,
                            metadata={"avg_duration": row[2], "success_rate": row[3]},
                        )
                    )

                return time_series_data

        except Exception as e:
            logger.error(f"❌ Error getting time series data: {e}")
            return []

    def _perform_statistical_analysis(
        self, time_series_data: List[TimeSeriesData]
    ) -> Dict[str, Any]:
        """Perform statistical analysis on time series data"""
        try:
            if not time_series_data:
                return {}

            values = [data.value for data in time_series_data]

            # Basic statistics
            mean_value = statistics.mean(values)
            median_value = statistics.median(values)
            std_value = statistics.stdev(values) if len(values) > 1 else 0
            min_value = min(values)
            max_value = max(values)

            # Trend analysis
            trend = self._calculate_trend(values)

            # Seasonality detection
            seasonality = self._detect_seasonality(values)

            # Volatility analysis
            volatility = self._calculate_volatility(values)

            return {
                "mean": mean_value,
                "median": median_value,
                "std": std_value,
                "min": min_value,
                "max": max_value,
                "trend": trend,
                "seasonality": seasonality,
                "volatility": volatility,
                "data_points": len(values),
            }

        except Exception as e:
            logger.error(f"❌ Statistical analysis failed: {e}")
            return {}

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        try:
            if len(values) < 2:
                return "insufficient_data"

            # Simple linear trend calculation
            x = list(range(len(values)))
            n = len(values)

            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(x[i] * values[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

            if slope > 0.1:
                return "increasing"
            elif slope < -0.1:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"❌ Trend calculation failed: {e}")
            return "error"

    def _detect_seasonality(self, values: List[float]) -> Dict[str, Any]:
        """Detect seasonality patterns"""
        try:
            if len(values) < 24:  # Need at least 24 data points
                return {"detected": False, "pattern": "insufficient_data"}

            # Simple seasonality detection using variance
            hourly_variance = []
            for hour in range(24):
                hour_values = [values[i] for i in range(hour, len(values), 24)]
                if len(hour_values) > 1:
                    hourly_variance.append(statistics.variance(hour_values))
                else:
                    hourly_variance.append(0)

            # Calculate seasonality score
            seasonality_score = statistics.mean(hourly_variance) / max(
                0.001, statistics.mean(values)
            )

            return {
                "detected": seasonality_score > 0.1,
                "score": seasonality_score,
                "pattern": "hourly" if seasonality_score > 0.1 else "none",
            }

        except Exception as e:
            logger.error(f"❌ Seasonality detection failed: {e}")
            return {"detected": False, "pattern": "error"}

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation)"""
        try:
            if not values:
                return 0.0

            mean_value = statistics.mean(values)
            if mean_value == 0:
                return 0.0

            std_value = statistics.stdev(values) if len(values) > 1 else 0
            return std_value / mean_value

        except Exception as e:
            logger.error(f"❌ Volatility calculation failed: {e}")
            return 0.0

    def _generate_time_series_insights(
        self,
        time_series_data: List[TimeSeriesData],
        statistical_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate insights from time series analysis"""
        insights = []

        try:
            if not time_series_data:
                insights.append("No data available for analysis")
                return insights

            # Trend insights
            trend = statistical_analysis.get("trend", "unknown")
            if trend == "increasing":
                insights.append("Usage is showing an upward trend")
            elif trend == "decreasing":
                insights.append("Usage is showing a downward trend")
            elif trend == "stable":
                insights.append("Usage is relatively stable")

            # Volatility insights
            volatility = statistical_analysis.get("volatility", 0)
            if volatility > 0.5:
                insights.append(
                    "High volatility detected - usage patterns are inconsistent"
                )
            elif volatility < 0.1:
                insights.append("Low volatility - usage patterns are very consistent")

            # Seasonality insights
            seasonality = statistical_analysis.get("seasonality", {})
            if seasonality.get("detected", False):
                insights.append(
                    f"Seasonal pattern detected: {seasonality.get('pattern', 'unknown')}"
                )

            # Performance insights
            mean_value = statistical_analysis.get("mean", 0)
            if mean_value > 1000:
                insights.append("High usage volume detected")
            elif mean_value < 100:
                insights.append("Low usage volume detected")

        except Exception as e:
            logger.error(f"❌ Insight generation failed: {e}")
            insights.append(f"Error generating insights: {e!s}")

        return insights

    def _generate_time_series_recommendations(
        self, statistical_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations from time series analysis"""
        recommendations = []

        try:
            # Trend-based recommendations
            trend = statistical_analysis.get("trend", "unknown")
            if trend == "increasing":
                recommendations.append(
                    "Consider scaling resources to handle increased demand"
                )
            elif trend == "decreasing":
                recommendations.append("Investigate reasons for declining usage")

            # Volatility-based recommendations
            volatility = statistical_analysis.get("volatility", 0)
            if volatility > 0.5:
                recommendations.append(
                    "Implement load balancing to handle usage spikes"
                )

            # Seasonality-based recommendations
            seasonality = statistical_analysis.get("seasonality", {})
            if seasonality.get("detected", False):
                recommendations.append(
                    "Implement seasonal resource allocation strategies"
                )

        except Exception as e:
            logger.error(f"❌ Recommendation generation failed: {e}")
            recommendations.append(f"Error generating recommendations: {e!s}")

        return recommendations

    def _calculate_confidence_score(
        self,
        time_series_data: List[TimeSeriesData],
        statistical_analysis: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for analysis"""
        try:
            if not time_series_data:
                return 0.0

            # Base confidence on data points
            data_points = len(time_series_data)
            base_confidence = min(
                1.0, data_points / 100.0
            )  # 100 data points = 100% confidence

            # Adjust for data quality
            volatility = statistical_analysis.get("volatility", 0)
            quality_factor = max(
                0.5, 1.0 - volatility
            )  # Lower volatility = higher quality

            # Final confidence score
            confidence_score = base_confidence * quality_factor

            return min(1.0, max(0.0, confidence_score))

        except Exception as e:
            logger.error(f"❌ Confidence score calculation failed: {e}")
            return 0.0

    def _calculate_usage_patterns(
        self, sessions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate usage patterns from sessions"""
        try:
            if not sessions:
                return {}

            # Calculate session duration patterns
            durations = [s["avg_duration"] for s in sessions]
            avg_duration = statistics.mean(durations)

            # Calculate session frequency
            session_frequency = (
                len(sessions) / 7.0
            )  # sessions per day (assuming 1 week)

            # Calculate feature diversity
            total_features = sum(s["unique_features"] for s in sessions)
            avg_features_per_session = total_features / len(sessions)

            return {
                "avg_session_duration": avg_duration,
                "session_frequency_per_day": session_frequency,
                "avg_features_per_session": avg_features_per_session,
                "total_sessions": len(sessions),
            }

        except Exception as e:
            logger.error(f"❌ Usage pattern calculation failed: {e}")
            return {}

    def _calculate_engagement_score(
        self, sessions: List[Dict[str, Any]], feature_usage: Dict[str, int]
    ) -> float:
        """Calculate user engagement score"""
        try:
            if not sessions:
                return 0.0

            # Session frequency score (0-1)
            session_frequency = len(sessions) / 7.0  # sessions per day
            frequency_score = min(1.0, session_frequency / 2.0)  # 2 sessions/day = 100%

            # Feature diversity score (0-1)
            unique_features = len(feature_usage)
            diversity_score = min(1.0, unique_features / 10.0)  # 10 features = 100%

            # Session duration score (0-1)
            avg_duration = statistics.mean([s["avg_duration"] for s in sessions])
            duration_score = min(1.0, avg_duration / 10000.0)  # 10s = 100%

            # Weighted engagement score
            engagement_score = (
                frequency_score * 0.4 + diversity_score * 0.3 + duration_score * 0.3
            )

            return min(1.0, max(0.0, engagement_score))

        except Exception as e:
            logger.error(f"❌ Engagement score calculation failed: {e}")
            return 0.0

    def _calculate_retention_rate(
        self, sessions: List[Dict[str, Any]], time_range_hours: int
    ) -> float:
        """Calculate user retention rate"""
        try:
            if not sessions:
                return 0.0

            # Calculate days between first and last session
            first_session = min(s["first_event"] for s in sessions)
            last_session = max(s["last_event"] for s in sessions)

            first_date = datetime.fromisoformat(first_session)
            last_date = datetime.fromisoformat(last_session)
            days_active = (last_date - first_date).days + 1

            # Calculate retention rate
            total_days = time_range_hours / 24.0
            retention_rate = min(1.0, days_active / total_days)

            return retention_rate

        except Exception as e:
            logger.error(f"❌ Retention rate calculation failed: {e}")
            return 0.0

    def _get_total_users(self, since_time: datetime) -> int:
        """Get total number of users in time range"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(DISTINCT user_id)
                    FROM usage_events
                    WHERE timestamp >= ? AND user_id IS NOT NULL
                """,
                    [since_time.isoformat()],
                )

                return cursor.fetchone()[0] or 0

        except Exception as e:
            logger.error(f"❌ Error getting total users: {e}")
            return 0

    def _calculate_usage_trend(self, feature_name: str, time_range_hours: int) -> str:
        """Calculate usage trend for a feature"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                # Get usage data for the feature over time
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                cursor = conn.execute(
                    """
                    SELECT 
                        strftime('%Y-%m-%d', timestamp) as date,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ? AND feature_name = ?
                    GROUP BY date
                    ORDER BY date
                """,
                    [since_time.isoformat(), feature_name],
                )

                daily_usage = [row[1] for row in cursor.fetchall()]

                if len(daily_usage) < 2:
                    return "insufficient_data"

                # Calculate trend
                trend = self._calculate_trend(daily_usage)
                return trend

        except Exception as e:
            logger.error(f"❌ Usage trend calculation failed: {e}")
            return "error"

    def _get_peak_usage_hours(self, hourly_usage: Dict[int, int]) -> List[int]:
        """Get peak usage hours"""
        try:
            if not hourly_usage:
                return []

            # Find hours with usage above 80% of maximum
            max_usage = max(hourly_usage.values())
            threshold = max_usage * 0.8

            peak_hours = [
                hour for hour, usage in hourly_usage.items() if usage >= threshold
            ]

            return sorted(peak_hours)

        except Exception as e:
            logger.error(f"❌ Peak usage hours calculation failed: {e}")
            return []

    def _calculate_feature_correlation(
        self, feature_name: str, time_range_hours: int
    ) -> Dict[str, float]:
        """Calculate correlation with other features"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                # Get usage data for all features
                cursor = conn.execute(
                    """
                    SELECT 
                        feature_name,
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ? AND feature_name IS NOT NULL
                    GROUP BY feature_name, hour
                """,
                    [since_time.isoformat()],
                )

                feature_hourly_usage = defaultdict(lambda: defaultdict(int))
                for feat_name, hour, usage_count in cursor.fetchall():
                    feature_hourly_usage[feat_name][hour] = usage_count

                # Calculate correlation with target feature
                target_usage = feature_hourly_usage[feature_name]
                correlations = {}

                for other_feature, other_usage in feature_hourly_usage.items():
                    if other_feature != feature_name:
                        correlation = self._calculate_correlation(
                            target_usage, other_usage
                        )
                        if correlation is not None:
                            correlations[other_feature] = correlation

                return correlations

        except Exception as e:
            logger.error(f"❌ Feature correlation calculation failed: {e}")
            return {}

    def _calculate_correlation(
        self, usage1: Dict[str, int], usage2: Dict[str, int]
    ) -> Optional[float]:
        """Calculate correlation between two usage patterns"""
        try:
            # Get common time points
            common_times = set(usage1.keys()) & set(usage2.keys())

            if len(common_times) < 2:
                return None

            # Extract values for common time points
            values1 = [usage1[time] for time in common_times]
            values2 = [usage2[time] for time in common_times]

            # Calculate Pearson correlation
            n = len(values1)
            sum1 = sum(values1)
            sum2 = sum(values2)
            sum1_sq = sum(x**2 for x in values1)
            sum2_sq = sum(x**2 for x in values2)
            sum12 = sum(values1[i] * values2[i] for i in range(n))

            numerator = n * sum12 - sum1 * sum2
            denominator = ((n * sum1_sq - sum1**2) * (n * sum2_sq - sum2**2)) ** 0.5

            if denominator == 0:
                return None

            correlation = numerator / denominator
            return correlation

        except Exception as e:
            logger.error(f"❌ Correlation calculation failed: {e}")
            return None

    def _calculate_business_impact_score(
        self,
        usage_count: int,
        user_adoption_rate: float,
        success_rate: float,
        avg_duration: float,
    ) -> float:
        """Calculate business impact score for a feature"""
        try:
            # Usage volume score (0-1)
            usage_score = min(1.0, usage_count / 10000.0)  # 10k uses = 100%

            # User adoption score (0-1)
            adoption_score = user_adoption_rate

            # Success rate score (0-1)
            success_score = success_rate

            # Efficiency score (0-1) - lower duration is better
            efficiency_score = max(0.0, 1.0 - (avg_duration / 10000.0))  # 10s = 0%

            # Weighted business impact score
            impact_score = (
                usage_score * 0.3
                + adoption_score * 0.3
                + success_score * 0.2
                + efficiency_score * 0.2
            )

            return min(1.0, max(0.0, impact_score))

        except Exception as e:
            logger.error(f"❌ Business impact score calculation failed: {e}")
            return 0.0

    def get_analysis_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get analysis summary"""
        try:
            return {
                "time_range_hours": time_range_hours,
                "analysis_types": ["time_series", "user_behavior", "feature_patterns"],
                "performance_metrics": {
                    "avg_analysis_time_ms": (
                        statistics.mean(self._analysis_times)
                        if self._analysis_times
                        else 0.0
                    ),
                    "total_analyses": len(self._analysis_times),
                },
                "cache_status": {
                    "time_series_cache_size": len(self._time_series_cache),
                    "analysis_cache_size": len(self._analysis_cache),
                },
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error getting analysis summary: {e}")
            return {"error": str(e)}


# Factory function
def create_multi_dimensional_analysis(
    metrics_db_path: str, config: Optional[Dict[str, Any]] = None
) -> MultiDimensionalAnalysis:
    """Factory function để create multi-dimensional analysis"""
    return MultiDimensionalAnalysis(metrics_db_path, config)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Dimensional Analysis")
    parser.add_argument("--metrics-db", required=True, help="Metrics database path")
    parser.add_argument("--time-series", help="Analyze time series for dimension")
    parser.add_argument(
        "--user-behavior", action="store_true", help="Analyze user behavior"
    )
    parser.add_argument(
        "--feature-patterns", action="store_true", help="Analyze feature patterns"
    )
    parser.add_argument(
        "--time-range", type=int, default=24, help="Time range in hours"
    )
    parser.add_argument("--summary", action="store_true", help="Get analysis summary")

    args = parser.parse_args()

    # Create analysis engine
    analysis = create_multi_dimensional_analysis(args.metrics_db)

    if args.time_series:
        result = analysis.analyze_time_series(args.time_series, args.time_range)
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.user_behavior:
        results = analysis.analyze_user_behavior(args.time_range)
        print(
            json.dumps(
                {k: asdict(v) for k, v in results.items()}, indent=2, default=str
            )
        )
    elif args.feature_patterns:
        results = analysis.analyze_feature_usage_patterns(args.time_range)
        print(
            json.dumps(
                {k: asdict(v) for k, v in results.items()}, indent=2, default=str
            )
        )
    elif args.summary:
        summary = analysis.get_analysis_summary(args.time_range)
        print(json.dumps(summary, indent=2, default=str))
    else:
        print("Use --help for usage information")
