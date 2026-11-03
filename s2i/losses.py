"""Loss functions for the conditional GAN objective.

    G* = arg min_G max_D  L_cGAN(G, D) + lambda_L1 * L_L1(G) [+ lambda_vgg * L_perc(G)]
"""
import torch
import torch.nn as nn


class GANLoss(nn.Module):
    """Adversarial loss against a target label of all-ones (real) or all-zeros (fake).

    vanilla : binary cross-entropy on logits (original GAN / Pix2Pix)
    lsgan   : least-squares loss (Mao et al., 2017), often more stable
    """

    def __init__(self, mode="vanilla", real_label=1.0, fake_label=0.0):
        super().__init__()
        self.real_label, self.fake_label = real_label, fake_label
        if mode == "vanilla":
            self.loss = nn.BCEWithLogitsLoss()
        elif mode == "lsgan":
            self.loss = nn.MSELoss()
        else:
            raise ValueError(f"unknown gan mode: {mode}")

    def forward(self, pred, is_real: bool):
        target = torch.full_like(pred, self.real_label if is_real else self.fake_label)
        return self.loss(pred, target)


class VGGPerceptualLoss(nn.Module):
    """Perceptual (feature-matching) loss on frozen ImageNet VGG-16 features (Johnson et al., 2016).

    Optional: enable with --lambda-vgg > 0. Downloads VGG-16 weights on first use.
    """

    def __init__(self, layers=(3, 8, 15, 22)):
        super().__init__()
        from torchvision.models import VGG16_Weights, vgg16

        features = vgg16(weights=VGG16_Weights.IMAGENET1K_V1).features[: max(layers) + 1].eval()
        for p in features.parameters():
            p.requires_grad_(False)
        self.features, self.layers = features, set(layers)
        self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, fake, real):
        # inputs are in [-1, 1]; convert to ImageNet normalisation
        x = ((fake + 1) / 2 - self.mean) / self.std
        y = ((real + 1) / 2 - self.mean) / self.std
        loss = 0.0
        for i, layer in enumerate(self.features):
            x, y = layer(x), layer(y)
            if i in self.layers:
                loss = loss + nn.functional.l1_loss(x, y)
        return loss
