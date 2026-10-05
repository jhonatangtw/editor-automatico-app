"""
HyperFrames no Ambiente (0.21.3): Node certo, versão fixa, atalho, render de
teste. Tudo com subprocesso FALSO e pastas temporárias — nada é instalado,
nenhum Chrome abre, a máquina de quem roda o teste não é tocada.

    .venv/bin/python -m unittest testes.test_hyperframes -v
"""

import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import ambiente, preparar, so  # noqa: E402
from nucleo import hyperframes as hf  # noqa: E402


def ler(p, **kw):
    with open(p, **kw) as f:
        return f.read()


def _versao(mapa):
    """so.run falso que responde `node --version` conforme o caminho."""
    def run(cmd, **kw):
        return types.SimpleNamespace(stdout=mapa.get(cmd[0], "") + "\n", stderr="", returncode=0)
    return run


class Base(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hf-unit-")
        self.pasta = os.path.join(self.tmp, "hyperframes")
        self.bin = os.path.join(self.tmp, "bin")
        self.env = mock.patch.dict(os.environ, {"EDITOR_HF_PASTA": self.pasta,
                                                "EDITOR_HF_BIN": self.bin})
        self.env.start()
        hf._cache_versao.clear()

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)
        hf._cache_versao.clear()

    def fingir_pacote(self, versao=hf.VERSAO):
        d = os.path.join(self.pasta, "lib", "node_modules", "hyperframes")
        os.makedirs(os.path.join(d, "bin"), exist_ok=True)
        open(os.path.join(d, "bin", "hyperframes.mjs"), "w").close()
        with open(os.path.join(d, "package.json"), "w") as f:
            json.dump({"name": "hyperframes", "version": versao}, f)

    def fingir_node(self, nome="node24"):
        p = os.path.join(self.tmp, nome, "node")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()
        return p


class Node(Base):

    def test_prefere_o_node_compativel_ao_padrao_velho(self):
        velho, novo = self.fingir_node("node20"), self.fingir_node("node24")
        with mock.patch.object(hf, "_candidatos_node", return_value=[velho, novo]), \
             mock.patch.object(so, "run", _versao({velho: "v20.18.0", novo: "v24.20.0"})):
            self.assertEqual(hf.node_compativel(), {"node": novo, "versao": "v24.20.0"})

    def test_nenhum_node_22_ou_mais(self):
        velho = self.fingir_node("node20")
        with mock.patch.object(hf, "_candidatos_node", return_value=[velho]), \
             mock.patch.object(so, "run", _versao({velho: "v20.18.0"})):
            self.assertIsNone(hf.node_compativel())

    @unittest.skipIf(so.WIN, "caminhos do Homebrew")
    def test_keg_only_do_homebrew_vem_antes_do_path(self):
        with mock.patch("os.path.isfile", return_value=True), \
             mock.patch.dict(os.environ, {"PATH": "/x/bin"}):
            lista = hf._candidatos_node()
        self.assertEqual(lista[0], "/opt/homebrew/opt/node@24/bin/node")
        self.assertIn("/usr/local/opt/node@24/bin/node", lista)     # Mac Intel
        self.assertEqual(lista[-1], "/x/bin/node")

    def test_versao_do_node_fica_guardada(self):
        n = self.fingir_node()
        chamadas = []

        def run(cmd, **kw):
            chamadas.append(cmd)
            return types.SimpleNamespace(stdout="v24.1.0\n", stderr="", returncode=0)
        with mock.patch.object(so, "run", run):
            hf._versao_node(n)
            hf._versao_node(n)
        self.assertEqual(len(chamadas), 1)

    def test_sem_node_e_sem_homebrew_explica(self):
        with mock.patch.object(so, "WIN", False), mock.patch.object(so, "onde", return_value=None):
            with self.assertRaises(RuntimeError) as e:
                hf._instalar_node(None)
        self.assertIn("Homebrew", str(e.exception))

    def test_mac_instala_node24_keg_only(self):
        rodados = []
        novo = self.fingir_node()
        with mock.patch.object(so, "WIN", False), \
             mock.patch.object(so, "onde", side_effect=lambda b: "/opt/homebrew/bin/brew" if b == "brew" else None), \
             mock.patch.object(hf, "_rodar", side_effect=lambda c, e, d, l: rodados.append(c) or (0, "")), \
             mock.patch.object(hf, "node_compativel", return_value={"node": novo, "versao": "v24.0.0"}), \
             mock.patch("nucleo.caminho.recarregar"):
            hf._instalar_node(None)
        self.assertEqual(rodados, [["brew", "install", "node@24"]])

    def test_no_path_so_mexe_quando_o_padrao_e_velho(self):
        velho, novo = self.fingir_node("node20"), self.fingir_node("node24")
        run = _versao({velho: "v20.18.0", novo: "v24.20.0"})
        with mock.patch.object(hf, "node_compativel", return_value={"node": novo, "versao": "v24.20.0"}), \
             mock.patch.object(so, "run", run):
            env = hf.no_path({"PATH": os.path.dirname(velho)})
            self.assertEqual(env["PATH"].split(os.pathsep)[0], os.path.dirname(novo))
            env = hf.no_path({"PATH": os.path.dirname(novo)})
            self.assertEqual(env["PATH"], os.path.dirname(novo))


