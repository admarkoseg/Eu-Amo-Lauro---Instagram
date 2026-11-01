# Eu Amo Lauro – mídia do Instagram

Repositório de apoio da automação que leva as matérias do portal **euamolauro.com.br** para o Instagram **@euamolauro**.

- `jobs/<post_id>.json` – pedido de publicação (gerado pelo Claude a partir da matéria).
- `covers/` – capas baixadas do site pelo GitHub Actions (`.github/workflows/fetch-covers.yml`).
- `posts/<data>-<post_id>/` – artes do carrossel (4:5) e Reels (9:16) prontos; o Instagram busca por
  `https://cdn.jsdelivr.net/gh/admarkoseg/eu-amo-lauro---instagram@main/posts/...`.
- `scripts/` – geradores de arte e vídeo.

Não guarde senhas nem tokens aqui: o repositório é público.
