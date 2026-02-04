# Nmap-MultiThreaded-Scanner
An Nmap multithreaded scanner that saves all scan outputs as a separate file.

```
usage: test.py [-h] [--threads THREADS] [--out-dir OUT_DIR] input_file

Nmap Multi-Threaded Scanner (Default 3 threads). All additional args are passed directly to nmap.

positional arguments:
  input_file         File containing targets (one per line). '#' comments allowed.

optional arguments:
  -h, --help         show this help message and exit
  --threads THREADS  Number of concurrent scans (default: 3)
  --out-dir OUT_DIR  Output directory (default: "output")
```
