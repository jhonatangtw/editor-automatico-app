#!/usr/bin/env python3
"""Gera web/GUIA-DE-COMANDOS.md a partir de web/guia.json.

O JSON é a fonte única: a tela "Guia de comandos" lê ele, e este documento é a
mesma coisa em texto, para imprimir, mandar para a equipe ou abrir fora do app.
O teste testes/test_guia.py falha se os dois se desencontrarem.

Uso:  python3 gerar-guia.py
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))


def skills_no_pacote():
    r = os.path.join(AQUI, "skills")
    try:
        return {n for n in os.listdir(r) if os.path.isdir(os.path.join(r, n))}
    except OSError:
        return set()


def visiveis(g, skills=None):
    """Grupo com `requer_skill` só aparece quando a skill VIAJA no app — a
    tela faz o mesmo filtro. Comando que pede skill que o aluno não tem é
    comando que não funciona."""
    skills = skills_no_pacote() if skills is None else skills
    return [gr for gr in g["grupos"] if not gr.get("requer_skill") or gr["requer_skill"] in skills]


def markdown(g):
    linhas = ["# %s — Editor Automático" % g["titulo"], "", g["intro"], "",
              "**Quem roda:** " + " · ".join("**%s** — %s" % (k, v) for k, v in g["legenda_ia"].items()), "",
              "**Nível:** " + " · ".join("**%s** — %s" % (k, v) for k, v in g.get("niveis", {}).items()), ""]
    for gr in visiveis(g):
        linhas += ["", "## %s" % gr["titulo"], "", gr["descricao"], ""]
        for c in gr["comandos"]:
            nivel = "*Nível: %s*" % c["nivel"] + (" · *Tempo: %s*" % c["tempo"] if c.get("tempo") else "")
            linhas += ["### %s" % c["titulo"], "", nivel, "",
                       "```text", c["comando"], "```", "",
                       "- **O que faz:** %s" % c["faz"],
                       "- **Quando usar:** %s" % c["quando"],
                       "- **Precisa:** %s" % "; ".join(c["precisa"]),
                       "- **Funciona com:** %s" % c["ia"],
                       "- **Por baixo:** %s" % ", ".join("`%s`" % u for u in c["usa"]), ""]
    return "\n".join(linhas).rstrip() + "\n"


if __name__ == "__main__":
    with open(os.path.join(AQUI, "web", "guia.json"), encoding="utf-8") as f:
        g = json.load(f)
    alvo = os.path.join(AQUI, "web", "GUIA-DE-COMANDOS.md")
    with open(alvo, "w", encoding="utf-8") as f:
        f.write(markdown(g))
    gs = visiveis(g)
    n = sum(len(gr["comandos"]) for gr in gs)
    print("%s: %d comandos em %d grupos" % (os.path.relpath(alvo, AQUI), n, len(gs)))
    for gr in g["grupos"]:
        if gr not in gs:
            print("  (fora até a skill %s entrar no pacote: %s)" % (gr["requer_skill"], gr["titulo"]))
