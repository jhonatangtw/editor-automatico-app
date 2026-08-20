#!/usr/bin/env python3
"""
Reconstroi o audio EXATAMENTE como ele toca na timeline.

Por que existe: quando o anuncio ja tem edicao, a locucao costuma estar picotada
em dezenas de pedacos com offsets diferentes, as vezes em mais de uma trilha.
Transcrever os arquivos originais da timecode errado — e o mapa de marcacao
inteiro sai torto.

Entrada: o JSON que `pr_timeline_listar` devolve (ou so a parte de audio).
Saida: um WAV 16 kHz mono, pronto para o Whisper.

    python3 audio_da_timeline.py --timeline tl.json --midia "/caminho/dos/mp3" \
            --out ad02_timeline.wav --duracao-esperada 711.28

CONFERIR A DURACAO. Se nao bater com a da sequencia, parar e investigar antes
de transcrever — foi assim que os tres ADs do LinfaFlow sairam certos
(711,29 contra 711,28 e 599,67 exato).
"""
import argparse, json, os, subprocess, sys, tempfile


def dur(caminho):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", caminho], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def acha(nome, pastas):
    """Localiza o arquivo de origem pelo nome que aparece na timeline."""
    for p in pastas:
        direto = os.path.join(p, nome)
        if os.path.exists(direto):
            return direto
        for raiz, _, arqs in os.walk(p):
            if nome in arqs:
                return os.path.join(raiz, nome)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True, help="JSON de pr_timeline_listar")
    ap.add_argument("--midia", required=True, nargs="+", help="pasta(s) com os arquivos de audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--trilha", default=None,
                    help="so esta trilha (ex: A1). Sem isso, usa todas em ordem de tempo")
    ap.add_argument("--duracao-esperada", type=float, default=None)
    a = ap.parse_args()

    d = json.load(open(a.timeline))
    trilhas = d.get("audio", d if isinstance(d, list) else [])
    clipes = []
    for t in trilhas:
        if a.trilha and t.get("trilha") != a.trilha:
            continue
        for it in t.get("itens", []):
            clipes.append(it)
    clipes.sort(key=lambda x: x["inicio"])
    if not clipes:
        sys.exit("ERRO: nenhum clipe de audio encontrado no JSON")

    faltando = []
    tmp = tempfile.mkdtemp(prefix="tl_audio_")
    partes = []
    anterior_fim = 0.0

    for i, c in enumerate(clipes):
        src = acha(c["nome"], a.midia)
        if not src:
            faltando.append(c["nome"]); continue

        # silencio se houver buraco entre um clipe e o proximo
        buraco = c["inicio"] - anterior_fim
        if buraco > 0.02:
            s = os.path.join(tmp, f"sil{i:03d}.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "anullsrc=r=16000:cl=mono", "-t", f"{buraco:.3f}",
                            "-c:a", "pcm_s16le", s, "-y"], check=False)
            partes.append(s)

        o = os.path.join(tmp, f"p{i:03d}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(c.get("entrada", 0)),
                        "-t", str(c["duracao"]), "-i", src,
                        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", o, "-y"], check=False)
        partes.append(o)
        anterior_fim = c["inicio"] + c["duracao"]

    if faltando:
        sys.exit("ERRO: nao achei nas pastas informadas: " + ", ".join(sorted(set(faltando))))

    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w") as f:
        for p in partes:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista,
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", a.out, "-y"], check=False)

    saiu = dur(a.out)
    print(f"{a.out}  {saiu:.2f}s  ({len(clipes)} clipes)")

    if a.duracao_esperada:
        delta = abs(saiu - a.duracao_esperada)
        if delta > 0.5:
            sys.exit(f"ERRO: esperado {a.duracao_esperada:.2f}s, saiu {saiu:.2f}s "
                     f"(diferenca de {delta:.2f}s). NAO transcrever — investigar antes.")
        print(f"confere com a sequencia (diferenca de {delta:.2f}s)")


if __name__ == "__main__":
    main()
