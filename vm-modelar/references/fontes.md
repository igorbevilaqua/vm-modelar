# Onde achar material (para o `material.md`)

Testado neste Mac em out/2026, salvo onde diz "verificar". Não é parecer jurídico.

**Ordem de preferência:** material do usuário → registro real do fato → domínio público / CC0 / CC BY → banco de imagens (só conceito abstrato) → ilustração por IA (só metáfora óbvia, nunca "foto" falsa de fato real).

Guarde para cada item: URL, data de acesso, licença e crédito. Mande `User-Agent` nas APIs.

---

## 1. Imagens

| Fonte | Melhor para | Como buscar | Licença |
|---|---|---|---|
| **Wikimedia Commons** | pessoas públicas, lugares, logos (SVG), pinturas, gravuras, fotos históricas | `commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=TERMO&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url\|extmetadata&format=json` | por arquivo: `extmetadata.LicenseShortName` |
| **Openverse** | agrega Commons, Flickr, museus | `api.openverse.org/v1/images/?q=TERMO&license=pdm,cc0,by&page_size=20` (sem chave) | filtro `license=` |
| **Library of Congress** | fotos, cartazes, jornais dos EUA | loc.gov/free-to-use (a API JSON devolve 403 sem navegador: use o site) | sets "Free to Use" = PD |
| **NARA** | fotos e filmes do governo dos EUA | catalog.archives.gov | obra federal costuma ser PD |
| **Europeana** | arquivos e museus europeus | europeana.eu (filtro por licença) | por item |
| **Flickr Commons** | fotos históricas de museus | flickr.com/commons | "no known copyright restrictions" |
| **Agência Brasil / Senado / Câmara** | política brasileira | agenciabrasil.ebc.com.br, senado.leg.br/fotos, camara.leg.br/banco-imagens | CC BY com crédito "Fotógrafo/Agência"; confira cada foto |
| **Hemeroteca Digital (BN)** | manchetes de jornais BR, séc. XIX–XX | memoria.bn.gov.br | grátis; crédito "Hemeroteca Digital/BN – Jornal, data" |
| **Foto da própria matéria** | a foto real do fato | `meta[property="og:image"]` da página da notícia | do veículo: dê crédito |

## 2. Vídeo de arquivo

- **Internet Archive / Prelinger** (cinejornais, institucionais, propaganda dos EUA, anos 1930–70; Prelinger em geral PD/CC):
  ```bash
  curl -s "https://archive.org/advancedsearch.php?q=TERMO+AND+collection:prelinger&fl[]=identifier&fl[]=title&rows=20&output=json"
  curl -s "https://archive.org/metadata/IDENTIFICADOR/files"          # acha o .mp4
  # corta direto da URL, sem baixar o filme inteiro (testado: 4 s em ~20 s)
  ffmpeg -ss 30 -t 4 -i "https://archive.org/download/ID/ID.mp4" -c:v libx264 -an trecho.mp4
  ```
- **NASA** (espaço, Apollo, Terra vista de cima; sem copyright, mas logo/insígnia proibidos e sem endosso): `images-api.nasa.gov/search?q=TERMO&media_type=video` → `collection.json` de cada item lista os arquivos.
- **TV Câmara / TV Senado:** sessões CC BY sem tirar a marca d'água; TV Senado sem uso comercial nem propaganda política.
- **Pexels / Pixabay:** B-roll genérico (mãos, cidade, natureza, escritório). **Nada de pessoa identificável em contexto político** (os termos proíbem).
- **British Pathé, Reuters, AP Archive no YouTube:** assistir é grátis, reusar exige licença paga.

## 3. Cenas de filme, TV e redes

```bash
/opt/homebrew/bin/yt-dlp --cookies-from-browser opera -f "bv*[height<=1080]+ba/b" \
  --download-sections "*00:01:10-00:01:15" -o cena.mp4 URL
# achar o momento pela fala (legenda automática com tempo)
/opt/homebrew/bin/yt-dlp --skip-download --write-auto-subs --sub-langs en -o subs URL
```
- Busque "FILME cena DESCRIÇÃO" no YouTube; prefira canais de clipes em HD (Movieclips etc.).
- Trechos de 2–5 s, sem o áudio original (a voz segue por cima), salvo quando a fala da cena é o ponto.
- **Risco de Content ID:** filme, série, desenho famoso (Tom & Jerry, Bob Esponja) e música comercial podem mutar o áudio, cortar alcance ou derrubar o post. Marque esses itens com ⚠ no `material.md` e dê uma alternativa PD.
- A skill `edit-vm` tem `scripts/cena.py` (folha de quadros, corta faixas pretas e cortes escondidos) e um catálogo de cenas por emoção.

## 4. Manchetes reais

