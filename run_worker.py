"""Headless Background Dispatch Worker Runner.

Can be run manually from the command line, or scheduled via Windows Task Scheduler
or cron to run daily (e.g., at 09:00:00 AM Asia/Kolkata).
"""

import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from naps_engine.config import APP_TIMEZONE
from naps_engine.db import get_db_connection, init_db
from naps_engine.mailer import Mailer
from naps_engine.worker import DispatchWorker


def run():
    now_ist = datetime.now(APP_TIMEZONE)
    print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}] Starting NAPS Dispatch Worker...")

    conn = get_db_connection()
    init_db(conn)

    mailer = Mailer()
    print(f"Delivery Mode: {'SIMULATION (Dry-Run)' if mailer.dry_run else 'LIVE SMTP TRANSMISSION'}")

    worker = DispatchWorker(conn=conn, worker_id="scheduler-daemon", mailer=mailer)
    summary = worker.run_worker_cycle()

    print(f"Worker Cycle Completed Successfully:")
    print(f"  - Expired leases recovered : {summary.get('recovered', 0)}")
    print(f"  - Eligible schedules due   : {summary.get('due', 0)}")
    print(f"  - Successfully sent        : {summary.get('sent', 0)}")
    print(f"  - Failed dispatches        : {summary.get('failed', 0)}")
    print(f"  - Retrying transiently     : {summary.get('retrying', 0)}")
    print(f"  - Uncertain dispatches     : {summary.get('uncertain', 0)}")
    print(f"  - Cancelled/Skipped        : {summary.get('cancelled', 0) + summary.get('skipped', 0)}")

    conn.close()


if __name__ == "__main__":
    run()
