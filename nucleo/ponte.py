"""
Dar ao Tools PRO uma porta própria de depuração.

O problema que isto resolve, e que só apareceu na máquina de um aluno:

O app fala com o Premiere pela porta de depuração de um painel CEP. Essa porta
**não existe por padrão** — ela só abre quando a extensão tem um arquivo
`.debug` declarando host e porta, e o PlayerDebugMode está ligado.

O Tools PRO é distribuído SEM `.debug` (o build exclui de propósito, para não
publicar extensão em modo de depuração). Na máquina de casa o app funcionava
por CARONA: os painéis do blinkl instalados ali trazem os próprios `.debug` e
abrem 8860/8862. Numa máquina que só tem o Tools PRO — a de todo aluno — não há
porta nenhuma, e a tela dizia "abra o painel" para alguém que já estava com o
painel aberto. Conselho certo, causa errada.

O conserto é local e reversível: o app escreve o `.debug` na pasta da extensão
do usuário e liga o PlayerDebugMode. Não republica o plugin, não mexe em código
assinado — é um arquivo de configuração na casa dele.

⚠️ **Só vale depois de reiniciar o Premiere.** O CEP lê o `.debug` no arranque;
escrever com o Premiere aberto não abre porta nenhuma, e prometer que abriu seria
a mesma mentira de antes.
"""

import os
import re
import subprocess

from . import so

PASTA = os.path.join(so.CEP, "com.editorblackbelt.toolspro")
PORTA_PPRO = 8899
PORTA_AEFT = 8898
CSXS = range(6, 15)          # as versões que o Premiere/AE usam hoje

MODELO = """<?xml version="1.0" encoding="UTF-8"?>
<ExtensionList>
%s</ExtensionList>
"""
BLOCO = """  <Extension Id="%s">
    <HostList>
      <Host Name="PPRO" Port="%d"/>
      <Host Name="AEFT" Port="%d"/>
    </HostList>
  </Extension>
"""


def _ids(pasta):
    """Os Ids de extensão do manifesto. Sem eles o `.debug` não casa com nada —
    e o CEP ignora em silêncio, que é o pior jeito de errar."""
    manifesto = os.path.join(pasta, "CSXS", "manifest.xml")
    try:
        with open(manifesto, encoding="utf-8", errors="ignore") as f:
            texto = f.read()
    except OSError:
        return []
    vistos, saida = set(), []
    for i in re.findall(r'<Extension\s+Id="([^"]+)"', texto):
        if i not in vistos:
            vistos.add(i)
            saida.append(i)
    return saida


def estado():
    """O que a tela precisa saber para explicar o problema sem chutar."""
    tem_pasta = os.path.isdir(PASTA)
    debug = os.path.join(PASTA, ".debug")
    return {
        "plugin_instalado": tem_pasta,
        "pasta": PASTA,
        "tem_debug": os.path.isfile(debug),
        "ids": _ids(PASTA) if tem_pasta else [],
        "porta": PORTA_PPRO,
        "modo_debug": _debug_ligado(),
    }


def _debug_ligado():
    """PlayerDebugMode ligado em ao menos uma versão do CSXS."""
    try:
        if so.WIN:
            for v in CSXS:
                r = subprocess.run(
                    ["reg", "query", r"HKCU\Software\Adobe\CSXS.%d" % v,
                     "/v", "PlayerDebugMode"], capture_output=True, text=True, timeout=10)
                if r.returncode == 0 and "1" in r.stdout:
                    return True
            return False
        for v in CSXS:
            r = subprocess.run(["defaults", "read", "com.adobe.CSXS.%d" % v,
                                "PlayerDebugMode"], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip() in ("1", "1.0", "true"):
                return True
    except Exception:
        pass
    return False


def _ligar_debug():
    feitas = []
    for v in CSXS:
        try:
            if so.WIN:
                r = subprocess.run(
                    ["reg", "add", r"HKCU\Software\Adobe\CSXS.%d" % v, "/v",
                     "PlayerDebugMode", "/t", "REG_SZ", "/d", "1", "/f"],
                    capture_output=True, timeout=15)
            else:
                r = subprocess.run(["defaults", "write", "com.adobe.CSXS.%d" % v,
                                    "PlayerDebugMode", "1"],
                                   capture_output=True, timeout=15)
            if r.returncode == 0:
                feitas.append(v)
        except Exception:
            continue
    return feitas


def preparar():
    """Escreve o `.debug` e liga o modo de depuração. Idempotente de propósito:
    o instalador do plugin apaga a pasta inteira ao atualizar, então isto precisa
    poder rodar de novo sem estragar nada."""
    if not os.path.isdir(PASTA):
        raise RuntimeError(
            "O plugin Tools PRO não está instalado nesta máquina. Instale por "
            "Ambiente > Instalar plugin no Premiere e depois prepare a ponte.")

    ids = _ids(PASTA)
    if not ids:
        raise RuntimeError(
            "Achei a pasta do plugin mas não consegui ler o manifesto dele "
            "(CSXS/manifest.xml). Reinstale o plugin.")

    blocos = ""
    for n, i in enumerate(ids):
        blocos += BLOCO % (i, PORTA_PPRO + n * 2, PORTA_AEFT + n * 2)

    destino = os.path.join(PASTA, ".debug")
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(MODELO % blocos)
    os.replace(tmp, destino)

    versoes = _ligar_debug()
    return {
        "ok": True,
        "arquivo": destino,
        "ids": ids,
        "porta": PORTA_PPRO,
        "csxs": versoes,
        "precisa_reiniciar": True,
        "msg": ("Preparei a ponte: o painel do Tools PRO passa a abrir a porta "
                "%d. **Feche e reabra o Premiere**, depois abra Janela > "
                "Extensões > Tools PRO — a porta só nasce quando o Premiere "
                "arranca lendo este arquivo." % PORTA_PPRO),
    }
