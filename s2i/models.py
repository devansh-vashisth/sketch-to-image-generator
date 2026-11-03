"""Network architectures.

Generator     : U-Net encoder-decoder with skip connections (Ronneberger et al., 2015),
                as used in Pix2Pix (Isola et al., 2017).
Discriminator : 70x70 PatchGAN that classifies overlapping N x N patches as real/fake.
"""
import math

import torch
import torch.nn as nn


def norm_layer(kind: str, channels: int) -> nn.Module:
    if kind == "batch":
        return nn.BatchNorm2d(channels)
    if kind == "instance":
        return nn.InstanceNorm2d(channels, affine=True)
    raise ValueError(f"unknown norm: {kind}")


class Down(nn.Module):
    """Encoder block: Conv(4x4, stride 2) -> [Norm] -> LeakyReLU(0.2). Halves H and W."""

    def __init__(self, in_ch, out_ch, use_norm=True, norm="batch"):
        super().__init__()
        layers = [nn.Conv2d(in_ch, out_ch, 4, 2, 1, bias=not use_norm)]
        if use_norm:
            layers.append(norm_layer(norm, out_ch))
        layers.append(nn.LeakyReLU(0.2, inplace=True))
        self.block = nn.Sequential(*layers)

    def forward(self, x):
        return self.block(x)


class Up(nn.Module):
    """Decoder block: ConvTranspose(4x4, stride 2) -> Norm -> [Dropout 0.5] -> ReLU. Doubles H and W."""

    def __init__(self, in_ch, out_ch, dropout=False, norm="batch"):
        super().__init__()
        layers = [nn.ConvTranspose2d(in_ch, out_ch, 4, 2, 1, bias=False), norm_layer(norm, out_ch)]
        if dropout:
            # Pix2Pix uses dropout (also at test time in the paper) as the source of noise z.
            layers.append(nn.Dropout(0.5))
        layers.append(nn.ReLU(inplace=True))
        self.block = nn.Sequential(*layers)

    def forward(self, x):
        return self.block(x)


class UNetGenerator(nn.Module):
    """U-Net generator G(x): sketch (1 x H x W) -> RGB image (3 x H x W) in [-1, 1].

    For a 256x256 input there are 8 down-sampling steps (256 -> 1), giving the
    classic encoder C64-C128-C256-C512-C512-C512-C512-C512 and the mirrored decoder.
    Each decoder output is concatenated with the encoder feature map of the same
    resolution (skip connection), so low-level detail such as edge positions
    can bypass the bottleneck.
    """

    def __init__(self, in_ch=1, out_ch=3, ngf=64, image_size=256, norm="batch"):
        super().__init__()
        num_downs = int(math.log2(image_size))
        if 2 ** num_downs != image_size:
            raise ValueError("image_size must be a power of two")
        enc_ch = [min(ngf * 2 ** i, ngf * 8) for i in range(num_downs)]

        self.downs = nn.ModuleList()
        prev = in_ch
        for i, c in enumerate(enc_ch):
            # No norm on the first layer or on the 1x1 bottleneck.
            self.downs.append(Down(prev, c, use_norm=0 < i < num_downs - 1, norm=norm))
            prev = c

        self.ups = nn.ModuleList()
        for j, i in enumerate(reversed(range(num_downs - 1))):
            in_c = enc_ch[i + 1] if j == 0 else enc_ch[i + 1] * 2
            self.ups.append(Up(in_c, enc_ch[i], dropout=j < 3, norm=norm))

        self.final = nn.Sequential(nn.ConvTranspose2d(enc_ch[0] * 2, out_ch, 4, 2, 1), nn.Tanh())

    def forward(self, x):
        skips = []
        for down in self.downs:
            x = down(x)
            skips.append(x)
        x = skips.pop()  # bottleneck
        for up in self.ups:
            x = up(x)
            x = torch.cat([x, skips.pop()], dim=1)
        return self.final(x)


class PatchDiscriminator(nn.Module):
    """PatchGAN discriminator D(x, y).

    Takes the sketch and a real/generated image concatenated along channels and
    outputs a grid of logits (30x30 for 256x256 input). Each logit judges one
    70x70 receptive-field patch, which pushes G toward sharp, high-frequency detail.
    """

    def __init__(self, in_ch=4, ndf=64, n_layers=3, norm="batch"):
        super().__init__()
        layers = [nn.Conv2d(in_ch, ndf, 4, 2, 1), nn.LeakyReLU(0.2, inplace=True)]
        mult = 1
        for n in range(1, n_layers + 1):
            prev, mult = mult, min(2 ** n, 8)
            stride = 2 if n < n_layers else 1
            layers += [
                nn.Conv2d(ndf * prev, ndf * mult, 4, stride, 1, bias=False),
                norm_layer(norm, ndf * mult),
                nn.LeakyReLU(0.2, inplace=True),
            ]
        layers.append(nn.Conv2d(ndf * mult, 1, 4, 1, 1))  # raw logits; loss applies sigmoid
        self.model = nn.Sequential(*layers)

    def forward(self, sketch, image):
        return self.model(torch.cat([sketch, image], dim=1))


def init_weights(module: nn.Module, gain: float = 0.02) -> None:
    """DCGAN/Pix2Pix initialisation: conv weights ~ N(0, 0.02), norm weights ~ N(1, 0.02)."""
    for m in module.modules():
        if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
            nn.init.normal_(m.weight, 0.0, gain)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, (nn.BatchNorm2d, nn.InstanceNorm2d)) and m.weight is not None:
            nn.init.normal_(m.weight, 1.0, gain)
            nn.init.zeros_(m.bias)


def count_params(module: nn.Module) -> int:
    return sum(p.numel() for p in module.parameters() if p.requires_grad)
