# O que trocar em templates/build.py para um upsell novo

O `build.py` é o do MarcaE (referência que funcionou, 811 linhas). Copie para `<job>/edicao/` e troque:

| onde (procure por) | o quê |
|---|---|
| docstring + `P = ...hyperframes/up1-MarcaE` | nome do projeto HyperFrames |
| `TEAL, YEL` | cor do rótulo do produto (medir no mockup) e o amarelo de destaque |
| `PRECO = {"A": ("15","139"), ...}` | preço por frasco e total de cada versão |
| `SUS(...)`, `DEP(...)`, `SEQ = [...]` | ordem dos blocos (S01.., PRECO_x, D01..) e qual _alin.json de cada depoente (v2 se refeito) |
| `NOMES` | nome e idade de cada depoente (nome completo nos primeiros, primeiro nome depois) |
| `CTA_FIXA` | quais depoentes recebem a CTA fixa (sem legenda) |
| `BROLL = [...]` | (cena, bloco, frase de entrada, frase de saída, fonte) — vem do `05_plano_edicao.md`; fontes `mf:` acervo, `tt:` TikTok, `ia:<cena>`, especiais `split`, `kit`, `mosaico` |
| `janelas()` | frases que ancoram kit, preço, garantia, contato, botão, amarelo, CTA fixa (achar(bloco, "frase")) |
| `MOCKS` / `kit9.png` | arquivos de mockup do produto |
| `FAST JOINT-RESTORING KIT` / `9 BOTTLES` | selo do kit (texto da copy) |
| `+1 (323) ...` / `support@...` | contato do briefing |
| `BREAKFAST/LUNCH/DINNER` | rótulos do split (se o produto tiver outra posologia) |
| `assets/graf/selo_garantia_1year.png`, `botao_get_triple_dose_alpha.png` | artes do usuário (copiar de templates/ ou trocar) |
| `MV, MF` | volume da trilha sob a fala / no card final (medir o bed: alvo ~20 dB abaixo da voz) |
| `IA_CFG`, `VID_REPROVADO` | janelas de corte de clipes de IA com defeito e cenas que ficam still |

`prep.py`: troca a lista de SFX (Baú), a trilha (`assets/music/bed.m4a`), os recortes do acervo (`broll/acervo/`) e do
TikTok. `render_3.sh`: troca `J` (pasta do job). `master.py`: troca o padrão de nome do entregável
(memória `nomenclatura-entregaveis-hw`).
