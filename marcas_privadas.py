"""Nomes de cliente, marca e pessoa NÃO moram neste repositório, que é público.

A lista fica só na máquina do autor (~/.config/editor-automatico/marcas.json, ou
a variável MARCAS_PRIVADAS). O limpar-skills.py se recusa a rodar sem ela, e os
testes usam a parte genérica quando ela não existe, como no CI."""
import json
import os

VAZIO = {"trocas": [], "auditoria": "", "guia": "", "renomear": []}


def caminho():
    return os.environ.get("MARCAS_PRIVADAS") or os.path.expanduser("~/.config/editor-automatico/marcas.json")


def existe():
    return os.path.isfile(caminho())


def carregar():
    if not existe():
        return dict(VAZIO)
    with open(caminho(), encoding="utf-8") as f:
        return dict(VAZIO, **json.load(f))