class Estado(Base):

    def setUp(self):
        super().setUp()
        self.n = mock.patch.object(hf, "node_compativel",
                                   return_value={"node": "/n/node", "versao": "v24.20.0"})
        self.n.start()

    def tearDown(self):
        self.n.stop()
        super().tearDown()

    def test_nada_instalado(self):
        e = hf.estado()
        self.assertFalse(e["tem"])
        self.assertIsNone(e["versao"])

    def test_instalado_sem_teste_nao_ganha_check(self):
        self.fingir_pacote()
        hf._escrever_atalho("/n/node", hf.cli())
        e = hf.estado()
        self.assertFalse(e["tem"])
        self.assertIn("falta o render de teste", e["rotulo"])

    def test_check_so_com_render_ok_da_mesma_versao(self):
        self.fingir_pacote()
        hf._escrever_atalho("/n/node", hf.cli())
        hf._gravar_teste({"ok": True, "msg": "ok"})
        self.assertTrue(hf.estado()["tem"])
        self.assertIn("render ok", hf.estado()["rotulo"])
        # pacote mudou de versão: o teste antigo não vale mais
        self.fingir_pacote("0.0.1")
        e = hf.estado()
        self.assertFalse(e["tem"])
        self.assertIn("Reparar", e["rotulo"])

    def test_teste_que_falhou_aparece(self):
        self.fingir_pacote()
        hf._escrever_atalho("/n/node", hf.cli())
        hf._gravar_teste({"ok": False, "msg": "x"})
        self.assertIn("falhou", hf.estado()["rotulo"])

    def test_item_na_tela_de_ambiente(self):
        self.fingir_pacote()
        it = ambiente._hyperframes()
        self.assertEqual(it["id"], "hyperframes")
        self.assertFalse(it["essencial"])
        self.assertEqual(it["acoes"], ["testar", "reparar"])

    def test_e_opcional_no_preparar(self):
        self.assertIn("hyperframes", preparar.OPCIONAIS)
        self.assertNotIn("hyperframes", preparar.ESSENCIAIS)


