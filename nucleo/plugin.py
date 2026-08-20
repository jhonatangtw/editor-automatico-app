"""
O plugin do Premiere — instalar e atualizar por dentro do app.

O Editor Black Belt Tools PRO é a extensão CEP que o app usa como PONTE para o
Premiere. Sem ela o app lê e escreve nada na timeline: as etapas 11 e 12 caem
na mensagem "abra o painel". Por isso a instalação dele não pode ser um PDF de
tutorial — é um botão.

Como o plugin se distribui (mesma casa, mesma regra): GitHub Releases públicas,
com um pacote OFFLINE (`...-Instalador.zip`) que traz a extensão e os dois
instaladores dentro. Baixar o zip e rodar o `.command` é exatamente o que o
aluno faria à mão, sem inventar um segundo caminho de instalação que depois
diverge do oficial.

⚠️ O instalador precisa de um TERMINAL de verdade: ele liga o PlayerDebugMode e
copia fontes. Disparado por Popen mudo, um passo falha e o app relata sucesso
sobre um processo morto — foi o que já aconteceu com os logins de CLI.
"""

import os
import shutil
import subprocess
import sys
import zipfile

from . import atualizacao, rede, so

REPO = "jhonatangtw/editor-black-belt-tools-pro"
ASSET = "EditorBlackBeltToolsPRO-Instalador.zip"
CEP = os.path.join(so.CEP, "com.editorblackbelt.toolspro")

# o mesmo pacote traz os dois instaladores; muda só qual deles se chama
INSTALADOR = ("instalar-windows", ".bat") if so.WIN else ("instalar-mac", ".command")
PAGINA = "https://github.com/%s/releases/latest" % REPO
BASE = "https://github.com/%s/releases/latest/download/" % REPO


def instalado():
    """A versão que está na pasta do CEP, ou None."""
    if not os.path.isdir(CEP):
        return None
    try:
        import json
        with open(os.path.join(CEP, "version.json"), encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return "instalado"


def estado():
    """O que a tela mostra. Não levanta: sem internet, o card ainda aparece."""
    tem = instalado()
    d = {"instalado": tem, "pasta": CEP, "pagina": PAGINA,
         "ultima": None, "notas": None, "tem_nova": False, "erro": None,
         "zip": BASE + ASSET}
    try:
        import json
        r = json.loads(atualizacao._pegar(BASE + "version.json"))
        d["ultima"] = r.get("version")
        d["notas"] = r.get("notes")
        d["tem_nova"] = bool(tem and d["ultima"] and
                             atualizacao.maior(d["ultima"], tem))
    except Exception as e:
        d["erro"] = "Não consegui ver a versão publicada: %s" % rede.explicar(e)[:220]
    return d


def _baixar(url, alvo, ao_vivo=None):
    import urllib.request
    req = urllib.request.Request(url, headers=atualizacao.UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        lido = 0
        tmp = alvo + ".parcial"
        with open(tmp, "wb") as f:
            while True:
                p = r.read(262144)
                if not p:
                    break
                f.write(p)
                lido += len(p)
                if ao_vivo and total:
                    ao_vivo("baixando o plugin… %d%% de %d MB"
                            % (int(lido * 100 / total), total // 1048576))
    os.replace(tmp, alvo)
    return alvo


def instalar(ao_vivo=None):
    """Baixa o pacote oficial, descompacta e entrega ao instalador de verdade."""
    diz = ao_vivo or (lambda _: None)
    # os.path.join, não "~/Downloads/...": no Windows a barra normal produz
    # caminho misto (C:\Users\x/Downloads/...) que funciona em quase tudo e
    # atrapalha na hora de citar entre aspas.
    pasta = os.path.join(os.path.expanduser("~"), "Downloads",
                         "Editor Black Belt Tools PRO")
    if os.path.isdir(pasta):
        shutil.rmtree(pasta, ignore_errors=True)
    os.makedirs(pasta, exist_ok=True)

    zipe = os.path.join(pasta, ASSET)
    _baixar(BASE + ASSET, zipe, diz)

    diz("descompactando…")
    try:
        with zipfile.ZipFile(zipe) as z:
            z.extractall(pasta)
    except Exception as e:
        raise RuntimeError("O pacote baixado não abriu: %s" % e)
    os.remove(zipe)

    # o .command pode vir sem bit de execução dependendo de como foi zipado
    prefixo, ext = INSTALADOR
    alvo = None
    for raiz, _, arquivos in os.walk(pasta):
        for n in arquivos:
            baixo = n.lower()
            if baixo.startswith(prefixo) and baixo.endswith(ext):
                alvo = os.path.join(raiz, n)
                break
        if alvo:
            break
    manual = "INSTALAR-WINDOWS.bat" if so.WIN else "INSTALAR-MAC.command"
    if not alvo:
        so.abrir(pasta)
        return {"ok": True, "manual": True, "pasta": pasta,
                "msg": "Baixei e abri a pasta do instalador. Dê dois cliques no "
                       "arquivo %s." % manual}

    diz("abrindo o instalador…")
    if so.WIN:
        r = so.terminal([alvo], "plugin do Premiere")
    else:
        os.chmod(alvo, 0o755)
        r = so.terminal(["bash", alvo], "plugin do Premiere")
    if not r.get("ok"):
        so.abrir(pasta)
        return {"ok": True, "manual": True, "pasta": pasta,
                "msg": "Baixei o instalador e abri a pasta. Dê dois cliques em "
                       "%s." % manual}
    return {"ok": True, "pasta": pasta, "instalador": alvo,
            "msg": "O instalador do plugin abriu no Terminal. Quando ele terminar, "
                   "FECHE e reabra o Premiere e abra Janela > Extensões > Tools PRO."}
