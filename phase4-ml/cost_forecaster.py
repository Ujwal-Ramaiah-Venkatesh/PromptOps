"""
Cost Forecasting Engine
========================

ML-based predictive cost forecasting using time series models.
Phase 4 - Advanced Intelligence

Author: PromptOps Team
Date: 2026-05-01
Phase: 4 - Advanced Intelligence
"""

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import pickle
import os
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


class CostForecaster:
    """
    Forecasts future cloud costs using Facebook Prophet.

    Features:
    - Daily, weekly, monthly predictions
    - Confidence intervals
    - Trend and seasonality detection
    - Budget exhaustion predictions
    """

    def __init__(self, seasonality_mode: str = 'additive'):
        """
        Initialize cost forecaster.

        Args:
            seasonality_mode: 'additive' or 'multiplicative'
        """
        self.seasonality_mode = seasonality_mode
        self.model = None
        self.trained = False
        self.training_history = None

        logger.info(f"Cost Forecaster initialized (seasonality: {seasonality_mode})")

    def prepare_data(self, cost_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare cost data for Prophet.

        Args:
            cost_data: List of cost records with date and cost

        Returns:
            DataFrame in Prophet format (ds, y columns)
        """
        if not cost_data:
            return pd.DataFrame()

        df = pd.DataFrame(cost_data)

        # Ensure required columns
        if 'date' not in df.columns or 'cost' not in df.columns:
            raise ValueError("Cost data must contain 'date' and 'cost' columns")

        # Convert to Prophet format
        df_prophet = pd.DataFrame({
            'ds': pd.to_datetime(df['date']),
            'y': df['cost']
        })

        # Sort by date
        df_prophet = df_prophet.sort_values('ds').reset_index(drop=True)

        # Store original data
        self.training_history = df_prophet.copy()

        return df_prophet

    def train(
        self,
        cost_data: List[Dict[str, Any]],
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = False
    ) -> Dict[str, Any]:
        """
        Train forecasting model.

        Args:
            cost_data: Historical cost data
            weekly_seasonality: Enable weekly patterns
            yearly_seasonality: Enable yearly patterns

        Returns:
            Training results
        """
        try:
            # Prepare data
            df = self.prepare_data(cost_data)

            if df.empty or len(df) < 7:
                return {
                    'success': False,
                    'error': 'Insufficient data (need at least 7 days)'
                }

            # Initialize Prophet model
            self.model = Prophet(
                seasonality_mode=self.seasonality_mode,
                weekly_seasonality=weekly_seasonality,
                yearly_seasonality=yearly_seasonality,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                interval_width=0.95
            )

            # Fit model
            self.model.fit(df)
            self.trained = True

            # Calculate training metrics
            df_pred = self.model.predict(df)
            mae = mean_absolute_error(df['y'], df_pred['yhat'])
            rmse = np.sqrt(mean_squared_error(df['y'], df_pred['yhat']))
            mape = np.mean(np.abs((df['y'] - df_pred['yhat']) / df['y'])) * 100

            logger.info(f"Model trained on {len(df)} days (MAE: ${mae:.2f}, MAPE: {mape:.1f}%)")

            return {
                'success': True,
                'training_days': len(df),
                'date_range': {
                    'start': df['ds'].min().isoformat(),
                    'end': df['ds'].max().isoformat()
                },
                'metrics': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'mape': float(mape)
                },
                'average_daily_cost': float(df['y'].mean())
            }

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def forecast(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate cost forecast.

        Args:
            days: Number of days to forecast

        Returns:
            Forecast results with predictions and confidence intervals
        """
        if not self.trained or self.model is None:
            return {
                'success': False,
                'error': 'Model not trained yet'
            }

        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=days)

            # Generate predictions
            forecast_df = self.model.predict(future)

            # Extract forecast period only (exclude historical)
            last_training_date = self.training_history['ds'].max()
            forecast_only = forecast_df[forecast_df['ds'] > last_training_date].copy()

            # Prepare forecast data
            forecasts = []
            for _, row in forecast_only.iterrows():
                forecasts.append({
                    'date': row['ds'].isoformat(),
                    'predicted_cost': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper']),
                    'confidence_interval': float(row['yhat_upper'] - row['yhat_lower'])
                })

            # Calculate summary statistics
            total_forecast = sum(f['predicted_cost'] for f in forecasts)
            avg_daily = total_forecast / len(forecasts) if forecasts else 0

            # Compare to historical average
            historical_avg = float(self.training_history['y'].mean())
            trend_change = ((avg_daily - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

            return {
                'success': True,
                'forecast_days': days,
                'forecast_period': {
                    'start': forecasts[0]['date'] if forecasts else None,
                    'end': forecasts[-1]['date'] if forecasts else None
                },
                'total_forecast': total_forecast,
                'average_daily': avg_daily,
                'historical_average': historical_avg,
                'trend_change_pct': trend_change,
                'confidence': 'high' if days <= 30 else 'medium' if days <= 90 else 'low',
                'forecasts': forecasts
            }

        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def forecast_multiple_periods(self) -> Dict[str, Any]:
        """
        Generate forecasts for multiple time periods (7, 30, 90 days).

        Returns:
            Forecasts for multiple periods
        """
        if not self.trained:
            return {
                'success': False,
                'error': 'Model not trained yet'
            }

        periods = {
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90
        }

        results = {}
        for period_name, days in periods.items():
            forecast = self.forecast(days)
            if forecast['success']:
                results[period_name] = {
                    'days': days,
                    'total_cost': forecast['total_forecast'],
                    'average_daily': forecast['average_daily'],
                    'trend_change_pct': forecast['trend_change_pct'],
                    'confidence': forecast['confidence']
                }

        return {
            'success': True,
            'periods': results,
            'generated_at': datetime.utcnow().isoformat()
        }

    def predict_budget_exhaustion(
        self,
        current_budget: float,
        spent_to_date: float
    ) -> Dict[str, Any]:
        """
        Predict when budget will be exhausted.

        Args:
            current_budget: Total budget
            spent_to_date: Amount spent so far

        Returns:
            Budget exhaustion prediction
        """
        if not self.trained:
            return {
                'success': False,
                'error': 'Model not trained yet'
            }

        remaining_budget = current_budget - spent_to_date

        if remaining_budget <= 0:
            return {
                'success': True,
                'budget_exhausted': True,
                'days_until_exhaustion': 0,
                'message': 'Budget already exhausted',
                'recommendation': 'Immediate action required'
            }

        # Forecast 180 days (max)
        forecast = self.forecast(180)

        if not forecast['success']:
            return forecast

        # Find when cumulative cost exceeds remaining budget
        cumulative_cost = 0
        exhaustion_date = None
        days_until_exhaustion = None

        for i, pred in enumerate(forecast['forecasts'], 1):
            cumulative_cost += pred['predicted_cost']
            if cumulative_cost >= remaining_budget:
                exhaustion_date = pred['date']
                days_until_exhaustion = i
                break

        if exhaustion_date is None:
            return {
                'success': True,
                'budget_exhausted': False,
                'days_until_exhaustion': None,
                'message': 'Budget sufficient for at least 180 days',
                'recommendation': 'Continue monitoring',
                'remaining_budget': remaining_budget,
                'projected_180day_cost': cumulative_cost
            }

        # Calculate burn rate
        burn_rate = remaining_budget / days_until_exhaustion if days_until_exhaustion > 0 else 0

        return {
            'success': True,
            'budget_exhausted': False,
            'days_until_exhaustion': days_until_exhaustion,
            'exhaustion_date': exhaustion_date,
            'remaining_budget': remaining_budget,
            'daily_burn_rate': burn_rate,
            'recommendation': self._get_budget_recommendation(days_until_exhaustion),
            'severity': self._calculate_budget_severity(days_until_exhaustion)
        }

    def _get_budget_recommendation(self, days_until_exhaustion: int) -> str:
        """Generate budget recommendation based on days remaining."""
        if days_until_exhaustion < 7:
            return 'Critical: Budget will exhaust within a week - immediate cost reduction required'
        elif days_until_exhaustion < 30:
            return 'Warning: Budget will exhaust within a month - implement cost controls'
        elif days_until_exhaustion < 60:
            return 'Caution: Budget running low - review spending patterns'
        else:
            return 'Normal: Budget on track - continue monitoring'

    def _calculate_budget_severity(self, days_until_exhaustion: int) -> str:
        """Calculate budget severity level."""
        if days_until_exhaustion < 7:
            return 'critical'
        elif days_until_exhaustion < 30:
            return 'high'
        elif days_until_exhaustion < 60:
            return 'medium'
        else:
            return 'low'

    def get_trend_analysis(self) -> Dict[str, Any]:
        """
        Analyze cost trends from trained model.

        Returns:
            Trend analysis results
        """
        if not self.trained or self.model is None:
            return {
                'success': False,
                'error': 'Model not trained yet'
            }

        try:
            # Get trend component
            forecast_df = self.model.predict(self.training_history)

            # Calculate trend statistics
            trend = forecast_df['trend'].values
            trend_start = float(trend[0])
            trend_end = float(trend[-1])
            trend_change = trend_end - trend_start
            trend_pct = (trend_change / trend_start * 100) if trend_start > 0 else 0

            # Determine trend direction
            if abs(trend_pct) < 5:
                direction = 'stable'
            elif trend_pct > 0:
                direction = 'increasing'
            else:
                direction = 'decreasing'

            return {
                'success': True,
                'trend_direction': direction,
                'trend_change': trend_change,
                'trend_change_pct': trend_pct,
                'start_value': trend_start,
                'end_value': trend_end,
                'interpretation': self._interpret_trend(direction, trend_pct)
            }

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _interpret_trend(self, direction: str, change_pct: float) -> str:
        """Interpret trend results."""
        if direction == 'stable':
            return 'Costs are stable with minimal trend'
        elif direction == 'increasing':
            if abs(change_pct) > 50:
                return f'Costs are rapidly increasing ({change_pct:+.1f}%) - investigate causes'
            elif abs(change_pct) > 20:
                return f'Costs are moderately increasing ({change_pct:+.1f}%) - monitor closely'
            else:
                return f'Costs are slowly increasing ({change_pct:+.1f}%) - normal growth'
        else:  # decreasing
            if abs(change_pct) > 50:
                return f'Costs are rapidly decreasing ({change_pct:+.1f}%) - verify accuracy'
            elif abs(change_pct) > 20:
                return f'Costs are moderately decreasing ({change_pct:+.1f}%) - good optimization'
            else:
                return f'Costs are slowly decreasing ({change_pct:+.1f}%) - slight improvement'

    def save_model(self, filepath: str) -> bool:
        """Save trained model to file."""
        try:
            if not self.trained:
                logger.warning("No trained model to save")
                return False

            model_data = {
                'model': self.model,
                'training_history': self.training_history,
                'seasonality_mode': self.seasonality_mode,
                'trained': self.trained
            }

            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Model saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """Load trained model from file."""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found: {filepath}")
                return False

            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.model = model_data['model']
            self.training_history = model_data['training_history']
            self.seasonality_mode = model_data['seasonality_mode']
            self.trained = model_data['trained']

            logger.info(f"Model loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False


# Test function
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("  Cost Forecasting Test")
    print("  Phase 4 - Advanced Intelligence")
    print("=" * 60)

    # Generate sample cost data with trend
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', end='2026-04-30', freq='D')

    # Base cost with upward trend
    base_cost = 100 + np.arange(len(dates)) * 0.3

    # Add weekly seasonality (weekday vs weekend)
    weekly_pattern = np.sin(np.arange(len(dates)) * 2 * np.pi / 7) * 10

    # Combine with noise
    costs = base_cost + weekly_pattern + np.random.normal(0, 5, len(dates))

    # Prepare data
    cost_data = [
        {'date': date.strftime('%Y-%m-%d'), 'cost': cost}
        for date, cost in zip(dates, costs)
    ]

    # Initialize forecaster
    forecaster = CostForecaster()

    # Train model
    print("\n[1] Training forecasting model...")
    training_result = forecaster.train(cost_data)

    if training_result['success']:
        print(f"[PASS] Model trained successfully:")
        print(f"   Training days: {training_result['training_days']}")
        print(f"   Date range: {training_result['date_range']['start']} to {training_result['date_range']['end']}")
        print(f"   MAE: ${training_result['metrics']['mae']:.2f}")
        print(f"   MAPE: {training_result['metrics']['mape']:.1f}%")
        print(f"   Average daily cost: ${training_result['average_daily_cost']:.2f}")

        # Generate 30-day forecast
        print("\n[2] Generating 30-day forecast...")
        forecast = forecaster.forecast(30)

        if forecast['success']:
            print(f"[PASS] Forecast generated:")
            print(f"   Forecast period: {forecast['forecast_period']['start']} to {forecast['forecast_period']['end']}")
            print(f"   Total forecast (30 days): ${forecast['total_forecast']:.2f}")
            print(f"   Average daily: ${forecast['average_daily']:.2f}")
            print(f"   Historical average: ${forecast['historical_average']:.2f}")
            print(f"   Trend change: {forecast['trend_change_pct']:+.1f}%")
            print(f"   Confidence: {forecast['confidence']}")

            # Show first 5 days
            print(f"\n   First 5 days:")
            for i, pred in enumerate(forecast['forecasts'][:5], 1):
                print(f"   {i}. {pred['date'][:10]}: ${pred['predicted_cost']:.2f} "
                      f"(${pred['lower_bound']:.2f} - ${pred['upper_bound']:.2f})")

        # Multiple period forecasts
        print("\n[3] Generating multi-period forecasts...")
        multi_forecast = forecaster.forecast_multiple_periods()

        if multi_forecast['success']:
            print(f"[PASS] Multi-period forecasts:")
            for period, data in multi_forecast['periods'].items():
                print(f"   {period.capitalize()} ({data['days']} days): ${data['total_cost']:.2f} "
                      f"(trend: {data['trend_change_pct']:+.1f}%, confidence: {data['confidence']})")

        # Budget exhaustion
        print("\n[4] Predicting budget exhaustion...")
        budget = 5000
        spent = 1500
        budget_pred = forecaster.predict_budget_exhaustion(budget, spent)

        if budget_pred['success']:
            if budget_pred.get('days_until_exhaustion'):
                print(f"[PASS] Budget prediction:")
                print(f"   Days until exhaustion: {budget_pred['days_until_exhaustion']}")
                print(f"   Exhaustion date: {budget_pred['exhaustion_date'][:10]}")
                print(f"   Daily burn rate: ${budget_pred['daily_burn_rate']:.2f}")
                print(f"   Severity: {budget_pred['severity']}")
                print(f"   Recommendation: {budget_pred['recommendation']}")
            else:
                print(f"[PASS] {budget_pred['message']}")

        # Trend analysis
        print("\n[5] Analyzing cost trends...")
        trend = forecaster.get_trend_analysis()

        if trend['success']:
            print(f"[PASS] Trend analysis:")
            print(f"   Direction: {trend['trend_direction']}")
            print(f"   Change: ${trend['trend_change']:+.2f} ({trend['trend_change_pct']:+.1f}%)")
            print(f"   Interpretation: {trend['interpretation']}")

        print("\n[PASS] Cost Forecasting Test Complete")
    else:
        print(f"\n[FAIL] Training failed: {training_result.get('error')}")

    print("\n" + "=" * 60)
