"""Builds docs/DL_Concepts_Sketch2Image.pdf: every deep-learning concept and algorithm used in this project.

    python docs/build_concepts_pdf.py
"""
import re
import sys
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ---------- fonts (Arial has Greek letters; Arial Unicode covers math symbols) ----------
FONT_DIR = Path("C:/Windows/Fonts")
try:
    pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "arialbd.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Italic", str(FONT_DIR / "ariali.ttf")))
    pdfmetrics.registerFont(TTFont("Body-BoldItalic", str(FONT_DIR / "arialbi.ttf")))
    pdfmetrics.registerFont(TTFont("Math", str(FONT_DIR / "ARIALUNI.ttf")))
    pdfmetrics.registerFont(TTFont("Mono", str(FONT_DIR / "consola.ttf")))
    from reportlab.lib.fonts import addMapping
    addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-Bold")
    addMapping("Body", 0, 1, "Body-Italic"); addMapping("Body", 1, 1, "Body-BoldItalic")
    BODY, BOLD, MATH, MONO = "Body", "Body-Bold", "Math", "Mono"
except Exception:  # non-Windows fallback (Greek glyphs may not render)
    BODY, BOLD, MATH, MONO = "Helvetica", "Helvetica-Bold", "Helvetica", "Courier"

INK = colors.HexColor("#1d1d1f")
MUTED = colors.HexColor("#5f6368")
ACCENT = colors.HexColor("#2f5bd3")
ACCENT_SOFT = colors.HexColor("#e8eefc")
GREEN_SOFT = colors.HexColor("#e7f4ea")
GREEN = colors.HexColor("#1e7b34")
AMBER_SOFT = colors.HexColor("#fdf3e1")
LINE = colors.HexColor("#d9d9de")

ss = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=28, leading=34, textColor=INK, alignment=TA_CENTER),
    "subtitle": ParagraphStyle("subtitle", fontName=BODY, fontSize=14, leading=20, textColor=MUTED, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=18, leading=23, textColor=ACCENT, spaceBefore=4, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=10, leading=14.5, textColor=INK, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=10, leading=14, textColor=INK, leftIndent=14,
                             bulletIndent=4, spaceAfter=2),
    "math": ParagraphStyle("math", fontName=MATH, fontSize=11, leading=16, textColor=INK, alignment=TA_CENTER),
    "code": ParagraphStyle("code", fontName=MONO, fontSize=8.6, leading=11.5, textColor=INK),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=8.8, leading=11.5, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=8.8, leading=11.5, textColor=colors.white),
    "note": ParagraphStyle("note", fontName=BODY, fontSize=9.2, leading=13, textColor=INK),
    "q": ParagraphStyle("q", fontName=BOLD, fontSize=10, leading=14, textColor=INK, spaceBefore=6),
    "a": ParagraphStyle("a", fontName=BODY, fontSize=9.6, leading=13.5, textColor=INK, leftIndent=10, spaceAfter=3),
    "small": ParagraphStyle("small", fontName=BODY, fontSize=8.5, leading=11, textColor=MUTED),
}

story = []
P = lambda text, style="body": story.append(Paragraph(text, ss[style]))
H1 = lambda text: story.append(Paragraph(text, ss["h1"]))
H2 = lambda text: story.append(Paragraph(text, ss["h2"]))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, ss["bullet"], bulletText="•"))


def box(flowables, bg, border=None, pad=8):
    t = Table([[flowables]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.6, border or bg),
        ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad - 2), ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 2),
    ]))
    story.append(Spacer(1, 3)); story.append(t); story.append(Spacer(1, 6))


def formula(*lines):
    box([Paragraph(re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group()), l), ss["math"]) for l in lines], ACCENT_SOFT)


def in_code(text):
    box([Paragraph(f"<font name='{BOLD}' color='#1e7b34'>In our code: </font>{text}", ss["note"])], GREEN_SOFT)


def code(text):
    lines = text.strip("\n").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").split("\n")
    box([Paragraph(l.replace(" ", "&nbsp;") or "&nbsp;", ss["code"]) for l in lines], colors.HexColor("#f4f4f6"), LINE)


def table(rows, widths, header=True):
    data = [[Paragraph(str(c), ss["cellb"] if header and i == 0 else ss["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f9")]),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), ACCENT))
    t.setStyle(TableStyle(style))
    story.append(t); story.append(Spacer(1, 8))


# ---------- diagrams ----------
def arrow(d, x1, y1, x2, y2, color=INK):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.2))
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    s = 5
    d.add(Polygon([x2, y2, x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4),
                   x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4)], fillColor=color, strokeColor=color))


def node(d, x, y, w, h, text, fill, size=8, sub=None):
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=fill, strokeColor=INK, strokeWidth=0.7))
    ty = y + h / 2 + (2 if sub else -3)
    d.add(String(x + w / 2, ty, text, fontName=BOLD, fontSize=size, textAnchor="middle", fillColor=INK))
    if sub:
        d.add(String(x + w / 2, ty - 10, sub, fontName=BODY, fontSize=size - 1.5, textAnchor="middle", fillColor=MUTED))


def pipeline_diagram():
    d = Drawing(480, 230)
    blue, green, amber, grey = ACCENT_SOFT, GREEN_SOFT, AMBER_SOFT, colors.HexColor("#f0f0f2")
    # training row
    d.add(String(0, 218, "TRAINING", fontName=BOLD, fontSize=8, fillColor=MUTED))
    node(d, 0, 160, 78, 44, "Paired data", grey, sub="edges2shoes")
    node(d, 96, 160, 82, 44, "Preprocess", grey, sub="jitter, flip, [-1,1]")
    node(d, 196, 160, 86, 44, "Generator G", blue, sub="U-Net")
    node(d, 300, 160, 86, 44, "Discriminator D", amber, sub="70x70 PatchGAN")
    node(d, 404, 160, 76, 44, "Losses", green, sub="GAN + 100 L1")
    arrow(d, 78, 182, 96, 182); arrow(d, 178, 182, 196, 182); arrow(d, 282, 182, 300, 182)
    arrow(d, 386, 182, 404, 182)
    d.add(Line(442, 160, 442, 140, strokeColor=ACCENT, strokeWidth=1))
    d.add(Line(442, 140, 239, 140, strokeColor=ACCENT, strokeWidth=1))
    arrow(d, 239, 140, 239, 160, ACCENT)
    d.add(Line(343, 140, 343, 158, strokeColor=ACCENT, strokeWidth=1))
    d.add(String(340, 128, "backprop: Adam updates D, then G", fontName=BODY, fontSize=7.5,
                 fillColor=ACCENT, textAnchor="middle"))
    # inference row
    d.add(String(0, 100, "INFERENCE / DEPLOYMENT", fontName=BOLD, fontSize=8, fillColor=MUTED))
    node(d, 0, 40, 78, 44, "Browser canvas", grey, sub="HTML / JS")
    node(d, 96, 40, 82, 44, "FastAPI", grey, sub="POST /api/generate")
    node(d, 196, 40, 86, 44, "Sketch cleaning", grey, sub="crop, binarise, resize")
    node(d, 300, 40, 86, 44, "Trained G", blue, sub="eval mode, no grad")
    node(d, 404, 40, 76, 44, "RGB image", green, sub="PNG back to UI")
    arrow(d, 78, 62, 96, 62); arrow(d, 178, 62, 196, 62); arrow(d, 282, 62, 300, 62); arrow(d, 386, 62, 404, 62)
    d.add(Line(239, 160, 239, 120, strokeColor=MUTED, strokeWidth=0.6, strokeDashArray=[2, 2]))
    d.add(Line(239, 120, 343, 120, strokeColor=MUTED, strokeWidth=0.6, strokeDashArray=[2, 2]))
    arrow(d, 343, 120, 343, 84, MUTED)
    d.add(String(352, 100, "best.pt checkpoint", fontName=BODY, fontSize=7, fillColor=MUTED))
    return d


