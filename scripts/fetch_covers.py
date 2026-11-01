"""Baixa a imagem de capa de cada job (jobs/<post_id>.json -> covers/<post_id>.<ext>).
Roda no GitHub Actions, que tem acesso ao site. So aceita URLs de dominios confiaveis."""
import json, os, glob, urllib.request, urllib.parse

# Fontes oficiais e bancos livres (protocolo de imagens do portal). Nunca jornais/portais de noticia.
ALLOWED = ("euamolauro.com.br", "laurodefreitas.ba.gov.br", "ba.gov.br", "gov.br", "neoenergia.com",
           "embasa.ba.gov.br", "sebrae.com.br", "sesc-ba.com.br", "senai.ba", "ifba.edu.br",
           "parqueshoppingbahia.com.br", "salvadordabahia.com", "upload.wikimedia.org",
           "images.unsplash.com", "images.pexels.com")
os.makedirs("covers", exist_ok=True)
for path in sorted(glob.glob("jobs/*.json")):
    job = json.load(open(path, encoding="utf-8"))
    pid = str(job["post_id"])
    urls = [job.get("cover_url")] + list(job.get("extra_image_urls", []))
    for n, url in enumerate(u for u in urls if u):
        host = urllib.parse.urlparse(url).hostname or ""
        if not any(host == d or host.endswith("." + d) for d in ALLOWED):
            print(f"[{pid}] dominio nao permitido: {url}"); continue
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
        dest = f"covers/{pid}{'' if n == 0 else '-' + str(n)}{ext}"
        if os.path.exists(dest):
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 euamolauro-bot"})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        print(f"[{pid}] ok -> {dest}")
