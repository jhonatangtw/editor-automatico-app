# Editor Automático

App de mesa que edita criativo de b-roll do começo ao fim: decupa a fala, planeja
onde entra cada insert, gera o visual, **monta na sua timeline do Premiere** e
confere o resultado antes de liberar a exportação.

Roda na sua máquina, com as suas contas. O material não sobe para lugar nenhum
para ser transcrito — o Whisper roda local.

## Instalar (macOS)

1. Baixe o [instalador mais recente](https://github.com/jhonatangtw/editor-automatico-app/releases/latest/download/EditorAutomatico.dmg).
2. Arraste o **Editor Automático** para a pasta Aplicativos.
3. Na primeira abertura: **botão direito no app → Abrir → Abrir**. O app não é
   assinado com Developer ID, então o macOS avisa uma vez.

Atualizações aparecem sozinhas dentro do app — pill **⬆ Atualizar** no rodapé da
barra lateral.

## O plugin do Premiere

O app fala com o Premiere pela extensão **Editor Black Belt Tools PRO**. Sem ela
o app planeja, gera e confere arquivo, mas não escreve na timeline.

Instale por dentro do app: aba **Ambiente → Instalar plugin no Premiere**. Ou
baixe direto: [EditorBlackBeltToolsPRO-Instalador.zip](https://github.com/jhonatangtw/editor-black-belt-tools-pro/releases/latest/download/EditorBlackBeltToolsPRO-Instalador.zip).

Depois de instalar, reabra o Premiere e deixe o painel aberto em
**Janela → Extensões → Tools PRO**: a ponte só existe com o painel aberto.

## As 12 etapas

O app é uma máquina de estados. Cada etapa só roda com a anterior concluída, e
as que gastam crédito exigem aprovação escrita — concluído pode ser automático,
aprovado nunca é.

| # | Etapa | Gasta |
|---|---|---|
| 1 | Análise inicial | |
| 2 | Verificação da copy contra a fala | |
| 3 | Marcação da timeline | |
| 4 | **Aprovação do planejamento** (portão) | |
| 5 | Criação dos avatares | crédito |
| 6 | Imagens de b-roll | crédito |
| 7 | Aprovação das imagens (uma a uma) | |
| 8 | Animação dos b-rolls | crédito |
| 9 | Aprovação dos vídeos (um a um) | |
| 10 | Letterings, voz e legendas | crédito |
| 11 | **Montagem no Premiere** | |
| 12 | **Controle de qualidade** (portão) | |

## Para quem vai mexer no código

- `LEIA-ME.md` — arquitetura, decisões e as armadilhas que já custaram caro.
- `MANUAL.md` — o manual do usuário.
- A **regra de edição** (punch, cadência, marcador) mora na skill
  `editor-automatico-de-broll`, não aqui. `nucleo/skill.py` importa a de lá.

```bash
python3 -m venv .venv && .venv/bin/pip install pywebview keyring
.venv/bin/python app.py
```

Publicar uma versão: edite `version.json` e rode `./publicar.sh`.
