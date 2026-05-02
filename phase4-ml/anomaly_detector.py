"""
Cost Anomaly Detection Engine
==============================

ML-based anomaly detection for cloud cost spikes.
Phase 4 - Advanced Intelligence

Author: PromptOps Team
Date: 2026-05-01
Phase: 4 - Advanced Intelligence
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class CostAnomalyDetector:
    """
    Detects anomalies in cloud cost data using multiple methods.

    Methods:
    - Statistical (Z-score, IQR)
    - Machine Learning (Isolation Forest)
    - Time series decomposition
    """

    def __init__(self, sensitivity: str = 'medium'):
        """
        Initialize anomaly detector.

        Args:
            sensitivity: Detection sensitivity ('low', 'medium', 'high')
        """
        self.sensitivity = sensitivity
        self.scaler = StandardScaler()
        self.model = None
        self.trained = False

        # Sensitivity thresholds
        self.thresholds = {
            'low': {'z_score': 3.5, 'iqr_multiplier': 3.0, 'contamination': 0.05},
            'medium': {'z_score': 3.0, 'iqr_multiplier': 2.5, 'contamination': 0.1},
            'high': {'z_score': 2.5, 'iqr_multiplier': 2.0, 'contamination': 0.15}
        }

        logger.info(f"Cost Anomaly Detector initialized (sensitivity: {sensitivity})")

    def prepare_data(self, cost_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare cost data for analysis.

        Args:
            cost_data: List of cost records with date and amount

        Returns:
            DataFrame with processed cost data
        """
        if not cost_data:
            return pd.DataFrame()

        df = pd.DataFrame(cost_data)

        # Ensure required columns
        if 'date' not in df.columns or 'cost' not in df.columns:
            raise ValueError("Cost data must contain 'date' and 'cost' columns")

        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Add time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month

        # Add rolling statistics
        df['rolling_mean_7d'] = df['cost'].rolling(window=7, min_periods=1).mean()
        df['rolling_std_7d'] = df['cost'].rolling(window=7, min_periods=1).std()
        df['rolling_mean_30d'] = df['cost'].rolling(window=30, min_periods=1).mean()

        # Calculate percent change
        df['pct_change'] = df['cost'].pct_change()

        return df

    def detect_statistical_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies using statistical methods (Z-score and IQR).

        Args:
            df: DataFrame with cost data

        Returns:
            DataFrame with anomaly flags
        """
        if df.empty or len(df) < 7:
            df['is_anomaly_zscore'] = False
            df['is_anomaly_iqr'] = False
            return df

        thresholds = self.thresholds[self.sensitivity]

        # Z-score method
        mean_cost = df['cost'].mean()
        std_cost = df['cost'].std()
        if std_cost > 0:
            df['z_score'] = np.abs((df['cost'] - mean_cost) / std_cost)
            df['is_anomaly_zscore'] = df['z_score'] > thresholds['z_score']
        else:
            df['z_score'] = 0
            df['is_anomaly_zscore'] = False

        # IQR method
        Q1 = df['cost'].quantile(0.25)
        Q3 = df['cost'].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - thresholds['iqr_multiplier'] * IQR
        upper_bound = Q3 + thresholds['iqr_multiplier'] * IQR

        df['is_anomaly_iqr'] = (df['cost'] < lower_bound) | (df['cost'] > upper_bound)

        return df

    def train_ml_model(self, df: pd.DataFrame) -> None:
        """
        Train Isolation Forest model for anomaly detection.

        Args:
            df: DataFrame with cost data and features
        """
        if df.empty or len(df) < 30:
            logger.warning("Insufficient data to train ML model (need 30+ days)")
            return

        # Select features for ML
        feature_cols = ['cost', 'rolling_mean_7d', 'rolling_std_7d',
                       'rolling_mean_30d', 'pct_change']

        # Remove NaN values
        df_train = df[feature_cols].fillna(0)

        # Scale features
        X_scaled = self.scaler.fit_transform(df_train)

        # Train Isolation Forest
        contamination = self.thresholds[self.sensitivity]['contamination']
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
        self.trained = True

        logger.info(f"ML model trained on {len(df)} days of data")

    def detect_ml_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies using trained ML model.

        Args:
            df: DataFrame with cost data and features

        Returns:
            DataFrame with ML anomaly predictions
        """
        if not self.trained or self.model is None:
            df['is_anomaly_ml'] = False
            df['anomaly_score'] = 0
            return df

        # Select features
        feature_cols = ['cost', 'rolling_mean_7d', 'rolling_std_7d',
                       'rolling_mean_30d', 'pct_change']

        df_pred = df[feature_cols].fillna(0)

        # Scale and predict
        X_scaled = self.scaler.transform(df_pred)
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)

        # -1 indicates anomaly in Isolation Forest
        df['is_anomaly_ml'] = predictions == -1
        df['anomaly_score'] = -scores  # Negative for better interpretation

        return df

    def detect_anomalies(
        self,
        cost_data: List[Dict[str, Any]],
        train_model: bool = True
    ) -> Dict[str, Any]:
        """
        Detect all anomalies using multiple methods.

        Args:
            cost_data: List of cost records
            train_model: Whether to train ML model

        Returns:
            Dict with anomaly detection results
        """
        try:
            # Prepare data
            df = self.prepare_data(cost_data)

            if df.empty:
                return {
                    'success': False,
                    'error': 'No data provided',
                    'anomalies': []
                }

            # Statistical detection
            df = self.detect_statistical_anomalies(df)

            # ML detection
            if train_model and len(df) >= 30:
                self.train_ml_model(df)

            if self.trained:
                df = self.detect_ml_anomalies(df)
            else:
                df['is_anomaly_ml'] = False
                df['anomaly_score'] = 0

            # Combine detection methods (any method flags as anomaly)
            df['is_anomaly'] = (
                df['is_anomaly_zscore'] |
                df['is_anomaly_iqr'] |
                df['is_anomaly_ml']
            )

            # Extract anomalies
            anomalies = []
            for idx, row in df[df['is_anomaly']].iterrows():
                anomaly = {
                    'date': row['date'].isoformat(),
                    'cost': float(row['cost']),
                    'expected_cost': float(row['rolling_mean_7d']) if pd.notna(row['rolling_mean_7d']) else float(df['cost'].mean()),
                    'deviation': float(row['cost'] - row['rolling_mean_7d']) if pd.notna(row['rolling_mean_7d']) else 0,
                    'deviation_pct': float(row['pct_change'] * 100) if pd.notna(row['pct_change']) else 0,
                    'methods': {
                        'z_score': bool(row['is_anomaly_zscore']),
                        'iqr': bool(row['is_anomaly_iqr']),
                        'ml': bool(row['is_anomaly_ml'])
                    },
                    'severity': self._calculate_severity(row),
                    'z_score': float(row['z_score']) if pd.notna(row['z_score']) else 0,
                    'anomaly_score': float(row['anomaly_score']) if pd.notna(row['anomaly_score']) else 0
                }
                anomalies.append(anomaly)

            # Calculate statistics
            total_days = len(df)
            anomaly_days = len(anomalies)
            anomaly_rate = (anomaly_days / total_days * 100) if total_days > 0 else 0

            total_cost = float(df['cost'].sum())
            anomaly_cost = float(df[df['is_anomaly']]['cost'].sum())

            return {
                'success': True,
                'total_days': total_days,
                'anomaly_days': anomaly_days,
                'anomaly_rate': anomaly_rate,
                'total_cost': total_cost,
                'anomaly_cost': anomaly_cost,
                'sensitivity': self.sensitivity,
                'methods_used': ['z_score', 'iqr', 'ml'] if self.trained else ['z_score', 'iqr'],
                'anomalies': sorted(anomalies, key=lambda x: x['date'], reverse=True),
                'summary': self._generate_summary(anomalies, df)
            }

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'anomalies': []
            }

    def _calculate_severity(self, row: pd.Series) -> str:
        """Calculate anomaly severity based on multiple factors."""
        severity_score = 0

        # Z-score contribution
        if pd.notna(row['z_score']):
            if row['z_score'] > 4:
                severity_score += 3
            elif row['z_score'] > 3:
                severity_score += 2
            else:
                severity_score += 1

        # Percent change contribution
        if pd.notna(row['pct_change']):
            pct_change_abs = abs(row['pct_change'])
            if pct_change_abs > 1.0:  # >100% change
                severity_score += 3
            elif pct_change_abs > 0.5:  # >50% change
                severity_score += 2
            else:
                severity_score += 1

        # Anomaly score contribution (if ML used)
        if pd.notna(row['anomaly_score']) and row['anomaly_score'] > 0:
            if row['anomaly_score'] > 0.7:
                severity_score += 2
            else:
                severity_score += 1

        # Map score to severity
        if severity_score >= 6:
            return 'critical'
        elif severity_score >= 4:
            return 'high'
        elif severity_score >= 2:
            return 'medium'
        else:
            return 'low'

    def _generate_summary(self, anomalies: List[Dict], df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary of anomaly detection results."""
        if not anomalies:
            return {
                'message': 'No anomalies detected',
                'recommendation': 'Cost patterns appear normal'
            }

        # Count by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for anomaly in anomalies:
            severity_counts[anomaly['severity']] += 1

        # Find largest spike
        largest_spike = max(anomalies, key=lambda x: abs(x['deviation']))

        return {
            'message': f"Detected {len(anomalies)} anomalies",
            'severity_breakdown': severity_counts,
            'largest_spike': {
                'date': largest_spike['date'],
                'cost': largest_spike['cost'],
                'deviation': largest_spike['deviation'],
                'deviation_pct': largest_spike['deviation_pct']
            },
            'recommendation': self._get_recommendation(severity_counts)
        }

    def _get_recommendation(self, severity_counts: Dict[str, int]) -> str:
        """Generate recommendation based on anomaly severity."""
        if severity_counts['critical'] > 0:
            return 'Immediate investigation required - critical cost spikes detected'
        elif severity_counts['high'] > 2:
            return 'Review high-severity anomalies and identify root causes'
        elif severity_counts['medium'] > 5:
            return 'Monitor cost trends closely - multiple medium anomalies detected'
        else:
            return 'Low-risk anomalies detected - routine monitoring recommended'

    def save_model(self, filepath: str) -> bool:
        """Save trained model to file."""
        try:
            if not self.trained:
                logger.warning("No trained model to save")
                return False

            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'sensitivity': self.sensitivity,
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
            self.scaler = model_data['scaler']
            self.sensitivity = model_data['sensitivity']
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
    print("  Cost Anomaly Detection Test")
    print("  Phase 4 - Advanced Intelligence")
    print("=" * 60)

    # Generate sample cost data with anomalies
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', end='2026-04-30', freq='D')

    # Base cost with slight trend
    base_cost = 100 + np.arange(len(dates)) * 0.5

    # Add normal variation
    costs = base_cost + np.random.normal(0, 10, len(dates))

    # Inject anomalies
    costs[30] = 250  # Spike on day 30
    costs[60] = 280  # Spike on day 60
    costs[90] = 50   # Drop on day 90

    # Prepare data
    cost_data = [
        {'date': date.strftime('%Y-%m-%d'), 'cost': cost}
        for date, cost in zip(dates, costs)
    ]

    # Initialize detector
    detector = CostAnomalyDetector(sensitivity='medium')

    # Detect anomalies
    print("\n[1] Running anomaly detection...")
    results = detector.detect_anomalies(cost_data, train_model=True)

    if results['success']:
        print(f"\n[PASS] Anomaly Detection Results:")
        print(f"   Total days analyzed: {results['total_days']}")
        print(f"   Anomalies detected: {results['anomaly_days']}")
        print(f"   Anomaly rate: {results['anomaly_rate']:.1f}%")
        print(f"   Total cost: ${results['total_cost']:.2f}")
        print(f"   Anomaly cost: ${results['anomaly_cost']:.2f}")
        print(f"   Detection methods: {', '.join(results['methods_used'])}")

        # Show top anomalies
        print(f"\n   Top 5 Anomalies:")
        for i, anomaly in enumerate(results['anomalies'][:5], 1):
            print(f"   {i}. {anomaly['date']}: ${anomaly['cost']:.2f} "
                  f"(deviation: ${anomaly['deviation']:+.2f}, "
                  f"{anomaly['deviation_pct']:+.1f}%, "
                  f"severity: {anomaly['severity']})")

        # Show summary
        summary = results['summary']
        print(f"\n   Summary:")
        print(f"   {summary['message']}")
        print(f"   Severity breakdown: {summary['severity_breakdown']}")
        print(f"   Recommendation: {summary['recommendation']}")

        print("\n[PASS] Cost Anomaly Detection Test Complete")
    else:
        print(f"\n[FAIL] Test failed: {results.get('error')}")

    print("\n" + "=" * 60)
