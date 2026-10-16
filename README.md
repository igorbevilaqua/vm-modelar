# vm-modelar

Skill do Claude Code que **modela um vídeo curto de referência** (Reel, TikTok, Shorts, YouTube ou arquivo local) e entrega três arquivos na pasta do projeto:

1. `analise_estilo.md` — estratégia para replicar o vídeo: ritmo (cortes/s, plano médio, palavras/s), estrutura por blocos, gancho, imagens, inserções, enquadramentos, efeitos, sonoplastia, cor, lettering (fonte parecida no Google Fonts), motion graphics, adaptação 9:16 e **Melhorias** de alta confiança.
2. `roteiro.txt` — roteiro **original** em PT-BR para gravar, em blocos curtos marcados [CÂMERA] / [VOZ], com o mesmo ritmo do original e fatos checados com fontes.
3. `material.md` — o que buscar para a edição (imagens, arquivo, manchetes, trilha, SFX), com onde procurar, consulta sugerida e risco de Content ID.

Medição é feita por scripts (rápido, sem gastar tokens); o modelo só julga. Vídeos ≥ 40 s usam dois subagentes em paralelo (visual e narrativa).

## Instalar

```bash
git clone https://github.com/igorbevilaqua/vm-modelar.git
ln -s "$PWD/vm-modelar/vm-modelar" ~/.claude/skills/vm-modelar
```

Requisitos (macOS Apple Silicon testado): `ffmpeg`, `uv`, `jq`, `yt-dlp` do Homebrew (com `deno`). A transcrição usa `mlx-whisper` (fallback `faster-whisper`), instalado sozinho pelo `uv` na primeira execução.

## Uso

No Claude Code, dentro da pasta do projeto: "modela esse vídeo: URL" (ou o caminho de um `.mp4`).

Scripts avulsos:

```bash
bash vm-modelar/scripts/baixar.sh URL modelar           # baixa para modelar/original.mp4
uv run vm-modelar/scripts/extrair.py VIDEO -o modelar   # dados.json, folhas de contato, transcrição
uv run vm-modelar/scripts/extrair.py --check            # autoteste
```

## Conteúdo

- `vm-modelar/SKILL.md`: o fluxo e o formato dos três arquivos.
- `vm-modelar/scripts/baixar.sh`: download com yt-dlp + cookies do navegador.
- `vm-modelar/scripts/extrair.py`: probe, cortes de cena, folhas de contato, transcrição por palavra, loudness, silêncios, BPM, cor por cena.
- `vm-modelar/references/fontes.md`: onde achar imagens, arquivo, cenas, manchetes, trilha, SFX e fontes; direito autoral BR; legendar × dublar.
