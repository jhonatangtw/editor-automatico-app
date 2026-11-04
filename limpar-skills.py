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

import marcas_privadas

PRIVADAS = marcas_privadas.carregar()

# ---------------------------------------------------------------- 1. arquivos que não viajam

TIRAR = [
    "hooks-meat-hook/referencia",
    # prompt pronto de um cliente (o estilo continua documentado nas references)
    "motion-omni-vsl/scripts/promptC_01.txt",
    # exemplos visuais e builds de jobs reais: mostram produto e copy de cliente
    "upsell-premium-916/references/regua_tamanho_produto.png",   # frascos de cliente na imagem
    "upsell-premium-916/references/ref_price_reveal_premium",
    "upsell-premium-916/references/ref_caixas_envio_logo",
    "upsell-premium-916/references/ref_entrega_ups",
    "upsell-premium-916/references/ref_celular_tela_gerada",
    "upsell-premium-916/references/ref_dinamica_katana",
    "upsell-premium-916/templates/build_motor_storyboard.py",
    "upsell-agente/templates/build.py",
    # falas e prompts de anúncios reais
    "samurai/dr/referencias",
    "editor-senior-dr/references/biblioteca-referencias.md",
    "clone-ad-validado/templates/gerar_index_exemplo.py",
    "analise-criativo-ficha/references/exemplo-analise.json",
    "advalidado-weightloss/scripts/plano_broll.py",
    "advalidado-weightloss/scripts/build_hyperframes.py",
    "motion-omni-vsl/scripts/gerar_lote.py",
    "motion-omni-vsl/scripts/gerar_lote_clean.py",
    "hooks-meat-hook/scripts/anim.py",
    "hooks-meat-hook/scripts/frames.py",
    "upsell-agente/references/TROCAR_NO_BUILD.md",
    "upsell-premium-916/templates/build_motor_362bm.py",
    "upsell-premium-916/templates/build_referencia_345bm.py",
    # o Baú é só do autor: luz, trilha e SFX do kit saem dele ou de packs de
    # terceiros, e o prep.py lista os arquivos dele. O aluno usa o acervo próprio.
    "upsell-agente/templates/prep.py",
    "upsell-premium-916/templates/kit/luz",
    "upsell-premium-916/templates/kit/music",
    "upsell-premium-916/templates/kit/sfx",
    # só fala com o HWStudio da empresa, que o aluno não tem
    "upsell-premium-916/scripts/hws.py",
]

# ---------------------------------------------------------------- 2. trocas

# (arquivo ou "*", padrão, troca, flags) — aplicadas em ordem
AVISO_EXEMPLOS = ("\n> **Sobre os exemplos:** arquivos de jobs reais citados aqui (scripts de lote, build de exemplo, "
                  "fichas e análise preenchida) não acompanham o app, porque traziam material de cliente. Escreva os "
                  "seus seguindo as regras desta skill.\n")

