"""Load a trained generator and turn sketches into images."""
from pathlib import Path

import torch
from PIL import Image

from .dataset import to_image, to_tensor
from .models import UNetGenerator
from .sketch import clean_user_sketch


class SketchToImage:
    def __init__(self, checkpoint, device=None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        ckpt = torch.load(Path(checkpoint), map_location=self.device, weights_only=False)
        cfg = ckpt["config"]
        self.image_size = cfg["image_size"]
        self.G = UNetGenerator(1, 3, cfg["ngf"], cfg["image_size"], cfg["norm"]).to(self.device)
        self.G.load_state_dict(ckpt["G"])
        self.G.eval()
        self.epoch = ckpt.get("epoch")

    @torch.no_grad()
    def __call__(self, sketch: Image.Image, clean=True) -> Image.Image:
        if clean:
            sketch = clean_user_sketch(sketch, self.image_size)
        else:
            sketch = sketch.convert("L").resize((self.image_size, self.image_size))
        x = to_tensor(sketch).unsqueeze(0).to(self.device)
        return to_image(self.G(x)[0])
