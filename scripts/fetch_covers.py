"""Baixa fotos candidatas de cada job (roda no GitHub Actions, que tem acesso aos sites).

jobs/<post_id>.json pode ter:
  cover_url          -> imagem direta (salva como covers/<id>/cand-0.<ext>)
  extra_image_urls   -> outras imagens diretas
  photo_pages        -> paginas oficiais (noticia-fonte etc.): extrai og:image e as fotos do corpo
Saida: covers/<post_id>/cand-N.<ext> + covers/<post_id>/sources.json (origem de cada arquivo).
So aceita dominios oficiais/bancos livres (protocolo de imagens do portal). Nunca jornais/portais de noticia.
"""
import json, os, glob, re, html, urllib.request, urllib.parse

ALLOWED = ("euamolauro.com.br", "laurodefreitas.ba.gov.br", "ba.gov.br", "gov.br", "neoenergia.com",
           "sebrae.com.br", "sesc-ba.com.br", "ifba.edu.br", "parqueshoppingbahia.com.br",
           "salvadordabahia.com", "fieb.org.br", "senaibahia.com.br", "wikimedia.org", "unsplash.com", "pexels.com")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
SKIP = re.compile(r"logo|icon|banner|sprite|avatar|whatsapp|facebook|instagram|twitter|youtube|selo|badge|\.svg|\.gif", re.I)


def allowed(url):
    host = urllib.parse.urlparse(url).hostname or ""
    return any(host == d or host.endswith("." + d) for d in ALLOWED)


def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def images_from_page(url):
    raw, _ = get(url)
    text = raw.decode("utf-8", "ignore")
    found = []
    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]*content=["\']([^"\']+)', text, re.I):
        found.append(m.group(1))
    for m in re.finditer(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)', text, re.I):
        found.append(m.group(1))
    out = []
    for u in found:
        u = urllib.parse.urljoin(url, html.unescape(u))
        if u.startswith("http") and not SKIP.search(u) and u not in out:
            out.append(u)
    return out[:8]


for path in sorted(glob.glob("jobs/*.json")):
    job = json.load(open(path, encoding="utf-8"))
    pid = str(job["post_id"])
    d = f"covers/{pid}"
    src_file = f"{d}/sources.json"
    if os.path.exists(src_file):
        continue  # ja baixado; apague a pasta para baixar de novo
    os.makedirs(d, exist_ok=True)
    urls = [u for u in [job.get("cover_url")] + list(job.get("extra_image_urls", [])) if u]
    for page in job.get("photo_pages", []):
        if not allowed(page):
            print(f"[{pid}] pagina fora da lista: {page}"); continue
        try:
            urls += images_from_page(page)
        except Exception as e:
            print(f"[{pid}] erro lendo {page}: {e}")
    sources, n = {}, 0
    for url in urls:
        if not allowed(url):
            print(f"[{pid}] dominio nao permitido: {url}"); continue
        try:
            data, ctype = get(url)
        except Exception as e:
            print(f"[{pid}] erro {url}: {e}"); continue
        if len(data) < 15000:
            continue  # icone/miniatura
        ext = {"image/png": ".png", "image/webp": ".webp", "image/jpeg": ".jpg"}.get(ctype.split(";")[0].strip(),
              os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg")
        name = f"cand-{n}{ext}"
        open(f"{d}/{name}", "wb").write(data)
        sources[name] = url; n += 1
        print(f"[{pid}] ok {name} <- {url}")
    json.dump(sources, open(src_file, "w"), indent=1)
