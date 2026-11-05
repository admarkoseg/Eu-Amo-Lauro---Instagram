"""Gera as pecas de Instagram de uma materia do Eu Amo Lauro.

Uso:  python3 scripts/render.py jobs/<post_id>.json
Saida: posts/<post_id>/  -> slide-1.jpg ... (carrossel 4:5), story.jpg (9:16), reel.mp4 (9:16, se kind=reel)
       posts/<post_id>/manifest.json com as URLs publicas (jsDelivr) de cada arquivo.

Campos do job (JSON):
  post_id, link, kind ("carousel" | "reel"), label (selo, ex. "OPORTUNIDADE"),
  title (use *asteriscos* para o trecho em verde), cover_file (ex. covers/7229.jpg),
  credit (ex. "Foto: Divulgacao/Neoenergia"),
  slides: [{"label": "...", "heading": "...", "bullets": ["...", ...]}]  (1 a 3 cards)
  cta (opcional), caption (legenda do post)
"""
import json, os, sys, subprocess, math, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
NAVY = (3, 43, 68); GREEN = (146, 211, 85); RED = (226, 46, 13); WHITE = (255, 255, 255)
SOFT = (200, 215, 225)
REPO_CDN = "https://cdn.jsdelivr.net/gh/admarkoseg/eu-amo-lauro---instagram@main/"


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, f"Poppins-{weight}.ttf"), size)


# ---------- texto ----------
def parse_marked(text):
    """'Curso *gratuito*: 27 vagas' -> [(palavra, destaque?)]; pontuação colada após o destaque
    (ex.: '*Buraquinho*:') fica grudada na palavra anterior, sem espaço."""
    out, hi, prev = [], False, " "
    for part in text.split("*"):
        cur_part = part
        if out and part[:1] and not part[:1].isspace() and prev[-1:] and not prev[-1:].isspace():
            first, _, rest = part.partition(" ")
            out.append((first, hi, True))  # True = colar na anterior
            part = rest
        for w in part.split():
            out.append((w, hi, False))
        prev = cur_part or prev
        hi = not hi
    # junta os pedaços colados mantendo a cor de cada um
    merged = []
    for w, h, glue in out:
        if glue and merged:
            merged[-1] = merged[-1] + [(w, h)]
        else:
            merged.append([(w, h)])
    return merged


def _txt(item):
    return "".join(p[0] for p in item) if isinstance(item, list) else item[0]


def wrap_words(words, fnt, max_w, draw):
    lines, cur = [], []
    for w in words:
        test = cur + [w]
        if draw.textlength(" ".join(_txt(x) for x in test), font=fnt) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur); cur = [w]
    if cur:
        lines.append(cur)
    return lines


def fit_title(draw, text, max_w, max_h, sizes=(84, 76, 70, 64, 58, 52, 48, 44)):
    words = parse_marked(text)
    for s in sizes:
        f = font("Bold", s)
        lines = wrap_words(words, f, max_w, draw)
        lh = int(s * 1.18)
        if lh * len(lines) <= max_h:
            return f, lines, lh
    return f, lines, lh


def draw_marked_lines(draw, lines, fnt, x, y, lh, color=WHITE, hi=GREEN):
    space = draw.textlength(" ", font=fnt)
    for line in lines:
        cx = x
        for item in line:
            for w, h in (item if isinstance(item, list) else [item]):
                draw.text((cx, y), w, font=fnt, fill=hi if h else color)
                cx += draw.textlength(w, font=fnt)
            cx += space
        y += lh
    return y


def wrap_plain(draw, text, fnt, max_w):
    return [" ".join(l[0] for l in line) if False else " ".join(w for w, _ in line)
            for line in wrap_words([(w, False) for w in text.split()], fnt, max_w, draw)]


