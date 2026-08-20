#!/bin/bash
# Atalho de duplo-clique enquanto o instalador nativo não é gerado.
cd "$(dirname "$0")"
exec .venv/bin/python app.py
