"""Evaluate a trained generator on a held-out split.

    python evaluate.py --checkpoint runs/pix2pix/checkpoints/best.pt \
        --data-dir data/edges2shoes/val --fid
Writes metrics.json and qualitative grids to <out>.
"""
import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from s2i.dataset import PairedSketchDataset
from s2i.metrics import FIDCalculator, image_metrics
from s2i.models import UNetGenerator
from s2i.utils import save_grid


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--data-dir", required=True)
    p.add_argument("--layout", choices=["aligned", "photos"], default=None, help="defaults to training layout")
    p.add_argument("--max-samples", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--fid", action="store_true", help="also compute FID (downloads Inception-v3)")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    G = UNetGenerator(1, 3, cfg["ngf"], cfg["image_size"], cfg["norm"]).to(device)
    G.load_state_dict(ckpt["G"])
    G.eval()

    ds = PairedSketchDataset(args.data_dir, args.layout or cfg["layout"], cfg["image_size"], False,
                             args.max_samples, cfg.get("sketch_method", "xdog"))
    dl = DataLoader(ds, args.batch_size, shuffle=False, num_workers=2)
    out = Path(args.out or Path(args.checkpoint).parent.parent / "eval")
    out.mkdir(parents=True, exist_ok=True)

    fid = FIDCalculator(device) if args.fid else None
    totals, n = {"l1": 0.0, "psnr": 0.0, "ssim": 0.0}, 0
    with torch.no_grad():
        for b, (sketch, real) in enumerate(dl):
            sketch, real = sketch.to(device), real.to(device)
            fake = G(sketch)
            for f, r in zip(fake, real):
                for k, v in image_metrics(f, r).items():
                    totals[k] += v
                n += 1
            if fid is not None:
                fid.update(fake, real)
            if b < 4:
                save_grid(sketch, fake, real, out / f"qualitative_{b}.png")

    results = {k: v / n for k, v in totals.items()}
    results["n_images"] = n
    results["epoch"] = ckpt["epoch"] + 1
    if fid is not None:
        results["fid"] = fid.compute()
    (out / "metrics.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"saved to {out}")


if __name__ == "__main__":
    main()
