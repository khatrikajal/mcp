"""
Delegation Background Tasks

These tasks should be run periodically via cron or a task scheduler:

1. process_meetings_task - Every 5 minutes
   - Scans calendar for upcoming meetings
   - Creates delegation records
   - Auto-approves low/medium importance meetings

2. join_meetings_task - Every 1-2 minutes
   - Finds approved delegations for meetings starting soon
   - Joins meetings via Nylas Notetaker

3. complete_meetings_task - Every 5-10 minutes
   - Finds joined delegations where meeting has ended
   - Fetches transcripts and generates reports
   - Sends reports via email

Usage:
    # Run as standalone script
    python -m backend.src.tasks.delegation_tasks

    # Or import and use with APScheduler, Celery, etc.
    from backend.src.tasks.delegation_tasks import (
        process_meetings_task,
        join_meetings_task,
        complete_meetings_task,
    )
"""
import logging
import time
from datetime import datetime
from typing import Optional

from backend.src.db.connection import SessionLocal, init_db
from backend.src.db.models import User
from backend.src.services.delegation_service import DelegationService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_active_users():
    """Get all users who have delegation enabled (all users for now)."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return users
    finally:
        db.close()


def process_meetings_task(
    user_id: Optional[int] = None,
    look_ahead_hours: int = 24,
):
    """
    Process upcoming meetings for users.

    Should run every 5 minutes.

    Args:
        user_id: Process for specific user (None = all users)
        look_ahead_hours: How far ahead to look for meetings
    """
    logger.info("Starting process_meetings_task")
    start_time = datetime.utcnow()

    db = SessionLocal()
    try:
        if user_id:
            users = [db.query(User).get(user_id)]
        else:
            users = db.query(User).all()

        total_delegations = 0

        for user in users:
            if not user:
                continue

            try:
                service = DelegationService(db)
                delegations = service.process_upcoming_meetings(
                    user=user,
                    look_ahead_hours=look_ahead_hours,
                )
                total_delegations += len(delegations)

                if delegations:
                    logger.info(
                        f"Created {len(delegations)} delegations for user {user.id}"
                    )

            except Exception as e:
                logger.error(f"Error processing meetings for user {user.id}: {e}")

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Completed process_meetings_task: "
            f"{total_delegations} delegations in {elapsed:.2f}s"
        )

    finally:
        db.close()


def join_meetings_task(
    user_id: Optional[int] = None,
    join_before_minutes: int = 5,
):
    """
    Join meetings that are about to start.

    Should run every 1-2 minutes.

    Args:
        user_id: Process for specific user (None = all users)
        join_before_minutes: How many minutes before meeting to join
    """
    logger.info("Starting join_meetings_task")
    start_time = datetime.utcnow()

    db = SessionLocal()
    try:
        if user_id:
            users = [db.query(User).get(user_id)]
        else:
            users = db.query(User).all()

        total_joined = 0

        for user in users:
            if not user:
                continue

            try:
                service = DelegationService(db)
                joined = service.process_meetings_to_join(
                    user_id=user.id,
                    organization_id=user.organization_id,
                    join_before_minutes=join_before_minutes,
                )
                total_joined += len(joined)

                for delegation in joined:
                    logger.info(
                        f"Joined meeting '{delegation.meeting_title}' for user {user.id}"
                    )

            except Exception as e:
                logger.error(f"Error joining meetings for user {user.id}: {e}")

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Completed join_meetings_task: "
            f"{total_joined} meetings joined in {elapsed:.2f}s"
        )

    finally:
        db.close()


def complete_meetings_task(user_id: Optional[int] = None):
    """
    Complete meetings that have ended (fetch transcripts, generate reports).

    Should run every 5-10 minutes.

    Args:
        user_id: Process for specific user (None = all users)
    """
    logger.info("Starting complete_meetings_task")
    start_time = datetime.utcnow()

    db = SessionLocal()
    try:
        if user_id:
            users = [db.query(User).get(user_id)]
        else:
            users = db.query(User).all()

        total_completed = 0

        for user in users:
            if not user:
                continue

            try:
                service = DelegationService(db)
                completed = service.process_completed_meetings(
                    user_id=user.id,
                    organization_id=user.organization_id,
                )
                total_completed += len(completed)

                for delegation in completed:
                    logger.info(
                        f"Completed meeting '{delegation.meeting_title}' for user {user.id}"
                    )

            except Exception as e:
                logger.error(f"Error completing meetings for user {user.id}: {e}")

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Completed complete_meetings_task: "
            f"{total_completed} meetings completed in {elapsed:.2f}s"
        )

    finally:
        db.close()


def run_all_tasks():
    """Run all delegation tasks once."""
    process_meetings_task()
    join_meetings_task()
    complete_meetings_task()


def run_scheduler(
    process_interval: int = 300,  # 5 minutes
    join_interval: int = 120,     # 2 minutes
    complete_interval: int = 300, # 5 minutes
):
    """
    Run tasks on a schedule (simple scheduler without external dependencies).

    For production, consider using APScheduler, Celery, or a proper cron setup.

    Args:
        process_interval: Seconds between process_meetings_task runs
        join_interval: Seconds between join_meetings_task runs
        complete_interval: Seconds between complete_meetings_task runs
    """
    logger.info("Starting delegation task scheduler")
    logger.info(f"  Process meetings: every {process_interval}s")
    logger.info(f"  Join meetings: every {join_interval}s")
    logger.info(f"  Complete meetings: every {complete_interval}s")

    last_process = 0
    last_join = 0
    last_complete = 0

    while True:
        try:
            now = time.time()

            # Process meetings
            if now - last_process >= process_interval:
                try:
                    process_meetings_task()
                except Exception as e:
                    logger.error(f"process_meetings_task failed: {e}")
                last_process = now

            # Join meetings
            if now - last_join >= join_interval:
                try:
                    join_meetings_task()
                except Exception as e:
                    logger.error(f"join_meetings_task failed: {e}")
                last_join = now

            # Complete meetings
            if now - last_complete >= complete_interval:
                try:
                    complete_meetings_task()
                except Exception as e:
                    logger.error(f"complete_meetings_task failed: {e}")
                last_complete = now

            # Sleep before next check
            time.sleep(30)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Delegation background tasks")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule"],
        default="once",
        help="Run once or on schedule"
    )
    parser.add_argument(
        "--task",
        choices=["all", "process", "join", "complete"],
        default="all",
        help="Which task to run (only for --mode once)"
    )

    args = parser.parse_args()

    # Initialize database
    init_db()

    if args.mode == "schedule":
        run_scheduler()
    else:
        if args.task == "all":
            run_all_tasks()
        elif args.task == "process":
            process_meetings_task()
        elif args.task == "join":
            join_meetings_task()
        elif args.task == "complete":
            complete_meetings_task()
