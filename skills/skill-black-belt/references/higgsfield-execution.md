# EXECUÇÃO — Higgsfield MCP vs Manual

Depois de gerar os prompts (qualquer modo), existem dois caminhos de execução. **Manual é o padrão.** Só execute via MCP quando o usuário pedir explicitamente ("gera aí", "roda no Higgsfield", "executa") ou quando ele confirmar a oferta.

## Caminho 1 — MANUAL (padrão)

Entregar os prompts **inline no chat**, prontos pra colar na plataforma (Higgsfield UI, FAL, Kling, Veo, etc.):
- Modo AVATAR: blocos únicos autocontidos ≤2500 chars, cabeçalho com duração.
- Modo STORYBOARD: cenas no formato obrigatório.
- Modo EFFECTS: as 4 seções.
- Modo PHOTOREALISM: 1–3 prompts diretos.

Nunca gerar arquivo, a menos que pedido. No fim, ofereça a execução: "Quer que eu execute direto no Higgsfield?" — uma vez só, sem insistir.

## Caminho 2 — HIGGSFIELD MCP

Pré-check: os tools do Higgsfield precisam estar disponíveis (buscar com tool_search por "higgsfield generate video/image"). Se o MCP não estiver conectado, avise e siga no manual.

### Fluxo de execução

1. **Confirme escopo e custo antes de gastar créditos.** Diga quantas gerações serão disparadas (ex.: "6 blocos × Seedance 2.0"). Se o job for grande (>5 gerações), confirme antes. Cheque saldo com o tool de balance se houver dúvida.
2. **Suba a imagem-base:**
   - Imagem enviada no chat / arquivo local → `media_upload` (ou widget de upload).
   - URL externa → `media_import_url`.
   - Imagem gerada no próprio fluxo (modo PHOTOREALISM/STORYBOARD via `generate_image`) → usar o resultado direto como referência.
3. **Escolha o modelo:**
   - Vídeo de avatar falante / cenas do storyboard → **Seedance 2.0** (image-to-video, fala nativa) via `generate_video`. Confira modelos disponíveis com `models_explore` se houver dúvida de nome/versão.
   - Imagens (start frame, cenas 3D, produto) → **Nano Banana Pro** via `generate_image`.
4. **Parâmetros por bloco (modo AVATAR):**
   - `duration`: a duração estimada no cabeçalho do bloco (arredondar pro valor aceito).
   - `aspect_ratio`: o da imagem-base (nunca assumir 9:16).
   - Prompt: o bloco único autocontido inteiro. **Aspas simples na fala** (anti-422), sem travessão longo (—) nem reticências (…) no payload.
   - Áudio/fala ligado.
5. **Dispare em sequência, um bloco por vez.** Ao concluir, exiba com `job_display` e pergunte se aprova antes do próximo — assim um bug de geração (boca, voz extra, legenda) é corrigido no prompt antes de queimar créditos nos blocos seguintes. Se o usuário mandar "roda tudo", dispare todos e exiba no fim.
6. **Bug numa geração** → aplicar correção de `troubleshooting.md` no prompt e regerar SÓ aquele bloco.

### Pipeline completo (storyboard → imagem → vídeo)

Quando o usuário quiser o criativo 3D executado de ponta a ponta:
1. Storyboard aprovado (modo STORYBOARD).
2. `generate_image` (Nano Banana Pro) por cena — CHARACTER BIBLE no início de todo prompt.
3. Usuário aprova as imagens (consistência do personagem é o gate crítico — regerar cena que fugiu do CHARACTER BIBLE antes de animar).
4. `generate_video` (Seedance 2.0) por cena, imagem como start frame + nota de ANIMAÇÃO expandida (usar `effects-seedance.md` se a cena pedir efeitos).
5. Entregar os jobs com `job_display` e lembrar: legenda karaokê, fake UI e disclaimer são camada de EDIÇÃO (Premiere/CapCut), não entram na geração.

### Regras de segurança de créditos

- Nunca disparar gerações em massa sem confirmação explícita do escopo.
- Falha 422 → problema de payload (aspas/travessões/duração/aspect), não de conteúdo. Corrigir e tentar 1x. Ver `troubleshooting.md`.
- Falha repetida no mesmo bloco (2x) → parar, mostrar o erro e decidir junto com o usuário.
