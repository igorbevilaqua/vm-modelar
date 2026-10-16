#!/bin/bash
# Baixa o vídeo de referência para PASTA/original.mp4 (+ original.info.json com título, perfil e legenda do post).
# Uso: baixar.sh URL [PASTA=modelar]
# Use o yt-dlp do Homebrew (recente, resolve os desafios JS do YouTube com deno).
# O de venv Python 3.9 fica preso numa versão velha e leva 403/429.
set -u
URL="$1"; DIR="${2:-modelar}"
YT=/opt/homebrew/bin/yt-dlp; [ -x "$YT" ] || YT=yt-dlp
mkdir -p "$DIR"
OUT=(-o "$DIR/original.%(ext)s" --write-info-json --no-playlist --no-progress -f "bv*[height<=1920]+ba/b" --merge-output-format mp4)

# Opera tem login no YouTube; Instagram precisa de sessão (tenta os navegadores em ordem).
for nav in opera brave chrome; do
  "$YT" --cookies-from-browser "$nav" "${OUT[@]}" "$URL" && { echo "ok: $DIR/original.mp4 (cookies: $nav)"; exit 0; }
done
"$YT" "${OUT[@]}" "$URL" && { echo "ok: $DIR/original.mp4"; exit 0; }

echo "FALHOU. Instagram exige login e nenhum navegador aqui tem sessão do Instagram." >&2
echo "Peça ao usuário para baixar (ex.: saveclip.app) e colocar o .mp4 na pasta do projeto; a skill aceita arquivo local." >&2
exit 1
