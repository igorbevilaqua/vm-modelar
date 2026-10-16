---
name: vm-modelar
description: Modela um vídeo curto de referência (Reel, TikTok, Shorts, YouTube ou arquivo local) e entrega, na pasta do projeto, a análise de estilo para replicá-lo (ritmo, estrutura, gancho, imagens, som, cor, lettering, 9:16), um roteiro ORIGINAL em PT-BR pronto para gravar (falas [CÂMERA]/[VOZ], fatos checados) e a lista de material para a edição. Use quando o usuário mandar um link ou arquivo de vídeo e pedir para modelar, replicar, copiar o estilo, analisar o estilo, "fazer um igual", ou criar um roteiro a partir de uma referência.
---

# vm-modelar: da referência ao roteiro

Entrada: URL de vídeo curto ou arquivo local. Saída, na pasta atual do projeto:

1. `analise_estilo.md` — como o vídeo funciona e como replicá-lo, com a seção **Melhorias**.
2. `roteiro.txt` — o que gravar: texto original em PT-BR, blocos curtos, [CÂMERA]/[VOZ].
3. `material.md` — o que buscar para a edição, item por item.

**Regra de ouro:** replicar a maioria das coisas. Só mude algo com alta confiança de que fica melhor. O objetivo é igualar ou superar o original.

**Eficiência:** scripts fazem tudo o que é medição (rápido, sem tokens); o modelo só julga. Não assista o vídeo quadro a quadro, não abra `audio.wav`, não leia `transcricao.json` inteiro (use o `.txt`; o `.json` só para conferir o tempo de uma palavra específica) nem o `original.info.json` inteiro.

`S=~/.claude/skills/vm-modelar/scripts`

---

## 1. Baixar (pule se for arquivo local)

```bash
bash $S/baixar.sh "URL" modelar        # -> modelar/original.mp4 + original.info.json
jq '{title,uploader,description,duration,view_count,like_count}' modelar/original.info.json
```

- Usa o yt-dlp do Homebrew com `--cookies-from-browser` (opera → brave → chrome). O Opera tem login no YouTube.
- **Instagram exige login** e nenhum navegador desta máquina tem sessão. Se falhar, peça ao usuário para baixar (ex.: saveclip.app) e pôr o `.mp4` na pasta. Siga com o arquivo local.

## 2. Extrair (determinístico, ~10–20 s para 90 s de vídeo)

```bash
uv run $S/extrair.py modelar/original.mp4 -o modelar     # ou o arquivo local
```

Imprime o resumo e grava em `modelar/`:

| Arquivo | Conteúdo |
|---|---|
| `dados.json` | probe (duração, fps, resolução, proporção, HDR); ritmo (cortes, cortes/s, plano médio/mediano/mín/máx, tempo de cada corte); `cenas` (início, duração, cor média, saturação, luminância, temperatura); fala (idioma, palavras, palavras/s no total e falando, 1ª palavra); áudio (LUFS integrado, LRA, pico, silêncios < -40 dB, BPM, nível fora das palavras, trilha contínua provável, trechos fala × música/som × silêncio) |
| `folha_NN.jpg` | folhas de contato: 2 quadros/s, grade 6×5 = 15 s por folha, tempo carimbado, **borda vermelha = houve corte desde o quadro anterior** |
| `transcricao.txt` / `.json` | frases com tempo / tempo por palavra (mlx-whisper large-v3-turbo; fallback faster-whisper) |

- Cortes estranhos nas folhas (borda vermelha demais em câmera tremida, ou de menos em fusões)? Rode de novo com `--limiar 0.3` ou `0.12`.
- BPM só vale se `trilha_continua_provavel` for true ou houver trechos de música. É estimativa.
- Problema no script: `uv run $S/extrair.py --check` (autoteste com vídeo sintético).
- Idioma errado na transcrição: `--idioma en` (ou `pt`, `es`…).

## 3. Analisar

**Vídeo < 40 s:** faça tudo na sessão principal (subagente não compensa).

