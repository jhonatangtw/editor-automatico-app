"""Id de projeto vem da tela, do painel e da IA: `..` não pode apagar a pasta
inteira, e etapa em projeto que não existe não cria pasta-fantasma."""
import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import app  # noqa: E402
from nucleo import conversas, pipeline, projetos  # noqa: E402


class TestValidacao(unittest.TestCase):
    def test_ids_ruins(self):
        for ruim in ("..", "../x", "a/b", "a\\b", ".oculto", "", "  ", None, 5):
            self.assertFalse(projetos.valido(ruim), repr(ruim))
            if isinstance(ruim, str):
                with self.assertRaises(projetos.NaoEncontrado):
                    projetos.dir_projeto(ruim)
        self.assertTrue(projetos.valido("ad07-body-123456"))


class TestRotas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls._raizes = (projetos.RAIZ, conversas.RAIZ, getattr(conversas, "CASA", None))
        cls.base = os.path.join(cls.tmp, "Editor Automático")
        projetos.RAIZ = os.path.join(cls.base, "Projetos")
        conversas.RAIZ = os.path.join(cls.base, "Conversas")
        if hasattr(conversas, "CASA"):
            conversas.CASA = cls.base
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        projetos.RAIZ, conversas.RAIZ = cls._raizes[0], cls._raizes[1]
        if cls._raizes[2] is not None:
            conversas.CASA = cls._raizes[2]

    def pedir(self, rota, corpo=None, metodo=None):
        # http.client manda o caminho como está (sem resolver o "..")
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        dados = json.dumps(corpo).encode() if corpo is not None else None
        c.request(metodo or ("POST" if dados is not None else "GET"), rota, body=dados,
                  headers={"X-Token": app.TOKEN, "Content-Type": "application/json"})
        r = c.getresponse()
        bruto = r.read()
        c.close()
        return r.status, (json.loads(bruto) if bruto else None), r

    def test_ponto_ponto_nao_apaga_nada(self):
        os.makedirs(os.path.join(projetos.RAIZ, "meu-job-1"), exist_ok=True)
        os.makedirs(os.path.join(conversas.RAIZ, "conv-1"), exist_ok=True)
        st, r, _ = self.pedir("/api/projetos/../apagar", {})
        self.assertEqual(st, 404)
        self.assertNotIn("/", r["erro"])
        self.assertTrue(os.path.isdir(os.path.join(projetos.RAIZ, "meu-job-1")))
        self.assertTrue(os.path.isdir(os.path.join(conversas.RAIZ, "conv-1")))

    def test_get_com_id_ruim(self):
        st, r, _ = self.pedir("/api/projetos/../pipeline")
        self.assertEqual(st, 404)

    def test_etapa_em_projeto_inexistente_nao_cria_pasta(self):
        st, r, _ = self.pedir("/api/projetos/nao-existe-1/etapa/analise/iniciar", {})
        self.assertEqual(st, 404)
        self.assertEqual(r["erro"], "Projeto não encontrado.")
        self.assertFalse(os.path.exists(os.path.join(projetos.RAIZ, "nao-existe-1")))

    def test_rota_direta_tambem_recusa(self):
        with self.assertRaises(projetos.NaoEncontrado):
            app.rota_etapa_iniciar("fantasma-2", pipeline.ORDEM[0], {})
        self.assertFalse(os.path.exists(os.path.join(projetos.RAIZ, "fantasma-2")))

    def test_limpar_conversa_com_id_ruim(self):
        st, r, _ = self.pedir("/api/conversas/../limpar", {})
        self.assertIn(st, (400, 404))
        with self.assertRaises(ValueError):
            app.rota_limpar("..")

    def test_estatico_404_tem_tamanho(self):
        # sem Content-Length em HTTP/1.1 o cliente fica esperando o corpo
        st, _, r = self.pedir("/nao-existe.js")
        self.assertEqual(st, 404)
        self.assertEqual(r.getheader("Content-Length"), "0")


if __name__ == "__main__":
    unittest.main()