def unet_diagram():
    d = Drawing(480, 250)
    sizes = [256, 128, 64, 32, 16, 8, 4, 2, 1]
    chans = [1, 64, 128, 256, 512, 512, 512, 512, 512]
    x0, step, top = 10, 26, 225
    for i, (s, c) in enumerate(zip(sizes, chans)):
        h = max(14, 140 * (s / 256) ** 0.5)
        x, y = x0 + i * step, top - i * 22 - h
        d.add(Rect(x, y, 14, h, fillColor=ACCENT_SOFT if i else colors.HexColor("#eeeeee"), strokeColor=INK, strokeWidth=0.6))
        d.add(String(x + 7, y - 9, f"{s}", fontName=BODY, fontSize=6.5, textAnchor="middle", fillColor=MUTED))
        d.add(String(x + 7, top - i * 22 + 3, f"{c}", fontName=BOLD, fontSize=6.5, textAnchor="middle", fillColor=INK))
        # mirrored decoder
        if i < 8:
            xr = 466 - i * step
            hr = max(14, 140 * (s / 256) ** 0.5)
            d.add(Rect(xr, y, 14, hr, fillColor=GREEN_SOFT if i else colors.HexColor("#ffe9d6"), strokeColor=INK, strokeWidth=0.6))
            d.add(String(xr + 7, y - 9, f"{s}", fontName=BODY, fontSize=6.5, textAnchor="middle", fillColor=MUTED))
            d.add(String(xr + 7, top - i * 22 + 3, "3" if i == 0 else f"{2 * chans[i]}", fontName=BOLD, fontSize=6.5,
                         textAnchor="middle", fillColor=INK))
            if 0 < i:
                d.add(Line(x + 14, y + h / 2, xr, y + hr / 2, strokeColor=colors.HexColor("#9aa9d8"), strokeWidth=0.8,
                           strokeDashArray=[3, 2]))
    d.add(String(240, 238, "skip connections (concatenate encoder features with decoder features)", fontName=BODY,
                 fontSize=7.5, textAnchor="middle", fillColor=ACCENT))
    d.add(String(10, 8, "Encoder: Conv 4x4 s2 + BN + LeakyReLU(0.2)", fontName=BODY, fontSize=7.5, fillColor=INK))
    d.add(String(470, 8, "Decoder: ConvT 4x4 s2 + BN + Dropout + ReLU", fontName=BODY, fontSize=7.5, fillColor=INK,
                 textAnchor="end"))
    d.add(String(240, 20, "bottleneck 1x1x512", fontName=BOLD, fontSize=7.5, fillColor=INK, textAnchor="middle"))
    d.add(String(14, 240, "input sketch", fontName=BODY, fontSize=7, fillColor=MUTED))
    d.add(String(470, 240, "output RGB (tanh)", fontName=BODY, fontSize=7, fillColor=MUTED, textAnchor="end"))
    return d


def patchgan_diagram():
    d = Drawing(480, 120)
    layers = [("x ⊕ y", "4×256×256", colors.HexColor("#eeeeee")), ("C64 s2", "64×128×128", AMBER_SOFT),
              ("C128 s2", "128×64×64", AMBER_SOFT), ("C256 s2", "256×32×32", AMBER_SOFT),
              ("C512 s1", "512×31×31", AMBER_SOFT), ("Conv s1", "1×30×30", GREEN_SOFT)]
    for i, (name, shape, fill) in enumerate(layers):
        x = i * 80
        node(d, x, 50, 66, 44, name, fill, sub=shape)
        if i:
            arrow(d, x - 14, 72, x, 72)
    d.add(String(240, 22, "each of the 30×30 outputs = real/fake logit for one 70×70 patch of the input",
                 fontName=BODY, fontSize=8, textAnchor="middle", fillColor=MUTED))
    return d


def gan_diagram():
    d = Drawing(480, 130)
    node(d, 0, 76, 70, 36, "Sketch x", colors.HexColor("#eeeeee"))
    node(d, 100, 76, 80, 36, "G(x)", ACCENT_SOFT, sub="generator")
    node(d, 210, 76, 80, 36, "fake ŷ", colors.HexColor("#eeeeee"))
    node(d, 210, 14, 80, 36, "real y", colors.HexColor("#eeeeee"))
    node(d, 320, 46, 80, 36, "D(x, ·)", AMBER_SOFT, sub="discriminator")
    node(d, 420, 46, 60, 36, "real?", GREEN_SOFT, sub="P(real)")
    arrow(d, 70, 94, 100, 94); arrow(d, 180, 94, 210, 94)
    arrow(d, 290, 94, 320, 74); arrow(d, 290, 32, 320, 56); arrow(d, 400, 64, 420, 64)
    d.add(Line(35, 76, 35, 4, strokeColor=MUTED, strokeWidth=0.8, strokeDashArray=[2, 2]))
    d.add(Line(35, 4, 360, 4, strokeColor=MUTED, strokeWidth=0.8, strokeDashArray=[2, 2]))
    arrow(d, 360, 4, 360, 46, MUTED)
    d.add(String(200, 120, "conditioning: D always sees the sketch too", fontName=BODY, fontSize=7.5,
                 fillColor=MUTED, textAnchor="middle"))
    return d


# ---------- parameter counts straight from the code ----------
try:
    from s2i.models import PatchDiscriminator, UNetGenerator, count_params
    G_PARAMS = count_params(UNetGenerator(1, 3, 64, 256))
    D_PARAMS = count_params(PatchDiscriminator(4, 64))
    G_STR, D_STR = f"{G_PARAMS / 1e6:.2f} M", f"{D_PARAMS / 1e6:.2f} M"
except Exception:
    G_STR, D_STR = "~54.4 M", "~2.8 M"


# =====================================================================================
# COVER
# =====================================================================================
story.append(Spacer(1, 55 * mm))
P("Sketch-to-Image Generator", "title")
story.append(Spacer(1, 6))
P("Deep Learning Concepts &amp; Algorithms Used", "subtitle")
story.append(Spacer(1, 18))
P("Conditional GAN (Pix2Pix) · U-Net Generator · PatchGAN Discriminator", "subtitle")
story.append(Spacer(1, 40))
P("Deep Learning &amp; Generative AI, CA-2 Project<br/>Track A: Generative Adversarial Networks (Unit 3)", "subtitle")
story.append(Spacer(1, 50))
table([["Team member", "Roll number", "Section"]] + [["<br/>&nbsp;", "", ""]] * 3, [70, 55, 45])
story.append(PageBreak())

