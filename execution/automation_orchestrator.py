"""
Automation Orchestrator
Master controller that runs all automation tasks:
1. Maintain inventory (21+ Draft posts)
2. Process scheduling queue
3. Run cleanup (delete 7-day-old posts)

Run this on a schedule (every 5 minutes recommended).
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent))

from draft_post_generator import DraftPostGenerator
from smart_scheduler import SmartScheduler
from post_cleanup import PostCleanup


class AutomationOrchestrator:
    """Orchestrates all automation tasks."""

    def __init__(self):
        """Initialize orchestrator."""
        self.draft_generator = DraftPostGenerator()
        self.scheduler = SmartScheduler()
        self.cleanup = PostCleanup()

    def run_cycle(self):
        """Run one complete automation cycle."""
        print("\n" + "="*80)
        print(f"🔄 AUTOMATION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

        # Step 1: Cleanup old posts
        print("📋 STEP 1: Cleaning up expired posts...")
        self.cleanup.run_cleanup()
        time.sleep(1)

        # Step 2: Maintain inventory
        print("📋 STEP 2: Maintaining Draft post inventory...")
        self.draft_generator.maintain_inventory(target=21)
        time.sleep(1)

        # Step 3: Process scheduling queue
        print("📋 STEP 3: Processing scheduling queue...")
        self.scheduler.process_queue()

        print("="*80)
        print("✅ AUTOMATION CYCLE COMPLETE")
        print("="*80 + "\n")

    def run_continuous(self, interval_seconds: int = 300):
        """Run automation continuously on a schedule.

        Args:
            interval_seconds: How often to run (default: 300 = 5 minutes)
        """
        print("="*80)
        print("🚀 STARTING CONTINUOUS AUTOMATION")
        print("="*80)
        print(f"Running every {interval_seconds} seconds ({interval_seconds/60} minutes)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                self.run_cycle()
                print(f"⏰ Next cycle in {interval_seconds} seconds...\n")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n" + "="*80)
            print("⏹️  AUTOMATION STOPPED")
            print("="*80 + "\n")


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run LinkedIn post automation")
    parser.add_argument("--mode", choices=["once", "continuous"], default="once",
                        help="Run once or continuously")
    parser.add_argument("--interval", type=int, default=300,
                        help="Interval in seconds for continuous mode (default: 300)")

    args = parser.parse_args()

    orchestrator = AutomationOrchestrator()

    if args.mode == "once":
        orchestrator.run_cycle()
    else:
        orchestrator.run_continuous(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