TROCAS = [
    # nomes de marca, cliente e pessoa: lista fora do repositório público
    *[("*", pad, troca, 0) for pad, troca in PRIVADAS["trocas"]],
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

    # --- nome do job e do cliente

    # --- ferramentas de som: da máquina do autor para a do aluno
    ("real-sfx/SKILL.md", r'^> \*\*Nesta máquina[^\n]*\n',
     '> **No Editor Automático:** o FFmpeg instalado pelo app (aba Ambiente) já traz o que esta skill usa. A skill vem '
     'SEM biblioteca de sons: aponte a sua com `python scripts/setup.py init --library main="SUA_PASTA" --uisfx --index`. '
     'Só com `--uisfx`, ficam disponíveis apenas os sons de interface.\n', re.M),
    ("earshot/SKILL.md", r'^pip install -e "/Users/[^\n]*$',
     '# No Editor Automático: aba Ambiente > Earshot. O comando `earshot` fica disponível.', re.M),
    ("earshot/SKILL.md", r'"command": "/Users/[^"]*/python", "args": \["-m", "earshot", "mcp"\]',
     '"command": "earshot", "args": ["mcp"]', 0),
    ("earshot/SKILL.md", r'/Users/\S*?/\.venv/bin/python -m earshot', 'earshot', 0),
    ("real-sound/SKILL.md", r"the earshot repo's venv\n?\s*\(`<earshot repo>/\.venv/Scripts/python\.exe` on Windows, `<earshot repo>/\.venv/bin/python` elsewhere\)",
     "the Python of the earshot installed by Editor Automático\n(`uv tool dir`/earshot, `Scripts/python.exe` on Windows, `bin/python` elsewhere)", 0),

    # --- pacote de upsell: o que apontava para a casa
    ("_agentes/", r'[^\n]*`scripts/hws\.py`[^\n]*\n', '', 0),
    ("upsell-premium-916/SKILL.md", r'^- `hws\.py`[^\n]*\n', '', re.M),
    ("upsell-premium-916/SKILL.md", r'^- \*\*Versão nova = \.tsv novo no hws\.py\*\*[^\n]*\n', '', re.M),
    ("upsell-premium-916/SKILL.md", r'^- \*\*HWStudio da empresa[^\n]*\n', '', re.M),
    ("upsell-premium-916/SKILL.md", r'copiar `templates/kit/` para `assets/`, adaptar o build \(só o roteiro visual muda\)',
     'copiar `templates/kit/` para `assets/` e pôr em `assets/` a sua trilha, os seus SFX e os seus light leaks '
     '(o kit traz só fontes, grão e selo), escrever o build', 0),
    ("upsell-premium-916/SKILL.md", r'Dois builds de referência: .*?\)\. (?=Leia)',
     'Os builds de jobs reais não acompanham o app: escreva o seu com a skill `hyperframes`, seguindo o padrão abaixo. ', 0),
    ("upsell-premium-916/SKILL.md", r'^- Motor do storyboard:', '- Build montado a partir do storyboard:', re.M),
    ("upsell-premium-916/references/PADRAO_DINAMICA_KATANA.md", r'\*\*Implementação de referência:\*\*.*?não reinvente\.\n', '', re.S),
    ("upsell-premium-916/references/PADRAO.md", r'`kit/luz/lk0\.\.5\.mp4`', 'seus clipes de luz', 0),
    ("upsell-premium-916/references/PADRAO.md", r'trilha `kit/music/bed\.m4a`', 'sua trilha', 0),
    ("_agentes/", r'Builds de referência: `templates/build_motor_storyboard\.py`.*?\. Kit de assets',
     'Os builds de jobs reais não acompanham o app: escreva o build com a skill `hyperframes`. Kit de assets', 0),
    ("*", r' (?:\+|e o) build de referência em `?(?:references/)?ref_dinamica_katana/[^`\s,;)]*`?', '', 0),
    ("upsell-agente/SKILL.md", r'build\.py · prep\.py · master\.py · render_3\.sh \(copiar de templates/ e adaptar\)',
     'build.py e prep.py (escritos por você) · master.py e render_3.sh (copiar de templates/)', 0),
    ("upsell-agente/SKILL.md", r'`prep\.py` \(SFX do Baú, trilha, recortes 4:3, grão\), `build\.py <A\|B\|C>`',
     'um `prep.py` seu (SFX e trilha do seu acervo, recortes 4:3, grão), um `build.py <A|B|C>` seu', 0),
    ("upsell-agente/SKILL.md", r' O que trocar no build: ver `references/TROCAR_NO_BUILD\.md`\.', '', 0),
    ("*", r'biblioteca SFX-Bau-nucleo', 'a sua biblioteca', 0),
    ("*", r'\bBaú\b', 'seu acervo', 0),
    ("*", r'`?~/\.claude/projects/[^`\s]*regras-gerais-upsell\.md`?',
     '`~/.claude/skills/upsell-premium-916/references/REGRAS_GERAIS.md`', 0),
    ("_agentes/", r'`~/\.claude/skills/[^`]*`? ?\+? ?`?~/\.claude/projects/-Users-[^`\s]*`?', lambda m: m.group(0).split(' ')[0], 0),
    ("*", r'`?(?:references/)?ref_(?:price_reveal_premium|caixas_envio_logo|entrega_ups|celular_tela_gerada|dinamica_katana)/[^`\s,;)]*`?',
     '(exemplo visual que não acompanha o app)', 0),
    ("*", r'`real-sfx` com a biblioteca `[^`]*`(?: e `PATH="/opt/homebrew/opt/ffmpeg-full/bin:\$PATH"` na frente)?',
     '`real-sfx` com a biblioteca configurada no `setup.py`', 0),
    # operação interna da casa: fila de render, Controle, projetos vivos de cliente
    ("_agentes/", r'^- Mensagens ao Controle[^\n]*\n', '', re.M),
    ("_agentes/", r'^- Projetos vivos para copiar:[^\n]*\n', '', re.M),
    ("_agentes/", r' Projeto de referência: `[^`]*`\.?', '', 0),
    ("_agentes/", r' \+ projeto `~/Documents/01_Producao/_SAMURAI/[^`]*` \([^)]*\)', '', 0),
    ("_agentes/", r'^6\. Referências visuais:[^\n]*\n', '', re.M),
    ("_agentes/", r' e a imagem `regua_tamanho_produto\.png`', '', 0),
    ("*", r' e a imagem `regua_tamanho_produto\.png`', '', 0),
    ("_agentes/", r' \(o Jhon não lê inglês\)', '', 0),
    ("_agentes/", r', sempre com a vez do Controle', '', 0),
    ("_agentes/", r'prévia/pedir a vez', 'prévia/renderizar', 0),
    ("_agentes/", r'peça a vez de render', 'renderize', 0),
    ("_agentes/", r'pedir a vez de render', 'renderizar', 0),
    ("_agentes/", r', pedir vez na fila', '', 0),
    ("_agentes/", r'fontes, SFX, luz, trilha, grão, selo de garantia validado', 'fontes, grão, selo de garantia validado; luz, trilha e SFX são os seus', 0),
    ("_agentes/", r'memória `regras-gerais-upsell`', '`references/REGRAS_GERAIS.md` da skill upsell-premium-916', 0),
    ("_agentes/", r' \(node 24 em `/opt/homebrew/opt/node@24/bin`\)', '', 0),
    ("_agentes/", r'npx hyperframes', 'hyperframes', 0),
    ("upsell-premium-916/", r'npx hyperframes', 'hyperframes', 0),
    ("_agentes/", r'[^\n]*fichas-(?:microlead|vsl-upsell|criativos)\.md[^\n]*\n', '', 0),
    ("samurai/dr/padroes-de-formato.md", r' As fichas, com caminho de origem e medições, estão e[^\n]*', '', 0),
    *[(q, r'\Z', AVISO_EXEMPLOS, 0) for q in (
        "clone-ad-validado/SKILL.md", "analise-criativo-ficha/SKILL.md", "advalidado-weightloss/SKILL.md",
        "motion-omni-vsl/SKILL.md", "hooks-meat-hook/SKILL.md", "samurai/SKILL.md", "editor-senior-dr/SKILL.md")],
    ("_agentes/", r'`?editor-broll:marcar-vsl`?( → `?broll-narrativo`?)?( → `?fechar-lacunas`?)?( → `?conferir-broll`?)?', 'skill `editor-automatico-de-broll`', 0),
    ("*", r'~/\.config/hw-creative/\.env', 'ELEVENLABS_API_KEY (variável de ambiente)', 0),
    ("upsell-premium-916/scripts/", r'^K = \[l\.split.*?\]\[0\]\n',
     lambda m: 'K = os.environ.get("ELEVENLABS_API_KEY") or ""\n'
               'if not K:\n    sys.exit("Defina ELEVENLABS_API_KEY (a mesma chave da aba Contas do Editor Automatico).")\n',
     re.M | re.S),
    ("*", r'docs\.google\.com/document/d/<ID>', '<link do documento>', 0),

    # --- agente IA Creator (samurai e as exclusivas dele): o dono dos gates
    #     e das escolhas era o autor; no aluno, é o próprio aluno. Regras com
    #     pasta terminada em "/" valem para tudo dentro dela.
    *[(pasta, pad, troca, 0) for pasta in ("samurai/", "upsell-agente/", "upsell-premium-916/", "editor-senior-dr/", "_agentes/")
      for pad, troca in (
        (r'`~/Library/CloudStorage/[^`]*`', '`<pasta do Drive da equipe>`'),
        (r'`~/\.claude/projects/[^`]*`', '`a memória do Claude`'),
        (r'~/Documents/01_Producao/', '<pasta de trabalho>/'),
        (r'`~/Documents/[^`]*`', '`<arquivo local da referência>`'),
        (r'Frame\.io f\.io/\w+', 'ferramenta de revisão'),
        (r'\b([dn])o Frame\.io\b', lambda m: {'d': 'da', 'n': 'na'}[m.group(1)] + ' ferramenta de revisão'),
        (r'Frame\.io', 'ferramenta de revisão'),
        (r'\b\d{3}_[A-Z]{2}\b', 'NNN_XX'), (r'\b\d{3}[A-Z]{2}\b', 'NNNXX'), (r'\b\d{3}(?:bm|pg|da|mv)\b', 'NNNxx'),
        (r'\b(d|n|a|pel)o Jhon\b', r'\1o usuário'),
        (r'\bJhon\b', 'usuário'),
      )],
    ("upsell-agente/templates/render_3.sh", r'^J=/Users/\S+', 'J="${JOB:-$PWD}"   # pasta do job', re.M),
    ("upsell-agente/scripts/tts_lote.py", r'Chave em ~/\.config/hw-creative/\.env \(não imprimir\)',
     'Chave em ELEVENLABS_API_KEY (variável de ambiente; não imprimir)', 0),
    ("upsell-agente/scripts/tts_lote.py", r'^K = \[l\.split.*?\]\[0\]\n',
     lambda m: 'K = os.environ.get("ELEVENLABS_API_KEY") or ""\n'
               'if not K:\n    sys.exit("Defina ELEVENLABS_API_KEY (a mesma chave da aba Contas do Editor Automatico).")\n',
     re.M | re.S),
    # --- a casa
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
        r"\bJhon\b|Jhonatan|jhonatangtw" + ("|" + PRIVADAS["auditoria"] if PRIVADAS["auditoria"] else "")),
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
            # o NOME do arquivo também vaza: "Marca - box.png" nem texto tem
            for m in PADROES["casa ou cliente"].finditer(a):
                if not _permitido(os.path.relpath(p, raiz), "casa ou cliente", m.group(0)):
                    achados.append((os.path.relpath(p, raiz), 0, "casa ou cliente", m.group(0)[:60]))
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
    for de, para in PRIVADAS["renomear"]:
        if os.path.isfile(os.path.join(raiz, de)):
            os.replace(os.path.join(raiz, de), os.path.join(raiz, para))
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
                if qual != "*" and qual != rel and not (qual.endswith("/") and rel.startswith(qual)):
                    continue
                t = re.sub(pad, troca, t, flags=flags)
            if t != antes:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(t)
                trocas += 1
                print("  limpei  %s" % rel)
    return trocas


