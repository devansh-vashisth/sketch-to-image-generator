# Sketch-to-Image Generator

**Track A: Generative Adversarial Networks (Unit 3).** A conditional GAN (Pix2Pix) that turns a
hand-drawn line sketch into a realistic, coloured image. It ships with a web app: you draw on a
canvas in the browser, and a FastAPI backend runs the trained PyTorch generator.

```
 sketch (1×256×256) ──► U-Net Generator G ──► fake image (3×256×256)
        │                                         │
        └──────────────► concat ◄─────────────────┘   (or the real photo)
                           │
                  PatchGAN Discriminator D ──► 30×30 real/fake logits

 Loss_G = BCE(D(x, G(x)), 1) + 100 · |y − G(x)|₁       Loss_D = ½[BCE(D(x,y),1) + BCE(D(x,G(x)),0)]
```

## Project structure

| Path | Purpose |
|---|---|
| `s2i/models.py` | U-Net generator (skip connections, dropout), 70×70 PatchGAN discriminator, N(0, 0.02) init |
| `s2i/losses.py` | Adversarial loss (BCE / LSGAN), optional VGG-16 perceptual loss |
| `s2i/dataset.py` | Paired dataset (aligned A\|B images *or* plain photos + on-the-fly sketch), random jitter + flip |
| `s2i/sketch.py` | XDoG and Canny sketch extraction; cleaning of user sketches (crop, centre, binarise) |
| `s2i/metrics.py` | L1, PSNR, SSIM, FID |
| `s2i/inference.py` | Loads a checkpoint and runs sketch → image |
| `train.py` | Training loop: alternating D/G updates, Adam, linear LR decay, AMP, checkpoints, sample grids |
| `evaluate.py` | Test-set metrics (+ FID) and qualitative grids → `metrics.json` |
| `infer.py` | CLI inference on a file or folder |
| `app/` | FastAPI server and HTML/JS drawing canvas |
| `scripts/download_data.py` | Downloads edges2shoes / edges2handbags |
| `scripts/prepare_dataset.py` | Builds your own paired dataset from any photo folder |
| `scripts/plot_curves.py` | Loss and metric curves for the report |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate                 # Windows   (Linux/macOS: source .venv/bin/activate)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # NVIDIA GPU
pip install -r requirements.txt
```

## 1. Data

**Option A: edges2shoes** (50,025 train / 200 val pairs, UT-Zappos50K shoes with HED edge maps):
```bash
python scripts/download_data.py edges2shoes
```
Each file is 512×256, with the sketch on the left half and the photo on the right half.

**Option B: your own domain** (faces, cars, anime, …). Collect photos in a folder, then:
```bash
python scripts/prepare_dataset.py --src my_photos --dst data/custom --method xdog
```

## 2. Train

```bash
# RTX 3050 6 GB: about 6–8 min per epoch on 10k images at 256 px with AMP
python train.py --train-dir data/edges2shoes/train --val-dir data/edges2shoes/val ^
    --max-train 10000 --epochs 15 --epochs-decay 10 --batch-size 8 --out runs/pix2pix
```
Every epoch writes `runs/pix2pix/samples/epoch_XXX.png` (sketch | generated | real),
`log.csv`, `checkpoints/latest.pt` and `checkpoints/best.pt` (best val SSIM).
Use `--resume runs/pix2pix/checkpoints/latest.pt` to continue an interrupted run.

Useful flags: `--gan-mode lsgan`, `--lambda-vgg 10` (perceptual loss), `--real-label 0.9`
(label smoothing), `--norm instance`, `--image-size 128` (faster).

**Ablation baseline (no adversarial loss):**
```bash
python train.py ... --lambda-gan 0 --out runs/l1_only
```

## 3. Evaluate

```bash
python evaluate.py --checkpoint runs/pix2pix/checkpoints/best.pt --data-dir data/edges2shoes/val --fid
python scripts/plot_curves.py runs/pix2pix
```

## 4. Run the app

```bash
set S2I_CHECKPOINT=runs/pix2pix/checkpoints/best.pt      # PowerShell: $env:S2I_CHECKPOINT="..."
uvicorn app.server:app --port 8000
```
Open http://localhost:8000, draw a shoe outline and click **Generate**.

CLI alternative: `python infer.py --checkpoint runs/pix2pix/checkpoints/best.pt --input sketch.png --output out.png`

## Training hyper-parameters

| Setting | Value |
|---|---|
| Input / output | 1×256×256 sketch → 3×256×256 RGB, scaled to [-1, 1] |
| Generator | U-Net with 8 down / 8 up blocks, ~54.4 M params |
| Discriminator | 70×70 PatchGAN with 3 strided layers, ~2.8 M params |
| Loss | BCE-with-logits adversarial + λ_L1 = 100 |
| Optimiser | Adam, lr 2e-4, β = (0.5, 0.999), for both G and D |
| Schedule | constant LR for 15 epochs, then linear decay to 0 over 10 |
| Augmentation | resize to 286, random 256 crop, horizontal flip (same transform on the pair) |
| Precision | Automatic mixed precision (fp16) on CUDA |

## Results

Fill this in after training. `evaluate.py` prints the numbers.

| Model | L1 ↓ | PSNR ↑ | SSIM ↑ | FID ↓ |
|---|---|---|---|---|
| L1 only (`--lambda-gan 0`) | | | | |
| Pix2Pix (cGAN + L1) | | | | |

L1-only output usually scores well on PSNR but looks blurry. The cGAN gives sharper, more
realistic texture and a lower FID.

## References
- Isola et al., *Image-to-Image Translation with Conditional Adversarial Networks*, CVPR 2017
- Goodfellow et al., *Generative Adversarial Nets*, NeurIPS 2014
- Ronneberger et al., *U-Net*, MICCAI 2015
- Winnemöller et al., *XDoG: An eXtended Difference-of-Gaussians*, 2012
- Heusel et al., *GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium (FID)*, 2017
