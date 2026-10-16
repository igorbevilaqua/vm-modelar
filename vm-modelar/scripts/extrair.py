#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "numpy", "pillow", "librosa",
#   "mlx-whisper; sys_platform == 'darwin' and platform_machine == 'arm64'",
#   "faster-whisper; sys_platform != 'darwin' or platform_machine != 'arm64'",
# ]
# ///
"""Extrai tudo o que é determinístico de um vídeo de referência para a skill vm-modelar.

Uso:  uv run scripts/extrair.py VIDEO [-o modelar] [--idioma pt] [--limiar 0.2]
      uv run scripts/extrair.py --check     (autoteste com vídeo sintético, sem transcrição)

Saída em -o: dados.json (resumo de tudo), folha_NN.jpg (2 qps, 6x5, 15 s por folha,
borda vermelha = houve corte desde o quadro anterior), transcricao.json/.txt, audio.wav.
"""
import argparse, json, math, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS_FOLHA, COLS, ROWS, LARG = 2, 6, 5, 240


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(v):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", v]).stdout)
    vs = next(s for s in j["streams"] if s["codec_type"] == "video")
    w, h = vs["width"], vs["height"]
    rot = next((int(sd["rotation"]) for sd in vs.get("side_data_list", []) if "rotation" in sd), 0)
    if abs(rot) in (90, 270):
        w, h = h, w
    n, d = map(int, vs["avg_frame_rate"].split("/"))
    trc = vs.get("color_transfer", "")
    prop = min(["9:16", "3:4", "4:5", "1:1", "16:9", "4:3"], key=lambda r: abs(eval(r.replace(":", "/")) - w / h))
    return dict(duracao=round(float(j["format"]["duration"]), 2), fps=round(n / d, 2) if d else None,
                largura=w, altura=h, proporcao=prop, vertical=h > w,
                hdr={"arib-std-b67": "HLG", "smpte2084": "PQ"}.get(trc),
                cor=f'{vs.get("color_primaries", "?")}/{trc or "?"}',
                tem_audio=any(s["codec_type"] == "audio" for s in j["streams"]))


def cortes(v, limiar):
    # showinfo só imprime com -v info; escala antes para ficar rápido
    r = sh(["ffmpeg", "-hide_banner", "-v", "info", "-i", v, "-an", "-vf",
            f"scale=320:-2,select='gt(scene,{limiar})',showinfo", "-f", "null", "-"])
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def quadros(v, w, h):
    """Lê o vídeo a 2 qps em LARG px de largura. Devolve [(t, array RGB)]."""
    H = int(round(LARG * h / w / 2)) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-an", "-vf", f"fps={FPS_FOLHA},scale={LARG}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (LARG * H * 3)
    arr = np.frombuffer(raw[: n * LARG * H * 3], np.uint8).reshape(n, H, LARG, 3)
    return [(i / FPS_FOLHA, arr[i]) for i in range(n)]


