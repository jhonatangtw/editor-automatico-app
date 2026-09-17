"""
Preparar esta máquina — UM botão que instala tudo.

A tela de Ambiente tinha cinco botões para a mesma pergunta ("deixa este
computador pronto?"): Homebrew, "Instalar o que falta", cada opcional, as
skills e o plugin. E o "Instalar o que falta" decidia o que dava para instalar
OLHANDO A FOTO DO COMEÇO: sem Node na máquina, Claude e Higgsfield vinham como
"não instalável" e ficavam de fora — mesmo que o Node fosse instalado dois
passos antes. O aluno clicava, via "pronto", e faltava metade.

Aqui é uma fila só, na ordem de dependência, reconferindo o disco ANTES de cada
passo. O Homebrew e o instalador do plugin precisam de um Terminal de verdade
(senha de administrador, PlayerDebugMode) — o app abre o Terminal e FICA
OLHANDO até o resultado aparecer no disco, em vez de dizer "abri" e seguir.

Cada passo vira um item estruturado na tarefa (`passos`), para a tela mostrar
uma lista de checagem viva: o que já foi, o que está rodando, o que ficou
esperando o Terminal, o que não dava.
"""

import os
import time

from . import ambiente, caminho, plugin, ponte, skills, so

# Ordem de DEPENDÊNCIA, não a ordem da tela. Node antes de tudo que é npm;
# ffmpeg antes do whisper só porque é mais rápido de falhar (sem Homebrew).
ESSENCIAIS = ["node", "ffmpeg", "whisper", "claude", "higgsfield"]
OPCIONAIS = ["codex", "mmx", "ant", "heygen"]

# Quanto tempo esperar por um Terminal de fora antes de desistir do passo.
ESPERA_GERENCIADOR = 15 * 60     # o Homebrew baixa o Xcode CLT — demora mesmo
ESPERA_PLUGIN = 10 * 60


def plano(com_opcionais=True):
    """O que o botão VAI fazer nesta máquina, para a tela mostrar antes de
    começar. Sem isto o aluno clica e só descobre no meio que o Terminal vai
    pedir a senha dele."""
    d = ambiente.conferir()
    por_id = {i["id"]: i for i in d["itens"]}
    passos = []

    if not d["brew"]:
        passos.append({"id": "gerenciador", "nome": "Homebrew" if so.MAC else "winget",
                       "para": ("instala FFmpeg, Node e o resto — pede a senha do Mac "
                                "numa janela do Terminal") if so.MAC else
                               "vem pela Microsoft Store (Instalador de Aplicativo)",
                       "terminal": so.MAC, "manual": so.WIN, "tipo": "base"})

    for i in ESSENCIAIS + (OPCIONAIS if com_opcionais else []):
        it = por_id.get(i)
        if not it or it["tem"]:
            continue
        passos.append({"id": i, "nome": it["nome"], "para": it["para"],
                       "tipo": "essencial" if it["essencial"] else "opcional",
                       "manual": bool(it.get("manual"))})

    sk = skills.estado()
    if sk["faltam"]:
        passos.append({"id": "skills", "nome": "Skills do Claude",
                       "para": "%d de %d faltando na pasta do Claude"
                               % (len(sk["faltam"]), sk["total"]),
                       "tipo": "essencial"})

    pl = plugin.estado()
    if not pl["instalado"] or pl["tem_nova"]:
        passos.append({"id": "plugin", "nome": "Plugin do Premiere (Tools PRO)",
                       "para": ("atualizar para v%s" % pl["ultima"]) if pl["instalado"]
                               else "baixa ~100 MB e abre o instalador numa janela do Terminal",
                       "tipo": "opcional", "terminal": True})
    elif pl["instalado"] and not ponte.estado()["tem_debug"]:
        passos.append({"id": "ponte", "nome": "Ponte com o Premiere",
                       "para": "escreve a configuração que abre a porta do painel",
                       "tipo": "opcional"})

    prem = por_id.get("premiere")
    if prem and not prem["tem"]:
        passos.append({"id": "premiere", "nome": "Adobe Premiere Pro",
                       "para": "só pelo Creative Cloud — o app não instala",
                       "tipo": "opcional", "manual": True})

    return {"passos": passos, "sistema": so.SISTEMA,
            "abre_terminal": any(p.get("terminal") for p in passos),
            "nada": not [p for p in passos if not p.get("manual")]}


