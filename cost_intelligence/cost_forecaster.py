"""
Cost Forecasting Engine
========================

ML-powered cost forecasting using Facebook Prophet.

Features:
- Time series forecasting
- Trend and seasonality detection
- Confidence intervals
- Multi-horizon predictions
- Target <5% MAPE accuracy

Author: PromptOps Team - Q3 2026
Date: July 9, 2026
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error

try:
    from prophet import Prophet
except ImportError:
    Prophet = None


class _LinearForecastModel:
    """Small fallback model for environments without Prophet."""

    def fit(self, data: pd.DataFrame):
        self.data = data.copy()
        self.x = np.arange(len(data), dtype=float)
        self.coefficients = np.polyfit(self.x, data['y'].to_numpy(dtype=float), 1)
        fitted = np.polyval(self.coefficients, self.x)
        self.residual_std = float(np.std(data['y'].to_numpy(dtype=float) - fitted))

    def make_future_dataframe(self, periods: int) -> pd.DataFrame:
        last_date = self.data['ds'].iloc[-1]
        future_dates = [last_date + timedelta(days=index) for index in range(1, periods + 1)]
        return pd.concat([
            self.data[['ds']],
            pd.DataFrame({'ds': future_dates}),
        ], ignore_index=True)

    def predict(self, dates: pd.DataFrame) -> pd.DataFrame:
        x = np.arange(len(dates), dtype=float)
        predicted = np.polyval(self.coefficients, x)
        interval = max(self.residual_std * 1.96, 1.0)
        return pd.DataFrame({
            'ds': dates['ds'],
            'yhat': predicted,
            'yhat_lower': predicted - interval,
            'yhat_upper': predicted + interval,
            'trend': predicted,
        })


@dataclass
class ForecastConfig:
    """Configuration for cost forecasting"""
    # Forecast horizon (days)
    forecast_days: int = 30

    # Seasonality
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False

    # Changepoint detection
    changepoint_prior_scale: float = 0.05
    seasonality_prior_scale: float = 10.0

    # Confidence intervals
    interval_width: float = 0.95

    # Growth type
    growth: str = 'linear'  # 'linear' or 'logistic'


@dataclass
class Forecast:
    """Cost forecast result"""
    date: datetime
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    trend: float
    confidence: float


@dataclass
class ForecastAnalysis:
    """Forecast analysis and metrics"""
    forecasts: List[Forecast]
    total_predicted_cost: float
    average_daily_cost: float
    cost_trend: str  # 'increasing', 'decreasing', 'stable'
    trend_percentage: float
    peak_date: datetime
    peak_cost: float
    savings_opportunity: Optional[float] = None
    mape: Optional[float] = None
    mae: Optional[float] = None


class CostForecaster:
    """
    Cost forecasting engine using Facebook Prophet.

    Features:
    - Automatic trend detection
    - Seasonality modeling
    - Confidence intervals
    - Multi-horizon forecasting
    - Model evaluation

    Example:
        forecaster = CostForecaster()
        forecast = forecaster.forecast(historical_data, days=30)
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        """Initialize forecaster with configuration"""
        self.config = config or ForecastConfig()
        self.model = None
        self.training_data: Optional[pd.DataFrame] = None
        self.is_trained: bool = False

    def forecast(
        self,
        historical_data: List[Dict],
        days: Optional[int] = None,
        resource_id: Optional[str] = None
    ) -> ForecastAnalysis:
        """
        Generate cost forecast.

        Args:
            historical_data: List of {timestamp, value} dicts
            days: Forecast horizon (default: from config)
            resource_id: Optional resource identifier

        Returns:
            Forecast analysis with predictions
        """
        days = days or self.config.forecast_days

        # Prepare data
        df = self._prepare_data(historical_data)

        # Train model
        self._train_model(df)

        # Generate forecast
        future = self.model.make_future_dataframe(periods=days)
        forecast_df = self.model.predict(future)

        # Extract future predictions
        future_forecasts = forecast_df.tail(days)

        # Build forecast objects
        forecasts = []
        for _, row in future_forecasts.iterrows():
            forecast = Forecast(
                date=row['ds'],
                predicted_cost=max(0, row['yhat']),
                lower_bound=max(0, row['yhat_lower']),
                upper_bound=max(0, row['yhat_upper']),
                trend=row['trend'],
                confidence=self._calculate_forecast_confidence(row)
            )
            forecasts.append(forecast)

        # Analyze forecast
        analysis = self._analyze_forecast(forecasts, df)

        # Calculate metrics if we have actual future data
        if len(historical_data) > days:
            analysis.mape = self._calculate_mape(historical_data[-days:], forecasts[:len(historical_data[-days:])])
            analysis.mae = self._calculate_mae(historical_data[-days:], forecasts[:len(historical_data[-days:])])

        return analysis

    def forecast_with_scenarios(
        self,
        historical_data: List[Dict],
        scenarios: List[str] = None
    ) -> Dict[str, ForecastAnalysis]:
        """
        Generate multiple forecast scenarios.

        Args:
            historical_data: Historical cost data
            scenarios: List of scenario names ('baseline', 'optimistic', 'pessimistic')

        Returns:
            Dictionary of scenario name -> forecast analysis
        """
        if scenarios is None:
            scenarios = ['baseline', 'optimistic', 'pessimistic']

        results = {}

        for scenario in scenarios:
            # Adjust configuration based on scenario
            config = self._get_scenario_config(scenario)
            forecaster = CostForecaster(config)
            analysis = forecaster.forecast(historical_data)
            results[scenario] = analysis

        return results

    def evaluate_model(
        self,
        historical_data: List[Dict],
        test_size: int = 7
    ) -> Dict:
        """
        Evaluate forecast model accuracy.

        Args:
            historical_data: Historical cost data
            test_size: Number of days to hold out for testing

        Returns:
            Evaluation metrics
        """
        if len(historical_data) < test_size + 30:
            raise ValueError("Insufficient data for evaluation")

        # Split data
        train_data = historical_data[:-test_size]
        test_data = historical_data[-test_size:]

        # Train on historical data
        df = self._prepare_data(train_data)
        self._train_model(df)

        # Forecast test period
        future = self.model.make_future_dataframe(periods=test_size)
        forecast_df = self.model.predict(future)
        predictions = forecast_df.tail(test_size)

        # Calculate metrics
        actual = np.array([d['value'] for d in test_data])
        predicted = predictions['yhat'].values

        mape = mean_absolute_percentage_error(actual, predicted) * 100
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))

        # Calculate direction accuracy
        direction_correct = 0
        for i in range(1, len(actual)):
            actual_direction = actual[i] > actual[i-1]
            predicted_direction = predicted[i] > predicted[i-1]
            if actual_direction == predicted_direction:
                direction_correct += 1

        direction_accuracy = direction_correct / (len(actual) - 1) * 100

        return {
            'mape': round(mape, 2),
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'direction_accuracy': round(direction_accuracy, 2),
            'test_size': test_size,
            'meets_target': mape < 5.0,  # Target <5% MAPE
        }

    def detect_cost_spikes(
        self,
        historical_data: List[Dict],
        threshold_std: float = 2.0
    ) -> List[Dict]:
        """
        Detect cost spikes in historical data.

        Args:
            historical_data: Cost data
            threshold_std: Standard deviation threshold

        Returns:
            List of detected spikes
        """
        values = np.array([d['value'] for d in historical_data])
        mean = np.mean(values)
        std = np.std(values)

        spikes = []
        for i, data_point in enumerate(historical_data):
            if abs(data_point['value'] - mean) > threshold_std * std:
                spikes.append({
                    'index': i,
                    'timestamp': data_point['timestamp'],
                    'value': data_point['value'],
                    'expected': mean,
                    'deviation': data_point['value'] - mean,
                    'deviation_std': abs(data_point['value'] - mean) / std
                })

        return sorted(spikes, key=lambda x: x['deviation_std'], reverse=True)

    # ========================================================================
    # Internal Methods
    # ========================================================================

    def _prepare_data(self, data: List[Dict]) -> pd.DataFrame:
        """Prepare data for Prophet (requires 'ds' and 'y' columns)"""
        df = pd.DataFrame([
            {
                'ds': d['timestamp'] if isinstance(d['timestamp'], datetime)
                      else datetime.fromisoformat(d['timestamp']),
                'y': d['value']
            }
            for d in data
        ])
        return df

    def _train_model(self, df: pd.DataFrame):
        """Train Prophet model"""
        if Prophet is None:
            self.model = _LinearForecastModel()
            self.model.fit(df)
        else:
            self.model = Prophet(
                yearly_seasonality=self.config.yearly_seasonality,
                weekly_seasonality=self.config.weekly_seasonality,
                daily_seasonality=self.config.daily_seasonality,
                changepoint_prior_scale=self.config.changepoint_prior_scale,
                seasonality_prior_scale=self.config.seasonality_prior_scale,
                interval_width=self.config.interval_width,
                growth=self.config.growth
            )

            import logging
            logging.getLogger('prophet').setLevel(logging.WARNING)
            self.model.fit(df)
        self.training_data = df
        self.is_trained = True

    def _analyze_forecast(
        self,
        forecasts: List[Forecast],
        historical_df: pd.DataFrame
    ) -> ForecastAnalysis:
        """Analyze forecast results"""
        # Calculate totals
        total_cost = sum(f.predicted_cost for f in forecasts)
        avg_cost = total_cost / len(forecasts)

        # Detect trend
        first_week_avg = np.mean([f.predicted_cost for f in forecasts[:7]])
        last_week_avg = np.mean([f.predicted_cost for f in forecasts[-7:]])
        trend_change = (last_week_avg - first_week_avg) / first_week_avg * 100

        if abs(trend_change) < 5:
            trend = 'stable'
        elif trend_change > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        # Find peak
        peak_forecast = max(forecasts, key=lambda x: x.predicted_cost)

        # Estimate savings opportunity
        savings = None
        if trend == 'increasing':
            # Potential savings if trend is reversed
            baseline = np.mean(historical_df['y'].tail(7))
            excess = total_cost - (baseline * len(forecasts))
            if excess > 0:
                savings = round(excess, 2)

        return ForecastAnalysis(
            forecasts=forecasts,
            total_predicted_cost=round(total_cost, 2),
            average_daily_cost=round(avg_cost, 2),
            cost_trend=trend,
            trend_percentage=round(trend_change, 2),
            peak_date=peak_forecast.date,
            peak_cost=round(peak_forecast.predicted_cost, 2),
            savings_opportunity=savings
        )

    def _calculate_forecast_confidence(self, row: pd.Series) -> float:
        """Calculate confidence score for forecast point"""
        # Confidence based on prediction interval width
        predicted = row['yhat']
        lower = row['yhat_lower']
        upper = row['yhat_upper']

        if predicted <= 0:
            return 0.5

        interval_width = upper - lower
        relative_width = interval_width / predicted

        # Narrower interval = higher confidence
        confidence = max(0.0, min(1.0, 1.0 - (relative_width / 2.0)))
        return round(confidence, 3)

    def _get_scenario_config(self, scenario: str) -> ForecastConfig:
        """Get configuration for specific scenario"""
        config = ForecastConfig()

        if scenario == 'optimistic':
            # More aggressive seasonality, lower growth
            config.seasonality_prior_scale = 15.0
            config.changepoint_prior_scale = 0.03

        elif scenario == 'pessimistic':
            # More conservative, higher growth
            config.seasonality_prior_scale = 5.0
            config.changepoint_prior_scale = 0.08

        # 'baseline' uses default config

        return config

    def _calculate_mape(self, actual_data: List[Dict], forecasts: List[Forecast]) -> float:
        """Calculate Mean Absolute Percentage Error"""
        if len(actual_data) != len(forecasts):
            return None

        actual = np.array([d['value'] for d in actual_data])
        predicted = np.array([f.predicted_cost for f in forecasts])

        return round(mean_absolute_percentage_error(actual, predicted) * 100, 2)

    def _calculate_mae(self, actual_data: List[Dict], forecasts: List[Forecast]) -> float:
        """Calculate Mean Absolute Error"""
        if len(actual_data) != len(forecasts):
            return None

        actual = np.array([d['value'] for d in actual_data])
        predicted = np.array([f.predicted_cost for f in forecasts])

        return round(mean_absolute_error(actual, predicted), 2)


