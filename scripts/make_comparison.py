"""Side-by-side comparison figure for the slides: sketch / L1-only / Pix2Pix / ground truth.

    python scripts/make_comparison.py --pix2pix runs/pix2pix/checkpoints/best.pt \
        --l1 runs/l1_only/checkpoints/best.pt --data-dir data/edges2shoes/val --out docs/comparison.png
"""
import argparse
import sys
from pathlib import Path

import torch
from torchvision.utils import save_image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from s2i.dataset import PairedSketchDataset  # noqa: E402
from s2i.models import UNetGenerator  # noqa: E402


def load(path, device):
    ckpt = torch.load(path, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    G = UNetGenerator(1, 3, cfg["ngf"], cfg["image_size"], cfg["norm"]).to(device)
    G.load_state_dict(ckpt["G"])
    return G.eval(), cfg


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pix2pix", required=True)
    p.add_argument("--l1", default=None)
    p.add_argument("--data-dir", required=True)
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--stride", type=int, default=29, help="pick every k-th val image for variety")
    p.add_argument("--out", default="docs/comparison.png")
    a = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    G, cfg = load(a.pix2pix, device)
    G_l1 = load(a.l1, device)[0] if a.l1 else None
    ds = PairedSketchDataset(a.data_dir, cfg["layout"], cfg["image_size"], False)
    idx = [(i * a.stride) % len(ds) for i in range(a.n)]
    sketch = torch.stack([ds[i][0] for i in idx]).to(device)
    real = torch.stack([ds[i][1] for i in idx]).to(device)
    with torch.no_grad():
        rows = [sketch.repeat(1, 3, 1, 1)]
        if G_l1 is not None:
            rows.append(G_l1(sketch))
        rows += [G(sketch), real]
    grid = torch.cat(rows)  # row-major: each row is one method
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    save_image((grid.float().cpu() + 1) / 2, a.out, nrow=a.n, padding=4, pad_value=1.0)
    print("saved", a.out, "rows:", "sketch," + ("L1-only," if G_l1 else "") + "pix2pix,real")


if __name__ == "__main__":
    main()
