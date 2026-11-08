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
    if tem:
        try:
            d["legendas"] = legendas_estado()
        except Exception:
            d["legendas"] = None
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


# ------------------------------------------------ painel "Tools PRO Legendas"
# O Tools PRO 1.8.3+ traz um SEGUNDO painel, UXP, que mexe nas legendas nativas
# do Premiere (Janela > Plug-ins UXP > Tools PRO Legendas). O painel CEP tenta
# instalá-lo sozinho 8 s depois de abrir (js/uxp-companheiro.js), mas isso
# falha calado em máquina de aluno (Premiere velho, CEP aberto pouco tempo,
# erro do instalador da Adobe que só vai para o log). Aqui é o mesmo caminho —
# o instalador de plug-ins da Adobe (UPIA) com o .ccx que veio DENTRO do
# plugin instalado — só que num botão, com o motivo na tela quando falha.
#
# ⚠️ O UPIA instala versões LADO A LADO e o Premiere segue na mais velha; cada
# `--remove` tira UMA. Remove em laço antes de instalar, igual ao companheiro.

LEGENDAS = "Tools PRO Legendas"
UPIA = (r"C:\Program Files\Common Files\Adobe\Adobe Desktop Common\RemoteComponents"
        r"\UPI\UnifiedPluginInstallerAgent\UnifiedPluginInstallerAgent.exe" if so.WIN
        else "/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents"
             "/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app"
             "/Contents/MacOS/UnifiedPluginInstallerAgent")
MARCA_LEGENDAS = os.path.join(os.path.expanduser("~"), ".editorblackbelt", "uxp-legendas.json")
PREMIERE_MINIMO = (25, 6)


def _ccx():
    p = os.path.join(CEP, "uxp", "ToolsPROLegendas.ccx")
    return p if os.path.isfile(p) else None


def _versao_ccx():
    try:
        import json
        with open(os.path.join(CEP, "uxp", "legendas", "manifest.json"), encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return None


def _upia(*args, timeout=120):
    r = so.run([UPIA] + list(args), capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


def _numeros(v):
    import re
    return tuple(int(x) for x in re.findall(r"\d+", str(v or ""))[:2])


def _premiere_versao():
    """(versão legível, atende ao mínimo? True/False/None quando não dá pra saber)."""
    nome = so.premiere()
    if not nome:
        return None, None
    if so.MAC:
        import plistlib
        plist = os.path.join("/Applications", nome, nome + ".app", "Contents", "Info.plist")
        try:
            with open(plist, "rb") as f:
                v = plistlib.load(f).get("CFBundleShortVersionString")
            return v, _numeros(v) >= PREMIERE_MINIMO
        except Exception:
            pass
    # Windows (e Mac sem plist): só o ano da pasta. 2026+ = 26.x; 2025 pode ser
    # 25.0 a 25.6, aí só o UPIA sabe; 2024 ou antes não tem UXP de painel.
    ano = _numeros(nome)
    if not ano:
        return nome, None
    ano = ano[0]
    return nome, (True if ano >= 2026 else None if ano == 2025 else False)


def legendas_instalada():
    """Versão do painel de legendas que o Premiere enxerga, ou None."""
    if not os.path.isfile(UPIA):
        return None
    try:
        for linha in _upia("--list", "all", timeout=20).splitlines():
            if LEGENDAS.lower() in linha.lower():
                partes = linha.split()
                return partes[-1] if partes else "instalado"
    except Exception:
        pass
    return None


def legendas_estado():
    pr, ok = _premiere_versao()
    return {"instalada": legendas_instalada(), "disponivel": _versao_ccx(),
            "tem_ccx": bool(_ccx()), "tem_upia": os.path.isfile(UPIA),
            "premiere": pr, "premiere_ok": ok}


def instalar_legendas(ao_vivo=None):
    diz = ao_vivo or (lambda _: None)
    ccx = _ccx()
    if not instalado():
        raise RuntimeError("Instale primeiro o plugin do Premiere (Tools PRO) — "
                           "o painel de legendas vem dentro dele.")
    if not ccx:
        raise RuntimeError("O seu Tools PRO é antigo e não traz o painel de legendas. "
                           "Clique em Atualizar no cartão do plugin e tente de novo.")
    pr, ok = _premiere_versao()
    if ok is False:
        raise RuntimeError("O painel de legendas precisa do Premiere 25.6 (2025) ou mais novo, "
                           "e o seu é %s. Atualize o Premiere pelo Creative Cloud." % pr)
    if not os.path.isfile(UPIA):
        # Sem o instalador da Adobe por linha de comando, o .ccx aberto com dois
        # cliques cai no Creative Cloud, que instala do mesmo jeito.
        so.abrir(ccx)
        return {"ok": True, "manual": True,
                "msg": "Abri o instalador do painel no Creative Cloud. Confirme lá, "
                       "depois feche e abra o Premiere e vá em Janela > Plug-ins UXP > "
                       "Tools PRO Legendas."}

    diz("tirando versões antigas do painel…")
    for _ in range(10):
        try:
            if "successful" not in _upia("--remove", LEGENDAS).lower():
                break
        except Exception:
            break

    diz("instalando o painel de legendas…")
    saida = _upia("--install", ccx)
    if "successful" not in saida.lower():
        fim = " ".join(saida.strip().splitlines()[-3:])[:300]
        dica = ""
        if ok is None:
            dica = (" Se o seu Premiere for anterior à versão 25.6, atualize pelo "
                    "Creative Cloud — o painel não roda nele.")
        raise RuntimeError("O instalador da Adobe recusou: %s.%s" % (fim or "sem resposta", dica))

    # mesma marca do painel CEP, para ele não reinstalar por cima no próximo boot
    try:
        import json
        from datetime import datetime, timezone
        os.makedirs(os.path.dirname(MARCA_LEGENDAS), exist_ok=True)
        with open(MARCA_LEGENDAS, "w", encoding="utf-8") as f:
            json.dump({"versao": _versao_ccx(),
                       "em": datetime.now(timezone.utc).isoformat()}, f)
    except Exception:
        pass
    return {"ok": True, "versao": _versao_ccx(),
            "msg": "Painel de legendas instalado. Feche e abra o Premiere e vá em "
                   "Janela > Plug-ins UXP > Tools PRO Legendas."}