class _Lista:
    """A lista de checagem que a tela desenha. Cada passo é publicado na hora em
    que entra na fila e atualizado no lugar quando muda de estado — a tela nunca
    fica sem saber o que está acontecendo."""

    def __init__(self, ao_vivo):
        self.diz = ao_vivo or (lambda _: None)
        self.itens = []

    def novo(self, id_, nome):
        p = {"id": id_, "nome": nome, "estado": "fila", "nota": ""}
        self.itens.append(p)
        self.diz(dict(p))
        return len(self.itens) - 1

    def poe(self, i, estado, nota=""):
        p = self.itens[i]
        p["estado"], p["nota"] = estado, nota
        self.diz(dict(p, atualiza=True, indice=i))


def _esperar(pronto, segundos, diz, rotulo):
    """Fica olhando o disco até `pronto()` responder, ou o tempo acabar.
    Relê o PATH com o shell a cada volta: o instalador pode ter escrito uma
    linha nova no perfil, e é de lá que sai o PATH de verdade."""
    fim = time.time() + segundos
    n = 0
    while time.time() < fim:
        time.sleep(5)
        n += 1
        caminho.recarregar(com_shell=(n % 6 == 0))
        if pronto():
            return True
        if n % 12 == 0:
            diz("ainda esperando o %s terminar no Terminal… (%d min)"
                % (rotulo, int((time.time() - (fim - segundos)) / 60)))
    return False


