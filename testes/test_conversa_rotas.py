"""
As rotas que a tela nova da Conversa usa (app.py), batendo no servidor de
verdade numa porta livre, com as pastas de projetos e conversas em sandbox.

O que fica provado:
- a pesquisa da tarefa devolve só o que MUDOU desde a versão que a tela tem;
- o cartão de aprovação aparece quando aprovar libera gasto, NÃO aprova nada
  sozinho, e some depois do clique explícito em Aprovar (rota de sempre);
- aprovar fora de hora continua dando 409 (o portão não afrouxou);
- "@" acha arquivo sem acento e dentro da pasta do projeto;
- arquivo arrastado vira caminho dentro da conversa; /limpar zera a conversa;
- CLI velho que recusa `--include-partial-messages` é refeito sem a flag.
"""

import json
import os
import stat
import sys
import tempfile
import textwrap
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import app  # noqa: E402
from nucleo import conversa, conversas, pipeline, projetos  # noqa: E402


class Servidor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls._raizes = (projetos.RAIZ, conversas.RAIZ, getattr(conversas, "CASA", None))
        projetos.RAIZ = os.path.join(cls.tmp, "Projetos")
        conversas.RAIZ = os.path.join(cls.tmp, "Conversas")
        if hasattr(conversas, "CASA"):
            conversas.CASA = cls.tmp
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        projetos.RAIZ, conversas.RAIZ = cls._raizes[0], cls._raizes[1]
        if cls._raizes[2] is not None:
            conversas.CASA = cls._raizes[2]

    def pedir(self, rota, corpo=None, cru=None, cab=None):
        url = "http://127.0.0.1:%d%s" % (self.porta, rota)
        h = {"X-Token": app.TOKEN, "Content-Type": "application/json"}
        h.update(cab or {})
        dados = cru if cru is not None else (json.dumps(corpo).encode() if corpo is not None else None)
        req = urllib.request.Request(url, data=dados, headers=h,
                                     method="POST" if dados is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            corpo = json.loads(e.read())
            e.close()
            return e.code, corpo

    def projeto(self, nome="AD07 Body"):
        """Projeto sem passar pelo ffprobe: plano mínimo + pipeline novo."""
        pid = projetos._id(nome)
        d = projetos.dir_projeto(pid)
        os.makedirs(os.path.join(d, "broll"), exist_ok=True)
        projetos._gravar(projetos.caminho(pid, "plano.json"), {
            "job": nome, "fonte": {"body": os.path.join(self.tmp, "brutos", "body.mp4"),
                                   "duracao": 30, "largura": 1080, "altura": 1920},
            "beats": [{"tipo": "insert", "inicio": 1, "fim": 3}] * 5})
        projetos._gravar(projetos.caminho(pid, "pipeline.json"), pipeline.novo())
        return pid

    # ------------------------------------------------------------ tarefa
    def test_pesquisa_so_traz_o_que_mudou(self):
        tid = app.tarefa_nova("Conversando")
        app.tarefa_log(tid, {"tipo": "ferramenta", "nome": "Read", "estado": "rodando"})
        app.tarefa_log(tid, {"tipo": "parcial", "texto": "Ol"})
        st, t = self.pedir("/api/tarefas/%s?v=-1" % tid)
        self.assertEqual(st, 200)
        self.assertEqual(t["total"], 2)
        self.assertEqual([i for i, _ in t["novos"]], [0, 1])
        v = t["seq"]
        app.tarefa_log(tid, {"tipo": "parcial", "texto": "Olá", "indice": 1, "atualiza": True})
        st, t = self.pedir("/api/tarefas/%s?v=%d" % (tid, v))
        self.assertEqual(t["novos"], [[1, {"tipo": "parcial", "texto": "Olá"}]])
        self.assertNotIn("passos", t)
        # sem ?v= continua igual ao de antes (telas e bancas antigas)
        st, t = self.pedir("/api/tarefas/%s" % tid)
        self.assertEqual(len(t["passos"]), 2)
        self.assertNotIn("versoes", t)

    # ------------------------------------------------------------ aprovação
    def test_cartao_de_aprovacao_nao_aprova_sozinho(self):
        pid = self.projeto()
        cid = conversas.criar(projeto=pid)
        st, r = self.pedir("/api/conversas/%s/aprovacao" % cid)
        self.assertIsNone(r["cartao"])            # nada esperando aprovação

        # etapas 1–3 concluídas, o plano (4) entregue esperando aprovação
        est = projetos.estado_pipeline(pid)
        for eid in ("analise", "copy", "marcacao"):
            pipeline.marcar(est, eid, pipeline.CONCLUIDO)
        pipeline.marcar(est, "plano", pipeline.AGUARDANDO)
        projetos.gravar_pipeline(pid, est)

        # aprovar a etapa 4 libera "avatar", que gasta crédito
        st, r = self.pedir("/api/conversas/%s/aprovacao" % cid)
        c = r["cartao"]
        self.assertEqual((c["etapa"], c["libera"]), ("plano", "avatar"))
        # olhar o cartão não registrou aprovação nenhuma
        self.assertFalse(pipeline.aprovada(projetos.estado_pipeline(pid), "plano"))

        # gastar antes da aprovação: o portão segura (409), como sempre
        st, r = self.pedir("/api/projetos/%s/etapa/avatar/iniciar" % pid, {})
        self.assertEqual(st, 409)
        self.assertTrue(r["bloqueado"])

        # o clique explícito vai pela rota de sempre e grava quem/quando
        st, r = self.pedir("/api/projetos/%s/etapa/plano/aprovar" % pid,
                           {"nota": "aprovado pelo cartão da conversa"})
        self.assertEqual(st, 200)
        est = projetos.estado_pipeline(pid)
        self.assertTrue(pipeline.aprovada(est, "plano"))
        self.assertEqual(est["aprovacoes"][-1]["nota"], "aprovado pelo cartão da conversa")
        st, r = self.pedir("/api/conversas/%s/aprovacao" % cid)
        self.assertIsNone(r["cartao"])

    def test_cartao_traz_o_custo_das_imagens(self):
        pid = self.projeto("Custo")
        cid = conversas.criar(projeto=pid)
        est = projetos.estado_pipeline(pid)
        for eid in ("analise", "copy", "marcacao", "plano"):
            pipeline.marcar(est, eid, pipeline.CONCLUIDO)
        pipeline.marcar(est, "avatar", pipeline.AGUARDANDO)
        projetos.gravar_pipeline(pid, est)
        orc = {"inserts": 5, "motor_imagem": "nano_banana_pro", "motor_video": "kling3_0_turbo",
               "custo_imagem": 2, "custo_video": 7.5, "total": 47.5, "saldo": 820}
        with mock.patch.object(app.gerar, "orcamento", return_value=orc):
            st, r = self.pedir("/api/conversas/%s/aprovacao" % cid)
        c = r["cartao"]
        self.assertEqual(c["libera"], "imagens")
        self.assertEqual(c["custo"], {"itens": 5, "unitario": 2, "motor": "nano_banana_pro",
                                      "total": 10, "saldo": 820})

    def test_aprovar_fora_de_hora_continua_409(self):
        pid = self.projeto("Fora")
        st, r = self.pedir("/api/projetos/%s/etapa/imagens/aprovar" % pid, {"nota": "x"})
        self.assertEqual(st, 409)

    # ------------------------------------------------------------ "@", anexo, limpar
    def test_arroba_acha_sem_acento_na_pasta_do_projeto(self):
        pid = self.projeto("Busca")
        cid = conversas.criar(projeto=pid)
        d = projetos.dir_projeto(pid)
        with open(os.path.join(d, "decupagem-ação.md"), "w") as f:
            f.write("x")
        os.makedirs(os.path.join(d, ".git"), exist_ok=True)
        with open(os.path.join(d, ".git", "decupagem-acao.md"), "w") as f:
            f.write("x")
        st, r = self.pedir("/api/conversas/%s/arquivos?q=acao" % cid)
        self.assertEqual(st, 200)
        self.assertEqual([a["rel"] for a in r["arquivos"]], ["decupagem-ação.md"])

    def test_anexo_vira_caminho_e_limpar_zera(self):
        cid = conversas.criar()
        conteudo = b"\x89PNG\r\n" + b"0" * 5000
        st, r = self.pedir("/api/conversas/%s/anexo" % cid, cru=conteudo,
                           cab={"Content-Type": "application/octet-stream",
                                "X-Nome": "refer%C3%AAncia.png"})
        self.assertEqual(st, 200, r)
        self.assertTrue(r["caminho"].startswith(conversas.dir_conversa(cid)))
        self.assertEqual(r["nome"], "referência.png")
        with open(r["caminho"], "rb") as f:
            self.assertEqual(f.read(), conteudo)
        # o mesmo nome de novo não sobrescreve
        st, r2 = self.pedir("/api/conversas/%s/anexo" % cid, cru=b"x",
                            cab={"Content-Type": "application/octet-stream", "X-Nome": "refer%C3%AAncia.png"})
        self.assertNotEqual(r2["caminho"], r["caminho"])
        # e a miniatura sai pela rota de arquivo (anexos de conversa são permitidos)
        from urllib.parse import quote
        with urllib.request.urlopen("http://127.0.0.1:%d/api/arquivo?p=%s&t=%s"
                                    % (self.porta, quote(r["caminho"]), app.TOKEN)) as a:
            self.assertEqual(a.read(), conteudo)
        # nome com caminho não escapa da pasta
        st, r3 = self.pedir("/api/conversas/%s/anexo" % cid, cru=b"x",
                            cab={"Content-Type": "application/octet-stream", "X-Nome": "..%2F..%2Fsai.txt"})
        self.assertTrue(r3["caminho"].startswith(conversas.dir_conversa(cid)))

        conversas.gravar_mensagens(cid, [{"role": "user", "content": "oi"}])
        with open(conversas.caminho(cid, "sessao.txt"), "w") as f:
            f.write("sessao-velha")
        st, r = self.pedir("/api/conversas/%s/limpar" % cid, {})
        self.assertTrue(r["ok"])
        self.assertEqual(conversas.mensagens(cid), [])
        self.assertFalse(os.path.exists(conversas.caminho(cid, "sessao.txt")))

    def test_conversa_traz_o_nome_do_projeto(self):
        pid = self.projeto("Nome Bonito")
        cid = conversas.criar(projeto=pid)
        st, r = self.pedir("/api/conversas/%s" % cid)
        self.assertEqual(r["meta"]["projeto_nome"], "Nome Bonito")

    def test_sem_token_nada_feito(self):
        url = "http://127.0.0.1:%d/api/conversas/x/arquivos?q=a" % self.porta
        with self.assertRaises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(url, timeout=5)
        self.assertEqual(e.exception.code, 403)
        e.exception.close()


@unittest.skipUnless(os.name == "posix", "o claude falso é um script com shebang")
class CliSemAFlag(unittest.TestCase):
    """Um `claude` velho que não conhece --include-partial-messages."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        b = os.path.join(self.tmp, "bin")
        os.makedirs(b)
        falso = os.path.join(b, "claude")
        with open(falso, "w") as f:
            f.write("#!%s\n" % sys.executable + textwrap.dedent("""
                import json, sys
                if "--include-partial-messages" in sys.argv:
                    sys.stderr.write("error: unknown option '--include-partial-messages'\\n")
                    sys.exit(1)
                for ev in ({"type": "system", "subtype": "init", "session_id": "s"},
                           {"type": "assistant", "message": {"content": [{"type": "text", "text": "OK"}]}},
                           {"type": "result", "is_error": False, "num_turns": 1, "usage": {}}):
                    print(json.dumps(ev), flush=True)
            """))
        os.chmod(falso, os.stat(falso).st_mode | stat.S_IEXEC)
        self._path = os.environ.get("PATH", "")
        os.environ["PATH"] = b + os.pathsep + self._path
        self._raiz = conversas.RAIZ
        conversas.RAIZ = os.path.join(self.tmp, "Conversas")
        self._ctx, self._mcp = conversa._contexto_ambiente, conversa._mcp_config
        conversa._contexto_ambiente = lambda pid: "contexto"
        conversa._mcp_config = lambda: "{}"
        self._aceita = conversa.PARCIAIS["aceita"]

    def tearDown(self):
        os.environ["PATH"] = self._path
        conversas.RAIZ = self._raiz
        conversa._contexto_ambiente, conversa._mcp_config = self._ctx, self._mcp
        conversa.PARCIAIS["aceita"] = self._aceita

    def test_refaz_sem_a_flag_e_lembra(self):
        conversa.PARCIAIS["aceita"] = True
        fala, passos, uso = conversa._sessao_claude("c-velho", None, "oi", None)
        self.assertEqual(fala, "OK")
        self.assertFalse(conversa.PARCIAIS["aceita"])
        self.assertEqual(uso["turnos"], 1)


if __name__ == "__main__":
    unittest.main()