**Vídeo ≥ 40 s:** depois do `extrair.py`, lance **dois subagentes em paralelo** (uma mensagem, duas chamadas Agent), cada um com só o que precisa:

- **A — visual.** Lê `dados.json` (ritmo, cenas, cor) e as `folha_NN.jpg`. Escreve `modelar/visual.md`: ritmo por trecho, enquadramentos do apresentador, tipos de imagem e de onde parecem vir, inserções, efeitos e transições, motion graphics, lettering (fonte parecida no Google Fonts, tamanho relativo, posição, ritmo, cor, destaques e com que frequência), tratamento de cor, adaptação 9:16. Cite os tempos.
- **B — narrativa.** Lê `transcricao.txt`, o bloco `fala`/`audio` do `dados.json` e o título/legenda do post. Escreve `modelar/narrativa.md` (estrutura por blocos com tempos, função de cada bloco, fórmula do gancho, CTA, erros factuais do original, melhorias de texto) e o `roteiro.txt` final na pasta do projeto (regras da seção 5), com fatos checados na web.

Passe aos subagentes os caminhos absolutos, as regras das seções 4–6 relevantes e o formato de saída. A sessão principal lê os dois `.md`, ajusta o roteiro se precisar e escreve `analise_estilo.md` e `material.md`.

## 4. `analise_estilo.md`

Modelo de qualidade: tabelas e listas curtas, números reais do `dados.json`, tempos do original, tudo acionável. Seções:

1. **Ficha técnica** — duração, fps, resolução/proporção original → a nossa será 1080×1920; cortes, cortes/s, plano médio (apresentador × B-roll); palavras/s; LUFS; silêncios.
2. **Estrutura narrativa** — tabela `Bloco | Tempo | Função | Visual`, e a **fórmula** em uma linha (ex.: afirmação → prova pelo passado → problema → antagonista → tese → convite).
3. **Gancho** — o que acontece nos primeiros 1–3 s (fala, imagem, texto na tela) e por que prende.
4. **Imagens** — tipo e estilo (arquivo, pintura, print, meme, filme, B-roll), lógica de troca ("cada substantivo ganha uma imagem", corte na palavra), movimento (Ken Burns, punch-in).
5. **Inserções** — quais, com áudio original ou não, duração.
6. **Enquadramentos e apresentador** — plano, olhar, luz, figurino, cenário.
7. **Efeitos e motion graphics** — transições, RGB split, recortes, contadores, setas, mapas.
8. **Sonoplastia** — trilha (clima, BPM, contínua ou não, onde cresce), SFX prováveis, silêncios estratégicos, loudness alvo (-14 LUFS).
9. **Cor** — temperatura, saturação, contraste; quente/fria por tipo de plano.
10. **Lettering** — fonte parecida no Google Fonts, tamanho base, posição, palavras por tela, sincronia, destaques (gigante, cor, script, vazado) e frequência.
11. **Adaptação 9:16** — áreas seguras do Instagram (`references/fontes.md` §8), o que fazer com material horizontal (nunca barra preta).
12. **Melhorias** — ver abaixo.

### Melhorias (só alta confiança, cada uma com justificativa curta)

- **Adaptação cultural para o Brasil:** exemplos, referências e nostalgia que o público BR reconhece.
- **Palavras de mais impacto** e **mais clareza** (trocar termo vago por concreto, número redondo por exato).
- **Gancho mais forte** se o original demora a chegar no conflito.
- **Corrigir erros factuais** do original (verificados na web).
- **Legendar inserções estrangeiras** (`references/fontes.md` §10).
- Riscos: Content ID, pessoa comum identificável.

Não "melhore" o que já funciona: ritmo, estrutura e estilo visual ficam.

## 5. `roteiro.txt`

**Texto ORIGINAL em PT-BR:** mesma estrutura de beats, mesma fórmula de gancho, mesmo ritmo, mas com palavras próprias. **Nunca traduza nem copie** o texto do criador original (plágio e denúncia). Citação curta de terceiros pode, com atribuição.