# =====================================================================================
# CONTENTS
# =====================================================================================
H1("Contents")
toc = [
    ("1", "Project overview and end-to-end pipeline"),
    ("2", "Neural-network foundations: neurons, backpropagation, gradient descent"),
    ("3", "Convolutional building blocks: convolution, transposed convolution, activations, normalisation, dropout, init"),
    ("4", "Generative Adversarial Networks: minimax game, training algorithm"),
    ("5", "Conditional GANs and the Pix2Pix objective (cGAN + L1)"),
    ("6", "Generator architecture: encoder-decoder and U-Net skip connections"),
    ("7", "Discriminator architecture: PatchGAN and receptive fields"),
    ("8", "Dataset, sketch extraction (XDoG, Canny) and preprocessing"),
    ("9", "Optimisation: Adam, LR schedule, alternating updates, mixed precision"),
    ("10", "GAN training stability: failure modes and fixes"),
    ("11", "Evaluation metrics: L1, PSNR, SSIM, FID; ablation study"),
    ("12", "Inference and deployment"),
    ("13", "Hyper-parameter summary and concept-to-code map"),
    ("14", "Viva preparation: likely questions and answers"),
    ("15", "References"),
]
table([["#", "Section"]] + [[a, b] for a, b in toc], [12, 158])
P("This document explains every deep-learning idea used in the project repository. For each concept it "
  "gives the intuition, the maths, and where it appears in the code (green boxes). Track A covers "
  "image-to-image translation with Pix2Pix, conditional image generation (cGAN), and DCGAN design principles.",
  "body")
story.append(PageBreak())

# =====================================================================================
# 1 OVERVIEW
# =====================================================================================
H1("1. Project overview")
H2("Problem statement")
P("Designers, artists and e-commerce teams often begin with a rough line drawing. Turning that sketch into "
  "a realistic, coloured image takes skill and time. The task is <b>image-to-image translation</b>: learn a "
  "mapping G: sketch → photo from paired examples, so that a new hand-drawn outline produces a plausible "
  "image with correct shape, texture, colour and shading.")
P("This is ill-posed, because one sketch has many valid colourings. A plain regression network trained "
  "with pixel loss averages over all of them and gives blurry, grey output. A <b>conditional GAN</b> "
  "fixes this: a learned critic (the discriminator) penalises anything that does not look real, which "
  "pushes the generator to commit to one sharp, realistic answer.")
H2("Motivation")
bullets([
    "Rapid prototyping for product design (shoes, bags, apparel) and concept art.",
    "Data augmentation: generate many photo-realistic variants from cheap line art.",
    "A clear demonstration of the core Unit 3 ideas: adversarial training, conditioning, U-Net, PatchGAN.",
])
H2("End-to-end pipeline")
story.append(pipeline_diagram())
P("Figure 1. Training (top) learns G and D jointly. Deployment (bottom) uses only the trained generator "
  "behind a FastAPI endpoint called from a browser drawing canvas.", "small")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 2 FOUNDATIONS
# =====================================================================================
H1("2. Neural-network foundations")
H2("2.1 Artificial neuron and deep networks")
P("A neuron computes a weighted sum of its inputs plus a bias, then applies a non-linear activation. "
  "Stacking layers of neurons gives a deep network f(x; θ) that can approximate very complex functions "
  "(universal approximation). Without the non-linearity, any stack of layers would collapse into one "
  "linear map.")
formula("z = W·x + b,      a = φ(z)")
H2("2.2 Loss function and empirical risk")
P("Training minimises the average loss over the dataset, which measures how far predictions are from the "
  "targets. This project uses three kinds of loss: <b>binary cross-entropy</b> (adversarial), <b>L1 / mean "
  "absolute error</b> (reconstruction) and, optionally, a <b>perceptual</b> feature loss.")
formula("θ* = arg min<sub>θ</sub>  (1/N) Σ<sub>i</sub> L( f(x<sub>i</sub>; θ), y<sub>i</sub> )")
H2("2.3 Backpropagation")
P("Backpropagation applies the chain rule from the loss back to every weight, giving ∂L/∂θ for every "
  "parameter in one backward pass. PyTorch's <b>autograd</b> records the forward computation graph and "
  "calls <font name='Mono'>loss.backward()</font> to fill each parameter's <font name='Mono'>.grad</font>.")
formula("∂L/∂W<sup>(l)</sup> = δ<sup>(l)</sup> · a<sup>(l−1)T</sup>,     "
        "δ<sup>(l)</sup> = (W<sup>(l+1)T</sup> δ<sup>(l+1)</sup>) ⊙ φ′(z<sup>(l)</sup>)")
H2("2.4 Gradient descent and mini-batches")
P("Parameters move a small step against the gradient. <b>Mini-batch stochastic gradient descent</b> "
  "estimates the gradient from a small batch (8 images here), which is cheap and adds helpful noise. "
  "An <b>epoch</b> is one full pass over the training set.")
formula("θ ← θ − η · ∇<sub>θ</sub> L<sub>batch</sub>(θ)")
in_code("<font name='Mono'>DataLoader(batch_size=8, shuffle=True)</font> in <font name='Mono'>train.py</font>; "
        "the update rule is Adam (Section 9), a refined form of gradient descent.")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 3 CNN BUILDING BLOCKS
# =====================================================================================
H1("3. Convolutional building blocks")
H2("3.1 2-D convolution")
P("A convolution slides a small learnable kernel over the image. Each output value is a dot product "
  "between the kernel and a local patch. Two properties make CNNs the standard model for images: "
  "<b>weight sharing</b> (the same kernel is used at every position, so there are far fewer parameters) and "
  "<b>local connectivity</b> (nearby pixels are processed together, which builds in translation equivariance).")
formula("Y[i, j] = Σ<sub>c</sub> Σ<sub>u,v</sub> K[c, u, v] · X[c, s·i + u − p, s·j + v − p] + b",
        "H<sub>out</sub> = floor( (H<sub>in</sub> + 2p − k) / s ) + 1")
P("With kernel k=4, stride s=2 and padding p=1, every encoder layer exactly halves the resolution "
  "(256→128→…→1). <b>Strided convolution</b> replaces max-pooling, so the network learns its own "
  "down-sampling. This is one of the DCGAN guidelines.")
H2("3.2 Transposed convolution (up-sampling)")
P("Transposed convolution, sometimes called deconvolution, is the gradient of a convolution with respect "
  "to its input. Each input pixel scatters a weighted copy of the kernel into a larger output, so it "
  "<b>learns</b> how to up-sample. With k=4, s=2, p=1 it exactly doubles H and W.")