# ---------- elementos de marca ----------
def load_logo(width):
    for name in ("brand/logo-branco.png", "brand/logo.png"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            lg = Image.open(p).convert("RGBA")
            r = width / lg.width
            return lg.resize((width, int(lg.height * r)), Image.LANCZOS)
    return None


def wordmark(img, x_right, y, size=34):
    """Logo do portal; sem arquivo de logo, escreve 'Eu ♥ Lauro' em texto."""
    d = ImageDraw.Draw(img)
    lg = load_logo(int(size * 4.4))
    if lg is None:
        sys.exit("ERRO: falta o logo oficial em brand/logo-branco.png (ou brand/logo.png). "
                 "Regra do dono: nunca recriar o logo do Eu Amo Lauro. Nao publique.")
    if lg:
        img.alpha_composite(lg, (x_right - lg.width, y)) if img.mode == "RGBA" else img.paste(lg, (x_right - lg.width, y), lg)
        return
    f1, f2 = font("ExtraBold", size), font("Bold", size)
    parts = [("Eu ", WHITE, f1), ("♥ ", RED, font("Bold", size)), ("Lauro", GREEN, f2)]
    try:
        heart = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        parts[1] = ("♥ ", RED, heart)
    except Exception:
        parts[1] = ("+ ", RED, f1)
    total = sum(d.textlength(t, font=f) for t, _, f in parts)
    cx = x_right - total
    for t, c, f in parts:
        d.text((cx + 2, y + 2), t, font=f, fill=(0, 0, 0, 120))
        d.text((cx, y), t, font=f, fill=c)
        cx += d.textlength(t, font=f)


def pill(draw, x, y, text, size=30, bg=GREEN, fg=NAVY):
    f = font("Bold", size)
    w = draw.textlength(text, font=f)
    h = int(size * 1.75)
    draw.rounded_rectangle((x, y, x + w + size * 1.4, y + h), radius=h // 2, fill=bg)
    draw.text((x + size * 0.7, y + h / 2), text, font=f, fill=fg, anchor="lm")
    return h


def footer(img, H, W, height=92):
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - height, W, H), fill=RED)
    f = font("SemiBold", 30)
    d.text((60, H - height / 2), "euamolauro.com.br", font=f, fill=WHITE, anchor="lm")
    d.text((W - 60, H - height / 2), "@euamolauro", font=f, fill=WHITE, anchor="rm")


def side_stripe(img, H, x=0, w=16):
    ImageDraw.Draw(img).rectangle((x, 0, x + w, H), fill=GREEN)


def cover_crop(photo, w, h, zoom=1.0, pan=0.5):
    """Recorta a foto para preencher w x h (estilo object-fit: cover)."""
    r = max(w / photo.width, h / photo.height) * zoom
    pw, ph = int(photo.width * r) + 1, int(photo.height * r) + 1
    p = photo.resize((pw, ph), Image.LANCZOS)
    left = int((pw - w) * pan); top = int((ph - h) / 2)
    return p.crop((left, top, left + w, top + h))


def fade_bottom(img, y0, y1, color=NAVY):
    """Degrade da foto para o azul-marinho."""
    W = img.width
    grad = Image.new("L", (1, y1 - y0))
    for i in range(y1 - y0):
        grad.putpixel((0, i), int(255 * (i / (y1 - y0)) ** 1.6))
    grad = grad.resize((W, y1 - y0))
    solid = Image.new("RGB", (W, y1 - y0), color)
    region = img.crop((0, y0, W, y1))
    img.paste(Image.composite(solid, region, grad), (0, y0))


# ---------- pecas ----------
def cover_slide(job, photo, W=1080, H=1350, photo_h=None, title_box=None, zoom=1.0, pan=0.5, story=False):
    img = Image.new("RGB", (W, H), NAVY)
    pan = job.get("pan", pan)
    photo_h = photo_h or int(H * 0.56)
    img.paste(cover_crop(photo, W, photo_h, zoom, pan), (0, 0))
    fade_bottom(img, int(photo_h * 0.55), photo_h)
    img = img.convert("RGBA")
    # vinheta no topo para o logo aparecer
    VH = 480 if story else 290
    top = Image.new("RGBA", (W, VH), (0, 0, 0, 0)); td = ImageDraw.Draw(top)
    for i in range(VH):
        td.line((0, i, W, i), fill=(3, 43, 68, int(215 * (1 - i / VH) ** 1.1)))
    img.alpha_composite(top, (0, 0))
    wordmark(img, W - 60, 56 if not story else 120, size=40 if not story else 46)
    img = img.convert("RGB")
    side_stripe(img, H)
    d = ImageDraw.Draw(img)
    x = 70
    y = photo_h - 40
    y += pill(d, x, y, job["label"].upper(), size=30) + 34
    footer_h = 92 if not story else 0
    bottom_limit = H - footer_h - (70 if not story else 330)
    sizes = (96, 90, 84, 78, 72, 66, 60, 54) if story else (84, 76, 70, 64, 58, 52, 48, 44)
    f, lines, lh = fit_title(d, job["title"], W - x - 70, bottom_limit - y, sizes)
    y = draw_marked_lines(d, lines, f, x, y, lh)
    if job.get("credit"):
        cf = font("Medium", 22)
        d.text((W - 30, photo_h - 70), job["credit"], font=cf, fill=(235, 240, 245), anchor="rs")
    if story:
        cta(d, W, H, "Matéria completa no link da bio", y0=H - 290)
    else:
        footer(img, H, W)
        d.text((W - 60, H - 92 - 40), "arraste para o lado  ›", font=font("Medium", 28), fill=SOFT, anchor="rm")
    return img


