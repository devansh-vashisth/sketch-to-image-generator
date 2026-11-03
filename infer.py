"""Generate an image from one sketch (or a folder of sketches).

    python infer.py --checkpoint runs/pix2pix/checkpoints/best.pt --input my_sketch.png --output out.png
"""
import argparse
from pathlib import Path

from PIL import Image

from s2i.dataset import list_images
from s2i.inference import SketchToImage


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--input", required=True, help="sketch image or folder")
    p.add_argument("--output", required=True, help="output image or folder")
    p.add_argument("--no-clean", action="store_true", help="skip crop/binarise preprocessing")
    args = p.parse_args()

    model = SketchToImage(args.checkpoint)
    src, dst = Path(args.input), Path(args.output)
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for f in list_images(src):
            model(Image.open(f), clean=not args.no_clean).save(dst / f"{f.stem}_gen.png")
            print("wrote", dst / f"{f.stem}_gen.png")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        model(Image.open(src), clean=not args.no_clean).save(dst)
        print("wrote", dst)


if __name__ == "__main__":
    main()
