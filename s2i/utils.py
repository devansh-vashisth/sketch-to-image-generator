import random

import numpy as np
import torch
from torchvision.utils import save_image


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def save_grid(sketch, fake, real, path, nrow_max=8):
    """Save rows of [sketch | generated | ground truth] for qualitative inspection."""
    n = min(sketch.size(0), nrow_max)
    sk = sketch[:n].repeat(1, 3, 1, 1)
    rows = torch.stack([sk, fake[:n], real[:n]], dim=1).flatten(0, 1)
    save_image((rows.float().cpu() + 1) / 2, path, nrow=3, padding=2, pad_value=1.0)
