#!/usr/bin/env python3
"""
log_analyzer.py
Simple analyzer for Apache/Nginx combined logs.

Usage:
    python3 log_analyzer.py -f /path/to/access.log --top 20
"""

import re
import gzip
import argparse
from collections import Counter
from urllib.parse import urlparse

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) '                 
    r'\S+ \S+ '                    
    r'\[(?P<time>.*?)\] '           
    r'"(?P<request>.*?)" '          
    r'(?P<status>\d{3}) '           
    r'(?P<size>\S+)'               
    r'(?: "(?P<referrer>.*?)" "(?P<agent>.*?)")?'  
)

def parse_request_line(request):
    parts = request.split()
    if len(parts) >= 2:
        method = parts[0]
        raw_url = parts[1]
        path = urlparse(raw_url).path
        return method, path
    return None, None

def open_maybe_gz(path):
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', errors='replace')
    return open(path, 'r', errors='replace')

def analyze_log_file(path, top_n=10):
    """
    Parse the log file and return a summary dictionary.
    """
    status_counter = Counter()
    ip_counter = Counter()
    path_counter = Counter()
    agent_counter = Counter()
    total = 0
    skipped = 0

    with open_maybe_gz(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            m = LOG_PATTERN.search(line)
            if not m:
                skipped += 1
                continue
            total += 1
            ip = m.group('ip')
            status = m.group('status')
            req = m.group('request')
            agent = m.group('agent') or '-'
            method, p = parse_request_line(req)
            p = p or '-'
            status_counter[status] += 1
            ip_counter[ip] += 1
            path_counter[p] += 1
            agent_counter[agent] += 1

    report = {
        'total_requests': total,
        'skipped_lines': skipped,
        'status_counts': status_counter,
        'top_404': status_counter.get('404', 0),
        'top_paths': path_counter.most_common(top_n),
        'top_ips': ip_counter.most_common(top_n),
        'top_user_agents': agent_counter.most_common(5),
    }
    return report

def print_report(report):
    print("\n=== Web Server Log Summary Report ===\n")
    print(f"Total parsed requests: {report['total_requests']}")
    if report['skipped_lines']:
        print(f"Skipped (unparsed) lines: {report['skipped_lines']}")
    print("\nStatus codes (top):")
    for code, cnt in report['status_counts'].most_common(10):
        print(f"  {code}: {cnt}")
    print(f"\nNumber of 404 errors: {report['top_404']}\n")
    print("Top requested paths:")
    for path, cnt in report['top_paths']:
        print(f"  {path} — {cnt} requests")
    print("\nTop IP addresses by request count:")
    for ip, cnt in report['top_ips']:
        print(f"  {ip} — {cnt} requests")
    print("\nTop user agents (sample):")
    for agent, cnt in report['top_user_agents']:
        print(f"  {agent[:60]}{'...' if len(agent) > 60 else ''} — {cnt}")
    print("\n=====================================\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze Apache/Nginx access logs for common patterns.")
    parser.add_argument('-f', '--file', required=True, help='Path to access.log (supports .gz)')
    parser.add_argument('--top', type=int, default=10, help='How many top items to show (default 10)')
    args = parser.parse_args()

    report = analyze_log_file(args.file, top_n=args.top)
    print_report(report)

if __name__ == '__main__':
    main()
