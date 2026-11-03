"""Builds docs/Sketch2Image_Project_Report.pdf: a complete written summary of the project.

    python docs/build_report_pdf.py
Reads metrics from runs/*/eval/metrics.json when present, otherwise uses the recorded values.
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "Sketch2Image_Project_Report.pdf"

FONT_DIR = Path("C:/Windows/Fonts")
try:
    pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Italic", str(FONT_DIR / "ariali.ttf")))
    pdfmetrics.registerFont(TTFont("Body-BoldItalic", str(FONT_DIR / "arialbi.ttf")))
    pdfmetrics.registerFont(TTFont("Head", str(FONT_DIR / "cambriab.ttf")))
    pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "cour.ttf")))
    from reportlab.lib.fonts import addMapping
    addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-Bold")
    addMapping("Body", 0, 1, "Body-Italic"); addMapping("Body", 1, 1, "Body-BoldItalic")
    BODY, BOLD, HEAD, MONO = "Body", "Body-Bold", "Head", "Mono"
except Exception:  # non-Windows fallback
    BODY, BOLD, HEAD, MONO = "Helvetica", "Helvetica-Bold", "Times-Bold", "Courier"

INK = colors.HexColor("#1F2430")
MUTED = colors.HexColor("#5F6573")
ACCENT = colors.HexColor("#E8743B")
BLUE = colors.HexColor("#2E86AB")
LIGHT = colors.HexColor("#F1F2F5")
RULE = colors.HexColor("#D9DCE3")

H1 = ParagraphStyle("H1", fontName=HEAD, fontSize=26, leading=31, textColor=INK, spaceAfter=4)
SUB = ParagraphStyle("Sub", fontName=BODY, fontSize=12.5, leading=17, textColor=ACCENT, spaceAfter=10)
H2 = ParagraphStyle("H2", fontName=HEAD, fontSize=16, leading=20, textColor=INK, spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle("H3", fontName=BOLD, fontSize=11.5, leading=15, textColor=INK, spaceBefore=8, spaceAfter=3)
P = ParagraphStyle("P", fontName=BODY, fontSize=10.5, leading=15, textColor=INK, spaceAfter=6, alignment=TA_LEFT)
CAP = ParagraphStyle("Cap", fontName=BODY, fontSize=9, leading=12, textColor=MUTED, spaceBefore=3, spaceAfter=10)
CELL = ParagraphStyle("Cell", fontName=BODY, fontSize=9.5, leading=12.5, textColor=INK)
CELLB = ParagraphStyle("CellB", parent=CELL, fontName=BOLD, textColor=colors.white)
CODE = ParagraphStyle("Code", fontName=MONO, fontSize=8.8, leading=12, textColor=INK, backColor=LIGHT,
                      borderPadding=(5, 6, 5, 6), spaceBefore=4, spaceAfter=10)
FORM = ParagraphStyle("Form", fontName=BODY, fontSize=10.5, leading=15, textColor=BLUE, leftIndent=12, spaceAfter=6)

CONTENT_W = A4[0] - 2 * 20 * mm


def bullets(items):
    return ListFlowable([ListItem(Paragraph(t, P), leftIndent=12, value="•") for t in items],
                        bulletType="bullet", start="•", leftIndent=12, bulletFontName=BODY, bulletFontSize=9)


def table(rows, widths, header=True, mono_first=False):
    data = []
    for i, r in enumerate(rows):
        row = []
        for j, c in enumerate(r):
            st = CELLB if header and i == 0 else CELL
            if mono_first and j == 0 and i > 0:
                c = f'<font face="{MONO}">{c}</font>'
            row.append(Paragraph(c, st))
        data.append(row)
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), INK))
    for i in range(1 if header else 0, len(rows)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    return t


def figure(path, width, caption):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    img = Image(str(path), width=width, height=width * h / w)
    img.hAlign = "LEFT"
    return KeepTogether([img, Paragraph(caption, CAP)])


def load_metrics():
    rec = {"l1_only": {"l1": 0.0745, "psnr": 18.17, "ssim": 0.733, "fid": 176.2},
           "pix2pix": {"l1": 0.0862, "psnr": 16.51, "ssim": 0.695, "fid": 184.0}}
    for k in rec:
        f = ROOT / "runs" / k / "eval" / "metrics.json"
        if f.exists():
            m = json.loads(f.read_text())
            rec[k] = {"l1": m["l1"], "psnr": m["psnr"], "ssim": m["ssim"], "fid": m.get("fid", rec[k]["fid"])}
    return rec


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 12 * mm, "Sketch-to-Image Generator · Project Report")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def build():
    m = load_metrics()
    s = []
    s.append(Paragraph("Sketch-to-Image Generator", H1))
    s.append(Paragraph("A Pix2Pix conditional GAN that turns line sketches into realistic images, "
                       "served through a drawing web app", SUB))
    s.append(Paragraph("Track A: Generative Adversarial Networks (Unit 3) · Devansh Vashisth · November 2026 · "
                       "github.com/devansh-vashisth/sketch-to-image-generator", CAP))

    s.append(Paragraph("Summary", H2))
    s.append(Paragraph(
        "This project implements image-to-image translation from hand-drawn line sketches to coloured photographs "
        "using Pix2Pix (Isola et al., 2017). A U-Net generator learns to fill in an outline with colour, shading and "
        "texture. A PatchGAN discriminator, conditioned on the same sketch, judges whether each image patch looks real. "
        "The model was trained on a 3,000-image subset of edges2shoes at 128 × 128 px in about 12 minutes on an "
        "RTX 3050 laptop GPU. An L1-only ablation was trained for comparison. A FastAPI web app lets a user draw a "
        "sketch in the browser and get a generated image back.", P))
    s.append(table([
        ["Item", "Outcome"],
        ["Model", "U-Net generator (41.8 M params at 128 px) + 70 × 70 PatchGAN discriminator (2.8 M)"],
        ["Training", "3,000 pairs, 20 epochs (12 constant + 8 decay), batch 8, mixed precision, ~35 s / epoch"],
        ["Pix2Pix results", f"L1 {m['pix2pix']['l1']:.4f} · PSNR {m['pix2pix']['psnr']:.2f} dB · "
                            f"SSIM {m['pix2pix']['ssim']:.3f} · FID {m['pix2pix']['fid']:.1f} (200 val images)"],
        ["Main finding", "L1-only wins on pixel metrics but is blurry; the adversarial loss gives sharper, "
                         "more realistic texture, as reported in the original paper"],
        ["Deliverables", "Code, training and evaluation pipeline, ablation, web app, concepts PDF, slide deck, this report"],
    ], [32 * mm, CONTENT_W - 32 * mm]))

    s.append(Paragraph("1. Problem and approach", H2))
    s.append(Paragraph(
        "Given a sketch x, the task is to produce an image y that matches the outline and looks like a real photo. "
        "The mapping has many valid answers: a sketch does not determine colour or material. A plain regression "
        "loss such as L1 therefore averages over the valid answers and produces a blurry result. A conditional "
        "GAN fixes this by adding a learned loss: a discriminator that penalises any output that does not look real.", P))

    s.append(Paragraph("2. Architecture", H2))
    s.append(Paragraph("Generator: U-Net", H3))
    s.append(bullets([
        "Encoder of 7 strided 4 × 4 convolutions (at 128 px) that halve the resolution down to a 1 × 1 bottleneck; "
        "LeakyReLU(0.2) and BatchNorm.",
        "Decoder of 7 transposed convolutions back to 128 × 128 with ReLU; dropout 0.5 in the first three decoder "
        "blocks provides stochasticity.",
        "Skip connections concatenate each encoder feature map with the decoder map of the same size. This carries "
        "the exact edge positions across, so the output keeps the outline. Final Tanh gives an RGB image in [−1, 1].",
    ]))
    s.append(Paragraph("Discriminator: 70 × 70 PatchGAN", H3))
    s.append(bullets([
        "Input is the sketch concatenated with a real or generated image (4 channels).",
        "Three strided convolutions plus two stride-1 layers produce a grid of logits (14 × 14 at 128 px). Each "
        "logit scores one overlapping 70 × 70 patch as real or fake.",
        "Judging patches instead of the whole image focuses D on local texture and sharpness, the part L1 cannot "
        "supervise, and keeps the network small (2.8 M parameters).",
        "All weights are initialised from N(0, 0.02), following the paper.",
    ]))

    s.append(Paragraph("3. Training objective", H2))
    s.append(Paragraph("Generator loss:", P))
    s.append(Paragraph("L<sub>G</sub> = BCE(D(x, G(x)), 1) + λ<sub>L1</sub> · ‖y − G(x)‖<sub>1</sub>, "
                       "with λ<sub>L1</sub> = 100", FORM))
    s.append(Paragraph("Discriminator loss:", P))
    s.append(Paragraph("L<sub>D</sub> = ½ [BCE(D(x, y), 1) + BCE(D(x, G(x)), 0)]", FORM))
    s.append(Paragraph(
        "Each iteration first updates D on one real and one generated pair, then updates G. The L1 term pins down "
        "low-frequency structure (shape, overall colour). The adversarial term supplies high-frequency detail. "
        "Halving the D loss slows the discriminator so it does not overpower the generator. The code also supports "
        "LSGAN loss, label smoothing and a VGG-16 perceptual loss.", P))

    s.append(Paragraph("4. Data", H2))
    s.append(Paragraph(
        "edges2shoes contains 50,025 training pairs built from UT-Zappos50K shoe photos with HED edge maps. "
        "Each file is 512 × 256, with the sketch on the left and the photo on the right. This run used the first "
        "3,000 training pairs and all 200 validation pairs. Augmentation (resize, random crop, horizontal flip) "
        "is applied identically to both halves of a pair so they stay aligned. Pixel values are scaled to [−1, 1]. "
        "For other domains, scripts/prepare_dataset.py builds pairs from any folder of photos using XDoG or Canny "
        "edge extraction. At inference, user drawings are cropped, centred and binarised to resemble the training "
        "sketches.", P))
    s.append(figure(DOCS / "figures" / "pairs.png", 80 * mm, "Figure 1. edges2shoes validation pairs: sketch (top), photo (bottom)."))

    s.append(Paragraph("5. Training setup", H2))
    s.append(table([
        ["Setting", "Value"],
        ["Resolution", "128 × 128 px (reduced from 256 to fit the time budget)"],
        ["Data", "3,000 train / 200 validation pairs"],
        ["Batch size", "8"],
        ["Epochs", "12 at constant learning rate, then 8 with linear decay to 0"],
        ["Optimiser", "Adam, learning rate 2e-4, β = (0.5, 0.999), for both G and D"],
        ["Loss weights", "λ_GAN = 1, λ_L1 = 100 (Pix2Pix); λ_GAN = 0 for the L1-only ablation"],
        ["Normalisation", "BatchNorm"],
        ["Precision", "Automatic mixed precision (fp16) on CUDA"],
        ["Hardware / time", "NVIDIA RTX 3050 6 GB laptop GPU, ~35 s per epoch, ~12 min in total"],
        ["Checkpoint selection", "Best validation SSIM (epoch 12 for both models)"],
    ], [38 * mm, CONTENT_W - 38 * mm]))

    s.append(Paragraph("6. Training dynamics", H2))
    s.append(figure(DOCS / "figures" / "curves_pix2pix.png", CONTENT_W,
                    "Figure 2. Pix2Pix training curves: adversarial losses, generator L1 on the training set, "
                    "and validation SSIM / PSNR per epoch."))
    s.append(bullets([
        "<b>The adversarial game is stable.</b> D loss stays around 0.4–0.45 and never collapses to zero, so the "
        "generator keeps receiving useful gradients.",
        "<b>Reconstruction improves steadily.</b> Training L1 falls from 0.29 to 0.18, fastest once the learning "
        "rate starts to decay.",
        "<b>Validation metrics are noisy.</b> They swing from epoch to epoch because validation runs the generator in "
        "eval mode with BatchNorm running statistics, which are unstable with batch 8 and short training. "
        "InstanceNorm, or keeping BatchNorm in train mode at test time as the original Pix2Pix does, would fix this.",
    ]))
    s.append(figure(DOCS / "figures" / "progress.png", 120 * mm,
                    "Figure 3. Generator output on four validation sketches. Columns: sketch, epochs 1, 3, 9 and 20, "
                    "real photo. Shape is learned first; texture and colour variation arrive later."))

    s.append(Paragraph("7. Results", H2))
    s.append(Paragraph("Quantitative (all 200 validation images, best-SSIM checkpoint):", P))
    s.append(table([
        ["Model", "L1 ↓", "PSNR ↑", "SSIM ↑", "FID ↓"],
        ["L1 only (λ_GAN = 0)", f"{m['l1_only']['l1']:.4f}", f"{m['l1_only']['psnr']:.2f} dB",
         f"{m['l1_only']['ssim']:.3f}", f"{m['l1_only']['fid']:.1f}"],
        ["Pix2Pix (cGAN + L1)", f"{m['pix2pix']['l1']:.4f}", f"{m['pix2pix']['psnr']:.2f} dB",
         f"{m['pix2pix']['ssim']:.3f}", f"{m['pix2pix']['fid']:.1f}"],
    ], [58 * mm] + [(CONTENT_W - 58 * mm) / 4] * 4))
    s.append(Spacer(1, 8))
    s.append(figure(DOCS / "comparison.png", 130 * mm,
                    "Figure 4. Qualitative comparison. Rows: input sketch, L1-only, Pix2Pix, ground truth."))
    s.append(Paragraph("Discussion", H3))
    s.append(bullets([
        "<b>The pixel metrics favour L1-only, as expected.</b> L1, PSNR and SSIM are maximised by predicting the "
        "per-pixel mean of all plausible images. That mean is the smooth, uniform brown shoe in row 2 of Figure 4.",
        "<b>Pix2Pix trades pixel accuracy for realism.</b> The adversarial loss produces laces, highlights and "
        "material texture (row 3). Because this texture is plausible but not identical to the specific ground-truth "
        "photo, it lowers the pixel metrics. This matches the original paper's ablation.",
        "<b>FID is inconclusive at this sample size.</b> FID estimates 2048-dimensional feature statistics and needs "
        "thousands of images. With 200 it is high-variance and biased upwards, so the 8-point gap is within noise.",
        "<b>The short training leaves visible artefacts.</b> The Pix2Pix outputs show checkerboard patterns and "
        "colour noise, which typically fade with longer training at full resolution.",
    ]))

    s.append(Paragraph("8. Web application", H2))
    s.append(bullets([
        "<b>Front end</b> (app/static): an HTML canvas with pen, eraser, brush size, undo, clear, image upload and an "
        "optional live mode that generates after every stroke. The result is shown next to the canvas and can be "
        "downloaded as PNG.",
        "<b>Back end</b> (app/server.py): FastAPI. <font face=\"%s\">POST /api/generate</font> cleans the sketch "
        "(crop, centre, binarise, resize), runs the generator on the GPU and returns a PNG. "
        "<font face=\"%s\">GET /api/health</font> reports whether a checkpoint is loaded." % (MONO, MONO),
        "<b>Verified:</b> the server loads the checkpoint on CUDA and returns a generated image for a validation "
        "sketch.",
    ]))
    s.append(Paragraph('$env:S2I_CHECKPOINT="runs/pix2pix/checkpoints/best.pt"<br/>'
                       "uvicorn app.server:app --port 8000   # then open http://localhost:8000", CODE))

    s.append(Paragraph("9. Code structure and reproduction", H2))
    s.append(table([
        ["Path", "Purpose"],
        ["s2i/models.py", "U-Net generator, PatchGAN discriminator, weight init"],
        ["s2i/losses.py", "Adversarial loss (BCE / LSGAN), VGG-16 perceptual loss"],
        ["s2i/dataset.py", "Paired dataset (aligned or photos + on-the-fly sketch), joint augmentation"],
        ["s2i/sketch.py", "XDoG and Canny sketch extraction, user-sketch cleaning"],
        ["s2i/metrics.py", "L1, PSNR, SSIM, FID"],
        ["train.py", "Alternating D/G updates, Adam, LR decay, AMP, checkpoints, sample grids"],
        ["evaluate.py", "Validation metrics, FID and qualitative grids → metrics.json"],
        ["infer.py", "Command-line inference on a file or folder"],
        ["app/", "FastAPI server and drawing canvas"],
        ["scripts/", "Data download, dataset preparation, curve plots, comparison figure"],
    ], [38 * mm, CONTENT_W - 38 * mm], mono_first=True))
    s.append(Spacer(1, 6))
    s.append(Paragraph(
        "python scripts/download_data.py edges2shoes<br/>"
        "python train.py --train-dir data/edges2shoes/train --val-dir data/edges2shoes/val \\<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;--max-train 3000 --image-size 128 --epochs 12 --epochs-decay 8 --out runs/pix2pix<br/>"
        "python train.py ... --lambda-gan 0 --out runs/l1_only<br/>"
        "python evaluate.py --checkpoint runs/pix2pix/checkpoints/best.pt --data-dir data/edges2shoes/val --fid<br/>"
        "python scripts/plot_curves.py runs/pix2pix<br/>"
        "python scripts/make_comparison.py --pix2pix runs/pix2pix/checkpoints/best.pt --l1 runs/l1_only/checkpoints/best.pt "
        "--data-dir data/edges2shoes/val", CODE))

    s.append(Paragraph("10. Limitations and next steps", H2))
    s.append(table([
        ["Limitation", "Next step"],
        ["Short run: 3k images, 128 px, 20 epochs", "Full schedule: 10k+ images at 256 px (about 2–3 h on the same GPU)"],
        ["Checkerboard noise and colour speckle", "Longer training; add perceptual loss (--lambda-vgg 10)"],
        ["Noisy validation from BatchNorm in eval mode", "Use --norm instance, or train-mode BN at test time"],
        ["FID on 200 images is unreliable", "Compute FID on at least 2,000 generated images"],
        ["Single domain (shoes)", "Build new domains from photo folders with XDoG (prepare_dataset.py)"],
    ], [CONTENT_W / 2, CONTENT_W / 2]))
    s.append(Paragraph("Conclusion", H3))
    s.append(Paragraph(
        "The project delivers a complete, working sketch-to-image system, from data preparation and GAN training "
        "to evaluation and an interactive web app. Even with a small training budget, the ablation reproduces the "
        "central Pix2Pix result: an L1 loss alone gives blurry averages, and the conditional adversarial loss is "
        "what produces realistic texture. Pixel metrics alone do not capture that improvement, so qualitative "
        "comparison and perceptual metrics such as FID matter when judging generative models.", P))

    s.append(Paragraph("References", H2))
    s.append(bullets([
        "Isola, Zhu, Zhou, Efros. <i>Image-to-Image Translation with Conditional Adversarial Networks.</i> CVPR 2017.",
        "Goodfellow et al. <i>Generative Adversarial Nets.</i> NeurIPS 2014.",
        "Ronneberger, Fischer, Brox. <i>U-Net: Convolutional Networks for Biomedical Image Segmentation.</i> MICCAI 2015.",
        "Winnemöller, Kyprianidis, Olsen. <i>XDoG: An eXtended Difference-of-Gaussians.</i> Computers &amp; Graphics 2012.",
        "Heusel et al. <i>GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium.</i> NeurIPS 2017.",
        "Yu, Grauman. <i>Fine-Grained Visual Comparisons with Local Learning (UT-Zappos50K).</i> CVPR 2014.",
    ]))

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                            bottomMargin=20 * mm, title="Sketch-to-Image Generator: Project Report",
                            author="Devansh Vashisth", subject="Pix2Pix sketch-to-image translation")
    doc.build(s, onFirstPage=on_page, onLaterPages=on_page)
    print("saved", OUT)


if __name__ == "__main__":
    build()
