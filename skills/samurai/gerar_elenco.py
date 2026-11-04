"""Regera ~/.claude/agency/ELENCO.md a partir dos .md da agência."""
import os, re
BASE = os.path.expanduser('~/.claude/agency')
FORA = ('examples', 'integrations', 'scripts')
out = ["# Elenco da Agência (gerado de ~/.claude/agency)", "", "Formato: `caminho` — Nome — o que faz", ""]
total = 0
for d in sorted(os.listdir(BASE)):
    if d.startswith('.') or d in FORA or not os.path.isdir(os.path.join(BASE, d)):
        continue
    rows = []
    for root, _, fs in os.walk(os.path.join(BASE, d)):
        for f in sorted(fs):
            if not f.endswith('.md'):
                continue
            p = os.path.join(root, f)
            t = open(p, encoding='utf-8', errors='ignore').read(3000)
            m = re.match(r'---\n(.*?)\n---', t, re.S)
            nm = m and re.search(r'^name:\s*(.+)$', m.group(1), re.M)
            if not nm:
                continue
            ds = re.search(r'^description:\s*(.+)$', m.group(1), re.M)
            desc = (ds.group(1).strip().strip('"\'') if ds else '')[:160]
            rows.append(f"- `{os.path.relpath(p, BASE)}` — {nm.group(1).strip()} — {desc}")
    if rows:
        out += [f"## {d} ({len(rows)})"] + rows + [""]
        total += len(rows)
open(os.path.join(BASE, 'ELENCO.md'), 'w').write("\n".join(out))
print(f"{total} agentes no elenco")