class Atalho(Base):

    def test_mac_chama_o_node_pelo_caminho_e_desliga_autoatualizacao(self):
        with mock.patch.object(so, "WIN", False):
            p = hf._escrever_atalho("/opt/homebrew/opt/node@24/bin/node", "/a b/hyperframes.mjs")
        t = ler(p)
        self.assertTrue(t.startswith("#!/bin/sh"))
        self.assertIn("exec '/opt/homebrew/opt/node@24/bin/node' '/a b/hyperframes.mjs' \"$@\"", t)
        self.assertIn("HYPERFRAMES_NO_UPDATE_CHECK=1", t)
        self.assertIn("HYPERFRAMES_NO_AUTO_INSTALL=1", t)
        self.assertTrue(os.access(p, os.X_OK))

    def test_windows_vira_cmd(self):
        with mock.patch.object(so, "WIN", True):
            p = hf._escrever_atalho(r"C:\Program Files\nodejs\node.exe", r"C:\x\hyperframes.mjs")
            self.assertTrue(p.endswith("hyperframes.cmd"))
        t = ler(p, newline="")
        self.assertIn('"C:\\Program Files\\nodejs\\node.exe" "C:\\x\\hyperframes.mjs" %*', t)
        self.assertIn("\r\n", t)
        self.assertIn("set HYPERFRAMES_NO_UPDATE_CHECK=1", t)

    def test_cli_acha_o_layout_do_windows(self):
        d = os.path.join(self.pasta, "node_modules", "hyperframes", "bin")
        os.makedirs(d)
        open(os.path.join(d, "hyperframes.mjs"), "w").close()
        self.assertTrue(hf.cli().endswith(os.path.join("node_modules", "hyperframes", "bin", "hyperframes.mjs")))

    def test_ambiente_do_cli(self):
        with mock.patch.object(so, "onde", side_effect=lambda b: "/bin/" + b):
            env = hf.ambiente("/n24/bin/node", {"PATH": "/usr/bin"})
        self.assertEqual(env["PATH"].split(os.pathsep)[0], "/n24/bin")
        self.assertEqual(env["HYPERFRAMES_FFMPEG_PATH"], "/bin/ffmpeg")
        self.assertEqual(env["HYPERFRAMES_FFPROBE_PATH"], "/bin/ffprobe")
        self.assertEqual(env["HYPERFRAMES_NO_UPDATE_CHECK"], "1")


class Teste(Base):

    def _render(self, conteudo=b"mp4", rc=0):
        def rodar(cmd, env, diz, limite):
            self.cmd = cmd
            self.html = ler(os.path.join(cmd[3], "index.html"))
            saida = cmd[cmd.index("--output") + 1]
            if conteudo is not None:
                with open(saida, "wb") as f:
                    f.write(conteudo)
            return rc, "fim"
        return rodar

    def rodar_teste(self, rodar, duracao=1.0):
        with mock.patch.object(hf, "node_compativel", return_value={"node": "/n/node", "versao": "v24"}), \
             mock.patch.object(hf, "_duracao", return_value=duracao), \
             mock.patch.object(so, "onde", side_effect=lambda b: "/bin/" + b), \
             mock.patch.object(hf, "_rodar", side_effect=rodar):
            return hf.testar()

    def test_render_ok(self):
        self.fingir_pacote()
        r = self.rodar_teste(self._render())
        self.assertTrue(r["ok"], r)
        self.assertEqual(self.cmd[2], "render")
        self.assertIn("--quality", self.cmd)
        self.assertIn('data-duration="1"', self.html)
        self.assertIn("data-no-timeline", self.html)
        self.assertNotIn("http", self.html.replace("http-equiv", ""))   # teste não depende de rede
        self.assertTrue(hf.ultimo_teste()["ok"])
        self.assertFalse(os.path.exists(self.cmd[3]), "o temporário fica para trás")

    def test_arquivo_vazio_reprova(self):
        self.fingir_pacote()
        r = self.rodar_teste(self._render(b""))
        self.assertFalse(r["ok"])
        self.assertIn("falhou", r["msg"])

    def test_sem_arquivo_reprova_mesmo_com_codigo_zero(self):
        self.fingir_pacote()
        self.assertFalse(self.rodar_teste(self._render(None))["ok"])

    def test_duracao_errada_reprova(self):
        self.fingir_pacote()
        r = self.rodar_teste(self._render(), duracao=5.0)
        self.assertFalse(r["ok"])
        self.assertIn("5.00", r["msg"])

    def test_sem_pacote(self):
        with mock.patch.object(hf, "node_compativel", return_value={"node": "/n", "versao": "v24"}):
            self.assertFalse(hf.testar()["ok"])

    def test_teste_que_falha_vira_erro_na_tela(self):
        with mock.patch.object(hf, "testar", return_value={"ok": False, "msg": "quebrou"}):
            with self.assertRaises(RuntimeError) as e:
                ambiente.instalar("hyperframes-teste")
        self.assertIn("quebrou", str(e.exception))


