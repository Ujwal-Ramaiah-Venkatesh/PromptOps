"""
Training Data Validator for PromptOps
=====================================

Validates training data quality using Great Expectations before submitting to SageMaker.
Ensures data integrity, completeness, and schema compliance.

Author: ML Engineer - Phase 5 Week 42-43
Date: 2026-05-07
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Training Data Validator
# ============================================================================

class TrainingDataValidator:
    """
    Validates training data quality before submitting to SageMaker.
    Uses validation rules inspired by Great Expectations.
    """

    def __init__(self):
        """Initialize Training Data Validator."""
        self.validation_results = []

    def validate_dataset(
        self,
        data_path: str,
        model_type: str,
        expected_columns: Optional[List[str]] = None,
        target_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate training dataset.

        Args:
            data_path: Path to training data (CSV or Parquet)
            model_type: Model type (classification, regression, nlp, time_series, cv)
            expected_columns: Expected column names
            target_column: Target variable column name

        Returns:
            Validation results with pass/fail status and details
        """
        logger.info(f"Validating dataset: {data_path}")

        results = {
            "valid": True,
            "data_path": data_path,
            "model_type": model_type,
            "checks_passed": 0,
            "checks_failed": 0,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        try:
            # Load dataset
            df = self._load_dataset(data_path)
            if df is None:
                results["valid"] = False
                results["errors"].append("Failed to load dataset")
                return results

            results["statistics"]["row_count"] = len(df)
            results["statistics"]["column_count"] = len(df.columns)

            # Run validation checks
            self._check_not_empty(df, results)
            self._check_column_exists(df, expected_columns, results)
            self._check_target_column(df, target_column, results)
            self._check_missing_values(df, results)
            self._check_duplicates(df, results)
            self._check_data_types(df, model_type, target_column, results)
            self._check_target_distribution(df, target_column, model_type, results)
            self._check_feature_variance(df, target_column, results)

            # Model-specific validations
            if model_type == "classification":
                self._validate_classification_data(df, target_column, results)
            elif model_type == "regression":
                self._validate_regression_data(df, target_column, results)
            elif model_type == "time_series":
                self._validate_timeseries_data(df, results)

            # Final validation status
            if results["checks_failed"] > 0:
                results["valid"] = False

            logger.info(
                f"Validation complete: {results['checks_passed']} passed, "
                f"{results['checks_failed']} failed"
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            results["valid"] = False
            results["errors"].append(f"Validation exception: {str(e)}")

        return results

    def _load_dataset(self, data_path: str) -> Optional[pd.DataFrame]:
        """Load dataset from CSV or Parquet."""
        try:
            if data_path.endswith('.csv'):
                return pd.read_csv(data_path)
            elif data_path.endswith('.parquet'):
                return pd.read_parquet(data_path)
            else:
                logger.error(f"Unsupported file format: {data_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return None

    def _check_not_empty(self, df: pd.DataFrame, results: Dict[str, Any]):
        """Check dataset is not empty."""
        if len(df) == 0:
            results["checks_failed"] += 1
            results["errors"].append("Dataset is empty (0 rows)")
        else:
            results["checks_passed"] += 1

    def _check_column_exists(
        self,
        df: pd.DataFrame,
        expected_columns: Optional[List[str]],
        results: Dict[str, Any]
    ):
        """Check expected columns exist."""
        if expected_columns:
            missing = set(expected_columns) - set(df.columns)
            if missing:
                results["checks_failed"] += 1
                results["errors"].append(f"Missing columns: {missing}")
            else:
                results["checks_passed"] += 1

    def _check_target_column(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        results: Dict[str, Any]
    ):
        """Check target column exists and is not empty."""
        if target_column:
            if target_column not in df.columns:
                results["checks_failed"] += 1
                results["errors"].append(f"Target column '{target_column}' not found")
            elif df[target_column].isnull().all():
                results["checks_failed"] += 1
                results["errors"].append(f"Target column '{target_column}' is all null")
            else:
                results["checks_passed"] += 1

    def _check_missing_values(self, df: pd.DataFrame, results: Dict[str, Any]):
        """Check for excessive missing values."""
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        high_missing = {col: pct for col, pct in missing_pct.items() if pct > 50}

        if high_missing:
            results["checks_failed"] += 1
            results["warnings"].append(
                f"High missing values (>50%): {high_missing}"
            )
        else:
            results["checks_passed"] += 1

        results["statistics"]["missing_values_pct"] = missing_pct

    def _check_duplicates(self, df: pd.DataFrame, results: Dict[str, Any]):
        """Check for duplicate rows."""
        duplicate_count = df.duplicated().sum()
        duplicate_pct = (duplicate_count / len(df) * 100) if len(df) > 0 else 0

        results["statistics"]["duplicate_rows"] = int(duplicate_count)
        results["statistics"]["duplicate_pct"] = round(duplicate_pct, 2)

        if duplicate_pct > 10:
            results["checks_failed"] += 1
            results["warnings"].append(
                f"High duplicate percentage: {duplicate_pct:.2f}%"
            )
        else:
            results["checks_passed"] += 1

    def _check_data_types(
        self,
        df: pd.DataFrame,
        model_type: str,
        target_column: Optional[str],
        results: Dict[str, Any]
    ):
        """Check data types are appropriate for model type."""
        type_counts = df.dtypes.value_counts().to_dict()
        results["statistics"]["data_types"] = {str(k): int(v) for k, v in type_counts.items()}

        # Check for object types that might need encoding
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        if target_column and target_column in object_cols:
            object_cols.remove(target_column)

        if object_cols and model_type in ['classification', 'regression']:
            results["warnings"].append(
                f"Found {len(object_cols)} categorical columns that may need encoding: {object_cols[:5]}"
            )

        results["checks_passed"] += 1

    def _check_target_distribution(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        model_type: str,
        results: Dict[str, Any]
    ):
        """Check target variable distribution."""
        if not target_column or target_column not in df.columns:
            return

        target_series = df[target_column].dropna()

        if model_type == "classification":
            # Check class distribution
            class_counts = target_series.value_counts().to_dict()
            results["statistics"]["class_distribution"] = {str(k): int(v) for k, v in class_counts.items()}

            # Check for severe class imbalance
            if len(class_counts) >= 2:
                max_count = max(class_counts.values())
                min_count = min(class_counts.values())
                imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')

                if imbalance_ratio > 20:
                    results["checks_failed"] += 1
                    results["warnings"].append(
                        f"Severe class imbalance detected (ratio: {imbalance_ratio:.1f}:1)"
                    )
                else:
                    results["checks_passed"] += 1
            else:
                results["checks_passed"] += 1

        elif model_type == "regression":
            # Check target statistics
            results["statistics"]["target_mean"] = float(target_series.mean())
            results["statistics"]["target_std"] = float(target_series.std())
            results["statistics"]["target_min"] = float(target_series.min())
            results["statistics"]["target_max"] = float(target_series.max())
            results["checks_passed"] += 1

    def _check_feature_variance(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        results: Dict[str, Any]
    ):
        """Check for zero-variance features."""
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

        if target_column and target_column in numeric_cols:
            numeric_cols.remove(target_column)

        zero_variance_cols = []
        for col in numeric_cols:
            if df[col].nunique() == 1:
                zero_variance_cols.append(col)

        if zero_variance_cols:
            results["checks_failed"] += 1
            results["warnings"].append(
                f"Zero-variance features detected: {zero_variance_cols[:5]}"
            )
        else:
            results["checks_passed"] += 1

    def _validate_classification_data(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        results: Dict[str, Any]
    ):
        """Additional validations for classification models."""
        if not target_column or target_column not in df.columns:
            return

        num_classes = df[target_column].nunique()
        results["statistics"]["num_classes"] = num_classes

        if num_classes < 2:
            results["checks_failed"] += 1
            results["errors"].append(
                f"Classification requires at least 2 classes, found {num_classes}"
            )
        else:
            results["checks_passed"] += 1

    def _validate_regression_data(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        results: Dict[str, Any]
    ):
        """Additional validations for regression models."""
        if not target_column or target_column not in df.columns:
            return

        target_series = df[target_column].dropna()

        # Check if target is numeric
        if not pd.api.types.is_numeric_dtype(target_series):
            results["checks_failed"] += 1
            results["errors"].append(
                f"Regression target must be numeric, found {target_series.dtype}"
            )
        else:
            results["checks_passed"] += 1

    def _validate_timeseries_data(self, df: pd.DataFrame, results: Dict[str, Any]):
        """Additional validations for time series models."""
        # Check for datetime column
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        if not datetime_cols:
            results["checks_failed"] += 1
            results["warnings"].append(
                "No datetime column found for time series data"
            )
        else:
            results["checks_passed"] += 1

    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate human-readable validation report.

        Args:
            validation_results: Results from validate_dataset

        Returns:
            Formatted validation report
        """
        report = []
        report.append("=" * 60)
        report.append("TRAINING DATA VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Dataset: {validation_results['data_path']}")
        report.append(f"Model Type: {validation_results['model_type']}")
        report.append(f"Status: {'PASSED' if validation_results['valid'] else 'FAILED'}")
        report.append("")

        report.append(f"Checks Passed: {validation_results['checks_passed']}")
        report.append(f"Checks Failed: {validation_results['checks_failed']}")
        report.append("")

        if validation_results.get("statistics"):
            report.append("Statistics:")
            for key, value in validation_results["statistics"].items():
                report.append(f"  {key}: {value}")
            report.append("")

        if validation_results.get("errors"):
            report.append("ERRORS:")
            for error in validation_results["errors"]:
                report.append(f"  - {error}")
            report.append("")

        if validation_results.get("warnings"):
            report.append("WARNINGS:")
            for warning in validation_results["warnings"]:
                report.append(f"  - {warning}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)


# ============================================================================
# Testing
# ============================================================================

def test_validator():
    """Test validator with sample data."""
    logger.info("Testing Training Data Validator...")

    # Create sample classification dataset
    sample_data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'feature2': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'feature3': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
        'target': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    })

    # Save to temp file
    test_path = "test_training_data.csv"
    sample_data.to_csv(test_path, index=False)

    # Validate
    validator = TrainingDataValidator()
    results = validator.validate_dataset(
        data_path=test_path,
        model_type="classification",
        expected_columns=['feature1', 'feature2', 'feature3', 'target'],
        target_column='target'
    )

    # Generate report
    report = validator.generate_validation_report(results)
    print(report)

    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)


if __name__ == "__main__":
    test_validator()
