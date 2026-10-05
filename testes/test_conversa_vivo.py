"""
Conversa: a tela nunca fica muda, e Cancelar para DE VERDADE.

O defeito (gravação do curso, 0.21.1): a primeira mensagem levou ~2 min sem
nada na tela — o macOS pedia acesso à pasta Documentos e o app parecia
travado. Aqui ficam provados os pedaços do servidor: a etapa chega antes de
qualquer passo, Cancelar encerra o processo e a descendência dele, a tarefa
termina como "cancelada" (não "erro"), e a pasta de trabalho é tocada e
conferida num passo próprio.

Nada aqui chama o Claude de verdade: um "claude" falso no PATH faz o papel.
"""

import os
import stat
import sys
import tempfile
import textwrap
import threading
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import cancelar, conversa, conversas  # noqa: E402

POSIX = os.name == "posix"


def _vivo(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    # zumbi ainda responde ao kill 0; o `ps` diz se já morreu
    import subprocess
    r = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
    return bool(r.stdout.strip()) and not r.stdout.strip().startswith("Z")


def _esperar(cond, prazo=8.0):
    fim = time.time() + prazo
    while time.time() < fim:
        if cond():
            return True
        time.sleep(0.05)
    return cond()


@unittest.skipUnless(POSIX, "o claude falso é um script com shebang")
class CancelarSessao(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        self.pidneto = os.path.join(self.tmp, "neto.pid")
        falso = os.path.join(self.bin, "claude")
        with open(falso, "w") as f:
            f.write("#!%s\n" % sys.executable + textwrap.dedent("""
                import json, subprocess, sys, time
                print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
                # um neto, como um servidor MCP: tem que morrer junto
                neto = subprocess.Popen(["sleep", "60"])
                open(%r, "w").write(str(neto.pid))
                time.sleep(60)
            """ % self.pidneto))
        os.chmod(falso, os.stat(falso).st_mode | stat.S_IEXEC)

        self._path = os.environ.get("PATH", "")
        os.environ["PATH"] = self.bin + os.pathsep + self._path
        self._raiz = conversas.RAIZ
        conversas.RAIZ = os.path.join(self.tmp, "Conversas")
        self._ctx, self._mcp = conversa._contexto_ambiente, conversa._mcp_config
        conversa._contexto_ambiente = lambda pid: "contexto de teste"
        conversa._mcp_config = lambda: "{}"

    def tearDown(self):
        os.environ["PATH"] = self._path
        conversas.RAIZ = self._raiz
        conversa._contexto_ambiente, conversa._mcp_config = self._ctx, self._mcp
        try:
            with open(self.pidneto) as f:
                os.kill(int(f.read()), 9)
        except Exception:
            pass

    def test_cancelar_encerra_o_processo_e_o_neto(self):
        eventos, saida = [], {}
        ctl = cancelar.Controle()

        def rodar():
            try:
                conversa._sessao_claude("c1", None, "oi", eventos.append, controle=ctl)
                saida["fim"] = "voltou"
            except cancelar.Cancelado:
                saida["fim"] = "cancelado"
            except Exception as e:          # pragma: no cover — falha visível
                saida["fim"] = "erro: %r" % e

        th = threading.Thread(target=rodar, daemon=True)
        th.start()
        self.assertTrue(_esperar(lambda: os.path.exists(self.pidneto) and ctl.cancelavel),
                        "o claude falso não subiu")
        with open(self.pidneto) as f:
            neto = int(f.read())

        # a tela já tinha o que mostrar ANTES de qualquer passo da IA
        etapas = [e["texto"] for e in eventos if e.get("tipo") == "etapa"]
        self.assertIn("abrindo o Claude Code", etapas)
        self.assertTrue(any("Claude conectado" in t for t in etapas), etapas)

        t0 = time.time()
        ctl.cancelar()
        th.join(10)
        self.assertFalse(th.is_alive(), "a rodada não terminou depois do Cancelar")
        self.assertEqual(saida.get("fim"), "cancelado")
        self.assertLess(time.time() - t0, 6)
        self.assertFalse(ctl.cancelavel)
        self.assertTrue(_esperar(lambda: not _vivo(neto)), "o neto ficou de pé")

    def test_cancelar_antes_do_processo_existir(self):
        # clique rápido: o pedido chega antes do Popen — o processo já nasce morto
        ctl = cancelar.Controle()
        ctl.cancelar()
        with self.assertRaises(cancelar.Cancelado):
            conversa._sessao_claude("c2", None, "oi", None, controle=ctl)


class Controle(unittest.TestCase):

    def test_sem_processo_nao_e_cancelavel(self):
        # caminho por API: nada para encerrar, a tela não mostra o botão
        self.assertFalse(cancelar.Controle().cancelavel)

    def test_conferir_so_levanta_depois_do_pedido(self):
        c = cancelar.Controle()
        c.conferir()
        c.cancelar()
        with self.assertRaises(cancelar.Cancelado):
            c.conferir()


class TarefaNaTela(unittest.TestCase):
    """O que o app.py devolve para a tela enquanto a conversa roda."""

    @classmethod
    def setUpClass(cls):
        import app
        cls.app = app

    def test_etapa_nao_vira_passo(self):
        a = self.app
        tid = a.tarefa_nova("Conversando")
        a.tarefa_log(tid, {"tipo": "etapa", "texto": "abrindo o Claude Code"})
        t = a.tarefa_ver(tid)
        self.assertEqual(t["etapa"], "abrindo o Claude Code")
        self.assertEqual(t["passos"], [])
        self.assertFalse(t["cancelavel"])

    def test_cancelada_termina_como_cancelado_e_nao_erro(self):
        a = self.app
        ctl = cancelar.Controle()
        pronto = threading.Event()

        def trabalho(log):
            log({"tipo": "etapa", "texto": "esperando"})
            pronto.wait(5)
            ctl.conferir()
            return "não devia chegar aqui"

        tid = a.em_fundo("Conversando", trabalho, controle=ctl)
        self.assertEqual(a.tarefa_cancelar(tid), {"ok": True})
        pronto.set()
        self.assertTrue(_esperar(lambda: a.tarefa_ver(tid)["estado"] != "rodando"))
        t = a.tarefa_ver(tid)
        self.assertEqual(t["estado"], "cancelado")
        self.assertIsNone(t["erro"])
        self.assertFalse(t["cancelavel"])
        self.assertNotIn(tid, a.CONTROLES)

    def test_tarefa_sem_controle_nao_cancela(self):
        a = self.app
        tid = a.em_fundo("Outra", lambda log: time.sleep(0.2))
        self.assertFalse(a.tarefa_cancelar(tid)["ok"])


class PastaDeTrabalho(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._casa, self._raiz = conversas.CASA, conversas.RAIZ
        conversas.CASA = os.path.join(self.tmp, "Editor Automático")
        conversas.RAIZ = os.path.join(conversas.CASA, "Conversas")

    def tearDown(self):
        os.chmod(self.tmp, 0o755)
        conversas.CASA, conversas.RAIZ = self._casa, self._raiz

    def test_cria_a_pasta_e_nao_deixa_rastro(self):
        r = conversas.garantir_acesso()
        self.assertTrue(r["ok"], r)
        self.assertTrue(os.path.isdir(conversas.RAIZ))
        self.assertEqual(os.listdir(conversas.CASA), ["Conversas"])   # a prova foi apagada

    @unittest.skipUnless(POSIX and os.geteuid() != 0, "precisa de permissão de verdade")
    def test_sem_permissao_diz_que_foi_negado(self):
        os.chmod(self.tmp, 0o500)
        r = conversas.garantir_acesso()
        self.assertFalse(r["ok"])
        self.assertTrue(r["negado"])
        self.assertEqual(r["pasta"], conversas.CASA)


if __name__ == "__main__":
    unittest.main()
