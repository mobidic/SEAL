# (c) 2025, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
#
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2025  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Dedicated process for SEAL background jobs (VCF import, ClinVar update).

The web application (flask run / gunicorn / uwsgi) no longer starts any
scheduler, so it can safely run with several workers. Run exactly ONE
instance of this script next to it:

    python scheduler.py
    python scheduler.py --list    # show registered jobs and exit
"""

import argparse
import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from flask.logging import default_handler

from seal import app
from seal.schedulers import register_jobs


def build_scheduler():
    """Create a BlockingScheduler configured from seal/config.yaml."""
    job_defaults = app.config.get("SCHEDULER_JOB_DEFAULTS", {})
    timezone = app.config.get("SCHEDULER_TIMEZONE", "Europe/Paris")
    scheduler = BlockingScheduler(job_defaults=job_defaults, timezone=timezone)
    register_jobs(scheduler)
    return scheduler


def main():
    parser = argparse.ArgumentParser(
        description="SEAL scheduler: runs background jobs in a dedicated process"
    )
    parser.add_argument(
        "-l", "--list", action="store_true",
        help="List registered jobs and exit"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Debug logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    # Flask attaches its own handler to app.logger, and messages also
    # propagate to the root handler configured above: without this, every
    # app.logger message would be printed twice.
    app.logger.removeHandler(default_handler)
    app.logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    scheduler = build_scheduler()

    if args.list:
        for job in scheduler.get_jobs():
            print(f"{job.id:<20} {job.trigger}")
        return

    def stop(signum, frame):
        app.logger.info(f"Signal {signum} received, stopping scheduler...")
        # wait=True: let a running VCF import finish cleanly (lock file)
        scheduler.shutdown(wait=True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    app.logger.info("SEAL scheduler started")
    scheduler.start()


if __name__ == "__main__":
    main()