def cta(d, W, H, text, y0):
    f = font("Bold", 40)
    w = d.textlength(text, font=f)
    bx0 = (W - w) / 2 - 40
    d.rounded_rectangle((bx0, y0, bx0 + w + 80, y0 + 96), radius=48, fill=GREEN)
    d.text((W / 2, y0 + 48), text, font=f, fill=NAVY, anchor="mm")
    d.text((W / 2, y0 + 150), "euamolauro.com.br  ·  @euamolauro", font=font("SemiBold", 30), fill=WHITE, anchor="mm")


def info_slide(job, s, idx, total, W=1080, H=1350, footer_on=True, top=150):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    # detalhe grafico: circulo verde translucido no canto
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(deco)
    dd.ellipse((W - 330, -260, W + 230, 300), fill=(146, 211, 85, 38))
    img = Image.alpha_composite(img.convert("RGBA"), deco)
    wordmark(img, W - 60, 56)
    img = img.convert("RGB"); d = ImageDraw.Draw(img)
    side_stripe(img, H)
    x = 80
    if total:
        d.text((x, 70), f"{idx}/{total}", font=font("SemiBold", 28), fill=SOFT)
    bullets = s.get("bullets", [])
    bottom = H - (92 if footer_on else 160) - 70
    area_top = top
    for hs, size in ((72, 50), (68, 46), (64, 42), (60, 38), (56, 34), (52, 30)):
        hf = font("Bold", hs); hl = wrap_plain(d, s["heading"], hf, W - x - 80)
        bf = font("Medium", size); lh = int(size * 1.4)
        block = 50 + 40 + len(hl) * int(hs * 1.22) + 36 + 50 + sum(len(wrap_plain(d, b, bf, W - x - 130)) * lh + 32 for b in bullets)
        if area_top + block <= bottom:
            break
    y = area_top + max(0, (bottom - area_top - block) // 2)
    y += pill(d, x, y, s.get("label", job["label"]).upper(), size=28) + 40
    for line in hl:
        d.text((x, y), line, font=hf, fill=WHITE); y += int(hs * 1.22)
    y += 36
    d.line((x, y, x + 120, y), fill=GREEN, width=6); y += 50
    for b in bullets:
        lines = wrap_plain(d, b, bf, W - x - 130)
        d.ellipse((x, y + lh / 2 - 9, x + 18, y + lh / 2 + 9), fill=GREEN)
        for ln in lines:
            d.text((x + 44, y), ln, font=bf, fill=WHITE); y += lh
        y += 32
    if footer_on:
        footer(img, H, W)
    return img


def final_slide(job, W=1080, H=1350):
    img = Image.new("RGB", (W, H), NAVY)
    deco = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(deco)
    dd.ellipse((-260, H - 520, 360, H + 100), fill=(146, 211, 85, 34))
    dd.ellipse((W - 300, -200, W + 200, 300), fill=(226, 46, 13, 40))
    img = Image.alpha_composite(img.convert("RGBA"), deco)
    wordmark(img, W - 60, 56, 40)
    img = img.convert("RGB"); side_stripe(img, H)
    d = ImageDraw.Draw(img)
    f = font("Bold", 72)
    y = 380
    for line in ["Matéria completa", "no *link da bio*"]:
        y = draw_marked_lines(d, [parse_marked(line)], f, 80, y, 92)
    y += 40
    msg = job.get("cta") or "Salve este post e compartilhe com quem precisa saber."
    for ln in wrap_plain(d, msg, font("Medium", 40), W - 160):
        d.text((80, y), ln, font=font("Medium", 40), fill=SOFT); y += 58
    y += 60
    for t in ("Salve", "Compartilhe", "Marque um amigo de Lauro"):
        d.ellipse((80, y + 18, 100, y + 38), fill=GREEN)
        d.text((122, y), t, font=font("SemiBold", 40), fill=WHITE); y += 70
    footer(img, H, W)
    return img


def save_jpg(img, path, max_kb=900):
    q = 90
    while True:
        img.convert("RGB").save(path, "JPEG", quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) <= max_kb * 1024 or q <= 60:
            return
        q -= 5


# ---------- reel ----------
def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, t)))


