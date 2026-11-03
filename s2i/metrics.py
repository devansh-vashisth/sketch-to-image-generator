"""Evaluation metrics: L1, PSNR, SSIM (per image) and FID (distribution level)."""
import numpy as np
import torch
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def _to_np(t: torch.Tensor) -> np.ndarray:
    """(C, H, W) tensor in [-1, 1] -> (H, W, C) float array in [0, 1]."""
    return ((t.detach().float().cpu().clamp(-1, 1) + 1) / 2).permute(1, 2, 0).numpy()


def image_metrics(fake: torch.Tensor, real: torch.Tensor) -> dict:
    f, r = _to_np(fake), _to_np(real)
    return {
        "l1": float(np.abs(f - r).mean()),
        "psnr": float(peak_signal_noise_ratio(r, f, data_range=1.0)),
        "ssim": float(structural_similarity(r, f, channel_axis=2, data_range=1.0)),
    }


class FIDCalculator:
    """Frechet Inception Distance (Heusel et al., 2017).

    FID = ||mu_r - mu_f||^2 + Tr(S_r + S_f - 2 (S_r S_f)^(1/2))
    computed on 2048-d pool features of an ImageNet Inception-v3. Lower is better.
    """

    def __init__(self, device):
        from torchvision.models import Inception_V3_Weights, inception_v3

        net = inception_v3(weights=Inception_V3_Weights.IMAGENET1K_V1, aux_logits=True)
        net.fc = torch.nn.Identity()
        self.net = net.eval().to(device)
        self.device = device
        self.mean = torch.tensor([0.485, 0.456, 0.406], device=device).view(1, 3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225], device=device).view(1, 3, 1, 1)
        self.real, self.fake = [], []

    @torch.no_grad()
    def _features(self, x):
        x = ((x.to(self.device).float() + 1) / 2 - self.mean) / self.std
        x = torch.nn.functional.interpolate(x, size=(299, 299), mode="bilinear", align_corners=False)
        return self.net(x).cpu().numpy()

    def update(self, fake, real):
        self.fake.append(self._features(fake))
        self.real.append(self._features(real))

    def compute(self) -> float:
        from scipy import linalg

        r, f = np.concatenate(self.real), np.concatenate(self.fake)
        mu_r, mu_f = r.mean(0), f.mean(0)
        s_r, s_f = np.cov(r, rowvar=False), np.cov(f, rowvar=False)
        covmean = linalg.sqrtm(s_r @ s_f)
        if isinstance(covmean, tuple):  # older SciPy may return (sqrtm, errest)
            covmean = covmean[0]
        covmean = np.nan_to_num(covmean).real
        return float(((mu_r - mu_f) ** 2).sum() + np.trace(s_r + s_f - 2 * covmean))