class Instalar(Base):

    def rodar(self, skills_ja=False, versao_antes=None, rc_npm=0):
        if versao_antes:
            self.fingir_pacote(versao_antes)
        cmds = []

        def rodar(cmd, env, diz, limite):
            cmds.append(cmd)
            if "install" in cmd and rc_npm == 0:
                self.fingir_pacote()
            return (rc_npm if "install" in cmd else 0), "erro do npm"
        with mock.patch.object(hf, "node_compativel", return_value={"node": "/n24/bin/node", "versao": "v24"}), \
             mock.patch.object(so, "onde", side_effect=lambda b: "/bin/" + b), \
             mock.patch.object(hf, "_rodar", side_effect=rodar), \
             mock.patch.object(hf, "_tem_skills", return_value=skills_ja), \
             mock.patch.object(hf, "testar", return_value={"ok": True, "msg": "ok"}) as t, \
             mock.patch("nucleo.caminho.recarregar"):
            r = hf.instalar()
        return r, cmds, t

    def test_ordem_versao_fixa_e_prefixo_do_app(self):
        r, cmds, t = self.rodar()
        self.assertTrue(r["ok"])
        npm = cmds[0]
        self.assertIn("install", npm)
        self.assertIn("-g", npm)
        self.assertEqual(npm[npm.index("--prefix") + 1], self.pasta)
        self.assertIn("hyperframes@" + hf.VERSAO, npm)
        self.assertEqual(cmds[1][2:], ["browser", "ensure"])
        self.assertEqual(cmds[2][2:], ["skills"])
        self.assertEqual(cmds[1][0], "/n24/bin/node")          # o Node certo, explícito
        t.assert_called_once()
        self.assertTrue(os.path.isfile(hf.atalho()))

    def test_idempotente_nao_reinstala_nem_reinstala_skills(self):
        r, cmds, _ = self.rodar(skills_ja=True, versao_antes=hf.VERSAO)
        self.assertTrue(r["ok"])
        self.assertEqual([c[2:] for c in cmds], [["browser", "ensure"]])

    def test_reparar_volta_para_a_versao_fixa(self):
        _, cmds, _ = self.rodar(skills_ja=True, versao_antes="0.0.1")
        self.assertIn("hyperframes@" + hf.VERSAO, cmds[0])

    def test_npm_falhou(self):
        with self.assertRaises(RuntimeError) as e:
            self.rodar(rc_npm=1)
        self.assertIn("npm", str(e.exception))

    def test_sem_ffmpeg_avisa_em_portugues(self):
        with mock.patch.object(so, "onde", return_value=None):
            with self.assertRaises(RuntimeError) as e:
                hf.instalar()
        self.assertIn("FFmpeg", str(e.exception))

    def test_render_de_teste_falhou_e_erro(self):
        with mock.patch.object(hf, "node_compativel", return_value={"node": "/n/node", "versao": "v24"}), \
             mock.patch.object(so, "onde", side_effect=lambda b: "/bin/" + b), \
             mock.patch.object(hf, "_rodar", return_value=(0, "")), \
             mock.patch.object(hf, "_tem_skills", return_value=True), \
             mock.patch.object(hf, "testar", return_value={"ok": False, "msg": "Chrome não abriu"}), \
             mock.patch("nucleo.caminho.recarregar"):
            self.fingir_pacote()
            with self.assertRaises(RuntimeError) as e:
                hf.instalar()
        self.assertIn("Chrome", str(e.exception))

    def test_ambiente_instalar_encaminha(self):
        with mock.patch.object(hf, "instalar", return_value={"ok": True}) as i:
            ambiente.instalar("hyperframes")
        i.assert_called_once()


class Rodar(Base):

    def test_limite_de_tempo_mata_o_processo(self):
        r = hf._rodar([sys.executable, "-c", "import time; print('oi', flush=True); time.sleep(30)"],
                      None, None, 1)
        self.assertEqual(r[0], 124)

    def test_devolve_as_ultimas_linhas(self):
        rc, fim = hf._rodar([sys.executable, "-c", "print('a'); print('motivo'); raise SystemExit(3)"],
                            None, None, 30)
        self.assertEqual(rc, 3)
        self.assertIn("motivo", fim)


if __name__ == "__main__":
    unittest.main()