def folhas(qs, cuts, out):
    fonte = ImageFont.load_default(size=22)
    H, W = qs[0][1].shape[:2]
    por = COLS * ROWS
    nomes = []
    for k in range(0, len(qs), por):
        folha = Image.new("RGB", (COLS * W, ROWS * H), "black")
        for j, (t, a) in enumerate(qs[k:k + por]):
            im = Image.fromarray(a)
            d = ImageDraw.Draw(im)
            if any(t - 1 / FPS_FOLHA < c <= t for c in cuts):
                d.rectangle([0, 0, W - 1, H - 1], outline="red", width=5)
            d.rectangle([0, 0, 78, 28], fill="black")
            d.text((5, 2), f"{t:.1f}s", fill="white", font=fonte)
            folha.paste(im, ((j % COLS) * W, (j // COLS) * H))
        nome = f"folha_{k // por + 1:02d}.jpg"
        folha.save(out / nome, quality=80)
        nomes.append(f"{nome} ({qs[k][0]:.0f}–{qs[min(k + por, len(qs)) - 1][0]:.1f} s)")
    return nomes


def cor_cenas(qs, limites):
    st = []
    for _, a in qs:
        f = a.reshape(-1, 3).astype(np.float32) / 255
        mx, mn = f.max(1), f.min(1)
        st.append((f.mean(0), float(np.mean((mx - mn) / (mx + 1e-6))), float((f @ [0.2126, 0.7152, 0.0722]).mean())))
    ts = np.array([t for t, _ in qs])
    cenas = []
    for ini, fim in zip(limites, limites[1:]):
        idx = [i for i, t in enumerate(ts) if ini <= t < fim] or [int(np.abs(ts - (ini + fim) / 2).argmin())]
        rgb = np.mean([st[i][0] for i in idx], 0)
        temp = (rgb[0] - rgb[2]) / (rgb[0] + rgb[2] + 1e-6)
        cenas.append([round(ini, 2), round(fim - ini, 2), "#%02x%02x%02x" % tuple(int(x * 255) for x in rgb),
                      round(np.mean([st[i][1] for i in idx]), 2), round(np.mean([st[i][2] for i in idx]), 2),
                      "quente" if temp > 0.08 else "fria" if temp < -0.05 else "neutra"])
    return cenas


def transcrever(wav, idioma):
    try:
        import mlx_whisper
        r = mlx_whisper.transcribe(wav, path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                                   word_timestamps=True, language=idioma)
        segs = [dict(ini=s["start"], fim=s["end"], texto=s["text"].strip(),
                     palavras=[[w["word"].strip(), round(w["start"], 2), round(w["end"], 2)] for w in s.get("words", [])])
                for s in r["segments"]]
        return segs, r.get("language")
    except ImportError:  # fora do Mac Apple Silicon
        from faster_whisper import WhisperModel
        it, info = WhisperModel("large-v3-turbo", compute_type="int8").transcribe(wav, word_timestamps=True, language=idioma)
        segs = [dict(ini=s.start, fim=s.end, texto=s.text.strip(),
                     palavras=[[w.word.strip(), round(w.start, 2), round(w.end, 2)] for w in s.words]) for s in it]
        return segs, info.language


def audio(v, wav, palavras, dur):
    ebu = sh(["ffmpeg", "-nostats", "-hide_banner", "-i", v, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    resumo = ebu[ebu.rfind("Summary:"):]
    num = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", resumo).group(1).replace("-inf", "-99"))
    sil = sh(["ffmpeg", "-nostats", "-hide_banner", "-i", v, "-vn", "-af", "silencedetect=n=-40dB:d=0.3", "-f", "null", "-"]).stderr
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", sil)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sil)] + [dur]
    silencios = [[round(max(a, 0), 2), round(b, 2)] for a, b in zip(ini, fim)]

    import librosa
    y, sr = librosa.load(wav, sr=16000)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    hop = 512
    db = librosa.amplitude_to_db(librosa.feature.rms(y=y, hop_length=hop)[0], ref=1.0)
    t = np.arange(len(db)) * hop / sr
    # fala = palavras unidas quando o intervalo é < 0,6 s
    fala = []
    for _, a, b in palavras:
        if fala and a - fala[-1][1] < 0.6:
            fala[-1][1] = b
        else:
            fala.append([a, b])
    em_palavra = np.zeros(len(t), bool)
    for _, a, b in palavras:
        em_palavra |= (t >= a) & (t <= b)
    fora = db[~em_palavra]
    fundo = float(np.median(fora)) if len(fora) else None
    # trechos sem fala: silêncio ou música/som (heurística por nível)
    trechos, cursor = [], 0.0
    for a, b in fala + [[dur, dur]]:
        if a - cursor >= 0.4:
            m = (t >= cursor) & (t < a)
            nivel = float(np.median(db[m])) if m.any() else -99
            trechos.append([round(cursor, 2), round(a, 2), "silêncio" if nivel < -40 else "música/som", round(nivel, 1)])
        if b > a:
            trechos.append([round(a, 2), round(b, 2), "fala", None])
        cursor = max(cursor, b)
    return dict(lufs_integrado=num("I"), lra=num("LRA"), pico_real_dbfs=num("Peak"),
                silencios_abaixo_40db=silencios,
                bpm=round(float(np.atleast_1d(tempo)[0]), 1),
                nivel_fora_das_palavras_dbfs=round(fundo, 1) if fundo is not None else None,
                trilha_continua_provavel=bool(fundo is not None and fundo > -38),
                trechos=trechos)


def compacto(obj):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    return re.sub(r"\[\s+([^\[\]{}]*?)\s+\]", lambda m: "[" + re.sub(r"\s*\n\s*", " ", m.group(1)) + "]", s)


def extrair(v, out, idioma=None, limiar=0.2, transcrever_fala=True):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    p = probe(v)
    dur = p["duracao"]
    cuts = [c for c in cortes(v, limiar) if 0.05 < c < dur - 0.05]
    limites = [0.0] + cuts + [dur]
    planos = np.diff(limites)
    qs = quadros(v, p["largura"], p["altura"])
    dados = dict(arquivo=str(v), probe=p,
                 ritmo=dict(cortes=len(cuts), cortes_por_s=round(len(cuts) / dur, 2),
                            plano_medio_s=round(float(planos.mean()), 2), plano_mediano_s=round(float(np.median(planos)), 2),
                            plano_min_s=round(float(planos.min()), 2), plano_max_s=round(float(planos.max()), 2),
                            limiar_cena=limiar, tempos_dos_cortes=cuts),
                 folhas=folhas(qs, cuts, out))
    dados["cenas_campos"] = ["ini_s", "dur_s", "cor_media", "saturacao", "luminancia", "temperatura"]
    dados["cenas"] = cor_cenas(qs, limites)
    dados["cor_geral"] = dict(saturacao_media=round(float(np.mean([x[3] for x in dados["cenas"]])), 2),
                              luminancia_media=round(float(np.mean([x[4] for x in dados["cenas"]])), 2),
                              temperaturas={k: sum(x[5] == k for x in dados["cenas"]) for k in ("quente", "neutra", "fria")})
    palavras = []
    if p["tem_audio"]:
        wav = str(out / "audio.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", v, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
        if transcrever_fala:
            segs, lang = transcrever(wav, idioma)
            palavras = [w for s in segs for w in s["palavras"]]
            (out / "transcricao.json").write_text(compacto(dict(idioma=lang, segmentos=segs)))
            (out / "transcricao.txt").write_text("\n".join(f'[{s["ini"]:5.1f}–{s["fim"]:5.1f}] {s["texto"]}' for s in segs))
            dados["fala"] = dict(idioma=lang, palavras=len(palavras), texto=" ".join(s["texto"] for s in segs))
        dados["audio"] = audio(v, wav, palavras, dur)
        if palavras:
            t_fala = sum(b - a for a, b, k, _ in dados["audio"]["trechos"] if k == "fala")
            dados["fala"].update(palavras_por_s_total=round(len(palavras) / dur, 2),
                                 palavras_por_s_falando=round(len(palavras) / max(t_fala, 0.1), 2),
                                 tempo_falando_s=round(t_fala, 1), primeira_palavra_s=palavras[0][1])
    (out / "dados.json").write_text(compacto(dados))
    return dados


def check():
    with tempfile.TemporaryDirectory() as d:
        v = f"{d}/t.mp4"
        cores = "".join(f"-f lavfi -i color=c={c}:s=360x640:r=30:d=2 " for c in ("red", "blue", "green")).split()
        subprocess.run(["ffmpeg", "-v", "error", *cores, "-f", "lavfi", "-i",
                        "aevalsrc='if(between(t,2,4),0,0.3*sin(2*PI*440*t))':d=6:s=44100",
                        "-filter_complex", "[0][1][2]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", v], check=True)
        r = extrair(v, f"{d}/out", transcrever_fala=False)
        assert abs(r["probe"]["duracao"] - 6) < 0.2 and r["probe"]["proporcao"] == "9:16", r["probe"]
        assert len(r["ritmo"]["tempos_dos_cortes"]) == 2 and abs(r["ritmo"]["tempos_dos_cortes"][0] - 2) < 0.1, r["ritmo"]
        assert r["cenas"][0][5] == "quente" and r["cenas"][1][5] == "fria", r["cenas"]
        assert any(abs(a - 2) < 0.2 for a, _ in r["audio"]["silencios_abaixo_40db"]), r["audio"]
        assert -40 < r["audio"]["lufs_integrado"] < 0 and (Path(d) / "out/folha_01.jpg").exists()
    print("check ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?")
    ap.add_argument("-o", "--saida", default="modelar")
    ap.add_argument("--idioma", default=None, help="ex.: pt, en (padrão: detecta)")
    ap.add_argument("--limiar", type=float, default=0.2, help="sensibilidade do corte de cena")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    if not a.video:
        ap.error("informe o vídeo")
    d = extrair(a.video, a.saida, a.idioma, a.limiar)
    p, r = d["probe"], d["ritmo"]
    print(f'{p["duracao"]} s | {p["largura"]}x{p["altura"]} ({p["proporcao"]}) {p["fps"]} qps | HDR: {p["hdr"]}')
    print(f'{r["cortes"]} cortes ({r["cortes_por_s"]}/s) | plano médio {r["plano_medio_s"]} s, mediana {r["plano_mediano_s"]} s')
    if "fala" in d:
        f = d["fala"]
        print(f'{f["palavras"]} palavras ({f["idioma"]}) | {f.get("palavras_por_s_total")} pal/s no total, {f.get("palavras_por_s_falando")} falando')
    if "audio" in d:
        au = d["audio"]
        print(f'{au["lufs_integrado"]} LUFS | {len(au["silencios_abaixo_40db"])} silêncios | BPM {au["bpm"]} | trilha contínua: {au["trilha_continua_provavel"]}')
    print(f'folhas: {len(d["folhas"])} em {a.saida}/')


if __name__ == "__main__":
    sys.exit(main())