formula("H<sub>out</sub> = (H<sub>in</sub> − 1)·s − 2p + k  =  (H<sub>in</sub> − 1)·2 − 2 + 4  =  2·H<sub>in</sub>")
H2("3.3 Activation functions")
table([
    ["Function", "Formula", "Where used and why"],
    ["ReLU", "max(0, z)", "Decoder blocks of G. Cheap and does not saturate for z &gt; 0."],
    ["LeakyReLU (α = 0.2)", "max(αz, z)", "Encoder of G and all layers of D. Keeps a small gradient for z &lt; 0, "
     "avoids 'dead' units and keeps gradients flowing to G (DCGAN guideline)."],
    ["Tanh", "(e<super>z</super> − e<super>−z</super>)/(e<super>z</super> + e<super>−z</super>)",
     "Output layer of G. Bounded to [−1, 1], matching how the images are normalised."],
    ["Sigmoid", "1 / (1 + e<super>−z</super>)", "Folded into BCEWithLogitsLoss, which turns D's logits into "
     "probabilities. Using the fused form is numerically stable."],
], [32, 48, 90])
H2("3.4 Batch Normalisation and Instance Normalisation")
P("BatchNorm normalises each channel to zero mean and unit variance using batch statistics, then applies a "
  "learnable scale γ and shift β. It smooths the loss landscape, allows higher learning rates and "
  "stabilises GAN training. <b>InstanceNorm</b> normalises each image separately, which is common in style "
  "and translation models and is available as <font name='Mono'>--norm instance</font>.")
formula("x̂ = (x − μ<sub>B</sub>) / √(σ<sub>B</sub><super>2</super> + ε),      y = γ·x̂ + β")
P("Following Pix2Pix, there is <b>no normalisation</b> on the first encoder layer, on the 1×1 bottleneck "
  "(a single value per channel cannot be normalised), or on the first layer of D.")
H2("3.5 Dropout as the noise source")
P("Dropout randomly zeroes activations with probability p = 0.5. Normally it is a regulariser. In Pix2Pix "
  "it also acts as the <b>noise z</b> of the GAN: a random noise vector fed to G is simply ignored, so "
  "the randomness is injected through dropout in the first three decoder blocks.")
H2("3.6 Weight initialisation")
P("Every conv and transposed-conv weight is drawn from N(0, 0.02) and every norm scale γ from N(1, 0.02) "
  "(DCGAN / Pix2Pix). Small, symmetric initial weights keep early activations and gradients in a "
  "healthy range, so neither network dominates at the start.")
in_code("<font name='Mono'>Down</font>, <font name='Mono'>Up</font>, <font name='Mono'>init_weights()</font> in "
        "<font name='Mono'>s2i/models.py</font>.")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 4 GANs
# =====================================================================================
H1("4. Generative Adversarial Networks")
H2("4.1 Generative vs discriminative models")
P("A discriminative model learns p(label | data). A <b>generative</b> model learns to produce samples "
  "from the data distribution p<sub>data</sub>. GANs (Goodfellow et al., 2014) do this <i>implicitly</i>: "
  "there is no explicit likelihood. Instead, a generator G is trained to fool a discriminator D, and D is "
  "trained to tell real samples from generated ones.")
H2("4.2 The minimax game")
formula("min<sub>G</sub> max<sub>D</sub>  V(D, G) = E<sub>y∼p<sub>data</sub></sub>[ log D(y) ] + "
        "E<sub>z∼p<sub>z</sub></sub>[ log(1 − D(G(z))) ]")
P("For a fixed G, the optimal discriminator is D*(y) = p<sub>data</sub>(y) / (p<sub>data</sub>(y) + "
  "p<sub>g</sub>(y)). Substituting D* back in shows that G minimises the <b>Jensen–Shannon divergence</b> "
  "between the real and generated distributions. The global optimum is p<sub>g</sub> = p<sub>data</sub>, "
  "where D outputs 0.5 everywhere (a Nash equilibrium).")
formula("V(D*, G) = −log 4 + 2 · JSD( p<sub>data</sub> ‖ p<sub>g</sub> )")
H2("4.3 Non-saturating generator loss")
P("Early in training D easily rejects fakes, so log(1 − D(G(z))) saturates and gives almost no gradient. "
  "In practice G instead <b>maximises log D(G(z))</b>, which is equivalent to BCE with the target "
  "'real'. This has the same fixed point but much stronger gradients. Our code does exactly this: "
  "<font name='Mono'>gan_loss(D(sketch, fake), True)</font>.")
H2("4.4 GAN training algorithm (alternating SGD)")
code("""
for each mini-batch (x, y):
    # --- Discriminator step: ascend log D(x,y) + log(1 - D(x, G(x))) ---
    y_fake = G(x)
    L_D = 0.5 * [ BCE(D(x, y), 1) + BCE(D(x, y_fake.detach()), 0) ]
    update D with Adam on grad(L_D)

    # --- Generator step: fool D and stay close to the ground truth ---
    freeze D
    L_G = BCE(D(x, y_fake), 1) + lambda_L1 * |y - y_fake|_1
    update G with Adam on grad(L_G)
    unfreeze D
""")
P("<font name='Mono'>detach()</font> stops gradients from L<sub>D</sub> flowing into G. Freezing D "
  "(<font name='Mono'>requires_grad=False</font>) during the G step saves memory and compute, since only "
  "G's weights change there. The factor 0.5 on L<sub>D</sub> slows D down relative to G, as in Pix2Pix.")
H2("4.5 DCGAN design principles used")
bullets([
    "Strided convolutions instead of pooling, and transposed convolutions for up-sampling.",
    "Batch normalisation in both G and D (except the input/output layers).",
    "ReLU in G (Tanh at the output), LeakyReLU in D.",
    "Adam with lr = 2·10<super>−4</super> and β<sub>1</sub> = 0.5; weights initialised from N(0, 0.02).",
])
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 5 cGAN / Pix2Pix
# =====================================================================================
H1("5. Conditional GAN and the Pix2Pix objective")
H2("5.1 Conditional GAN (cGAN)")
P("A cGAN (Mirza &amp; Osindero, 2014) feeds extra information x to <b>both</b> networks. Here x is the "
  "input sketch. G learns p(y | x) instead of p(y), and D judges whether the pair (x, y) is a real match, "
  "not just whether y looks real. That is what forces the output to <b>follow the sketch's lines</b>.")
story.append(gan_diagram())
P("Figure 2. In a conditional GAN, D receives the sketch concatenated with either the real photo or "
  "G's output (4 channels in total).", "small")
formula("L<sub>cGAN</sub>(G, D) = E<sub>x,y</sub>[ log D(x, y) ] + E<sub>x</sub>[ log(1 − D(x, G(x))) ]")
H2("5.2 Adding a reconstruction loss (L1)")
P("Because training data is paired, G also gets a direct supervised signal: the L1 distance to the "
  "ground-truth photo. L1 captures <b>low-frequency</b> correctness (overall colour and layout). The "
  "adversarial loss supplies <b>high-frequency</b> realism (sharp edges, texture). L1 is preferred over "
  "L2 because it is less blurry: its minimiser is the median rather than the mean.")
formula("L<sub>L1</sub>(G) = E<sub>x,y</sub>[ ‖ y − G(x) ‖<sub>1</sub> ]")
H2("5.3 Final objective")
formula("G* = arg min<sub>G</sub> max<sub>D</sub>  L<sub>cGAN</sub>(G, D) + λ · L<sub>L1</sub>(G),"
        "        λ = 100")
