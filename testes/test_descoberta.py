"""
Painel do Tools PRO ↔ Editor Automático: arquivo de descoberta e CORS.

- o arquivo nasce 0600, atômico, com porta/token/pid/versão, e só o dono apaga;
- `ler()` ignora arquivo de pid morto;
- CORS: origem "null"/"file://" passa SÓ nas rotas da conversa e SÓ com o
  token; rota fora da lista, origem estranha ou token errado saem sem
  Access-Control-Allow-Origin.

Servidor de verdade (ThreadingHTTPServer com o Handler do app) numa porta
efêmera; HOME num diretório temporário. Nenhuma chamada paga roda.

    .venv/bin/python -m unittest testes.test_descoberta -v
"""

import http.client
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import descoberta  # noqa: E402


class _Home(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="ea-desc-")
        self._env = mock.patch.dict(os.environ, {"HOME": self.home, "USERPROFILE": self.home})
        self._env.start()
        self.assertEqual(os.path.expanduser("~"), self.home)

    def tearDown(self):
        self._env.stop()
        shutil.rmtree(self.home, ignore_errors=True)


class Arquivo(_Home):
    def test_grava_com_campos_e_0600(self):
        p = descoberta.gravar(51234, "TOK", "9.9.9")
        self.assertEqual(p, os.path.join(self.home, ".editorblackbelt", "editor-automatico.json"))
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        for k in ("porta", "token", "pid", "versao", "iniciado_em", "app"):
            self.assertIn(k, d)
        self.assertEqual((d["porta"], d["token"], d["pid"], d["versao"]),
                         (51234, "TOK", os.getpid(), "9.9.9"))
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(os.stat(p).st_mode), 0o600)
        # nada de temporário largado na pasta
        sobra = [n for n in os.listdir(os.path.dirname(p)) if n.endswith(".tmp")]
        self.assertEqual(sobra, [])

    def test_regravar_substitui_inteiro(self):
        descoberta.gravar(1, "A", "1")
        descoberta.gravar(2, "B", "2")
        self.assertEqual(descoberta.ler()["token"], "B")

    def test_ler_ignora_pid_morto(self):
        filho = subprocess.Popen([sys.executable, "-c", "pass"])
        filho.wait()
        descoberta.gravar(1, "T", "1", pid=filho.pid)
        self.assertIsNone(descoberta.ler())
        descoberta.gravar(1, "T", "1")
        self.assertEqual(descoberta.ler()["pid"], os.getpid())

    def test_ler_arquivo_quebrado(self):
        os.makedirs(descoberta.pasta(), exist_ok=True)
        with open(descoberta.caminho(), "w") as f:
            f.write("{meio arquivo")
        self.assertIsNone(descoberta.ler())

    def test_so_o_dono_apaga(self):
        descoberta.gravar(1, "T", "1", pid=os.getpid() + 100000)
        self.assertFalse(descoberta.apagar())            # é de outra abertura
        self.assertTrue(os.path.exists(descoberta.caminho()))
        descoberta.gravar(1, "T", "1")
        self.assertTrue(descoberta.apagar())
        self.assertFalse(os.path.exists(descoberta.caminho()))
        self.assertFalse(descoberta.apagar())            # já não existe