# ---------------------------------------------------------------- 2b. portão de crédito
# As skills nasceram fora do app e mandam rodar `higgsfield generate create`,
# `heygen video create`… direto. Dentro do app isso pula a aprovação — e a
# Conversa bloqueia esses comandos. O aviso no topo diz o caminho certo.

PAGO = re.compile(r"higgsfield generate|generate create|heygen (video|asset|avatar)|\bmmx \w|"
                  r"Higgsfield MCP|tools do Higgsfield")
MARCA_AVISO = "<!-- editor-automatico:portao-de-credito -->"
AVISO = (MARCA_AVISO + "\n"
         "> **No Editor Automático:** gerar imagem, vídeo, avatar ou voz que gasta crédito é feito "
         "**só pelas etapas do pipeline do app** (ferramenta `etapa_rodar` do MCP `editor`), que mostram "
         "o preço e esperam a aprovação do aluno. Os comandos de geração citados nesta skill "
         "(`higgsfield generate`, `heygen`, `mmx`) ficam bloqueados na Conversa — use-os só como "
         "referência de modelo, prompt e parâmetros. Preço e saldo: `motores_listar`.\n\n")


def avisar_portao(raiz):
    """Põe o aviso no SKILL.md de toda skill que ensina a gerar por fora."""
    n = 0
    for skill in sorted(os.listdir(raiz)):
        sk = os.path.join(raiz, skill, "SKILL.md")
        if not os.path.isfile(sk):
            continue
        ensina = False
        for d, subs, arqs in os.walk(os.path.join(raiz, skill)):
            subs[:] = [x for x in subs if x not in PULAR]
            for a in arqs:
                if os.path.splitext(a)[1].lower() not in TEXTO:
                    continue
                try:
                    with open(os.path.join(d, a), encoding="utf-8") as f:
                        if PAGO.search(f.read()):
                            ensina = True
                except (UnicodeDecodeError, OSError):
                    pass
        with open(sk, encoding="utf-8") as f:
            t = f.read()
        if not ensina or MARCA_AVISO in t:
            continue
        # logo depois do cabeçalho YAML (o `---` de fechamento)
        m = re.match(r"---\n.*?\n---\n\n?", t, re.S)
        corte = m.end() if m else 0
        t = t[:corte] + AVISO + t[corte:]
        with open(sk, "w", encoding="utf-8") as f:
            f.write(t)
        n += 1
        print("  aviso   %s/SKILL.md" % skill)
    return n


if __name__ == "__main__":
    if not marcas_privadas.existe():
        sys.exit("x falta a lista privada de marcas: %s" % marcas_privadas.caminho())
    raiz = sys.argv[1] if len(sys.argv) > 1 else "skills"
    n = limpar(raiz)
    avisar_portao(raiz)
    achados = auditar(raiz)
    for rel, linha, tipo, trecho in achados:
        print("  x %s:%d  [%s]  %s" % (rel, linha, tipo, trecho), file=sys.stderr)
    if achados:
        print("x %d achado(s) no retrato — corrija as TROCAS antes de publicar." % len(achados),
              file=sys.stderr)
        sys.exit(1)
    print("  auditoria: limpo (%d arquivo(s) ajustado(s))" % n)