P("λ = 100 balances the two terms. The L1 loss on [−1, 1] images is around 0.1–0.3 while the GAN loss is "
  "around 1, so scaling L1 by 100 makes the reconstruction signal dominant early on and keeps training "
  "stable. The adversarial term then sharpens the result.")
H2("5.4 Optional extensions implemented")
table([
    ["Flag", "Concept", "Effect"],
    ["--gan-mode lsgan", "Least-Squares GAN (Mao et al., 2017): L = (D − target)<super>2</super>",
     "Penalises samples by distance from the decision boundary. Smoother gradients, less vanishing."],
    ["--lambda-vgg 10", "Perceptual loss: L1 between VGG-16 feature maps of fake and real",
     "Transfer learning from ImageNet. Matches textures and structures rather than raw pixels."],
    ["--real-label 0.9", "One-sided label smoothing (Salimans et al., 2016)",
     "Stops D from becoming over-confident, which keeps G's gradients informative."],
    ["--lambda-gan 0", "Ablation: pure L1 regression (no GAN)",
     "Baseline showing what the adversarial loss adds (Section 11)."],
], [32, 70, 68])
in_code("<font name='Mono'>GANLoss</font> and <font name='Mono'>VGGPerceptualLoss</font> in "
        "<font name='Mono'>s2i/losses.py</font>; the combined objective is built in the G step of "
        "<font name='Mono'>train.py</font>.")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 6 U-NET
# =====================================================================================
H1("6. Generator: U-Net encoder-decoder")
H2("6.1 Encoder-decoder")
P("The encoder repeatedly halves the spatial resolution while increasing the channels, compressing the "
  "sketch into a 1×1×512 <b>bottleneck</b> that encodes global context (what object it is, what style). "
  "The decoder mirrors this to reconstruct a full-resolution image.")
H2("6.2 Why skip connections (U-Net)?")
P("In sketch-to-image translation, the input and output share the same <b>structure</b>: edges in the "
  "sketch must stay in the same place in the photo. Squeezing everything through a 1×1 bottleneck would "
  "lose those exact positions. A <b>U-Net</b> (Ronneberger et al., 2015) concatenates each encoder layer "
  "i with the decoder layer n−i, so fine spatial detail skips the bottleneck. Skip connections also "
  "shorten the gradient path, which makes a 16-layer network easy to train.")
story.append(unet_diagram())
P("Figure 3. U-Net generator for a 256×256 input. Numbers above the blocks are channels; numbers below are "
  "spatial size. Decoder blocks show channels after concatenation.", "small")
H2("6.3 Layer-by-layer shapes")
table([
    ["Block", "Operation", "Output shape", "Notes"],
    ["input", "sketch", "1 × 256 × 256", "grayscale, in [−1, 1]"],
    ["D1", "Conv4 s2, LReLU", "64 × 128 × 128", "no norm"],
    ["D2–D4", "Conv4 s2, BN, LReLU", "128×64², 256×32², 512×16²", ""],
    ["D5–D7", "Conv4 s2, BN, LReLU", "512 × 8², 4², 2²", ""],
    ["D8", "Conv4 s2, LReLU", "512 × 1 × 1", "bottleneck, no norm"],
    ["U1–U3", "ConvT4 s2, BN, Dropout 0.5, ReLU, concat", "1024 × 2², 4², 8²", "noise via dropout"],
    ["U4", "ConvT4 s2, BN, ReLU, concat", "1024 × 16²", ""],
    ["U5–U7", "ConvT4 s2, BN, ReLU, concat", "512×32², 256×64², 128×128²", ""],
    ["out", "ConvT4 s2, Tanh", "3 × 256 × 256", "RGB in [−1, 1]"],
], [18, 62, 50, 40])
P(f"Trainable parameters: <b>{G_STR}</b>. The number of down-sampling steps is computed as "
  "log<sub>2</sub>(image size), so the same code works at 64, 128 or 256 px.")
in_code("<font name='Mono'>UNetGenerator.forward()</font> pushes each encoder output onto a stack and pops "
        "them in reverse order for concatenation (<font name='Mono'>torch.cat([x, skips.pop()], 1)</font>).")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 7 PATCHGAN
# =====================================================================================
H1("7. Discriminator: PatchGAN")
H2("7.1 Idea")
P("Instead of one real/fake score for the whole image, a <b>PatchGAN</b> is a fully convolutional "
  "classifier that outputs an N×N grid. Each cell judges one local patch. The final score is the average "
  "loss over all patches. Because L1 already enforces low-frequency correctness, D only needs to model "
  "<b>high-frequency local texture</b>. In effect it treats the image as a Markov random field, assuming "
  "pixels more than a patch apart are independent.")
bullets([
    f"Far fewer parameters ({D_STR}) than a full-image classifier, so it is fast and less prone to over-fitting.",
    "Works on any image size, because it is fully convolutional.",
    "Produces sharp detail everywhere in the image instead of a single global judgement.",
])
story.append(patchgan_diagram())
P("Figure 4. The 70×70 PatchGAN. Input is the sketch concatenated with a real or fake image.", "small")
H2("7.2 Receptive-field calculation (why '70×70')")
P("The receptive field r of an output unit is computed backwards from the last layer using "
  "r<sub>in</sub> = (r<sub>out</sub> − 1)·s + k:")
table([
    ["Layer (from output)", "kernel k", "stride s", "receptive field r"],
    ["output unit", "–", "–", "1"],
    ["Conv → 1 ch", "4", "1", "(1−1)·1 + 4 = 4"],
    ["C512", "4", "1", "(4−1)·1 + 4 = 7"],
    ["C256", "4", "2", "(7−1)·2 + 4 = 16"],
    ["C128", "4", "2", "(16−1)·2 + 4 = 34"],
    ["C64", "4", "2", "(34−1)·2 + 4 = <b>70</b>"],
], [50, 30, 30, 60])
in_code("<font name='Mono'>PatchDiscriminator(in_ch=4, ndf=64, n_layers=3)</font> outputs raw logits of "
        "shape (B, 1, 30, 30); <font name='Mono'>GANLoss</font> compares them with an all-ones or all-zeros "
        "tensor of the same shape.")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 8 DATA
# =====================================================================================
H1("8. Dataset and preprocessing")
H2("8.1 Dataset: edges2shoes")
P("The main dataset is <b>edges2shoes</b> from the Pix2Pix authors: 50,025 training and 200 validation "
  "pairs built from UT-Zappos50K shoe photos. The sketches are edge maps made with the HED "
  "(Holistically-nested Edge Detection) CNN and post-processed into clean lines. Each file is 512×256, "
  "with the sketch on the left half and the photo on the right. edges2handbags (137k pairs) uses the same "
  "format. A random subset (<font name='Mono'>--max-train</font>, e.g. 10k) keeps training feasible on a "
  "6 GB laptop GPU.")
H2("8.2 Custom domains: XDoG sketch synthesis")
P("To train on any domain, <font name='Mono'>scripts/prepare_dataset.py</font> builds pairs automatically "
  "from photos with the <b>eXtended Difference-of-Gaussians (XDoG)</b> operator. A difference of two "
  "Gaussian blurs is a band-pass filter that approximates the Laplacian of Gaussian, so it responds to "
  "edges. A soft tanh threshold then turns the response into pencil-like strokes.")
