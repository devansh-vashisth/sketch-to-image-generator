"""Paired (sketch, photo) dataset.

Two on-disk layouts are supported:

aligned : each file is one image of width 2W with the sketch on the left and the
          photo on the right (the official pix2pix edges2shoes / edges2handbags format).
photos  : a folder of plain photos; the sketch is extracted on the fly with XDoG/Canny.
          This lets you train on any domain (faces, cars, anime, ...).
"""
import random
from pathlib import Path

import torch
import torchvision.transforms.functional as TF
from PIL import Image
from torch.utils.data import Dataset

from .sketch import photo_to_sketch

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_images(root):
    return sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in IMG_EXT)


def to_tensor(img: Image.Image) -> torch.Tensor:
    """PIL -> float tensor scaled to [-1, 1] (matches the generator's tanh output range)."""
    return TF.to_tensor(img) * 2.0 - 1.0


def to_image(t: torch.Tensor) -> Image.Image:
    """Tensor in [-1, 1] with shape (C, H, W) -> PIL image."""
    t = ((t.detach().float().cpu().clamp(-1, 1) + 1) / 2)
    return TF.to_pil_image(t)


class PairedSketchDataset(Dataset):
    def __init__(self, root, layout="aligned", image_size=256, train=True,
                 max_samples=None, sketch_method="xdog", seed=0):
        self.files = list_images(root)
        if not self.files:
            raise FileNotFoundError(f"no images found in {root}")
        if max_samples and len(self.files) > max_samples:
            self.files = random.Random(seed).sample(self.files, max_samples)
        self.layout, self.size, self.train = layout, image_size, train
        self.sketch_method = sketch_method

    def __len__(self):
        return len(self.files)

    def _load_pair(self, path):
        img = Image.open(path).convert("RGB")
        if self.layout == "aligned":
            w, h = img.size
            sketch, photo = img.crop((0, 0, w // 2, h)), img.crop((w // 2, 0, w, h))
        else:
            photo = img
            sketch = photo_to_sketch(photo, self.sketch_method)
        return sketch.convert("L"), photo

    def __getitem__(self, idx):
        sketch, photo = self._load_pair(self.files[idx])
        if self.train:
            # "Random jitter" from the Pix2Pix paper: upscale to ~1.12x, random crop back,
            # random horizontal flip. The SAME transform is applied to both images so they stay aligned.
            load = int(self.size * 1.12)
            sketch = TF.resize(sketch, [load, load], antialias=True)
            photo = TF.resize(photo, [load, load], antialias=True)
            i, j = random.randint(0, load - self.size), random.randint(0, load - self.size)
            sketch = TF.crop(sketch, i, j, self.size, self.size)
            photo = TF.crop(photo, i, j, self.size, self.size)
            if random.random() < 0.5:
                sketch, photo = TF.hflip(sketch), TF.hflip(photo)
        else:
            sketch = TF.resize(sketch, [self.size, self.size], antialias=True)
            photo = TF.resize(photo, [self.size, self.size], antialias=True)
        return to_tensor(sketch), to_tensor(photo)