- **Duração e ritmo próximos ao original:** total de palavras ≈ `palavras_por_s_falando` × tempo falando (±10%). Informe a conta no topo.
- **Cada frase curta = um corte.** Blocos curtos, numerados, com função e tempo aproximado.
- Marque cada fala:
  - **[CÂMERA]** — curta, para decorar e falar olhando para a lente. O editor só mostra o rosto quando ele olha para a lente. Use no gancho, nas viradas, nas opiniões e no CTA.
  - **[VOZ]** — pode ser lida; vira voice over coberto por imagem. Use em dados, história e explicação.
- Por bloco, **só quando ajudar**: enquadramento, gesto, tom de voz, expressão facial, objeto para mostrar. **Sem instruções de edição** (nada de TELA, B-roll, efeitos: isso fica no `material.md`).
- **Fatos e números:** cheque com WebSearch e liste as **fontes (URL)** no fim. Use "estima-se" quando for estimativa.

Formato:

```
ROTEIRO – "TÍTULO"  (~85 s · ~260 palavras · ~3,1 palavras/s, como o original)
Referência: URL

DICAS DE GRAVAÇÃO
  - Celular na vertical (9:16), lente na altura dos olhos, do peito para cima.
  - Um bloco por take. Repita cada bloco 2–3 vezes. Pausa de 1 s entre blocos.
  - Nos blocos [CÂMERA], olhe para a lente (não para a tela).
  - [VOZ] pode ser lido; fale no mesmo ritmo.
  - Microfone de lapela.
  (+ dicas do estilo: luz, figurino, cenário, energia)

==================================================================

[1] GANCHO (~3 s)
[CÂMERA] Frase curta.
  (sobrancelha levantada, tom de quem conta um segredo)

[2] PROMESSA (~1,5 s)
[CÂMERA] Calma, eu explico.

[3] CONTEXTO (~5 s)
[VOZ] Frase curta.
[VOZ] Outra frase curta.
...

==================================================================
FONTES
  - Fato — URL
```

## 6. `material.md`

Uma tabela por bloco do roteiro (ou uma tabela única com a coluna Bloco):

`# | Fala onde entra | O que | Onde procurar | Consulta sugerida | Licença / risco`

- Imagens, vídeos de arquivo, manchetes reais (com veículo e data se já achou), inserções com áudio, trilha (clima, BPM, 2–3 opções livres), SFX (lista com consultas), fontes tipográficas (link do Google Fonts).
- Priorize domínio público / CC0 / CC BY; marque **⚠ Content ID** em filme, série, desenho famoso e música comercial, sempre com uma alternativa PD.
- Onde procurar e como (APIs, comandos testados, manchete com Brave headless, corte direto do Internet Archive): **`references/fontes.md`**. Não busque todos os arquivos agora: só a consulta sugerida, salvo se o usuário pedir.

## 7. Depois: ponte para a edição

Recomende no fim da resposta qual skill usar com a gravação, pelo estilo da referência:

| Referência parece… | Skill |
|---|---|
| notícia/opinião provada com manchetes reais, tela dividida, apresentador presente | `edit-vm` |
| talking head explicativo/intelectual, alterna tela dividida, voice over e recorte, citações | `anthropic-skills:edit-tay` |
| quase todo voice over, imagem trocando a cada ~0,5 s, tipografia cinética, apresentador aparece pouco | `anthropic-skills:edit-voiceover` |
| ensaio cinematográfico: cenas de filme, obras de arte, imagens históricas, trilha clássica crescendo até um final majestoso | `edit-cinema` |

**Aviso de gravação:** o iPhone grava em HDR HLG (BT.2020). Converta antes de editar, senão a imagem fica lavada:

```bash
avconvert -s gravacao.MOV -o gravacao_sdr.mp4 -p Preset1920x1080 --replace
```

(o `edit-vm` faz isso no `preparar.sh`). O `dados.json` mostra `hdr` da referência, mas o que importa é a gravação nova.
