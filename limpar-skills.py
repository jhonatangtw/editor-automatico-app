#!/usr/bin/env python3
"""
Limpa o retrato das skills ANTES de ele virar parte do app.

As skills são escritas na máquina do autor, no meio de jobs reais — e carregam
o que é do autor e do cliente: caminho do Drive da casa, nome de produto de
cliente, o ID da voz clonada de alguém, um script que tira o token do MCP de
dentro do `claude mcp get`. O app vai para todo aluno e o repositório é
público: nada disso pode viajar.

Roda depois do rsync do `sincronizar-skills.sh`. Três passos:
  1. TIRA arquivos que só fazem sentido no job de origem;
  2. TROCA, em todo arquivo de texto, o que é pessoal por um equivalente
     genérico (marca de cliente -> MarcaA, caminho do Drive -> variável);
  3. AUDITA o resultado com os mesmos padrões do teste
     (testes/test_skills.py). Achou qualquer coisa: sai com erro e o
     retrato não vale — melhor travar aqui que publicar.

Uso:  python3 limpar-skills.py skills
"""

import os
import re
import shutil
import sys

# ---------------------------------------------------------------- 1. arquivos que não viajam

TIRAR = [
    # o registro do job 128_PG: prompts e pedidos de um cliente real
    "hooks-meat-hook/referencia",
    # prompt pronto de um cliente (o estilo continua documentado nas references)
    "motion-omni-vsl/scripts/promptC_01.txt",
]

# ---------------------------------------------------------------- 2. trocas