1. Achar: Google Notícias RSS (`news.google.com/rss/search?q=TERMO&hl=pt-BR&gl=BR&ceid=BR:pt-419`) ou o `scripts/manchetes.py` da skill `edit-vm`; WebSearch para veículo específico.
2. Print com Brave headless (o processo **não fecha sozinho**: espere o arquivo e mate):
   ```bash
   B="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
   "$B" --headless=new --window-size=600,1600 --force-device-scale-factor=2 --screenshot="$PWD/manchete.png" "URL" >/dev/null 2>&1 &
   P=$!; for i in $(seq 60); do [ -s manchete.png ] && break; perl -e 'select(undef,undef,undef,0.5)'; done; kill $P
   ```
   Paywall: `https://archive.ph/newest/URL`. Versão antiga: web.archive.org (cite a data).
3. O texto é exatamente o publicado. Guarde `{titulo, veiculo, data, link}`.

## 5. Trilha

| Fonte | Observação |
|---|---|
| **YouTube Audio Library** (Studio → Biblioteca de áudio) | segura para YouTube; filtre "sem atribuição" |
| **Pixabay Music** | licença Pixabay, sem atribuição; algumas faixas estão no Content ID (verificar) |
| **Free Music Archive** | filtre CC BY / CC0; atribuição obrigatória no CC BY |
| **Musopen** | música clássica em domínio público (gravação também livre) |
| **Incompetech** (Kevin MacLeod) | CC BY, crédito "Kevin MacLeod (incompetech.com)" |

Música comercial (a trilha do vídeo original, se for de artista) **não** vai no `material.md` como arquivo: indique o **clima/BPM** e uma alternativa livre parecida. No Instagram dá para usar a música pela biblioteca do app na hora de postar.

## 6. Efeitos sonoros (SFX)

- **Freesound** (filtre CC0): whoosh, clique, papel, máquina de escrever, riser.
- **Pixabay SFX** e **Mixkit**: sem atribuição.
- Consultas boas: "whoosh transition", "camera shutter", "paper crumple", "riser", "boom impact", "typing keyboard", "notification pop".

## 7. Fontes tipográficas (Google Fonts)

Download: `https://raw.githubusercontent.com/google/fonts/main/ofl/NOME/` (ex.: `ofl/inter/`). Parecidas com as comuns em Reels:

| Visual no original | Google Fonts |
|---|---|
| grotesca bold (SF Pro, Helvetica Now, Proxima) | Inter Display / Inter Tight, Manrope |
| condensada caixa alta (Impact, Bebas) | Anton, Bebas Neue, Oswald |
| geométrica pesada (Futura, Gotham) | Montserrat ExtraBold/Black, Poppins Black |
| serifa editorial | Playfair Display, Libre Baskerville, Lora |
| script elegante | Great Vibes, Pinyon Script, Playball |
| manuscrita / marcador | Caveat, Permanent Marker |
| máquina de escrever | Special Elite, Courier Prime |

## 8. Áreas seguras do Instagram (1080×1920)

Sem número oficial da Meta; consenso dos guias de 2026:
- livre em cima: ~200 px; embaixo: ~420 px (nome, legenda, áudio); direita: ~120–150 px (botões).
- texto crítico dentro de x 60–960, y 200–1500. A grade do perfil corta para 3:4 (1080×1440 centrado): o gancho em texto deve caber ali.

## 9. Direito autoral (Brasil) e plataformas

- **Lei 9.610/98, art. 46, III:** citação de trechos para crítica/comentário, na medida justificada, com autor e origem. **VIII:** pequenos trechos em obra nova, sem ser o foco principal. Aqui não existe *fair use* amplo.
- **Art. 44:** foto e audiovisual protegidos por 70 anos após a divulgação.
- **Content ID / Rights Manager** são automáticos e ignoram o art. 46. Boas práticas: poucos segundos, comentário por cima, crédito na tela, preferir PD/CC, log de URL + licença, sem a música original dos clipes.
- **Imagem de pessoa comum:** borrar ou não usar. Figura pública em fato jornalístico: ok.
- **Texto do criador original:** nunca traduzir/copiar o roteiro dele (plágio, denúncia). Citação curta de terceiros com atribuição pode.

## 10. Inserções em outro idioma (público BR)

| Situação | Escolha |
|---|---|
| fala de pessoa real, discurso, trecho de TV até ~15 s | **áudio original + legenda PT-BR** (a voz é a prova) |
| narração longa de documentário/cinejornal | o apresentador narra por cima, original baixo |
| entrevista central | legenda, ou voice over de telejornal com o original audível |

- Legenda da inserção diferente da do apresentador: frase inteira, fonte menor, faixa semitransparente, posição fixa, crédito ("This Morning, ITV – 2022").
- Não clonar a voz de pessoa real. Dublagem por IA → escrever "Dublagem por IA" na tela. Em período eleitoral (Res. TSE 23.732/2024), nunca dublar/clonar candidato.
