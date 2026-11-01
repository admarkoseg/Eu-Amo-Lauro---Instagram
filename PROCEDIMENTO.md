# Instagram @euamolauro – versão social de cada matéria

> **REGRA Nº 1 – SÓ PUBLIQUE PEÇAS GERADAS PELO `scripts/render.py` DESTE REPOSITÓRIO.**
> É ele que aplica o logo oficial do Eu Amo Lauro. É PROIBIDO postar no Instagram a capa do site,
> a foto crua, arte feita de outro jeito ou qualquer imagem sem passar pelo render.py.
> Se algo impedir (repositório, Actions, render.py, foto), NÃO publique no Instagram: publique só a
> matéria do site e avise o Rodrigo do que falhou. Sem exceção.


Toda matéria publicada em euamolauro.com.br ganha, no mesmo dia, uma versão no Instagram **@euamolauro**:
**feed (carrossel) ou Reels + 1 Story**. O dono autorizou publicação direta.

## Ferramentas
- **WordPress**: conector "Eu Amo Lauro - WP" (wp_list_posts, wp_get_post, wp_get_media).
- **Instagram**: Windsor.ai, conector `instagram`, conta **17841453870915611** (Eu Amo Lauro de Freitas).
  Ações: `create_carousel_post`, `create_video_post` (Reels), `create_story`.
- **Repositório de mídia** (público): `admarkoseg/eu-amo-lauro---instagram`.
  Numa sessão nova: `add_repo` (owner admarkoseg, repo eu-amo-lauro---instagram, access push) e
  `git clone --depth 1 https://github.com/admarkoseg/eu-amo-lauro---instagram`.
- O Instagram busca os arquivos pela CDN, **sempre fixada no commit**:
  `https://cdn.jsdelivr.net/gh/admarkoseg/eu-amo-lauro---instagram@<SHA>/posts/<id>/<arquivo>`.

## Logo (regra do dono)
- Use SOMENTE os arquivos oficiais em `brand/` (vindos da pasta do dono "LOGO EU AMO LAURO"):
  `logo-branco.png` (usado nas artes, sobre azul-marinho ou foto), `logo-colorido.png` (fundo claro),
  `logo-preto.png`, `logo-final.png`. Nunca redesenhe, recrie em texto ou altere cores/proporções.
- O `render.py` para com erro se o logo não estiver no repositório: nesse caso NÃO publique e avise o dono.

## Passo a passo
1. **O que publicar**: matéria nova desta execução + qualquer post dos últimos 3 dias que não esteja em
   `published.json` (nem em `_ignorados`). Não publique evento que já passou nem prazo encerrado.
2. **Fotos reais, sempre ligadas a Lauro** (regra do dono):
   - A sessão não acessa sites externos pelo terminal. Quem baixa é o GitHub Actions
     (`.github/workflows/fetch-covers.yml`), disparado ao subir `jobs/<id>.json`.
   - Em `photo_pages`, ponha as páginas oficiais da notícia-fonte da matéria (Prefeitura de Lauro,
     Governo da Bahia/SAC, Neoenergia, Embasa, Sesc, Sebrae, shoppings de Lauro...). O robô extrai a
     og:image e as fotos do corpo. Em `cover_url`, uma URL direta de foto oficial. O próprio
     euamolauro.com.br **não** baixa pelo robô (bloqueia o GitHub): use a fonte original.
   - Suba o job, aguarde `covers/<id>/sources.json` (git pull a cada 15 s, até ~5 min), monte uma folha
     de contato e **olhe as fotos** (Read). Escolha a que mostra o assunto da matéria em Lauro
     (o lugar, o serviço, o evento, gente de Lauro). Largura mínima 1000 px.
   - Proibido: arte padrão como foto, foto de jornal/portal, Instagram de terceiros, Google Imagens,
     imagem de IA, foto genérica sem relação com Lauro, foto de bom tom duvidoso (acidente, hospital).
   - Se nenhuma servir, busque outra página oficial sobre o mesmo lugar/assunto em Lauro
     (WebSearch com `allowed_domains`) e rode de novo. Só então use banco livre (Wikimedia/Unsplash).
   - Crédito sempre na peça: "Lugar · Foto: Nome/Instituição".
3. **Formato**:
   - **Reels**: agenda, eventos, cultura, história, receitas, notícias do bem, natureza.
   - **Carrossel**: serviços, onde resolver, vagas, cursos, oportunidades, prazos, telefones.
   - Sempre **+ 1 Story** (story.jpg) depois do feed/Reels.
4. **Job** (`jobs/<id>.json`): `post_id, link, kind (carousel|reel), label, title` (trecho em verde entre
   *asteriscos*), `cover_file, credit, pan` (0–1, posição horizontal do recorte),
   `slides` (3 cards: label, heading, 2–4 bullets curtos com o serviço: data, horário, local, valor,
   telefone, requisitos), `cta`, `caption`.
5. **Legenda**: gancho com emoji, 3–6 linhas de serviço com emoji, "🔗 ... link na bio", chamada para
   salvar/compartilhar/marcar, hashtags: `#LauroDeFreitas #EuAmoLauro #LauroDeFreitasBA #RMS #Bahia`
   + 3–4 do tema. Mesmo checagem do site: só dados que estão na matéria. Nada de política.
6. **Gerar**: `python3 scripts/render.py jobs/<id>.json` → `posts/<id>/` (slide-1..5.jpg ou reel.mp4 +
   reel-capa.jpg, story.jpg). Abra slide-1/story (ou um quadro do reel com ffmpeg) e confira texto,
   recorte e crédito. Commit + push; pegue o SHA.
7. **Publicar** (Windsor, conta 17841453870915611):
   - carrossel: `create_carousel_post {image_urls:[slide-1..5], caption}`;
   - Reels: `create_video_post {video_url: reel.mp4, cover_url: reel-capa.jpg, share_to_feed: true, caption}`;
   - depois `create_story {image_url: story.jpg}`.
   - "Media ID is not available": tente de novo até 3 vezes.
8. **Registrar** em `published.json` (`"<id>": {"feed": media_id, "story": media_id}`), commit e push.
9. **Avisar** o dono no resumo final: formato, foto escolhida (origem/crédito) e IDs; ou o que falhou.
