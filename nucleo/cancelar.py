"""
Cancelar uma rodada de conversa — de verdade, não só na tela.

Só existe onde o app tem um PROCESSO para encerrar: a sessão do Claude Code
(`claude -p`) e a do Codex (`codex exec`). Nos caminhos por API (chave da
Anthropic, API da OpenAI) a resposta é um pedido HTTP em voo que o app não
consegue interromper do lado de cá — por isso lá a tarefa nunca se declara
cancelável e a tela não mostra o botão. Botão que "cancela" e deixa a IA
trabalhando por trás é pior do que não ter botão.

O que se perde ao cancelar: a mensagem não entra no histórico do app (a
conversa só é gravada no fim da rodada). A sessão do Claude/Codex pode ter
guardado o pedido do lado dela — se a sessão nem chegou a existir, a próxima
mensagem cai na recuperação de "sessão não encontrada", que já começa outra.
"""

import threading


class Cancelado(RuntimeError):
    """A pessoa pediu para parar. Não é erro: a tela mostra como cancelado."""


class Controle:
    """Liga a tarefa da tela ao processo que está respondendo."""

    ESPERA_KILL = 3.0          # segundos entre o pedido educado e o à força

    def __init__(self):
        self._trava = threading.Lock()
        self._proc = None
        self.pedido = False

    @property
    def cancelavel(self):
        with self._trava:
            return self._proc is not None and not self.pedido

    def vincular(self, proc):
        """Chamado logo depois do Popen. Se o cancelamento chegou ANTES do
        processo existir (clique rápido), ele já nasce encerrado."""
        with self._trava:
            self._proc = proc
            pedido = self.pedido
        if pedido:
            _encerrar(proc, self.ESPERA_KILL)

    def soltar(self):
        with self._trava:
            self._proc = None

    def cancelar(self):
        """Devolve True se havia o que encerrar (ou se vai haver)."""
        with self._trava:
            self.pedido = True
            proc = self._proc
        if proc is not None:
            _encerrar(proc, self.ESPERA_KILL)
        return True

    def encerrou(self, proc):
        """Fim do processo: solta o vínculo e, se foi por Cancelar, fecha os
        canos (ninguém vai ler o resto) e levanta Cancelado."""
        self.soltar()
        if self.pedido:
            for cano in (proc.stdout, proc.stderr):
                try:
                    cano and cano.close()
                except Exception:
                    pass
        self.conferir()

    def conferir(self):
        """Levanta Cancelado se a pessoa pediu para parar."""
        if self.pedido:
            raise Cancelado("Cancelado por você.")


def _descendentes(pid):
    """Filhos, netos… do processo (Mac/Linux). Servidores MCP, comandos que a
    IA mandou rodar. Sem isso, um neto órfão segura o cano de saída aberto e a
    leitura do lado de cá nunca termina — a tela continuaria "pensando"."""
    import os
    import subprocess
    if os.name != "posix":
        return []
    vistos, fila = [], [pid]
    while fila:
        p = fila.pop()
        try:
            r = subprocess.run(["pgrep", "-P", str(p)], capture_output=True,
                               text=True, timeout=5)
        except Exception:
            continue
        for x in r.stdout.split():
            if x.isdigit() and int(x) not in vistos:
                vistos.append(int(x))
                fila.append(int(x))
    return vistos


def _sinal(pids, sinal):
    import os
    for p in pids:
        try:
            os.kill(p, sinal)
        except Exception:
            pass


def _encerrar(proc, espera):
    """SIGTERM primeiro, no processo e em toda a descendência: o Claude Code e
    o Codex fecham o que abriram. Quem não sair em `espera` segundos vai à
    força. No Windows o CLI de npm roda dentro de um `.cmd`: encerrar só o
    Popen mataria o cmd.exe e deixaria o node de pé — `taskkill /T` leva a
    árvore inteira."""
    import os
    import signal
    import subprocess
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, timeout=10,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        return
    netos = _descendentes(proc.pid)
    try:
        proc.terminate()
    except Exception:
        return
    _sinal(netos, signal.SIGTERM)

    def _forcar():
        try:
            proc.wait(timeout=espera)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        _sinal(netos, getattr(signal, "SIGKILL", signal.SIGTERM))
    threading.Thread(target=_forcar, daemon=True).start()
