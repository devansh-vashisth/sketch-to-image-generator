"""Plot training curves from runs/<name>/log.csv (for the results slide).

    python scripts/plot_curves.py runs/pix2pix
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main(run_dir):
    run = Path(run_dir)
    rows = list(csv.DictReader(open(run / "log.csv")))
    ep = [int(r["epoch"]) for r in rows]
    col = lambda k: [float(r[k]) for r in rows]

    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    ax[0].plot(ep, col("loss_D"), label="D loss")
    ax[0].plot(ep, col("loss_G_gan"), label="G adversarial loss")
    ax[0].set_title("Adversarial losses"); ax[0].legend()
    ax[1].plot(ep, col("loss_G_l1"), color="tab:green")
    ax[1].set_title("Generator L1 (train)")
    ax[2].plot(ep, col("val_ssim"), label="SSIM")
    ax2 = ax[2].twinx()
    ax2.plot(ep, col("val_psnr"), color="tab:red", label="PSNR (dB)")
    ax[2].set_title("Validation SSIM / PSNR")
    ax[2].legend(loc="lower left"); ax2.legend(loc="lower right")
    for a in ax:
        a.set_xlabel("epoch"); a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(run / "curves.png", dpi=150)
    print("saved", run / "curves.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "runs/pix2pix")
