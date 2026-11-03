"""Classical edge / sketch extraction used to (a) build paired training data from
plain photos and (b) normalise hand-drawn sketches at inference time.

All functions return a uint8 grayscale image with BLACK strokes on a WHITE background,
which matches the edges2shoes / edges2handbags convention.
"""
import cv2
import numpy as np
from PIL import Image


def xdog(gray: np.ndarray, sigma=0.8, k=1.6, gamma=0.98, epsilon=-0.1, phi=200.0) -> np.ndarray:
    """eXtended Difference-of-Gaussians (Winnemoeller et al., 2012).

    DoG = G_sigma(I) - gamma * G_{k*sigma}(I) approximates the Laplacian-of-Gaussian
    (a band-pass edge detector); a soft tanh threshold turns it into pencil-like strokes.
    """
    img = gray.astype(np.float32) / 255.0
    g1 = cv2.GaussianBlur(img, (0, 0), sigma)
    g2 = cv2.GaussianBlur(img, (0, 0), sigma * k)
    dog = g1 - gamma * g2
    out = np.where(dog >= epsilon, 1.0, 1.0 + np.tanh(phi * (dog - epsilon)))
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def canny(gray: np.ndarray, low=60, high=150) -> np.ndarray:
    """Canny edge detector (gradient magnitude + non-max suppression + hysteresis)."""
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 1.2), low, high)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8))
    return 255 - edges


def photo_to_sketch(img: Image.Image, method="xdog") -> Image.Image:
    gray = np.array(img.convert("L"))
    out = xdog(gray) if method == "xdog" else canny(gray)
    return Image.fromarray(out, mode="L")


def clean_user_sketch(img: Image.Image, size: int) -> Image.Image:
    """Preprocess a hand-drawn / uploaded sketch for the generator.

    - flatten transparency onto white
    - convert to grayscale and auto-invert if strokes are light on dark
    - crop to the drawing's bounding box, pad to a square with a margin, resize
    - binarise so line intensity matches the training edge maps
    """
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    gray = np.array(img.convert("L"))
    if gray.mean() < 127:
        gray = 255 - gray

    ys, xs = np.where(gray < 200)
    if len(xs) > 0:
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        side = int(max(x1 - x0, y1 - y0) * 1.15) + 1
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        canvas = np.full((side, side), 255, np.uint8)
        sx0, sy0 = max(cx - side // 2, 0), max(cy - side // 2, 0)
        crop = gray[sy0 : sy0 + side, sx0 : sx0 + side]
        oy, ox = (side - crop.shape[0]) // 2, (side - crop.shape[1]) // 2
        canvas[oy : oy + crop.shape[0], ox : ox + crop.shape[1]] = crop
        gray = canvas

    gray = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    gray = np.where(gray < 180, 0, 255).astype(np.uint8)
    return Image.fromarray(gray, mode="L")