def rodar(com_opcionais=True, com_plugin=True, ao_vivo=None):
    diz = ao_vivo or (lambda _: None)
    lista = _Lista(ao_vivo)
    resumo = {"instalados": [], "pulados": [], "erros": [], "aguardando": []}

    # ---------------------------------------------------------- 1. gerenciador
    d = ambiente.conferir()
    if not d["brew"]:
        i = lista.novo("gerenciador", "Homebrew" if so.MAC else "winget")
        if so.WIN:
            lista.poe(i, "manual", "instale o “Instalador de Aplicativo” pela "
                                   "Microsoft Store e rode de novo")
            resumo["pulados"].append("winget")
        else:
            lista.poe(i, "terminal", "o Terminal abriu — digite a senha do Mac lá")
            r = ambiente.instalar_gerenciador()
            if not r.get("ok"):
                lista.poe(i, "erro", r.get("msg", "")[:160])
                resumo["erros"].append("Homebrew: " + r.get("msg", ""))
            elif _esperar(lambda: so.onde("brew") is not None,
                          ESPERA_GERENCIADOR, diz, "Homebrew"):
                lista.poe(i, "ok", "instalado")
                resumo["instalados"].append("Homebrew")
            else:
                lista.poe(i, "aguardando", "não vi terminar — quando concluir, "
                                           "clique em Preparar de novo")
                resumo["aguardando"].append("Homebrew")

    # ---------------------------------------------------------- 2. programas
    fila = ESSENCIAIS + (OPCIONAIS if com_opcionais else [])
    for qual in fila:
        # reconferir ANTES de decidir: o passo anterior pode ter trazido o Node,
        # e é isso que torna Claude/Higgsfield instaláveis agora
        atual = {x["id"]: x for x in ambiente.conferir()["itens"]}.get(qual)
        if not atual or atual["tem"]:
            continue
        i = lista.novo(qual, atual["nome"])
        if atual.get("manual") and not atual.get("instalavel"):
            lista.poe(i, "manual", atual["manual"])
            resumo["pulados"].append(atual["nome"])
            continue
        if not atual.get("instalavel"):
            falta = ("Homebrew" if qual in ("ffmpeg", "node", "ant") and so.MAC
                     else "winget" if qual in ("ffmpeg", "node") else "Node.js")
            lista.poe(i, "pulado", "precisa do %s primeiro" % falta)
            resumo["pulados"].append(atual["nome"])
            continue
        lista.poe(i, "rodando", "instalando…")
        try:
            r = ambiente.instalar(qual, diz)
            if r.get("ok"):
                lista.poe(i, "ok", "instalado")
                resumo["instalados"].append(atual["nome"])
            else:
                lista.poe(i, "erro", "rodou sem erro, mas não encontro o programa — "
                                     "veja o log")
                resumo["erros"].append(atual["nome"] + ": não apareceu depois de instalar")
        except Exception as e:
            lista.poe(i, "erro", str(e)[:200])
            resumo["erros"].append("%s: %s" % (atual["nome"], e))

    # ---------------------------------------------------------- 3. skills
    sk = skills.estado()
    if sk["faltam"]:
        i = lista.novo("skills", "Skills do Claude")
        lista.poe(i, "rodando", "copiando %d…" % len(sk["faltam"]))
        try:
            r = skills.instalar(ao_vivo=diz)
            lista.poe(i, "ok", "%d instaladas" % r["novas"])
            resumo["instalados"].append("Skills do Claude")
        except Exception as e:
            lista.poe(i, "erro", str(e)[:200])
            resumo["erros"].append("Skills: %s" % e)

    # ---------------------------------------------------------- 4. plugin
    if com_plugin:
        pl = plugin.estado()
        if not pl["instalado"] or pl["tem_nova"]:
            i = lista.novo("plugin", "Plugin do Premiere (Tools PRO)")
            lista.poe(i, "rodando", "baixando o instalador…")
            antes = pl["instalado"]
            try:
                r = plugin.instalar(diz)
                if r.get("manual"):
                    lista.poe(i, "manual", r.get("msg", ""))
                    resumo["aguardando"].append("Plugin do Premiere")
                else:
                    lista.poe(i, "terminal", "o instalador está rodando no Terminal")
                    if _esperar(lambda: plugin.instalado() not in (None, antes),
                                ESPERA_PLUGIN, diz, "instalador do plugin"):
                        lista.poe(i, "ok", "instalado v%s" % plugin.instalado())
                        resumo["instalados"].append("Plugin do Premiere")
                    else:
                        lista.poe(i, "aguardando", "não vi terminar — se concluiu, "
                                                   "clique em Atualizar status")
                        resumo["aguardando"].append("Plugin do Premiere")
            except Exception as e:
                lista.poe(i, "erro", str(e)[:200])
                resumo["erros"].append("Plugin: %s" % e)

        # a ponte é o que faz o plugin ABRIR PORTA para o app. O instalador do
        # plugin apaga a pasta ao atualizar, então isto roda depois dele — e é
        # idempotente de propósito.
        if plugin.instalado() and not ponte.estado()["tem_debug"]:
            i = lista.novo("ponte", "Ponte com o Premiere")
            lista.poe(i, "rodando", "escrevendo a configuração…")
            try:
                r = ponte.preparar()
                lista.poe(i, "ok", "porta %d — feche e reabra o Premiere" % r["porta"])
                resumo["instalados"].append("Ponte com o Premiere")
                resumo["reiniciar_premiere"] = True
            except Exception as e:
                lista.poe(i, "erro", str(e)[:200])
                resumo["erros"].append("Ponte: %s" % e)

    # ---------------------------------------------------------- 5. só manual
    prem = {x["id"]: x for x in ambiente.conferir()["itens"]}.get("premiere")
    if prem and not prem["tem"]:
        i = lista.novo("premiere", "Adobe Premiere Pro")
        lista.poe(i, "manual", prem["manual"])
        resumo["pulados"].append("Adobe Premiere Pro")

    # quem diz se deu certo é a RECONFERÊNCIA, não a fila
    caminho.recarregar(com_shell=True)
    resumo["estado"] = ambiente.conferir()
    resumo["passos"] = lista.itens
    return resumo