# ============================================================================
# Utility Functions
# ============================================================================

def generate_cost_projection(
    current_monthly_cost: float,
    growth_rate: float,
    months: int = 12
) -> List[Dict]:
    """
    Generate simple cost projection based on growth rate.

    Args:
        current_monthly_cost: Current monthly cost
        growth_rate: Monthly growth rate (e.g., 0.05 for 5%)
        months: Number of months to project

    Returns:
        List of monthly cost projections
    """
    projections = []
    start_date = datetime.utcnow()

    for month in range(months):
        cost = current_monthly_cost * ((1 + growth_rate) ** month)
        projections.append({
            'month': start_date + timedelta(days=30 * month),
            'projected_cost': round(cost, 2),
            'growth_from_baseline': round((cost - current_monthly_cost) / current_monthly_cost * 100, 2)
        })

    return projections


def compare_forecasts(
    forecast1: ForecastAnalysis,
    forecast2: ForecastAnalysis,
    label1: str = "Forecast 1",
    label2: str = "Forecast 2"
) -> Dict:
    """
    Compare two forecasts and generate insights.

    Returns:
        Comparison analysis
    """
    cost_diff = forecast2.total_predicted_cost - forecast1.total_predicted_cost
    cost_diff_pct = cost_diff / forecast1.total_predicted_cost * 100

    return {
        'forecasts': {
            label1: {
                'total_cost': forecast1.total_predicted_cost,
                'avg_daily_cost': forecast1.average_daily_cost,
                'trend': forecast1.cost_trend,
            },
            label2: {
                'total_cost': forecast2.total_predicted_cost,
                'avg_daily_cost': forecast2.average_daily_cost,
                'trend': forecast2.cost_trend,
            }
        },
        'difference': {
            'absolute': round(cost_diff, 2),
            'percentage': round(cost_diff_pct, 2),
            'interpretation': 'higher' if cost_diff > 0 else 'lower'
        },
        'recommendation': _get_forecast_recommendation(cost_diff_pct)
    }


def _get_forecast_recommendation(diff_pct: float) -> str:
    """Get recommendation based on forecast difference"""
    if abs(diff_pct) < 5:
        return "Forecasts are similar. Either scenario is plausible."
    elif diff_pct > 20:
        return "Significant cost increase expected. Consider optimization strategies."
    elif diff_pct < -20:
        return "Significant cost decrease expected. Verify assumptions."
    else:
        return "Moderate variance between scenarios. Monitor closely."