class ModoServico(_Home):
    """O app de verdade subindo com --servico (sem janela), num HOME de sandbox."""

    def subir(self, ocioso="120"):
        env = dict(os.environ, HOME=self.home, USERPROFILE=self.home,
                   EDITOR_AUTOMATICO_OCIOSO=ocioso)
        p = subprocess.Popen([sys.executable, os.path.join(RAIZ, "app.py"), "--servico"],
                             cwd=RAIZ, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.addCleanup(lambda: p.poll() is None and p.kill())
        import time
        for _ in range(150):
            d = descoberta.ler()
            if d and d["pid"] == p.pid:
                return p, d
            time.sleep(0.1)
        p.kill()
        self.fail("o serviço não gravou a descoberta: " + p.stderr.read().decode()[-800:])

    def pedir(self, d, metodo, rota, cab=None):
        c = http.client.HTTPConnection("127.0.0.1", d["porta"], timeout=10)
        h = {"X-Token": d["token"], "Origin": "null"}
        h.update(cab or {})
        c.request(metodo, rota, body=b"{}" if metodo == "POST" else None, headers=h)
        r = c.getresponse()
        corpo = r.read()
        c.close()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, corpo

    def test_sobe_sem_janela_e_desliga_pelo_painel(self):
        p, d = self.subir()
        self.assertEqual(d["modo"], "servico")
        self.assertEqual(d["servico"][-1], "--servico")
        st, _, corpo = self.pedir(d, "GET", "/api/saude")
        self.assertEqual(json.loads(corpo)["modo"], "servico")
        st, cab, corpo = self.pedir(d, "POST", "/api/servico/desligar")
        self.assertEqual(st, 200)
        self.assertEqual(cab.get("access-control-allow-origin"), "null")
        self.assertEqual(p.wait(timeout=10), 0)
        self.assertFalse(os.path.exists(descoberta.caminho()))

    def test_desligar_sem_token_nao_desliga(self):
        p, d = self.subir()
        st, _, _ = self.pedir(d, "POST", "/api/servico/desligar", {"X-Token": "errado"})
        self.assertEqual(st, 403)
        self.assertIsNone(p.poll())

    def test_morre_sozinho_quando_o_painel_some(self):
        p, d = self.subir(ocioso="2")
        self.assertEqual(p.wait(timeout=15), 0)          # ninguém falou com ele
        self.assertFalse(os.path.exists(descoberta.caminho()))

    def test_servico_nao_sobe_por_cima_da_janela(self):
        descoberta.gravar(1, "JANELA", "1", modo="janela")      # pid deste teste: vivo
        env = dict(os.environ, HOME=self.home, USERPROFILE=self.home)
        p = subprocess.run([sys.executable, os.path.join(RAIZ, "app.py"), "--servico"],
                           cwd=RAIZ, env=env, capture_output=True, timeout=60)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(descoberta.ler()["token"], "JANELA")

    def test_app_com_janela_tira_o_servico(self):
        p, d = self.subir()
        self.assertTrue(descoberta.desligar_servico_vivo())
        self.assertEqual(p.wait(timeout=10), 0)


class Cors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        from http.server import ThreadingHTTPServer
        cls.app = app
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def pedir(self, metodo, rota, cab=None, corpo=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request(metodo, rota, body=corpo, headers=cab or {})
        r = c.getresponse()
        dados = r.read()
        c.close()
        return r.status, {k.lower(): v for k, v in r.getheaders()}, dados

    def test_preflight_rota_da_conversa(self):
        for origem in ("null", "file://"):
            st, cab, _ = self.pedir("OPTIONS", "/api/conversa", {
                "Origin": origem, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-token",
                "Access-Control-Request-Private-Network": "true"})
            self.assertEqual(st, 204)
            self.assertEqual(cab.get("access-control-allow-origin"), origem)
            self.assertIn("X-Token", cab.get("access-control-allow-headers", ""))
            self.assertEqual(cab.get("access-control-allow-private-network"), "true")

    def test_preflight_recusado_fora_da_conversa(self):
        for rota, origem in (("/api/servicos/chave", "null"), ("/api/projetos", "null"),
                             ("/api/conversa", "https://site-qualquer.com"),
                             ("/api/conversa", None)):
            cab = {"Access-Control-Request-Method": "POST"}
            if origem:
                cab["Origin"] = origem
            st, cab, _ = self.pedir("OPTIONS", rota, cab)
            self.assertEqual(st, 403, rota)
            self.assertNotIn("access-control-allow-origin", cab, rota)

    def test_saude_com_token(self):
        st, cab, corpo = self.pedir("GET", "/api/saude",
                                    {"Origin": "null", "X-Token": self.app.TOKEN})
        self.assertEqual(st, 200)
        d = json.loads(corpo)
        self.assertEqual((d["ok"], d["app"], d["pid"]), (True, "editor-automatico", os.getpid()))
        self.assertEqual(cab.get("access-control-allow-origin"), "null")

    def test_sem_token_nao_libera(self):
        st, cab, _ = self.pedir("GET", "/api/saude", {"Origin": "null", "X-Token": "errado"})
        self.assertEqual(st, 403)
        self.assertNotIn("access-control-allow-origin", cab)

    def test_rota_fora_da_lista_nao_libera_nem_com_token(self):
        st, cab, _ = self.pedir("GET", "/api/estilos",
                                {"Origin": "null", "X-Token": self.app.TOKEN})
        self.assertEqual(st, 200)                         # a janela do app continua usando
        self.assertNotIn("access-control-allow-origin", cab)

    def test_origem_estranha_nao_libera(self):
        st, cab, _ = self.pedir("GET", "/api/saude",
                                {"Origin": "http://evil.example", "X-Token": self.app.TOKEN})
        self.assertEqual(st, 200)
        self.assertNotIn("access-control-allow-origin", cab)

    def test_janela_nao_aceita_desligar(self):
        st, _, corpo = self.pedir("POST", "/api/servico/desligar",
                                  {"Origin": "null", "X-Token": self.app.TOKEN}, b"{}")
        self.assertEqual(st, 409)                         # app com janela: fecha pela janela
        self.assertIn("janela", json.loads(corpo)["erro"])

    def test_rotas_da_conversa(self):
        r = self.app._rota_da_conversa
        for ok in ("/api/saude", "/api/conversa", "/api/conversas", "/api/conversas/abc",
                   "/api/conversas/nova", "/api/tarefas/t1", "/api/tarefas/t1/cancelar",
                   "/api/conversas/abc/aprovacao", "/api/conversas/abc/arquivos",
                   "/api/conversas/abc/anexo", "/api/conversas/abc/limpar",
                   "/api/projetos/p1/etapa/imagens/aprovar",
                   "/api/projetos/p1/etapa/imagens/rejeitar",
                   "/api/ia", "/api/ia/escolher", "/api/skills"):
            self.assertTrue(r(ok), ok)
        for nao in ("/api/conversas/apagar/x", "/api/conversas/abc/outra",
                    "/api/tarefas/t1/outra", "/api/ia/chave",
                    "/api/projetos/p1/etapa/imagens/iniciar", "/api/projetos/p1/plano",
                    "/api/skills/instalar",
                    "/api/servicos/chave", "/api/arquivo", "/api/conta/sair", "/"):
            self.assertFalse(r(nao), nao)

    def test_janela_do_app_sem_origin_continua(self):
        st, cab, _ = self.pedir("GET", "/api/saude", {"X-Token": self.app.TOKEN})
        self.assertEqual(st, 200)
        self.assertNotIn("access-control-allow-origin", cab)


if __name__ == "__main__":
    unittest.main()