# (arquivo ou "*", padrão, troca, flags) — aplicadas em ordem
TROCAS = [
    # --- caminhos da máquina e do Drive da casa
    ("hooks-meat-hook/scripts/frames.py", r'PROJ = \(.*?\)\n',
     'PROJ = os.environ.get("HOOKS_JOB") or os.getcwd()   # pasta do job: export HOOKS_JOB="..."\n', re.S),
    ("hooks-meat-hook/scripts/export.py", r'J = \(.*?\)\n',
     'J = os.environ.get("HOOKS_JOB") or os.getcwd()   # pasta do job: export HOOKS_JOB="..."\n', re.S),
    ("*", r'os\.path\.expanduser\("~/\.npm-global/bin/higgsfield"\)',
     '(__import__("shutil").which("higgsfield") or "higgsfield")', 0),
    # o token do MCP é o do PRÓPRIO aluno, lido na hora — nunca gravado aqui
    ("hooks-meat-hook/scripts/pr.sh", r'^TK=\$\(cd /Users/[^\n]*$',
     lambda m: 'TK="${TOOLSPRO_TOKEN:-$(cd "$HOME" && claude mcp get toolspro-pr 2>&1 | '
               "sed -nE 's/.*Bearer ([^ ]+).*/\\1/p')}\"", re.M),
    ("hooks-meat-hook/scripts/premiere/ame3.js", r'E="/Users/[^"]+"',
     'E=Folder("~/Movies/HOOKS_EXPORT").fsName', 0),
    ("hooks-meat-hook/scripts/premiere/ame3.js", r'var DONE=\{[^}]*\};', 'var DONE={};', 0),
    ("motion-omni-vsl/scripts/gerar_lote_clean.py",
     r'REF_SOLO = os\.path\.expanduser\("[^"]+"\)',
     'REF_SOLO = os.environ.get("REF_PRODUTO", "ancoras/REF_produto.png")   # foto do produto, de frente', 0),
    ("motion-omni-vsl/scripts/gerar_lote_clean.py",
     r'REF_LABEL = os\.path\.expanduser\("[^"]+"\)',
     'REF_LABEL = os.environ.get("REF_ROTULO", "ancoras/REF_rotulo.png")   # close do rótulo', 0),

    # --- chaves: do ambiente do aluno, nunca de um arquivo da máquina do autor
    ("hooks-meat-hook/scripts/voz.py", r'^KEY = \[l\.split.*?\]\[0\]\n',
     lambda m: 'KEY = os.environ.get("ELEVENLABS_API_KEY") or ""   # export ELEVENLABS_API_KEY="..." antes de rodar\n'
               'if not KEY:\n    sys.exit("Defina ELEVENLABS_API_KEY (a mesma chave da aba Contas do Editor Automatico).")\n',
     re.M | re.S),
    ("*", r'Chaves em `~/\.config/hw-creative/\.env`\.',
     'Chaves: as que você conectou na aba Contas do Editor Automático (ou variáveis de ambiente).', 0),
    ("hooks-meat-hook/SKILL.md", r'Cofre tem 9/10 vagas ocupadas:',
     'O cofre de vozes da ElevenLabs tem poucas vagas:', 0),

    # --- o que mandava para fora do app (repositório e diagnóstico do autor)
    ("editor-automatico-de-broll/references/como-pedir-marcacoes.md",
     r'`/plugin marketplace add [^`]+`', 'vem com o Editor Automático (Ambiente › Skills do Claude)', 0),
    ("editor-automatico-de-broll/references/como-pedir-marcacoes.md",
     r'cd ~/Documents/[^\n]*diagnostico\.sh', '# no Editor Automático: aba Ambiente › Atualizar status', 0),

    # --- linhas que apontam para o registro do job que não viaja
    ("hooks-meat-hook/SKILL.md", r'Referência completa de um job real:[^\n]*\n', '', 0),
    ("hooks-meat-hook/SKILL.md", r'Os pedidos do editor nesse job[^\n]*\n', '', 0),
    ("hooks-meat-hook/SKILL.md", r'Documento para os editores:[^\n]*\n', '', 0),
    ("hooks-meat-hook/SKILL.md", r' \(ver memória [^)]*\)', '', 0),
    ("*", r'o Drive "H&W[^"]*"', 'o Drive compartilhado', 0),
    ("*", r'"(Drives compartilhados/)?H&W - Edi[^"]*"', '"<pasta do job>"', 0),

    # --- nome do job e do cliente
    ("*", r'\[230926\]\[OT\] 128_PG', '[DDMMAA][OT] NNN_XX', 0),
    ("*", r'128_PG', 'NNN_XX', 0),
    ("*", r'128PG', 'NNNXX', 0),
    ("*", r'(?i)leaftide', 'MarcaA', 0),
    ("*", r'(?i)memoflow', 'MarcaB', 0),
    ("*", r'(?i)linfaflow', 'MarcaC', 0),
    ("*", r'(?i)cardioflush', 'MarcaD', 0),

    # --- a casa
    ("*", r'\(HW Publishing\)', '(Editor Black Belt)', 0),
    ("*", r'HW Publishing', 'a equipe', 0),
    ("*", r' ?\bda H&W\b', '', 0),
    ("*", r' ?\bH&W\b', '', 0),
]

TEXTO = {".md", ".py", ".sh", ".js", ".jsx", ".json", ".txt", ".yaml", ".yml", ".html", ".css", ".csv", ".srt"}


# ---------------------------------------------------------------- 3. auditoria
# Os MESMOS padrões do teste. Mudou aqui, mude lá (o teste confere o retrato
# que está no repositório; este confere o que acabou de ser gerado).

