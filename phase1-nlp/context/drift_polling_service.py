"""
Drift Polling Service - Background Monitoring
==============================================

Background service that polls AWS infrastructure every 15 minutes,
detects drift, and triggers alerts.

Features:
- Scheduled polling (configurable interval)
- Automatic drift detection
- Error handling and retry logic
- Graceful shutdown
- Snapshot cleanup
- Health check endpoint

Deployment Options:
- Local: Python script with schedule library
- Production: AWS Lambda (CloudWatch Events trigger)
- Alternative: ECS scheduled task

Author: PromptOps Team - Week 7-8
Date: 2026-04-28
"""

import time
import signal
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Callable
import logging
from dataclasses import dataclass
import threading

# Import our context modules
from context_collector import ContextCollector
from drift_detector import DriftDetector, format_drift_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PollingStats:
    """Statistics for polling service."""
    total_polls: int = 0
    successful_polls: int = 0
    failed_polls: int = 0
    total_drift_events: int = 0
    critical_drift_events: int = 0
    last_poll_time: Optional[str] = None
    last_drift_time: Optional[str] = None
    uptime_seconds: int = 0


# ============================================================================
# Drift Polling Service
# ============================================================================

class DriftPollingService:
    """
    Background service for periodic infrastructure drift detection.

    Usage:
        service = DriftPollingService(interval_minutes=15)
        service.start()  # Blocks until stopped
    """

    def __init__(
        self,
        interval_minutes: int = 15,
        aws_region: str = 'us-east-1',
        aws_profile: Optional[str] = None,
        context_store_path: str = './context_snapshots',
        filter_tag: str = 'PromptOps',
        on_drift_callback: Optional[Callable] = None,
        cleanup_days: int = 7
    ):
        """
        Initialize Drift Polling Service.

        Args:
            interval_minutes: Polling interval in minutes
            aws_region: AWS region to monitor
            aws_profile: AWS profile name (optional)
            context_store_path: Path to store snapshots
            filter_tag: Tag value to filter resources
            on_drift_callback: Function to call when drift detected
            cleanup_days: Days to retain snapshots
        """
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.aws_region = aws_region
        self.aws_profile = aws_profile
        self.context_store_path = context_store_path
        self.filter_tag = filter_tag
        self.on_drift_callback = on_drift_callback
        self.cleanup_days = cleanup_days

        # Initialize components
        self.collector = ContextCollector(
            aws_region=aws_region,
            aws_profile=aws_profile,
            snapshot_dir=context_store_path,
            filter_tag=filter_tag
        )

        self.drift_detector = DriftDetector(
            context_store_path=context_store_path,
            enable_cloudtrail=False
        )

        # Service state
        self.running = False
        self.stats = PollingStats()
        self.start_time = None

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"DriftPollingService initialized: interval={interval_minutes}min, region={aws_region}")

    # ========================================================================
    # Service Control
    # ========================================================================

    def start(self):
        """
        Start the polling service.

        Blocks until stopped via SIGINT/SIGTERM or stop() method.
        """
        if self.running:
            logger.warning("Service already running")
            return

        self.running = True
        self.start_time = datetime.now(timezone.utc)

        logger.info("🚀 Drift Polling Service starting...")
        logger.info(f"   Interval: {self.interval_minutes} minutes")
        logger.info(f"   Region: {self.aws_region}")
        logger.info(f"   Filter Tag: Managed={self.filter_tag}")
        logger.info("")

        # Initial poll
        logger.info("Running initial poll...")
        self.poll_once()

        # Polling loop
        while self.running:
            try:
                # Calculate next poll time
                next_poll = datetime.now(timezone.utc).timestamp() + self.interval_seconds

                # Sleep until next poll (check for stop every 10 seconds)
                while self.running and datetime.now(timezone.utc).timestamp() < next_poll:
                    time.sleep(min(10, next_poll - datetime.now(timezone.utc).timestamp()))

                if not self.running:
                    break

                # Poll
                self.poll_once()

            except Exception as e:
                logger.error(f"Polling loop error: {str(e)}")
                self.stats.failed_polls += 1
                time.sleep(60)  # Wait 1 minute before retry

        logger.info("Drift Polling Service stopped")
        self._print_final_stats()

    def stop(self):
        """Stop the polling service gracefully."""
        logger.info("Stopping Drift Polling Service...")
        self.running = False

    def poll_once(self) -> bool:
        """
        Execute a single polling cycle.

        Returns:
            True if successful, False otherwise
        """
        poll_start = datetime.now(timezone.utc)
        logger.info(f"[POLL] Starting poll at {poll_start.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        try:
            # Step 1: Collect current infrastructure state
            logger.info("[POLL] Step 1/3: Collecting infrastructure state...")
            context_data = self.collector.collect_all_resources(parallel=True)

            resources_count = context_data['metadata']['total_resources']
            logger.info(f"[POLL] ✓ Collected {resources_count} resources")

            # Step 2: Detect drift
            logger.info("[POLL] Step 2/3: Detecting drift...")
            try:
                drift_report = self.drift_detector.detect_drift()

                if drift_report.total_drift_events > 0:
                    logger.warning(f"[POLL] ⚠️  Drift detected: {drift_report.total_drift_events} events "
                                 f"(critical={drift_report.critical_count}, "
                                 f"warning={drift_report.warning_count})")

                    # Update stats
                    self.stats.total_drift_events += drift_report.total_drift_events
                    self.stats.critical_drift_events += drift_report.critical_count
                    self.stats.last_drift_time = poll_start.isoformat()

                    # Trigger callback
                    if self.on_drift_callback:
                        try:
                            self.on_drift_callback(drift_report)
                        except Exception as e:
                            logger.error(f"Drift callback failed: {str(e)}")

                    # Log drift report
                    logger.info("\n" + format_drift_report(drift_report, verbose=False))

                else:
                    logger.info("[POLL] ✓ No drift detected")

            except Exception as e:
                logger.warning(f"[POLL] Drift detection skipped: {str(e)}")

            # Step 3: Cleanup old snapshots
            logger.info("[POLL] Step 3/3: Cleanup old snapshots...")
            deleted_count = self.collector.cleanup_old_snapshots(self.cleanup_days)
            if deleted_count > 0:
                logger.info(f"[POLL] ✓ Cleaned up {deleted_count} old snapshots")

            # Update stats
            self.stats.total_polls += 1
            self.stats.successful_polls += 1
            self.stats.last_poll_time = poll_start.isoformat()

            if self.start_time:
                self.stats.uptime_seconds = int((datetime.now(timezone.utc) - self.start_time).total_seconds())

            poll_duration = (datetime.now(timezone.utc) - poll_start).total_seconds()
            logger.info(f"[POLL] ✓ Poll complete in {poll_duration:.1f}s")
            logger.info(f"[POLL] Next poll in {self.interval_minutes} minutes")
            logger.info("")

            return True

        except Exception as e:
            logger.error(f"[POLL] ✗ Poll failed: {str(e)}")
            self.stats.total_polls += 1
            self.stats.failed_polls += 1
            return False

    # ========================================================================
    # Health Check
    # ========================================================================

    def get_health(self) -> dict:
        """
        Get service health status.

        Returns:
            Dict with health information
        """
        is_healthy = (
            self.running and
            self.stats.successful_polls > 0 and
            (self.stats.failed_polls / max(self.stats.total_polls, 1)) < 0.1  # <10% failure rate
        )

        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'running': self.running,
            'stats': {
                'total_polls': self.stats.total_polls,
                'successful_polls': self.stats.successful_polls,
                'failed_polls': self.stats.failed_polls,
                'success_rate': (self.stats.successful_polls / max(self.stats.total_polls, 1)) * 100,
                'total_drift_events': self.stats.total_drift_events,
                'critical_drift_events': self.stats.critical_drift_events,
                'last_poll_time': self.stats.last_poll_time,
                'last_drift_time': self.stats.last_drift_time,
                'uptime_seconds': self.stats.uptime_seconds
            },
            'config': {
                'interval_minutes': self.interval_minutes,
                'aws_region': self.aws_region,
                'filter_tag': self.filter_tag,
                'cleanup_days': self.cleanup_days
            }
        }

    def print_stats(self):
        """Print current statistics."""
        print("\n" + "="*70)
        print("DRIFT POLLING SERVICE - STATISTICS")
        print("="*70)
        print(f"Status: {'🟢 Running' if self.running else '🔴 Stopped'}")
        print(f"Uptime: {self._format_uptime(self.stats.uptime_seconds)}")
        print("")
        print(f"Total Polls: {self.stats.total_polls}")
        print(f"  Successful: {self.stats.successful_polls}")
        print(f"  Failed: {self.stats.failed_polls}")
        if self.stats.total_polls > 0:
            success_rate = (self.stats.successful_polls / self.stats.total_polls) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        print("")
        print(f"Drift Events Detected: {self.stats.total_drift_events}")
        print(f"  Critical: {self.stats.critical_drift_events}")
        print("")
        if self.stats.last_poll_time:
            print(f"Last Poll: {self.stats.last_poll_time}")
        if self.stats.last_drift_time:
            print(f"Last Drift: {self.stats.last_drift_time}")
        print("="*70 + "\n")

    def _print_final_stats(self):
        """Print statistics at shutdown."""
        self.print_stats()
        logger.info("Thank you for using Drift Polling Service!")

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\nReceived signal {signum}, shutting down...")
        self.stop()

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        """Format uptime in human-readable format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


# ============================================================================
# Lambda Handler (for AWS Lambda deployment)
# ============================================================================

def lambda_handler(event, context):
    """
    AWS Lambda handler for scheduled execution.

    Triggered by CloudWatch Events every 15 minutes.

    Args:
        event: CloudWatch event
        context: Lambda context

    Returns:
        Response with status
    """
    logger.info("Lambda handler invoked")

    # Initialize service (single poll)
    service = DriftPollingService(
        interval_minutes=15,
        aws_region=os.environ.get('AWS_REGION', 'us-east-1'),
        context_store_path='/tmp/context_snapshots',  # Lambda tmp storage
        filter_tag=os.environ.get('FILTER_TAG', 'PromptOps')
    )

    # Execute single poll
    success = service.poll_once()

    # Return response
    return {
        'statusCode': 200 if success else 500,
        'body': {
            'success': success,
            'stats': service.get_health()['stats']
        }
    }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Drift Polling Service')
    parser.add_argument('--interval', type=int, default=15, help='Polling interval in minutes')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--context-dir', default='./context_snapshots', help='Context directory')
    parser.add_argument('--filter-tag', default='PromptOps', help='Resource filter tag')
    parser.add_argument('--cleanup-days', type=int, default=7, help='Days to retain snapshots')
    parser.add_argument('--once', action='store_true', help='Run once and exit')

    args = parser.parse_args()

    # Drift callback (example: print to console)
    def on_drift(drift_report):
        if drift_report.critical_count > 0:
            logger.critical(f"🚨 CRITICAL DRIFT: {drift_report.critical_count} events")

    # Create service
    service = DriftPollingService(
        interval_minutes=args.interval,
        aws_region=args.region,
        aws_profile=args.profile,
        context_store_path=args.context_dir,
        filter_tag=args.filter_tag,
        on_drift_callback=on_drift,
        cleanup_days=args.cleanup_days
    )

    if args.once:
        # Single poll
        logger.info("Running single poll...")
        success = service.poll_once()
        service.print_stats()
        sys.exit(0 if success else 1)
    else:
        # Continuous polling
        try:
            service.start()
        except KeyboardInterrupt:
            logger.info("\nInterrupted by user")
            service.stop()


if __name__ == '__main__':
    main()