formula("D(x) = G<sub>σ</sub>(x) − γ · G<sub>kσ</sub>(x)",
        "T(x) = 1  if D(x) ≥ ε,   else  1 + tanh( φ · (D(x) − ε) )",
        "σ = 0.8,  k = 1.6,  γ = 0.98,  ε = −0.1,  φ = 200")
P("<b>Canny</b> is offered as an alternative. It applies Gaussian smoothing, computes Sobel gradient "
  "magnitude and direction, thins edges with non-maximum suppression, and links them with double-threshold "
  "hysteresis (thresholds 60 / 150).")
H2("8.3 Preprocessing and augmentation")
table([
    ["Step", "Detail", "Reason"],
    ["Split pair", "left half → sketch (1 ch), right half → photo (3 ch)", "aligned A|B format"],
    ["Normalise", "x′ = 2·x/255 − 1  →  [−1, 1]", "matches Tanh output range and centres the data"],
    ["Random jitter", "resize to 286×286, random crop 256×256", "translation robustness; Pix2Pix recipe"],
    ["Horizontal flip", "p = 0.5", "doubles the effective data, since shoes are mirror-symmetric"],
    ["Paired transform", "the SAME crop/flip is applied to sketch and photo", "keeps pixel alignment for L1"],
    ["Validation", "plain resize to 256, no augmentation", "deterministic metrics"],
], [30, 75, 65])
H2("8.4 Cleaning hand-drawn sketches (inference)")
P("User drawings differ from training edge maps (line thickness, position, scale). This "
  "<b>domain gap</b> is reduced by: flattening transparency onto white, auto-inverting light-on-dark "
  "input, cropping to the stroke bounding box, centring on a square canvas with a 15% margin, area "
  "resampling to 256 px, and binarising at threshold 180.")
in_code("<font name='Mono'>PairedSketchDataset</font> in <font name='Mono'>s2i/dataset.py</font>; "
        "<font name='Mono'>xdog()</font>, <font name='Mono'>canny()</font> and "
        "<font name='Mono'>clean_user_sketch()</font> in <font name='Mono'>s2i/sketch.py</font>.")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 9 OPTIMISATION
# =====================================================================================
H1("9. Optimisation and training details")
H2("9.1 Adam optimiser")
P("Adam (Kingma &amp; Ba, 2015) keeps exponential moving averages of the gradient (first moment m) and of "
  "the squared gradient (second moment v). This gives each parameter its own adaptive step size, with "
  "bias correction for the early steps.")
formula("m<sub>t</sub> = β<sub>1</sub> m<sub>t−1</sub> + (1 − β<sub>1</sub>) g<sub>t</sub>,     "
        "v<sub>t</sub> = β<sub>2</sub> v<sub>t−1</sub> + (1 − β<sub>2</sub>) g<sub>t</sub><super>2</super>",
        "m̂<sub>t</sub> = m<sub>t</sub> / (1 − β<sub>1</sub><super>t</super>),     "
        "v̂<sub>t</sub> = v<sub>t</sub> / (1 − β<sub>2</sub><super>t</super>),     "
        "θ<sub>t</sub> = θ<sub>t−1</sub> − η · m̂<sub>t</sub> / (√v̂<sub>t</sub> + ε)")
P("GANs use <b>β<sub>1</sub> = 0.5</b> instead of the default 0.9. The adversarial objective is "
  "non-stationary (each network's target keeps moving), so less momentum lets the optimiser react faster "
  "and reduces oscillation. Settings: η = 2·10<super>−4</super>, β<sub>2</sub> = 0.999, with a separate "
  "optimiser for G and for D.")
H2("9.2 Learning-rate schedule: constant, then linear decay")
formula("η(e) = η<sub>0</sub> · [ 1 − max(0, e + 1 − E<sub>const</sub>) / (E<sub>decay</sub> + 1) ]")
P("The learning rate stays at η<sub>0</sub> for E<sub>const</sub> = 15 epochs, then decreases linearly "
  "towards 0 over E<sub>decay</sub> = 10 epochs. Annealing reduces the noise of the adversarial game and "
  "lets both networks settle (<font name='Mono'>torch.optim.lr_scheduler.LambdaLR</font>).")
H2("9.3 Automatic Mixed Precision (AMP)")
P("On CUDA, the forward and backward passes run in float16 inside "
  "<font name='Mono'>torch.autocast</font>. This roughly halves memory use and speeds up Tensor-Core "
  "matrix multiplies, which is what makes batch size 8 at 256 px fit on a 6 GB RTX 3050. Small fp16 "
  "gradients can underflow to zero, so a <b>GradScaler</b> multiplies the loss by a large factor before "
  "<font name='Mono'>backward()</font>, un-scales the gradients before the optimiser step, and adjusts "
  "the factor dynamically. It skips the step if it finds inf or NaN values. G and D each have their own "
  "scaler.")
H2("9.4 Checkpointing, model selection and reproducibility")
bullets([
    "Each epoch saves <font name='Mono'>latest.pt</font>: G, D, both optimisers, both schedulers and the config, "
    "so training can resume exactly (<font name='Mono'>--resume</font>).",
    "<font name='Mono'>best.pt</font> is the checkpoint with the highest validation SSIM. This is a form of early "
    "stopping and model selection on held-out data.",
    "<font name='Mono'>seed_everything()</font> fixes the Python, NumPy and PyTorch RNGs so runs are repeatable.",
    "A qualitative grid (sketch | generated | real) is saved every epoch for visual monitoring.",
])
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 10 STABILITY
# =====================================================================================
H1("10. GAN training stability")
P("GAN training is a two-player game, not a single minimisation, so the losses do not have to go down "
  "steadily. The logs record D's mean probability on real images (D_real) and on fakes (D_fake) to "
  "diagnose the following failure modes.")
table([
    ["Failure mode", "Symptom", "Mitigation used / available"],
    ["Discriminator overpowers G", "D_real → 1, D_fake → 0, G loss keeps rising, vanishing gradients",
     "0.5 factor on L_D; non-saturating G loss; label smoothing (--real-label 0.9); LSGAN"],
    ["Mode collapse", "G produces the same output for many inputs",
     "Strong conditioning on the sketch + L1 loss tie each output to its own input"],
    ["Oscillation / non-convergence", "Losses swing wildly, samples get worse",
     "Adam β1 = 0.5, low LR 2e-4, BatchNorm, LR decay"],
    ["Blurry outputs", "Plausible layout but washed-out colours and texture",
     "Adversarial PatchGAN loss; optional VGG perceptual loss"],
    ["Checkerboard artefacts", "Grid-like patterns from transposed convs",
     "k = 4 divisible by s = 2 (even kernel overlap); more training"],
    ["Over-fitting D", "Validation quality drops while training D loss → 0",
     "Small PatchGAN, data augmentation (jitter + flip)"],
], [36, 60, 74])
P("A healthy run usually shows D_real ≈ 0.6–0.8 and D_fake ≈ 0.2–0.4, with L1 decreasing slowly. "
  "The equilibrium in theory is D = 0.5 for both.")
story.append(Spacer(1, 4))