def render_reel(job, photo, outdir, fps=30):
    W, H = 1080, 1920
    frames_dir = os.path.join(outdir, "_frames"); os.makedirs(frames_dir, exist_ok=True)
    slides = job.get("slides", [])[:3]
    # cenas: capa (5s), cards (4s cada), final (3.5s)
    scenes = [("cover", 5.0)] + [("info", 4.0)] * len(slides) + [("final", 3.5)]
    statics = {}
    for i, s in enumerate(slides):
        statics[i] = info_slide(job, s, 0, 0, W, H, footer_on=False, top=330)
    fin = final_slide(job, W, H)
    # final em 9:16: reaproveita o layout centralizado
    n = 0
    cover_frames = int(5.0 * fps)
    for k in range(cover_frames):
        t = k / cover_frames
        img = cover_slide(job, photo, W, H, photo_h=1100, zoom=1.0 + 0.10 * t, pan=0.5, story=True)
        # entrada do titulo: fade a partir do azul nos primeiros 0,6s
        a = ease(k / (0.6 * fps))
        if a < 1:
            base = cover_slide(job, photo, W, H, photo_h=1100, zoom=1.0 + 0.10 * t, story=True) if False else None
        img.save(os.path.join(frames_dir, f"{n:05d}.jpg"), quality=88); n += 1
    blocks = [statics[i] for i in range(len(slides))] + [fin]
    for bi, im in enumerate(blocks):
        dur = 4.0 if bi < len(slides) else 3.5
        nf = int(dur * fps)
        prev = Image.open(os.path.join(frames_dir, f"{n-1:05d}.jpg"))
        for k in range(nf):
            a = ease(k / (0.45 * fps))
            if a < 1:
                # desliza de baixo para cima com fade
                off = int((1 - a) * 160)
                canvas = Image.new("RGB", (W, H), NAVY); canvas.paste(im, (0, off))
                fr = Image.blend(prev, canvas, a)
            else:
                fr = im
            fr.save(os.path.join(frames_dir, f"{n:05d}.jpg"), quality=88); n += 1
    out = os.path.join(outdir, "reel.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(frames_dir, "%05d.jpg"),
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                    "-profile:v", "high", "-r", str(fps), "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(frames_dir)
    return out


def main(job_path):
    job = json.load(open(job_path, encoding="utf-8"))
    pid = str(job["post_id"])
    outdir = os.path.join(ROOT, "posts", pid)
    os.makedirs(outdir, exist_ok=True)
    photo = Image.open(os.path.join(ROOT, job["cover_file"])).convert("RGB")
    files = []
    slides = job.get("slides", [])[:3]
    total = len(slides) + 2
    if job.get("kind", "carousel") == "carousel":
        save_jpg(cover_slide(job, photo), p := os.path.join(outdir, "slide-1.jpg")); files.append(p)
        for i, s in enumerate(slides):
            save_jpg(info_slide(job, s, i + 2, total), p := os.path.join(outdir, f"slide-{i+2}.jpg")); files.append(p)
        save_jpg(final_slide(job), p := os.path.join(outdir, f"slide-{total}.jpg")); files.append(p)
    else:
        files.append(render_reel(job, photo, outdir))
        save_jpg(cover_slide(job, photo, 1080, 1920, photo_h=1100, story=True), p := os.path.join(outdir, "reel-capa.jpg")); files.append(p)
    save_jpg(cover_slide(job, photo, 1080, 1920, photo_h=1100, story=True), p := os.path.join(outdir, "story.jpg")); files.append(p)
    manifest = {"post_id": job["post_id"], "kind": job.get("kind", "carousel"), "caption": job.get("caption", ""),
                "files": {os.path.basename(f): REPO_CDN + os.path.relpath(f, ROOT) for f in files}}
    json.dump(manifest, open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(manifest, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
