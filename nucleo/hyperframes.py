"""
HyperFrames — vídeo escrito em HTML e renderizado no computador do aluno.

É o motor dos Reels premium (talking head com legenda animada, cartões e
cenas). Precisa de quatro coisas, e cada uma tem uma armadilha:

  1. **Node 22 ou mais novo.** ⚠️ O `node` padrão da máquina pode ser velho (no
     Mac do autor é o 20, de um gerenciador de versões) e o CLI recusa com
     "requires Node.js >= 22". O app NÃO troca o Node padrão do aluno: procura
     um Node compatível (no Homebrew o `node@24` é *keg-only* — fica em
     `/opt/homebrew/opt/node@24/bin`, fora do PATH de propósito) e chama ESSE
     binário pelo caminho. Sem nenhum, instala o `node@24` (Mac) ou o Node LTS
     (Windows) — o `node@24` não mexe no `node` que já existe.

  2. **O pacote `hyperframes`, numa versão FIXA, numa pasta do app.**
     `~/.editorblackbelt/hyperframes`, sem sudo e sem tocar no npm global do
     aluno. ⚠️ Instalar com `npm -g` no prefixo do Homebrew criaria um
     `hyperframes` com `#!/usr/bin/env node` — que roda no Node PADRÃO, o velho,
     e quebra do mesmo jeito. Por isso o atalho em `~/.editorblackbelt/bin`
     chama o Node certo pelo caminho absoluto. ⚠️ O CLI se ATUALIZA sozinho em
     segundo plano; o atalho desliga isso (`HYPERFRAMES_NO_UPDATE_CHECK`), senão
     a versão fixada deixa de ser fixa no primeiro uso.

  3. **O Chrome sem janela que ele usa para fotografar cada quadro** (~190 MB,
     em `~/.cache/hyperframes/chrome`). `browser ensure` baixa uma vez.

  4. **FFmpeg/FFprobe** — os mesmos que o app já instala. Passamos o caminho
     explícito (`HYPERFRAMES_FFMPEG_PATH`) para ele não escolher outro.

E só conta como instalado quando um RENDER DE VERDADE funciona: um vídeo de 1
segundo, 320×180, num temporário, conferido no disco (e no ffprobe, quando
tem). "O npm terminou sem erro" já mentiu demais neste app.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time

from . import so

VERSAO = "0.8.134"          # a que foi testada com o app; Reparar volta para ela
NODE_MIN = 22


def _casa():
    return os.path.join(os.path.expanduser("~"), ".editorblackbelt")


def pasta():
    """Onde o pacote mora. `EDITOR_HF_PASTA` existe para teste num prefixo
    temporário — instalar de verdade sem encostar na máquina do autor."""
    return os.environ.get("EDITOR_HF_PASTA") or os.path.join(_casa(), "hyperframes")


def pasta_bin():
    return os.environ.get("EDITOR_HF_BIN") or os.path.join(_casa(), "bin")


def _arquivo_teste():
    return os.path.join(pasta(), "teste.json")


# ---------------------------------------------------------------- Node

def _candidatos_node():
    """Onde procurar um Node, do mais provável ao menos. A ordem importa: os
    keg-only do Homebrew vêm ANTES do PATH porque o PATH pode ter um Node velho
    na frente (gerenciador de versões, instalação antiga)."""
    c = []
    if so.WIN:
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
                     os.path.join(os.environ.get("LOCALAPPDATA") or "", "Programs")):
            if base:
                c.append(os.path.join(base, "nodejs", "node.exe"))
        if os.environ.get("NVM_SYMLINK"):
            c.append(os.path.join(os.environ["NVM_SYMLINK"], "node.exe"))
    else:
        for brew in ("/opt/homebrew", "/usr/local"):        # Apple Silicon, Intel
            for f in ("node@24", "node@22", "node"):
                c.append("%s/opt/%s/bin/node" % (brew, f))
    # todo `node` do PATH, não só o primeiro
    nome = "node.exe" if so.WIN else "node"
    for d in (os.environ.get("PATH") or "").split(os.pathsep):
        if d:
            c.append(os.path.join(d, nome))
    vistos, saida = set(), []
    for p in c:
        if p not in vistos and os.path.isfile(p):
            vistos.add(p)
            saida.append(p)
    return saida


_cache_versao = {}


def _versao_node(caminho):
    """(maior, "v24.20.0") ou None. Guardado por caminho+data: a tela de
    Ambiente reconfere a cada poucos segundos e não pode abrir processo à toa."""
    try:
        chave = (caminho, os.path.getmtime(caminho))
    except OSError:
        return None
    if chave in _cache_versao:
        return _cache_versao[chave]
    r = None
    try:
        p = so.run([caminho, "--version"], capture_output=True, text=True, timeout=10)
        m = re.match(r"v(\d+)\.", (p.stdout or "").strip())
        if m:
            r = (int(m.group(1)), p.stdout.strip())
    except Exception:
        r = None
    _cache_versao[chave] = r
    return r


def node_compativel():
    for p in _candidatos_node():
        v = _versao_node(p)
        if v and v[0] >= NODE_MIN:
            return {"node": p, "versao": v[1]}
    return None


def _npm_de(node):
    d = os.path.dirname(node)
    p = os.path.join(d, "npm.cmd" if so.WIN else "npm")
    return p if os.path.isfile(p) else (so.onde("npm") or "npm")


def _instalar_node(diz):
    """Node compatível sem trocar o padrão do aluno."""
    if so.WIN:
        if not so.onde("winget"):
            raise RuntimeError(
                "Precisa do Node 22 ou mais novo, e o winget não respondeu para "
                "instalar. Abra a Microsoft Store, instale o “Instalador de "
                "Aplicativo” e tente de novo.")
        acao = "upgrade" if so.onde("node") else "install"
        cmd = ["winget", acao, "-e", "--accept-package-agreements",
               "--accept-source-agreements", "--id", "OpenJS.NodeJS.LTS"]
    else:
        if not so.onde("brew"):
            raise RuntimeError(
                "Precisa do Node 22 ou mais novo, e sem o Homebrew não consigo "
                "instalar. Instale o Homebrew pela aba Ambiente e tente de novo.")
        # keg-only: não vira o `node` padrão, então nada do aluno quebra
        cmd = ["brew", "install", "node@24"]
    rc, fim = _rodar(cmd, None, diz, 20 * 60)
    if rc != 0 and not so.WIN:
        raise RuntimeError("Não consegui instalar o Node 24: " + fim)
    from . import caminho
    caminho.recarregar(com_shell=True)
    _cache_versao.clear()
    n = node_compativel()
    if not n:
        raise RuntimeError("Instalei o Node, mas não achei uma versão 22 ou mais "
                           "nova. Feche e abra o app e tente de novo.")
    return n


# ---------------------------------------------------------------- pacote

def cli():
    """O hyperframes.mjs instalado. `npm -g --prefix` usa `lib/node_modules`
    no Mac e `node_modules` direto no Windows — confere os dois."""
    for sub in (("lib", "node_modules"), ("node_modules",)):
        p = os.path.join(pasta(), *sub, "hyperframes", "bin", "hyperframes.mjs")
        if os.path.isfile(p):
            return p
    return None


def versao_instalada():
    c = cli()
    if not c:
        return None
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(c)), "package.json"),
                  encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return None


def ambiente(node, base=None):
    """O ambiente em que o CLI roda: Node certo na frente do PATH (o npm e o
    npx que ele chama por dentro têm `#!/usr/bin/env node`), sem
    autoatualização e com o FFmpeg do app."""
    env = dict(base if base is not None else os.environ)
    env["PATH"] = os.pathsep.join([os.path.dirname(node), env.get("PATH", "")])
    env["HYPERFRAMES_NO_UPDATE_CHECK"] = "1"
    env["HYPERFRAMES_NO_AUTO_INSTALL"] = "1"
    for nome, var in (("ffmpeg", "HYPERFRAMES_FFMPEG_PATH"),
                      ("ffprobe", "HYPERFRAMES_FFPROBE_PATH")):
        p = so.onde(nome)
        if p and not env.get(var):
            env[var] = p
    return env


def atalho():
    return os.path.join(pasta_bin(), "hyperframes.cmd" if so.WIN else "hyperframes")


def _escrever_atalho(node, js):
    """`hyperframes` no terminal, já com o Node certo. É o que o aluno (e a IA)
    chamam; `npx hyperframes` também funciona quando o Node padrão é 22+."""
    os.makedirs(pasta_bin(), exist_ok=True)
    alvo = atalho()
    if so.WIN:
        txt = ("@echo off\r\nsetlocal\r\n"
               "set HYPERFRAMES_NO_UPDATE_CHECK=1\r\nset HYPERFRAMES_NO_AUTO_INSTALL=1\r\n"
               "set \"PATH=%s;%%PATH%%\"\r\n"
               "\"%s\" \"%s\" %%*\r\n") % (os.path.dirname(node), node, js)
    else:
        q = lambda s: "'" + s.replace("'", "'\\''") + "'"
        txt = ("#!/bin/sh\n# Editor Automático: HyperFrames %s com o Node certo\n"
               "export HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1\n"
               "PATH=%s:\"$PATH\"; export PATH\n"
               "exec %s %s \"$@\"\n") % (VERSAO, q(os.path.dirname(node)), q(node), q(js))
    with open(alvo, "w", encoding="utf-8", newline="") as f:
        f.write(txt)
    if not so.WIN:
        os.chmod(alvo, 0o755)
    return alvo


def _rodar(cmd, env, diz, limite):
    """Roda mostrando a saída no log da tela, com teto de tempo. Devolve
    (código, últimas linhas) — a última linha é quase sempre o motivo."""
    diz = diz or (lambda _: None)
    diz("$ " + " ".join(os.path.basename(str(cmd[0])) if i == 0 else str(x)
                        for i, x in enumerate(cmd)))
    proc = so.popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL, text=True, bufsize=1, env=env,
                    encoding="utf-8", errors="replace")
    estourou = []

    def matar():
        estourou.append(1)
        try:
            proc.kill()
        except Exception:
            pass
    t = threading.Timer(limite, matar)
    t.start()
    ultimas = []
    try:
        for linha in proc.stdout:
            linha = linha.rstrip()
            if not linha or "[Render:trace]" in linha:
                continue
            ultimas = (ultimas + [linha])[-6:]
            diz(linha[:160])
        proc.wait()
    finally:
        t.cancel()
        try:
            proc.stdout.close()
        except Exception:
            pass
    if estourou:
        return 124, "demorou mais de %d min e eu parei" % (limite // 60)
    return proc.returncode, " | ".join(ultimas)[-400:]


# ---------------------------------------------------------------- teste

COMPOSICAO = """<!doctype html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=320, height=180">
<title>teste do Editor Automatico</title>
<style>
body{margin:0;background:#111}
#root{position:relative;width:100%;height:100%;overflow:hidden;background:#111}
#c{position:absolute;inset:0;background:linear-gradient(135deg,#e8b04a,#7a3cff)}
</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="320"
     data-height="180" data-duration="1" data-no-timeline>
  <div id="c" class="clip" data-start="0" data-duration="1"></div>
</div>
</body></html>
"""


def testar(ao_vivo=None, limite=240):
    """Renderiza 1 segundo de verdade e confere o arquivo. `data-no-timeline`
    porque sem GSAP o render esperaria 45 s por uma timeline que não vem — e o
    GSAP vem de CDN, que é rede, que é outro jeito de o teste mentir."""
    diz = ao_vivo or (lambda _: None)
    n = node_compativel()
    js = cli()
    if not n or not js:
        return _gravar_teste({"ok": False, "msg": "O HyperFrames não está instalado."})
    if not so.onde("ffmpeg"):
        return _gravar_teste({"ok": False, "msg": "Falta o FFmpeg — instale ele primeiro."})
    tmp = tempfile.mkdtemp(prefix="hf-teste-")
    saida = os.path.join(tmp, "teste.mp4")
    try:
        with open(os.path.join(tmp, "index.html"), "w", encoding="utf-8") as f:
            f.write(COMPOSICAO)
        diz("▸ renderizando 1 segundo de teste…")
        env = ambiente(n["node"])
        env["HYPERFRAMES_NO_TELEMETRY"] = "1"
        t0 = time.time()
        rc, fim = _rodar([n["node"], js, "render", tmp, "--output", saida,
                          "--quality", "draft", "--workers", "1"], env, diz, limite)
        seg = round(time.time() - t0, 1)
        tam = os.path.getsize(saida) if os.path.isfile(saida) else 0
        if rc != 0 or tam == 0:
            return _gravar_teste({"ok": False, "segundos": seg,
                                  "msg": "O render de teste falhou: " + (fim or "sem saída")})
        dur = _duracao(saida)
        if dur is not None and not (0.5 <= dur <= 1.5):
            return _gravar_teste({"ok": False, "segundos": seg,
                                  "msg": "O vídeo de teste saiu com %.2f s em vez de 1 s." % dur})
        return _gravar_teste({"ok": True, "segundos": seg, "bytes": tam, "duracao": dur,
                              "msg": "render de teste ok em %.0f s" % seg})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _duracao(arq):
    if not so.onde("ffprobe"):
        return None
    try:
        r = so.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", arq], capture_output=True, text=True, timeout=20)
        return float((r.stdout or "").strip())
    except Exception:
        return None


def _gravar_teste(r):
    r = dict(r, versao=versao_instalada(), quando=time.strftime("%Y-%m-%d %H:%M"))
    try:
        os.makedirs(pasta(), exist_ok=True)
        with open(_arquivo_teste(), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False)
    except OSError:
        pass
    return r


def ultimo_teste():
    try:
        with open(_arquivo_teste(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------- estado

def estado():
    """O que a tela mostra. ✓ só quando a versão fixada está instalada, o
    atalho existe E o último render de teste dessa versão funcionou."""
    v = versao_instalada()
    n = node_compativel()
    t = ultimo_teste()
    testado = bool(t and t.get("ok") and t.get("versao") == v)
    tem = bool(v == VERSAO and n and os.path.isfile(atalho()) and testado)
    if tem:
        rotulo = "%s · render ok" % v
    elif not v:
        rotulo = "" if n else "precisa do Node %d+" % NODE_MIN
    elif v != VERSAO:
        rotulo = "%s (o app usa %s — Reparar)" % (v, VERSAO)
    elif not n:
        rotulo = "%s · sem Node %d+" % (v, NODE_MIN)
    elif t and not t.get("ok"):
        rotulo = "%s · o render de teste falhou" % v
    else:
        rotulo = "%s · falta o render de teste" % v
    return {"tem": tem, "versao": v, "fixada": VERSAO, "rotulo": rotulo,
            "node": n and n["versao"], "teste": t,
            "instalavel": bool(n) or bool(so.onde(so.GERENCIADOR))}


def _tem_skills():
    return os.path.isfile(os.path.join(os.path.expanduser("~"), ".claude", "skills",
                                       "hyperframes", "SKILL.md"))


def instalar(ao_vivo=None):
    """Instala ou repara, na ordem: Node → pacote → atalho → Chrome → skills
    da HyperFrames (só se faltarem) → render de teste. Idempotente: rodar de
    novo numa máquina pronta só confere e testa."""
    diz = ao_vivo or (lambda _: None)
    if not so.onde("ffmpeg"):
        raise RuntimeError("O HyperFrames usa o FFmpeg para montar o vídeo. "
                           "Instale o FFmpeg (aqui mesmo, na aba Ambiente) e tente de novo.")

    n = node_compativel()
    if n:
        diz("▸ Node %s (%s)" % (n["versao"], n["node"]))
    else:
        diz("▸ nenhum Node %d+ nesta máquina — instalando um à parte (o seu Node "
            "padrão não muda)…" % NODE_MIN)
        n = _instalar_node(diz)
    node = n["node"]
    env = ambiente(node)

    if versao_instalada() != VERSAO:
        diz("▸ instalando o HyperFrames %s em %s…" % (VERSAO, pasta()))
        os.makedirs(pasta(), exist_ok=True)
        rc, fim = _rodar([_npm_de(node), "install", "-g", "--prefix", pasta(),
                          "--no-audit", "--no-fund", "--loglevel=error",
                          "hyperframes@" + VERSAO], env, diz, 15 * 60)
        if rc != 0 or versao_instalada() != VERSAO:
            raise RuntimeError("O npm não conseguiu instalar o HyperFrames: "
                               + (fim or "código %s" % rc))
    else:
        diz("▸ HyperFrames %s já instalado" % VERSAO)

    js = cli()
    _escrever_atalho(node, js)
    diz("▸ atalho: " + atalho())
    from . import caminho
    caminho.recarregar()

    diz("▸ conferindo o Chrome de render (a 1ª vez baixa ~190 MB)…")
    rc, fim = _rodar([node, js, "browser", "ensure"], env, diz, 20 * 60)
    if rc != 0:
        raise RuntimeError("Não consegui baixar o Chrome que o HyperFrames usa: " + fim)

    if not _tem_skills():
        diz("▸ instalando as skills da HyperFrames para o Claude/Codex…")
        rc, fim = _rodar([node, js, "skills"], env, diz, 10 * 60)
        if rc != 0:
            # não trava: o motor funciona sem elas, só a IA fica sem o manual
            diz("! as skills da HyperFrames não instalaram (%s) — siga sem elas" % fim)

    r = testar(diz)
    if not r.get("ok"):
        raise RuntimeError(r.get("msg") or "o render de teste falhou")
    diz("✓ " + r["msg"])
    return {"ok": True, "qual": "hyperframes", "versao": VERSAO, "teste": r}


def no_path(env):
    """Para as sessões de IA que o app abre: se o `node` padrão é velho demais,
    põe o Node compatível na frente — senão `npx hyperframes` responde
    "requires Node.js >= 22" na cara do aluno. Não muda nada se já serve."""
    n = node_compativel()
    if not n:
        return env
    nome = "node.exe" if so.WIN else "node"
    primeiro = None
    for d in (env.get("PATH") or "").split(os.pathsep):
        p = os.path.join(d, nome) if d else ""
        if p and os.path.isfile(p):
            primeiro = p
            break
    v = _versao_node(primeiro) if primeiro else None
    if not v or v[0] < NODE_MIN:
        env["PATH"] = os.pathsep.join([os.path.dirname(n["node"]), env.get("PATH", "")])
    return env