# =====================================================================================
# 11 METRICS
# =====================================================================================
H1("11. Evaluation metrics")
H2("11.1 Mean Absolute Error (L1)")
formula("L1 = (1 / HWC) Σ | y − ŷ |,    images scaled to [0, 1]   (lower is better)")
H2("11.2 Peak Signal-to-Noise Ratio (PSNR)")
formula("MSE = (1 / HWC) Σ (y − ŷ)<super>2</super>,       PSNR = 10 · log<sub>10</sub>( MAX<super>2</super> / MSE )  dB")
P("A pixel-fidelity metric where higher is better. It rewards blurry 'average' predictions, which is "
  "why it is not enough on its own for generative models.")
H2("11.3 Structural Similarity (SSIM)")
formula("SSIM(a, b) = [(2μ<sub>a</sub>μ<sub>b</sub> + C<sub>1</sub>)(2σ<sub>ab</sub> + C<sub>2</sub>)] / "
        "[(μ<sub>a</sub><super>2</super> + μ<sub>b</sub><super>2</super> + C<sub>1</sub>)"
        "(σ<sub>a</sub><super>2</super> + σ<sub>b</sub><super>2</super> + C<sub>2</sub>)]")
P("Compares local luminance, contrast and structure in sliding windows. Its range is [−1, 1] and higher "
  "is better. It is closer to human perception than PSNR and is used here to select the best checkpoint.")
H2("11.4 Fréchet Inception Distance (FID)")
formula("FID = ‖ μ<sub>r</sub> − μ<sub>g</sub> ‖<super>2</super> + "
        "Tr( Σ<sub>r</sub> + Σ<sub>g</sub> − 2 (Σ<sub>r</sub> Σ<sub>g</sub>)<super>1/2</super> )")
P("Real and generated images are passed through an ImageNet-trained Inception-v3. A Gaussian (μ, Σ) is "
  "fitted to each set's 2048-d pool features, and FID is the Fréchet (Wasserstein-2) distance between the "
  "two Gaussians. It measures <b>realism and diversity</b> at the distribution level; lower is better. It "
  "is the standard GAN metric (Heusel et al., 2017). With only 200 validation images FID is noisy, so "
  "compare models on the same set.")
H2("11.5 Ablation study and qualitative evaluation")
P("Train the same network with <font name='Mono'>--lambda-gan 0</font> (L1 only) and compare it with the "
  "full cGAN + L1. The usual result is that L1-only scores similar or higher PSNR but looks blurry and "
  "has a much worse FID, while the cGAN gives sharp, realistic texture. This isolates the contribution of "
  "adversarial training. Qualitative grids (sketch | output | ground truth) and outputs for unseen "
  "hand-drawn sketches from the web app complete the evaluation.")
in_code("<font name='Mono'>image_metrics()</font> and <font name='Mono'>FIDCalculator</font> in "
        "<font name='Mono'>s2i/metrics.py</font>; <font name='Mono'>evaluate.py</font> writes "
        "<font name='Mono'>metrics.json</font>, and <font name='Mono'>scripts/plot_curves.py</font> plots the "
        "loss and metric curves.")
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 12 DEPLOYMENT
# =====================================================================================
H1("12. Inference and deployment")
bullets([
    "<b>Only G is deployed.</b> D exists only to train G and is thrown away afterwards.",
    "<font name='Mono'>model.eval()</font> switches BatchNorm to its running statistics and turns dropout off, "
    "so outputs are deterministic. <font name='Mono'>torch.no_grad()</font> skips building the autograd graph, "
    "which saves memory and time.",
    "The <b>FastAPI</b> server loads the checkpoint once at start-up and exposes "
    "<font name='Mono'>POST /api/generate</font> (PNG in, PNG out, with an X-Inference-Ms latency header) and "
    "<font name='Mono'>GET /api/health</font>.",
    "The <b>frontend</b> is a plain HTML5 canvas with pen, eraser, brush size, undo, upload and a live mode. "
    "It sends the canvas as a PNG blob through <font name='Mono'>fetch()</font>. All deep-learning work happens "
    "server-side in PyTorch, so the web layer is a thin client and the core of the project is the trained "
    "model.",
    "One forward pass of the 54 M-parameter U-Net at 256 px takes a few milliseconds on a GPU and well under a "
    "second on a CPU, which is fast enough for interactive use.",
])
H1("13. Hyper-parameters and concept-to-code map")
table([
    ["Hyper-parameter", "Value", "Hyper-parameter", "Value"],
    ["Image size", "256 × 256", "Batch size", "8"],
    ["Generator", f"U-Net-256, {G_STR}", "Discriminator", f"PatchGAN 70×70, {D_STR}"],
    ["ngf / ndf", "64 / 64", "Normalisation", "BatchNorm"],
    ["Adversarial loss", "BCE with logits", "λ<sub>L1</sub>", "100"],
    ["Optimiser", "Adam (0.5, 0.999)", "Learning rate", "2·10<super>−4</super>"],
    ["Epochs", "15 constant + 10 decay", "Dropout", "0.5 in U1–U3"],
    ["Init", "N(0, 0.02)", "Precision", "AMP fp16 (CUDA)"],
], [38, 47, 38, 47])
table([
    ["Concept", "File / symbol"],
    ["U-Net, skip connections, dropout noise", "s2i/models.py · UNetGenerator, Down, Up"],
    ["PatchGAN discriminator", "s2i/models.py · PatchDiscriminator"],
    ["Weight initialisation N(0, 0.02)", "s2i/models.py · init_weights"],
    ["Adversarial loss (BCE / LSGAN), label smoothing", "s2i/losses.py · GANLoss"],
    ["Perceptual loss (transfer learning, VGG-16)", "s2i/losses.py · VGGPerceptualLoss"],
    ["XDoG / Canny edge extraction", "s2i/sketch.py · xdog, canny"],
    ["Paired augmentation, [-1, 1] normalisation", "s2i/dataset.py · PairedSketchDataset"],
    ["Alternating D/G updates, detach, freeze D", "train.py · main loop"],
    ["Adam, LambdaLR linear decay, AMP + GradScaler", "train.py"],
    ["PSNR, SSIM, L1, FID", "s2i/metrics.py; evaluate.py"],
    ["Inference, eval mode, sketch cleaning", "s2i/inference.py · SketchToImage"],
    ["Serving", "app/server.py (FastAPI), app/static (canvas UI)"],
], [80, 90])
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 14 VIVA
# =====================================================================================
H1("14. Viva preparation")
qa = [
    ("Why a GAN and not a plain CNN trained with L1/L2 loss?",
     "Many photos are consistent with one sketch. Pixel losses are minimised by the average of those "
     "possibilities, which is a blurry image. The adversarial loss penalises any output that does not look "
     "like a real photo, which forces sharp, committed predictions."),
    ("What makes it a conditional GAN?",
     "Both G and D receive the sketch. G maps sketch → image, and D classifies the concatenated "
     "(sketch, image) pair, so it rejects realistic images that do not match the sketch."),
    ("Why keep the L1 loss at all, and why λ = 100?",
     "L1 makes the output match the ground truth in colour and layout (low frequencies) and stabilises "
     "early training. λ = 100 brings the L1 term (about 0.1) to a scale comparable with or larger than the "
     "GAN term (about 1). This is the value from the Pix2Pix paper."),
    ("Why L1 instead of L2?", "L2 grows quadratically and is minimised by the mean, which gives more "
     "blur. L1 is minimised by the median, is more robust to outliers and gives less blur."),
    ("What does the U-Net skip connection do?",
     "It concatenates encoder features with decoder features of the same resolution. The exact edge "
     "positions in the sketch therefore reach the output without passing through the 1×1 bottleneck. It "
     "also improves gradient flow."),
    ("What is a PatchGAN and why 70×70?",
     "A fully convolutional discriminator that outputs a 30×30 grid of real/fake logits, each with a "
     "70×70 receptive field (derived in Section 7.2). It models local texture, has few parameters and "
     "works at any image size."),
    ("Where is the random noise z?",
     "There is no explicit z. Pix2Pix found that G learns to ignore it, so stochasticity comes from "
     "dropout in the first decoder layers."),
    ("Why LeakyReLU in D but ReLU in G?",
     "LeakyReLU keeps a gradient for negative inputs, so D can always pass useful gradients back to G. "
     "This follows the DCGAN guidelines."),
    ("Why Tanh at the output and [−1, 1] normalisation?",
     "Tanh is bounded and zero-centred. Scaling the targets to the same range makes the L1 loss "
     "consistent and keeps the data centred."),
    ("Why does Adam use β1 = 0.5 here?",
     "The GAN objective is non-stationary, so less momentum reduces oscillation and overshoot "
     "(DCGAN recommendation)."),
    ("Why detach the fake image in the D step?",
     "The D loss should update only D. detach() stops gradients from flowing into G's graph, which "
     "saves compute and avoids pushing G the wrong way."),
    ("What is the non-saturating loss?",
     "Instead of minimising log(1 − D(G(x))), which has tiny gradients when D wins, G maximises "
     "log D(G(x)), i.e. BCE with label 'real'. It has the same fixed point and much stronger gradients."),
    ("What is mode collapse, and is it a problem here?",
     "It is when G maps many inputs to the same output. Strong conditioning plus the L1 loss tie each "
     "output to its own sketch, so it is much less of a problem than in unconditional GANs."),
    ("How do you know the model is good?",
     "Quantitatively: L1, PSNR and SSIM on held-out validation pairs, plus FID for realism. "
     "Qualitatively: the sample grids and outputs for new hand-drawn sketches. The L1-only ablation shows "
     "what the adversarial term adds."),
    ("Why is PSNR not enough for GANs?",
     "It is a per-pixel error and rewards blurry averages. FID compares feature distributions and "
     "correlates better with how realistic the images look to humans."),
    ("What does mixed precision do?",
     "It runs most operations in fp16 for speed and lower memory use. GradScaler scales the loss up to "
     "prevent fp16 gradient underflow, then un-scales the gradients before the optimiser step."),
    ("How do hand-drawn sketches differ from training data, and how do you handle it?",
     "Line thickness, position and scale all differ (a domain gap). The input is cropped to the strokes, "
     "centred, resized and binarised to look like the training edge maps."),
    ("Limitations and future work?",
     "One output per sketch (limited diversity), domain-specific (shoes), and 256 px resolution. "
     "Possible extensions: BicycleGAN or a style code for multi-modal outputs, pix2pixHD or SPADE for high "
     "resolution, CycleGAN for unpaired data, and latent diffusion models such as ControlNet."),
    ("How is this different from CycleGAN?",
     "Pix2Pix needs paired data and uses a supervised L1 loss. CycleGAN works with unpaired domains using "
     "two generators and a cycle-consistency loss ‖F(G(x)) − x‖<sub>1</sub>."),
]
for q, a in qa:
    story.append(KeepTogether([Paragraph("Q. " + q, ss["q"]), Paragraph(a, ss["a"])]))
