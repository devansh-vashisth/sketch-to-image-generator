"""Download an official pix2pix paired dataset.

    python scripts/download_data.py edges2shoes      # ~2 GB, 50k train / 200 val
    python scripts/download_data.py edges2handbags   # ~8.6 GB, 137k train / 200 val
"""
import sys
import tarfile
import urllib.request
from pathlib import Path

BASE = "http://efrosgans.eecs.berkeley.edu/pix2pix/datasets/{}.tar.gz"
CHOICES = ["edges2shoes", "edges2handbags"]


def progress(block, block_size, total):
    done = block * block_size
    if total > 0:
        pct = min(100, done * 100 / total)
        sys.stdout.write(f"\r{pct:5.1f}%  {done / 1e6:8.1f} / {total / 1e6:.1f} MB")
        sys.stdout.flush()


def main(name):
    if name not in CHOICES:
        sys.exit(f"choose one of {CHOICES}")
    data = Path("data")
    data.mkdir(exist_ok=True)
    archive = data / f"{name}.tar.gz"
    if not archive.exists():
        print("downloading", BASE.format(name))
        urllib.request.urlretrieve(BASE.format(name), archive, progress)
        print()
    print("extracting ...")
    with tarfile.open(archive) as tar:
        tar.extractall(data, filter="data")
    print(f"done: {data / name}/train and {data / name}/val")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "edges2shoes")
