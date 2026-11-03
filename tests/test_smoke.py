"""Quick shape / pipeline checks: python -m pytest tests  (or python tests/test_smoke.py)."""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s2i.models import PatchDiscriminator, UNetGenerator  # noqa: E402
from s2i.sketch import clean_user_sketch, photo_to_sketch  # noqa: E402


def test_shapes():
    for size in (64, 128, 256):
        G, D = UNetGenerator(1, 3, 32, size), PatchDiscriminator(4, 32)
        x = torch.randn(2, 1, size, size)
        y = G(x)
        assert y.shape == (2, 3, size, size) and y.abs().max() <= 1
        assert D(x, y).shape[1] == 1


def test_sketch_ops():
    img = Image.fromarray((np.random.rand(200, 300, 3) * 255).astype(np.uint8))
    assert photo_to_sketch(img).mode == "L"
    assert clean_user_sketch(img, 128).size == (128, 128)


if __name__ == "__main__":
    test_shapes()
    test_sketch_ops()
    print("all smoke tests passed")
