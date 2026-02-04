#!/usr/bin/env python3
import argparse
import os
import shlex
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def die(msg, code=1):
    print(msg, flush=True)
    raise SystemExit(code)

def sanitize_filename(s: str) -> str:
    s = s.replace('/', '-').replace(':', '_').replace(' ', '_')
    return s

def read_targets(path: str):
    if not os.path.isfile(path):
        die(f"[!] Error: targets file not found: {path}", 2)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            t = line.strip()
            if not t or t.startswith('#'):
                continue
            yield t

def ensure_nmap_exists():
    if shutil.which('nmap') is None:
        die("Get your fking shit together...\n[!] Error: nmap not found", 4)

def run_nmap(target: str, flags: list, out_dir: str):
    filename = sanitize_filename(target)
    prefix_tmp = os.path.join(out_dir, f".{filename}")   # hidden temp prefix
    prefix_final = os.path.join(out_dir, filename)

    # Build command: flags come BEFORE target or anywhere; we keep them before target
    cmd = ['nmap', *flags, target, '-oA', prefix_tmp]
    cmd_str = ' '.join(shlex.quote(x) for x in cmd)
    print(f"[i] Scanning: {target} -> {prefix_final}.nmap")
    print(f"[i] CMD: {cmd_str}")

    # Run nmap, suppress stdout; keep stderr for debug
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    if proc.returncode == 0:
        moved = []
        for ext in ('.nmap', '.gnmap', '.xml'):
            src = prefix_tmp + ext
            dst = prefix_final + ext
            if os.path.exists(src):
                os.replace(src, dst)
                moved.append(ext)
        print(f"[+] {target} - Scan Completed. Files: {', '.join(moved) if moved else 'none? (check flags/permissions)'}")
    else:
        # Cleanup partials
        for ext in ('.nmap', '.gnmap', '.xml'):
            try:
                os.remove(prefix_tmp + ext)
            except FileNotFoundError:
                pass
        print(f"[!] {target} - Scan Failed (exit {proc.returncode}).")
        if proc.stderr:
            # Print one condensed line of stderr for brevity
            first_line = proc.stderr.strip().splitlines()[0]
            print(f"    stderr: {first_line}")

def main():
    parser = argparse.ArgumentParser(
        description="Nmap Multi-Threaded Scanner (Default 3 threads). "
                    "All additional args are passed directly to nmap."
    )
    parser.add_argument("input_file", help="File containing targets (one per line). '#' comments allowed.")
    parser.add_argument("--threads", type=int, default=3, help="Number of concurrent scans (default: 3)")
    parser.add_argument("--out-dir", default="output", help='Output directory (default: "output")')

    # Capture all unknown/extra args and pass them verbatim to nmap
    args, nmap_flags = parser.parse_known_args()

    # Setup
    ensure_nmap_exists()
    os.makedirs(args.out_dir, exist_ok=True)

    targets = list(read_targets(args.input_file))
    if not targets:
        die("[!] No valid targets found in input file.", 2)

    print(f"[i] Threads={args.threads}")
    if nmap_flags:
        print(f"[i] Nmap flags: {' '.join(shlex.quote(x) for x in nmap_flags)}")
    else:
        print("[i] Nmap flags: (none provided)")

    # Concurrency
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = {pool.submit(run_nmap, t, nmap_flags, args.out_dir): t for t in targets}
        for fut in as_completed(futures):
            # trigger exception if any
            try:
                fut.result()
            except Exception as e:
                print(f"[!] Unexpected error scanning {futures[fut]}: {e}")

if __name__ == "__main__":
    main()