PADROES = {
    "caminho pessoal": re.compile(r"/Users/|C:\\\\Users\\\\|jhonwill|~/Documents/|~/Library/CloudStorage|/Volumes/|hw-creative"),
    "segredo": re.compile(
        r"sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{12}|AIza[0-9A-Za-z_-]{20,}|ghp_[A-Za-z0-9]{20,}"
        r"|xox[abprs]-[A-Za-z0-9-]{10,}|hf_[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"
        r"|Bearer [A-Za-z0-9._-]{20,}"
        r"|(?i:(?:api[_-]?key|secret|token|senha|password))[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-]{12,}"),
    "link interno": re.compile(r"(?i)drive\.google|docs\.google|frame\.io|slack\.com|monday\.com|notion\.so|hstgr|hostinger"),
    "casa ou cliente": re.compile(
        r"\bH&W\b|\bHW Publishing\b|hw-publishing|LeafTide|Leaftide|CardioFlush|MemoFlow|LinfaFlow|GlucoJaro|Ameripel"
        r"|\bBifi\b|\bJonas\b|\bMarcelo\b|\bRoque\b|\bGuino\b|\bJhon\b|Jhonatan|jhonatangtw"),
    # ID de voz da ElevenLabs (20 caracteres alfanuméricos) colado numa linha que fala de voz
    "id de voz": re.compile(r"(?i)voi(?:ce|z)[^\n]{0,60}\b[A-Za-z0-9]{20}\b"),
}
PULAR = {".venv", "node_modules", ".git", "runs", "__pycache__"}

# O que é PÚBLICO numa skill específica e por isso não é achado. A do Reels
# leva o nome do autor do curso no título e no estilo ("o Reels do Jhon") —
# é a vitrine, não dado pessoal. Só a palavra exata, só naquela pasta: o resto
# (sobrenome, e-mail, caminho da máquina, cliente) continua barrado lá dentro.
# O teste testes/test_skills.py tem a MESMA lista.
PERMITIDO = {
    "editor-de-reels-do-jhon": {"casa ou cliente": re.compile(r"Jhon")},
}


def _permitido(rel, tipo, trecho):
    skill = rel.split(os.sep)[0]
    pad = PERMITIDO.get(skill, {}).get(tipo)
    return bool(pad and pad.fullmatch(trecho))


def auditar(raiz):
    achados = []
    for d, subs, arqs in os.walk(raiz):
        subs[:] = [s for s in subs if s not in PULAR]
        for a in arqs:
            p = os.path.join(d, a)
            try:
                with open(p, encoding="utf-8") as f:
                    t = f.read()
            except (UnicodeDecodeError, OSError):
                continue
            for tipo, pad in PADROES.items():
                for m in pad.finditer(t):
                    if _permitido(os.path.relpath(p, raiz), tipo, m.group(0)):
                        continue
                    linha = t.count("\n", 0, m.start()) + 1
                    achados.append((os.path.relpath(p, raiz), linha, tipo, m.group(0)[:60]))
    return achados


def limpar(raiz):
    trocas = 0
    for rel in TIRAR:
        alvo = os.path.join(raiz, rel)
        if os.path.isdir(alvo):
            shutil.rmtree(alvo)
            print("  tirei   %s/" % rel)
        elif os.path.isfile(alvo):
            os.remove(alvo)
            print("  tirei   %s" % rel)

    for d, subs, arqs in os.walk(raiz):
        subs[:] = [s for s in subs if s not in PULAR]
        for a in arqs:
            p = os.path.join(d, a)
            if os.path.splitext(a)[1].lower() not in TEXTO:
                continue
            rel = os.path.relpath(p, raiz)
            with open(p, encoding="utf-8") as f:
                antes = f.read()
            t = antes
            for qual, pad, troca, flags in TROCAS:
                if qual != "*" and qual != rel:
                    continue
                t = re.sub(pad, troca, t, flags=flags)
            if t != antes:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(t)
                trocas += 1
                print("  limpei  %s" % rel)
    return trocas


if __name__ == "__main__":
    raiz = sys.argv[1] if len(sys.argv) > 1 else "skills"
    n = limpar(raiz)
    achados = auditar(raiz)
    for rel, linha, tipo, trecho in achados:
        print("  x %s:%d  [%s]  %s" % (rel, linha, tipo, trecho), file=sys.stderr)
    if achados:
        print("x %d achado(s) no retrato — corrija as TROCAS antes de publicar." % len(achados),
              file=sys.stderr)
        sys.exit(1)
    print("  auditoria: limpo (%d arquivo(s) ajustado(s))" % n)
