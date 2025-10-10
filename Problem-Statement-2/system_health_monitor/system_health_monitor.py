#!/usr/bin/env python3
"""
system_health_monitor.py
Monitors CPU, memory, disk usage, and process count.
Sends alerts to console and/or a log file when thresholds are exceeded.

Usage examples:
  Real metrics (requires psutil):
    python3 system_health_monitor.py --interval 5 --iterations 12 --log-file health.log
  Simulated metrics (no dependencies):
    python3 system_health_monitor.py --simulate --interval 1 --iterations 10 --log-file health.log
"""

import argparse
import logging
import time
import datetime
import random
import os
import sys

def try_import_psutil():
    try:
        import psutil  # type: ignore
        return psutil
    except Exception:
        return None

def get_metrics_real(psutil):
    # CPU
    cpu = psutil.cpu_percent(interval=None)
    # Memory
    mem = psutil.virtual_memory().percent
    # Disk (max percent used across non-temp partitions)
    max_disk = 0.0
    for part in psutil.disk_partitions(all=False):
        if any(skip in (part.fstype or '').lower() for skip in ('tmpfs', 'devtmpfs', 'squashfs')):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint).percent
            if usage > max_disk:
                max_disk = usage
        except Exception:
            continue
    # Process count
    proc_count = len(psutil.pids())
    return dict(cpu=cpu, memory=mem, disk=max_disk, processes=proc_count)

def get_metrics_simulated():
    # Reasonable random ranges; sometimes spike to trigger alerts
    cpu = random.choice([random.uniform(5, 60), random.uniform(80, 99)])
    mem = random.choice([random.uniform(20, 70), random.uniform(75, 95)])
    disk = random.choice([random.uniform(30, 75), random.uniform(80, 98)])
    processes = int(random.choice([random.uniform(50, 200), random.uniform(300, 800)]))
    return dict(cpu=cpu, memory=mem, disk=disk, processes=processes)

def build_parser():
    p = argparse.ArgumentParser(description="Monitor system health and alert on thresholds.")
    p.add_argument("--interval", type=int, default=5, help="Seconds between checks (default 5)")
    p.add_argument("--iterations", type=int, default=12, help="How many checks to run (default 12)")
    p.add_argument("--cpu-threshold", type=float, default=80.0, help="CPU percent threshold (default 80)")
    p.add_argument("--mem-threshold", type=float, default=85.0, help="Memory percent threshold (default 85)")
    p.add_argument("--disk-threshold", type=float, default=90.0, help="Disk percent threshold (default 90)")
    p.add_argument("--proc-threshold", type=int, default=500, help="Process count threshold (default 500)")
    p.add_argument("--log-file", type=str, default=None, help="Path to log file for alerts")
    p.add_argument("--console-only", action="store_true", help="Print alerts only to console, no file logging")
    p.add_argument("--simulate", action="store_true", help="Use simulated metrics (no psutil required)")
    return p

def setup_logger(log_file, console_only):
    logger = logging.getLogger("health")
    logger.setLevel(logging.INFO)
    logger.handlers = []
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    if not console_only and log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger

def main():
    args = build_parser().parse_args()
    logger = setup_logger(args.log_file, args.console_only)

    psutil = None
    if not args.simulate:
        psutil = try_import_psutil()
        if psutil is None:
            print("psutil is not installed. Install it or use --simulate for a test run.", file=sys.stderr)
            sys.exit(2)

    exceeded_any = False

    for i in range(1, args.iterations + 1):
        if args.simulate:
            metrics = get_metrics_simulated()
        else:
            metrics = get_metrics_real(psutil)

        cpu = metrics["cpu"]
        mem = metrics["memory"]
        disk = metrics["disk"]
        procs = metrics["processes"]

        status = []
        if cpu > args.cpu_threshold:
            status.append(f"CPU {cpu:.1f}% > {args.cpu_threshold}%")
        if mem > args.mem_threshold:
            status.append(f"MEM {mem:.1f}% > {args.mem_threshold}%")
        if disk > args.disk_threshold:
            status.append(f"DISK {disk:.1f}% > {args.disk_threshold}%")
        if procs > args.proc_threshold:
            status.append(f"PROCS {procs} > {args.proc_threshold}")

        # Always print a heartbeat line so you can see it working
        logger.info("Check %d/%d | cpu=%.1f%% mem=%.1f%% disk=%.1f%% procs=%d",
                    i, args.iterations, cpu, mem, disk, procs)

        if status:
            exceeded_any = True
            logger.warning("ALERT: " + " | ".join(status))

        if i < args.iterations:
            time.sleep(args.interval)

    if exceeded_any:
        # Non-zero exit helps CI or cron detect problems
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
