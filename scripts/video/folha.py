"""Junta os previews (PNG 1080x1920) numa folha só, para revisar de uma vez. Uso: python folha.py saida.png a.png b.png ..."""
import sys
from PIL import Image, ImageDraw
saida, fotos = sys.argv[1], sys.argv[2:]
W, H, col = 360, 640, 3
lin = (len(fotos) + col - 1) // col
folha = Image.new("RGB", (W * col + 10 * (col + 1), (H + 40) * lin + 10), "#ffffff")
d = ImageDraw.Draw(folha)
for i, f in enumerate(fotos):
    x, y = 10 + (i % col) * (W + 10), 10 + (i // col) * (H + 40)
    folha.paste(Image.open(f).convert("RGB").resize((W, H)), (x, y + 30))
    d.text((x, y + 8), f.rsplit("preview-", 1)[-1], fill="#000")
folha.save(saida)
