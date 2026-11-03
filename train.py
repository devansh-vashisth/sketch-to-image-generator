"""Train the Pix2Pix sketch-to-image cGAN.

Example (edges2shoes subset, RTX 3050 6 GB):
    python train.py --train-dir data/edges2shoes/train --val-dir data/edges2shoes/val \
        --max-train 10000 --epochs 15 --epochs-decay 10 --batch-size 8
"""
import argparse
import csv
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from s2i.dataset import PairedSketchDataset
from s2i.losses import GANLoss, VGGPerceptualLoss
from s2i.metrics import image_metrics
from s2i.models import PatchDiscriminator, UNetGenerator, count_params, init_weights
from s2i.utils import save_grid, seed_everything


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train-dir", required=True)
    p.add_argument("--val-dir", required=True)
    p.add_argument("--layout", choices=["aligned", "photos"], default="aligned")
    p.add_argument("--sketch-method", choices=["xdog", "canny"], default="xdog")
    p.add_argument("--max-train", type=int, default=None, help="use a random subset of N training images")
    p.add_argument("--max-val", type=int, default=200)
    p.add_argument("--image-size", type=int, default=256)
    p.add_argument("--ngf", type=int, default=64)
    p.add_argument("--ndf", type=int, default=64)
    p.add_argument("--norm", choices=["batch", "instance"], default="batch")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--epochs", type=int, default=15, help="epochs at the initial learning rate")
    p.add_argument("--epochs-decay", type=int, default=10, help="epochs to linearly decay LR to 0")
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--beta1", type=float, default=0.5)
    p.add_argument("--gan-mode", choices=["vanilla", "lsgan"], default="vanilla")
    p.add_argument("--lambda-gan", type=float, default=1.0, help="set 0 for the L1-only ablation baseline")
    p.add_argument("--lambda-l1", type=float, default=100.0)
    p.add_argument("--lambda-vgg", type=float, default=0.0, help=">0 adds VGG perceptual loss")
    p.add_argument("--real-label", type=float, default=1.0, help="e.g. 0.9 for one-sided label smoothing")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--no-amp", action="store_true", help="disable mixed precision")
    p.add_argument("--out", default="runs/pix2pix")
    p.add_argument("--resume", default=None, help="path to a checkpoint to resume from")
    p.add_argument("--save-every", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


@torch.no_grad()
def validate(G, loader, device, amp):
    G.eval()
    totals, n = {"l1": 0.0, "psnr": 0.0, "ssim": 0.0}, 0
    first = None
    for sketch, real in loader:
        sketch, real = sketch.to(device), real.to(device)
        with torch.autocast(device.type, enabled=amp):
            fake = G(sketch)
        if first is None:
            first = (sketch, fake, real)
        for f, r in zip(fake, real):
            for k, v in image_metrics(f, r).items():
                totals[k] += v
            n += 1
    G.train()
    return {k: v / n for k, v in totals.items()}, first


def main():
    args = parse_args()
    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp = device.type == "cuda" and not args.no_amp
    out = Path(args.out)
    (out / "samples").mkdir(parents=True, exist_ok=True)
    (out / "checkpoints").mkdir(exist_ok=True)
    (out / "config.json").write_text(json.dumps(vars(args), indent=2))

    train_ds = PairedSketchDataset(args.train_dir, args.layout, args.image_size, True,
                                   args.max_train, args.sketch_method, args.seed)
    val_ds = PairedSketchDataset(args.val_dir, args.layout, args.image_size, False,
                                 args.max_val, args.sketch_method, args.seed)
    train_dl = DataLoader(train_ds, args.batch_size, shuffle=True, num_workers=args.workers,
                          pin_memory=device.type == "cuda", drop_last=True, persistent_workers=args.workers > 0)
    val_dl = DataLoader(val_ds, args.batch_size, shuffle=False, num_workers=args.workers)

    G = UNetGenerator(1, 3, args.ngf, args.image_size, args.norm).to(device)
    D = PatchDiscriminator(1 + 3, args.ndf, 3, args.norm).to(device)
    init_weights(G)
    init_weights(D)
    print(f"device={device} amp={amp} train={len(train_ds)} val={len(val_ds)}")
    print(f"G params: {count_params(G) / 1e6:.2f}M | D params: {count_params(D) / 1e6:.2f}M")

    opt_G = torch.optim.Adam(G.parameters(), lr=args.lr, betas=(args.beta1, 0.999))
    opt_D = torch.optim.Adam(D.parameters(), lr=args.lr, betas=(args.beta1, 0.999))

    # Constant LR for `epochs`, then linear decay to zero over `epochs_decay`.
    def lr_lambda(epoch):
        return 1.0 - max(0, epoch + 1 - args.epochs) / float(args.epochs_decay + 1)

    sched_G = torch.optim.lr_scheduler.LambdaLR(opt_G, lr_lambda)
    sched_D = torch.optim.lr_scheduler.LambdaLR(opt_D, lr_lambda)
    scaler_G = torch.amp.GradScaler(device.type, enabled=amp)
    scaler_D = torch.amp.GradScaler(device.type, enabled=amp)

    gan_loss = GANLoss(args.gan_mode, real_label=args.real_label).to(device)
    l1_loss = nn.L1Loss()
    vgg_loss = VGGPerceptualLoss().to(device) if args.lambda_vgg > 0 else None

    start_epoch, best_ssim = 0, -1.0
    if args.resume:
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        G.load_state_dict(ckpt["G"]); D.load_state_dict(ckpt["D"])
        opt_G.load_state_dict(ckpt["opt_G"]); opt_D.load_state_dict(ckpt["opt_D"])
        sched_G.load_state_dict(ckpt["sched_G"]); sched_D.load_state_dict(ckpt["sched_D"])
        start_epoch, best_ssim = ckpt["epoch"] + 1, ckpt.get("best_ssim", -1.0)
        print(f"resumed from {args.resume} at epoch {start_epoch}")

    log_path = out / "log.csv"
    if not log_path.exists():
        with open(log_path, "w", newline="") as f:
            csv.writer(f).writerow(["epoch", "lr", "loss_D", "loss_G_gan", "loss_G_l1", "loss_G_vgg",
                                    "D_real", "D_fake", "val_l1", "val_psnr", "val_ssim", "sec"])

    total_epochs = args.epochs + args.epochs_decay
    for epoch in range(start_epoch, total_epochs):
        t0 = time.time()
        sums = dict(D=0.0, G_gan=0.0, G_l1=0.0, G_vgg=0.0, D_real=0.0, D_fake=0.0)
        for step, (sketch, real) in enumerate(train_dl):
            sketch, real = sketch.to(device, non_blocking=True), real.to(device, non_blocking=True)

            # ---- 1) Discriminator: maximise log D(x,y) + log(1 - D(x,G(x))) ----
            with torch.autocast(device.type, enabled=amp):
                fake = G(sketch)
                pred_real = D(sketch, real)
                pred_fake = D(sketch, fake.detach())  # detach: no gradient into G here
                loss_D = 0.5 * (gan_loss(pred_real, True) + gan_loss(pred_fake, False))
            opt_D.zero_grad(set_to_none=True)
            scaler_D.scale(loss_D).backward()
            scaler_D.step(opt_D)
            scaler_D.update()

            # ---- 2) Generator: fool D + stay close to ground truth (L1) ----
            for p in D.parameters():
                p.requires_grad_(False)
            with torch.autocast(device.type, enabled=amp):
                loss_gan = gan_loss(D(sketch, fake), True) if args.lambda_gan > 0 else torch.zeros((), device=device)
                loss_l1 = l1_loss(fake, real)
                loss_vgg = vgg_loss(fake, real) if vgg_loss is not None else torch.zeros((), device=device)
                loss_G = args.lambda_gan * loss_gan + args.lambda_l1 * loss_l1 + args.lambda_vgg * loss_vgg
            opt_G.zero_grad(set_to_none=True)
            scaler_G.scale(loss_G).backward()
            scaler_G.step(opt_G)
            scaler_G.update()
            for p in D.parameters():
                p.requires_grad_(True)

            sums["D"] += loss_D.item(); sums["G_gan"] += loss_gan.item()
            sums["G_l1"] += loss_l1.item(); sums["G_vgg"] += loss_vgg.item()
            sums["D_real"] += torch.sigmoid(pred_real.float()).mean().item()
            sums["D_fake"] += torch.sigmoid(pred_fake.float()).mean().item()
            if step % 100 == 0:
                print(f"[ep {epoch + 1}/{total_epochs}] step {step}/{len(train_dl)} "
                      f"D={loss_D.item():.3f} G_gan={loss_gan.item():.3f} G_L1={loss_l1.item():.3f}")

        sched_G.step(); sched_D.step()
        n = len(train_dl)
        avg = {k: v / n for k, v in sums.items()}
        val, (vs, vf, vr) = validate(G, val_dl, device, amp)
        save_grid(vs, vf, vr, out / "samples" / f"epoch_{epoch + 1:03d}.png")
        sec = time.time() - t0
        print(f"== epoch {epoch + 1}: D={avg['D']:.3f} G_gan={avg['G_gan']:.3f} L1={avg['G_l1']:.4f} | "
              f"val PSNR={val['psnr']:.2f} SSIM={val['ssim']:.4f} ({sec:.0f}s)")
        with open(log_path, "a", newline="") as f:
            csv.writer(f).writerow([epoch + 1, opt_G.param_groups[0]["lr"], avg["D"], avg["G_gan"], avg["G_l1"],
                                    avg["G_vgg"], avg["D_real"], avg["D_fake"], val["l1"], val["psnr"],
                                    val["ssim"], round(sec, 1)])

        ckpt = {"epoch": epoch, "config": vars(args), "G": G.state_dict(), "D": D.state_dict(),
                "opt_G": opt_G.state_dict(), "opt_D": opt_D.state_dict(),
                "sched_G": sched_G.state_dict(), "sched_D": sched_D.state_dict(),
                "best_ssim": max(best_ssim, val["ssim"]), "val": val}
        torch.save(ckpt, out / "checkpoints" / "latest.pt")
        if val["ssim"] > best_ssim:
            best_ssim = val["ssim"]
            torch.save(ckpt, out / "checkpoints" / "best.pt")
        if (epoch + 1) % args.save_every == 0:
            torch.save(ckpt, out / "checkpoints" / f"epoch_{epoch + 1:03d}.pt")

    print(f"done. best val SSIM={best_ssim:.4f}. checkpoints in {out / 'checkpoints'}")


if __name__ == "__main__":
    main()
