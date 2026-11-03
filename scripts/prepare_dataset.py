"""Build an aligned (sketch | photo) dataset from any folder of photos using XDoG or Canny.

    python scripts/prepare_dataset.py --src my_photos --dst data/custom --size 256 --val-frac 0.05
"""
import argparse
import random
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s2i.dataset import list_images  # noqa: E402
from s2i.sketch import photo_to_sketch  # noqa: E402


def center_square(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--dst", required=True)
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--method", choices=["xdog", "canny"], default="xdog")
    p.add_argument("--val-frac", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    files = list_images(args.src)
    random.Random(args.seed).shuffle(files)
    n_val = max(1, int(len(files) * args.val_frac))
    for split, subset in (("val", files[:n_val]), ("train", files[n_val:])):
        out = Path(args.dst) / split
        out.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(subset):
            photo = center_square(Image.open(f).convert("RGB")).resize((args.size, args.size), Image.BICUBIC)
            sketch = photo_to_sketch(photo, args.method).convert("RGB")
            pair = Image.new("RGB", (args.size * 2, args.size))
            pair.paste(sketch, (0, 0)); pair.paste(photo, (args.size, 0))
            pair.save(out / f"{i:06d}.jpg", quality=95)
        print(f"{split}: {len(subset)} pairs -> {out}")


if __name__ == "__main__":
    main()