story.append(CondPageBreak(110 * mm))

# =====================================================================================
# 15 REFERENCES
# =====================================================================================
H1("15. References")
refs = [
    "I. Goodfellow et al., \"Generative Adversarial Nets,\" NeurIPS, 2014.",
    "M. Mirza and S. Osindero, \"Conditional Generative Adversarial Nets,\" arXiv:1411.1784, 2014.",
    "A. Radford, L. Metz and S. Chintala, \"Unsupervised Representation Learning with Deep Convolutional GANs "
    "(DCGAN),\" ICLR, 2016.",
    "P. Isola, J.-Y. Zhu, T. Zhou and A. A. Efros, \"Image-to-Image Translation with Conditional Adversarial "
    "Networks,\" CVPR, 2017.",
    "O. Ronneberger, P. Fischer and T. Brox, \"U-Net: Convolutional Networks for Biomedical Image "
    "Segmentation,\" MICCAI, 2015.",
    "X. Mao et al., \"Least Squares Generative Adversarial Networks,\" ICCV, 2017.",
    "T. Salimans et al., \"Improved Techniques for Training GANs,\" NeurIPS, 2016.",
    "J. Johnson, A. Alahi and L. Fei-Fei, \"Perceptual Losses for Real-Time Style Transfer and "
    "Super-Resolution,\" ECCV, 2016.",
    "S. Ioffe and C. Szegedy, \"Batch Normalization,\" ICML, 2015.",
    "N. Srivastava et al., \"Dropout: A Simple Way to Prevent Neural Networks from Overfitting,\" JMLR, 2014.",
    "D. P. Kingma and J. Ba, \"Adam: A Method for Stochastic Optimization,\" ICLR, 2015.",
    "P. Micikevicius et al., \"Mixed Precision Training,\" ICLR, 2018.",
    "H. Winnemöller, J. E. Kyprianidis and S. C. Olsen, \"XDoG: An eXtended Difference-of-Gaussians "
    "Compendium,\" Computers &amp; Graphics, 2012.",
    "J. Canny, \"A Computational Approach to Edge Detection,\" IEEE TPAMI, 1986.",
    "S. Xie and Z. Tu, \"Holistically-Nested Edge Detection,\" ICCV, 2015.",
    "Z. Wang et al., \"Image Quality Assessment: From Error Visibility to Structural Similarity,\" IEEE TIP, 2004.",
    "M. Heusel et al., \"GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium,\" "
    "NeurIPS, 2017.",
    "A. Yu and K. Grauman, \"Fine-Grained Visual Comparisons with Local Learning (UT-Zappos50K),\" CVPR, 2014.",
]
for i, r in enumerate(refs, 1):
    P(f"[{i}] {r}", "body")


def decorate(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont(BODY, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 12 * mm, "Sketch-to-Image Generator · DL concepts & algorithms")
        canvas.drawRightString(190 * mm, 12 * mm, f"{doc.page}")
        canvas.setStrokeColor(LINE)
        canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    else:
        canvas.setFillColor(ACCENT)
        canvas.rect(0, A4[1] - 12 * mm, A4[0], 12 * mm, fill=1, stroke=0)
    canvas.restoreState()


out = ROOT / "docs" / "DL_Concepts_Sketch2Image.pdf"
doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=22 * mm,
                        title="Sketch-to-Image Generator: DL Concepts & Algorithms", author="CA-2 Team")
doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
print("wrote", out)
