"""
Prévia das entregas de mídia na Conversa (0.22.1) — nucleo/midia.py + rotas.

O que fica provado, sem internet e sem gastar crédito:
- detecção: caminho com espaço e com `~`, arquivo que não existe fica de fora,
  do Higgsfield vale `result_url` (NUNCA `min_result_url`), `video_url` da
  HeyGen, mídia de ENTRADA (`params.medias`) não é entrega, sem repetir;
- segurança: `/etc/passwd`, `~/.ssh`, `../` e symlink para fora são recusados
  em `/api/arquivo` e nas rotas `/api/midia/*`; sem token, 403;
- Range: 206 com Content-Range/Accept-Ranges certos, sufixo `-N`, faixa
  inválida → 416, HEAD, Content-Type de vídeo;
- picos da onda a partir de um .wav gerado aqui (precisa do ffmpeg);
- download de entrega por um servidor HTTP LOCAL: vai para
  `<projeto>/media/<tipo>/`, nome estável, não baixa duas vezes, extensão
  pelo conteúdo, teto de tamanho, só http(s) — e NUNCA grava fora da pasta do
  projeto; conversa sem projeto recebe 409 "Em qual projeto salvar?";
- a regra da pasta do projeto vai no contexto de toda conversa.
"""

import io
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import app  # noqa: E402
from nucleo import conversa, conversas, midia, pipeline, projetos  # noqa: E402
from nucleo.leitor_stream import LeitorClaude  # noqa: E402

FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")
PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
       b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00"
       b"\x00\x00\x00IEND\xaeB`\x82")


def gerar_wav(caminho, seg=1.0, taxa=8000):
    """Seno com volume subindo: a onda tem forma (começo baixo, fim alto)."""
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        n = int(seg * taxa)
        w.writeframes(b"".join(struct.pack("<h", int(30000 * (i / n) * math.sin(2 * math.pi * 440 * i / taxa)))
                               for i in range(n)))


class Base(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.realpath(tempfile.mkdtemp())
        cls._antes = (projetos.RAIZ, conversas.RAIZ, conversas.CASA, midia.CACHE)
        projetos.RAIZ = os.path.join(cls.tmp, "Projetos")
        conversas.RAIZ = os.path.join(cls.tmp, "Conversas")
        conversas.CASA = cls.tmp
        midia.CACHE = os.path.join(cls.tmp, "cache")
        os.makedirs(projetos.RAIZ)
        os.makedirs(conversas.RAIZ)

    @classmethod
    def tearDownClass(cls):
        projetos.RAIZ, conversas.RAIZ, conversas.CASA, midia.CACHE = cls._antes
        midia.esquecer_raizes()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        midia.esquecer_raizes()

    def projeto(self, nome="AD07 Body", body=None):
        pid = projetos._id(nome) + str(len(os.listdir(projetos.RAIZ)))
        projetos._gravar(projetos.caminho(pid, "plano.json"), {
            "job": nome, "fonte": {"body": body or os.path.join(self.tmp, "brutos", "body.mp4"),
                                   "duracao": 30, "largura": 1080, "altura": 1920},
            "beats": []})
        projetos._gravar(projetos.caminho(pid, "pipeline.json"), pipeline.novo())
        midia.esquecer_raizes()
        return pid

    def arquivo(self, *partes, dados=b"x" * 100):
        c = os.path.join(*partes)
        os.makedirs(os.path.dirname(c), exist_ok=True)
        with open(c, "wb") as f:
            f.write(dados)
        return c


# ====================================================================== detecção
class Deteccao(Base):

    def test_caminho_com_espaco_til_e_inexistente(self):
        pid = self.projeto()
        a = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "cena 01 final.png")
        b = self.arquivo(projetos.dir_projeto(pid), "media", "videos", "hook.mp4")
        texto = ("Salvei as entregas:\n- %s\n- `%s`\n- /nao/existe/fantasma.png\n"
                 "e de novo %s (repetido)" % (a, b, a))
        ms = midia.detectar(texto)
        self.assertEqual([m.get("caminho") for m in ms], [a, b])
        self.assertEqual([m["tipo"] for m in ms], ["imagem", "video"])
        self.assertEqual(ms[0]["nome"], "cena 01 final.png")
        # "~" é expandido
        with mock.patch.dict(os.environ, {"HOME": self.tmp}):
            rel = "~/" + os.path.relpath(b, self.tmp)
            self.assertEqual([m["caminho"] for m in midia.detectar("veja " + rel)], [b])

    def test_frase_antes_do_caminho_nao_atrapalha(self):
        pid = self.projeto()
        a = self.arquivo(projetos.dir_projeto(pid), "media", "audio", "locução 1.mp3")
        ms = midia.detectar("texto/qualquer coisa e o áudio em %s pronto." % a)
        self.assertEqual([m["caminho"] for m in ms], [a])

    def test_higgsfield_result_url_e_nunca_a_miniatura(self):
        saida = json.dumps([{
            "id": "5cea", "status": "completed",
            "result_url": "https://cdn.exemplo.invalid/u/hf_2k.png",
            "min_result_url": "https://cdn.exemplo.invalid/u/hf_min.webp",
            "params": {"prompt": "x", "medias": [{"data": {"url": "https://cdn.exemplo.invalid/entrada.png"}}]},
        }])
        ms = midia.detectar(saida)
        self.assertEqual(ms, [{"tipo": "imagem", "url": "https://cdn.exemplo.invalid/u/hf_2k.png"}])

    def test_miniatura_fora_tambem_em_texto_que_nao_e_json(self):
        texto = ('job pronto: "min_result_url": "https://cdn.exemplo.invalid/a_min.jpg", '
                 '"result_url": "https://cdn.exemplo.invalid/a.mp4" — confira')
        ms = midia.detectar(texto)
        self.assertEqual([m["url"] for m in ms], ["https://cdn.exemplo.invalid/a.mp4"])

    def test_heygen_video_url_sem_thumbnail(self):
        saida = json.dumps({"data": {"status": "completed",
                                     "video_url": "https://files.exemplo.invalid/v/abc?Expires=1&Signature=z",
                                     "thumbnail_url": "https://files.exemplo.invalid/v/abc.jpg",
                                     "gif_url": "https://files.exemplo.invalid/v/abc.gif"}})
        ms = midia.detectar(saida)
        self.assertEqual(len(ms), 1)
        self.assertEqual(ms[0]["tipo"], "video")             # pela chave: a URL não tem extensão
        self.assertTrue(ms[0]["url"].startswith("https://files.exemplo.invalid/v/abc?"))

    def test_url_de_midia_no_texto_e_sem_repetir(self):
        t = ("Aqui: https://x.exemplo.invalid/a/b.mp3. E de novo https://x.exemplo.invalid/a/b.mp3?v=2 "
             "e uma página https://x.exemplo.invalid/sobre")
        ms = midia.detectar(t)
        self.assertEqual(ms, [{"tipo": "audio", "url": "https://x.exemplo.invalid/a/b.mp3"}])

    def test_caminho_dentro_de_url_nao_vira_arquivo_local(self):
        ms = midia.detectar("https://exemplo.invalid/etc/x.png", existe=lambda p: True)
        self.assertEqual([m.get("caminho") for m in ms], [None])

    def test_so_permitidas_e_leitor_injeta(self):
        pid = self.projeto()
        dentro = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "ok.png")
        fora = self.arquivo(self.tmp, "solto", "fora.png")
        ms = midia.detectar_permitidas("%s\n%s" % (dentro, fora))
        self.assertEqual([m["caminho"] for m in ms], [dentro])
        # o leitor do stream passa o resultado INTEIRO ao detector
        vistos = []
        lt = LeitorClaude(midias=lambda t: vistos.append(len(t)) or [{"tipo": "imagem", "caminho": dentro}])
        lt.evento({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}]}})
        grande = dentro + "\n" + "x" * 9000
        lt.evento({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": grande}]}})
        self.assertEqual(vistos, [len(grande)])
        self.assertEqual(lt.passos[0]["midias"], [{"tipo": "imagem", "caminho": dentro}])
        self.assertLess(len(lt.passos[0]["resultado"]), len(grande))    # o guardado é truncado

    def test_historico_antigo_ganha_previa_e_apagado_some(self):
        pid = self.projeto()
        a = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "antiga.png")
        b = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "apagada.png")
        msgs = [{"role": "assistant", "content": "Pronto: %s" % a},           # sem passos
                {"role": "assistant", "content": "x", "passos": [
                    {"tipo": "ferramenta", "nome": "Bash", "resultado": "salvo em %s" % b},
                    {"tipo": "texto", "texto": "e também %s" % a}]}]
        os.remove(b)
        midia.anotar(msgs)
        self.assertEqual([m["caminho"] for m in msgs[0]["midias"]], [a])
        self.assertNotIn("midias", msgs[1]["passos"][0])                    # arquivo apagado
        self.assertEqual([m["caminho"] for m in msgs[1]["passos"][1]["midias"]], [a])


# ====================================================================== segurança
class Seguranca(Base):

    def test_fora_das_pastas_e_recusado(self):
        pid = self.projeto()
        ok = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "a.png")
        self.assertTrue(midia.permitido(ok))
        self.assertFalse(midia.permitido("/etc/passwd"))
        self.assertFalse(midia.permitido(os.path.expanduser("~/.ssh/id_rsa")))
        self.assertFalse(midia.permitido(os.path.expanduser("~/.ssh/known_hosts")))
        subir = os.path.join(projetos.dir_projeto(pid), "..", "..", "..", "..", "..", "..", "etc", "passwd")
        self.assertFalse(midia.permitido(subir))
        self.assertFalse(midia.permitido(projetos.RAIZ))                    # pasta não é arquivo
        self.assertFalse(midia.permitido(""))
        self.assertFalse(midia.permitido("a\x00b"))

    def test_symlink_para_fora_nao_escapa(self):
        pid = self.projeto()
        link = os.path.join(projetos.dir_projeto(pid), "media", "imagens", "senha.png")
        os.makedirs(os.path.dirname(link), exist_ok=True)
        os.symlink("/etc/passwd", link)
        self.assertFalse(midia.permitido(link))

    def test_pasta_do_job_so_serve_midia_e_casa_nunca_e_raiz(self):
        job = os.path.join(self.tmp, "Jobs", "AD07")
        body = self.arquivo(job, "body.mp4")
        doc = self.arquivo(job, "contrato.pdf")
        img = self.arquivo(job, "refs", "ref.png")
        self.projeto("Job", body=body)
        with mock.patch.object(midia, "_temporaria", lambda p: False):
            midia.esquecer_raizes()
            self.assertTrue(midia.permitido(img))
            self.assertTrue(midia.permitido(body))
            self.assertFalse(midia.permitido(doc))                         # só mídia na pasta do job
        # body solto na casa do usuário: a casa NÃO vira raiz
        self.projeto("Solto", body=os.path.join(os.path.expanduser("~"), "body.mp4"))
        _, job_raizes = midia.raizes()
        self.assertNotIn(os.path.realpath(os.path.expanduser("~")), job_raizes)
        self.assertTrue(midia.larga_demais(os.path.expanduser("~/Downloads")))

    def test_pasta_escolhida_recusa_temporaria_downloads_e_conversa(self):
        self.assertIn("temporária", midia.pasta_valida_para_projeto(tempfile.gettempdir()))
        self.assertIn("PROJETO", midia.pasta_valida_para_projeto(os.path.expanduser("~/Downloads"))
                      if os.path.isdir(os.path.expanduser("~/Downloads")) else "PROJETO")
        cid = conversas.criar()
        with mock.patch.object(midia, "_temporaria", lambda p: False):
            self.assertIn("conversa", midia.pasta_valida_para_projeto(conversas.dir_conversa(cid)))


# ====================================================================== servidor
class Rotas(Base):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.porta = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        super().tearDownClass()

    def pedir(self, rota, metodo="GET", cab=None, corpo=None, token=True):
        h = {"X-Token": app.TOKEN} if token else {}
        h.update(cab or {})
        dados = json.dumps(corpo).encode() if corpo is not None else None
        if dados:
            h["Content-Type"] = "application/json"
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.porta, rota), data=dados,
                                     headers=h, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, dict((k.lower(), v) for k, v in r.headers.items()), r.read()
        except urllib.error.HTTPError as e:
            corpo_ = e.read()
            hs = dict((k.lower(), v) for k, v in e.headers.items())
            e.close()
            return e.code, hs, corpo_

    def arq_url(self, caminho, token=True):
        from urllib.parse import quote
        return "/api/arquivo?p=%s%s" % (quote(caminho), "&t=" + app.TOKEN if token else "")

    def test_arquivo_exige_token_e_recusa_fora(self):
        pid = self.projeto()
        ok = self.arquivo(projetos.dir_projeto(pid), "media", "videos", "a.mp4", dados=bytes(range(256)) * 4)
        st, h, corpo = self.pedir(self.arq_url(ok), token=False)
        self.assertEqual(st, 200)
        self.assertEqual(h["content-type"], "video/mp4")
        self.assertEqual(h["accept-ranges"], "bytes")
        self.assertEqual(len(corpo), 1024)
        self.assertEqual(self.pedir(self.arq_url(ok, token=False), token=False)[0], 403)
        for ruim in ("/etc/passwd", os.path.expanduser("~/.ssh/id_rsa"),
                     os.path.join(projetos.dir_projeto(pid), "..", "..", "..", "..", "..", "etc", "passwd"),
                     "../../../../etc/passwd"):
            st, _, corpo = self.pedir(self.arq_url(ruim), token=False)
            self.assertEqual(st, 404, ruim)
            self.assertEqual(corpo, b"")
            st, _, corpo = self.pedir("/api/midia/info?p=%s" % urllib.request.quote(ruim))
            self.assertEqual(st, 404, ruim)
            self.assertNotIn(b"root", corpo)
        # rota de mídia sem token também é 403
        st, _, _ = self.pedir("/api/midia/info?p=%s" % urllib.request.quote(ok), token=False)
        self.assertEqual(st, 403)

    def test_range_206_sufixo_e_416(self):
        pid = self.projeto()
        dados = bytes(range(256)) * 4
        ok = self.arquivo(projetos.dir_projeto(pid), "media", "videos", "r.mp4", dados=dados)
        u = self.arq_url(ok)
        st, h, corpo = self.pedir(u, token=False, cab={"Range": "bytes=10-19"})
        self.assertEqual(st, 206)
        self.assertEqual(corpo, dados[10:20])
        self.assertEqual(h["content-range"], "bytes 10-19/1024")
        self.assertEqual(h["content-length"], "10")
        self.assertEqual(h["accept-ranges"], "bytes")
        self.assertEqual(h["content-type"], "video/mp4")
        st, h, corpo = self.pedir(u, token=False, cab={"Range": "bytes=1000-"})
        self.assertEqual((st, corpo, h["content-range"]), (206, dados[1000:], "bytes 1000-1023/1024"))
        st, h, corpo = self.pedir(u, token=False, cab={"Range": "bytes=-24"})
        self.assertEqual((st, corpo), (206, dados[-24:]))
        st, h, corpo = self.pedir(u, token=False, cab={"Range": "bytes=0-99999"})
        self.assertEqual((st, len(corpo), h["content-range"]), (206, 1024, "bytes 0-1023/1024"))
        for ruim in ("bytes=2000-", "bytes=50-10", "bytes=abc", "bytes=0-1,5-9", "bytes=-0"):
            st, h, corpo = self.pedir(u, token=False, cab={"Range": ruim})
            self.assertEqual(st, 416, ruim)
            self.assertEqual(h["content-range"], "bytes */1024", ruim)
        # unidade desconhecida: ignora e serve inteiro
        st, _, corpo = self.pedir(u, token=False, cab={"Range": "linhas=1-2"})
        self.assertEqual((st, len(corpo)), (200, 1024))
        st, h, corpo = self.pedir(u, metodo="HEAD", token=False)
        self.assertEqual((st, h["content-length"], corpo), (200, "1024", b""))

    def test_rotas_da_midia_entram_no_cors_do_painel_mas_arquivo_nao(self):
        r = app._rota_da_conversa
        for ok in ("/api/midia/info", "/api/midia/picos", "/api/midia/quadro", "/api/midia/baixar",
                   "/api/midia/mostrar", "/api/midia/destinos", "/api/conversas/abc/destino"):
            self.assertTrue(r(ok), ok)
        self.assertFalse(r("/api/arquivo"))
        self.assertFalse(r("/api/midia/info/x"))
        # origem "null" (painel) com token: libera; sem token: não
        pid = self.projeto()
        ok = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "c.png", dados=PNG)
        rota = "/api/midia/info?p=%s" % urllib.request.quote(ok)
        st, h, _ = self.pedir(rota, cab={"Origin": "null"})
        self.assertEqual(h.get("access-control-allow-origin"), "null")
        st, h, _ = self.pedir(rota, cab={"Origin": "null"}, token=False)
        self.assertEqual(st, 403)
        self.assertNotIn("access-control-allow-origin", h)

    def test_mostrar_no_finder_so_para_permitido(self):
        pid = self.projeto()
        ok = self.arquivo(projetos.dir_projeto(pid), "media", "imagens", "m.png", dados=PNG)
        with mock.patch.object(midia.subprocess, "run") as run, mock.patch.object(midia.subprocess, "Popen") as po:
            run.return_value = mock.Mock(returncode=0)
            st, _, corpo = self.pedir("/api/midia/mostrar", "POST", corpo={"p": "/etc/passwd"})
            self.assertEqual(st, 403)
            run.assert_not_called()
            po.assert_not_called()
            st, _, corpo = self.pedir("/api/midia/mostrar", "POST", corpo={"p": ok})
            self.assertEqual(st, 200)
            if midia.so.MAC:
                self.assertEqual(run.call_args[0][0], ["open", "-R", os.path.realpath(ok)])

    @unittest.skipUnless(FFMPEG, "ffmpeg/ffprobe não instalados")
    def test_picos_e_info_de_um_wav(self):
        pid = self.projeto()
        c = os.path.join(projetos.dir_projeto(pid), "media", "audio", "voz.wav")
        os.makedirs(os.path.dirname(c), exist_ok=True)
        gerar_wav(c, seg=2.0)
        st, _, corpo = self.pedir("/api/midia/picos?p=%s&n=20" % urllib.request.quote(c))
        self.assertEqual(st, 200)
        d = json.loads(corpo)
        self.assertEqual(len(d["picos"]), 20)
        self.assertAlmostEqual(d["duracao"], 2.0, places=1)
        self.assertEqual(max(d["picos"]), 1.0)
        self.assertLess(d["picos"][0], 0.2)                 # começo baixo…
        self.assertGreater(d["picos"][-1], 0.9)             # …fim alto: é a forma da onda
        self.assertTrue(os.listdir(os.path.join(midia.CACHE, "picos")))   # ficou em cache
        st, _, corpo = self.pedir("/api/midia/info?p=%s" % urllib.request.quote(c))
        inf = json.loads(corpo)
        self.assertEqual((inf["tipo"], round(inf["duracao"], 1)), ("audio", 2.0))

    @unittest.skipUnless(FFMPEG, "ffmpeg/ffprobe não instalados")
    def test_quadro_de_imagem_vira_jpeg(self):
        pid = self.projeto()
        c = os.path.join(projetos.dir_projeto(pid), "media", "imagens", "grande.png")
        os.makedirs(os.path.dirname(c), exist_ok=True)
        midia.so.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=800x600", "-frames:v", "1", c])
        st, h, corpo = self.pedir("/api/midia/quadro?p=%s&w=200&t=%s" % (urllib.request.quote(c), app.TOKEN), token=False)
        self.assertEqual((st, h["content-type"]), (200, "image/jpeg"))
        self.assertEqual(corpo[:3], b"\xff\xd8\xff")


# ====================================================================== download
class _Entregas(BaseHTTPRequestHandler):
    """Servidor de entregas FALSO (localhost): sem internet na banca."""
    acessos = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        _Entregas.acessos.append(self.path)
        if self.path.startswith("/png-sem-extensao"):
            corpo, tipo = PNG, "image/png"
        elif self.path.startswith("/miniatura.jpg"):
            corpo, tipo = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 50, "image/jpeg"   # .jpg que é webp
        elif self.path.startswith("/video.mp4"):
            corpo, tipo = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 2000, "video/mp4"
        elif self.path.startswith("/expirou"):
            corpo, tipo = b"<html>expired</html>", "text/html"
        elif self.path.startswith("/grande.mp4"):
            corpo, tipo = b"\x00" * 5000, "video/mp4"
        elif self.path.startswith("/pra-ftp"):
            self.send_response(302)
            self.send_header("Location", "ftp://exemplo.invalid/x.mp4")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


class Download(Rotas):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ent = ThreadingHTTPServer(("127.0.0.1", 0), _Entregas)
        cls.base = "http://127.0.0.1:%d" % cls.ent.server_address[1]
        threading.Thread(target=cls.ent.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.ent.shutdown()
        cls.ent.server_close()
        super().tearDownClass()

    def todos_os_arquivos(self):
        saida = set()
        for raiz, _, arqs in os.walk(self.tmp):
            for a in arqs:
                saida.add(os.path.join(raiz, a))
        return saida

    def test_baixa_para_media_do_projeto_uma_vez_so(self):
        pid = self.projeto()
        cid = conversas.criar(projeto=pid)
        antes = len(_Entregas.acessos)
        url = self.base + "/video.mp4?Expires=1&Signature=abc"
        st, _, corpo = self.pedir("/api/midia/baixar", "POST", corpo={"conversa": cid, "url": url})
        self.assertEqual(st, 200, corpo)
        r = json.loads(corpo)
        pasta = os.path.realpath(os.path.join(projetos.dir_projeto(pid), "media", "videos"))
        self.assertEqual(os.path.dirname(os.path.realpath(r["caminho"])), pasta)
        self.assertEqual((r["tipo"], r["ja_tinha"]), ("video", False))
        self.assertTrue(midia.permitido(r["caminho"]))           # e a tela consegue mostrar
        # o mesmo link (até com outra assinatura) não baixa de novo
        st, _, corpo2 = self.pedir("/api/midia/baixar", "POST",
                                   corpo={"conversa": cid, "url": self.base + "/video.mp4?Expires=2&Signature=zz"})
        r2 = json.loads(corpo2)
        self.assertEqual((r2["caminho"], r2["ja_tinha"]), (r["caminho"], True))
        self.assertEqual(len(_Entregas.acessos) - antes, 1)
        self.assertFalse([a for a in os.listdir(pasta) if a.endswith(".parte")])

    def test_extensao_pelo_conteudo_e_sem_extensao_na_url(self):
        pid = self.projeto()
        d = projetos.dir_projeto(pid)
        r = midia.baixar(self.base + "/png-sem-extensao", d)
        self.assertTrue(r["caminho"].endswith(".png"))
        self.assertIn(os.sep + os.path.join("media", "imagens") + os.sep, r["caminho"])
        r = midia.baixar(self.base + "/miniatura.jpg", d)
        self.assertTrue(r["caminho"].endswith(".webp"), r["caminho"])    # a armadilha do .jpg que é webp

    def test_recusas(self):
        pid = self.projeto()
        d = projetos.dir_projeto(pid)
        for ruim in ("file:///etc/passwd", "ftp://exemplo.invalid/a.mp4", "javascript:alert(1)", ""):
            with self.assertRaises(midia.ErroBaixar, msg=ruim):
                midia.baixar(ruim, d)
        with self.assertRaises(midia.ErroBaixar):
            midia.baixar(self.base + "/pra-ftp", d)                      # redirecionamento para ftp
        with self.assertRaisesRegex(midia.ErroBaixar, "página"):
            midia.baixar(self.base + "/expirou", d)
        with self.assertRaisesRegex(midia.ErroBaixar, "limite"):
            midia.baixar(self.base + "/grande.mp4", d, limite=1000)
        self.assertFalse(os.path.exists(os.path.join(d, "media", "videos")) and
                         [a for a in os.listdir(os.path.join(d, "media", "videos")) if "grande" in a])

    def test_download_nunca_grava_fora_da_pasta_do_projeto(self):
        """A regra do Jhon: tudo o que é baixado fica na PASTA DO PROJETO.
        Nem nome malicioso na URL, nem conversa, nem temporário."""
        pid = self.projeto()
        d = os.path.realpath(projetos.dir_projeto(pid))
        antes = self.todos_os_arquivos()
        cid = conversas.criar(projeto=pid)
        for url in (self.base + "/video.mp4/../../../../../../etc/x.mp4",
                    self.base + "/%2e%2e%2f%2e%2e%2fsaiu.mp4",
                    self.base + "/png-sem-extensao/..%2F..%2F..%2Fescapou",
                    self.base + "/video.mp4?nome=../../fora.mp4"):
            try:
                self.pedir("/api/midia/baixar", "POST", corpo={"conversa": cid, "url": url})
            except Exception:
                pass
        novos = self.todos_os_arquivos() - antes
        fora = [n for n in novos if not os.path.realpath(n).startswith(d + os.sep)
                and not n.endswith(("meta.json", "conversa.json"))]
        self.assertEqual(fora, [], "gravou fora da pasta do projeto")
        self.assertFalse([n for n in novos if os.path.realpath(n).startswith(
            os.path.realpath(conversas.dir_conversa(cid)) + os.sep) and "media" in n])
        # e tudo o que entrou no projeto está em media/<tipo>/
        for n in novos:
            if os.path.realpath(n).startswith(d + os.sep):
                rel = os.path.relpath(os.path.realpath(n), d).split(os.sep)
                self.assertEqual(rel[0], "media", n)
                self.assertIn(rel[1], ("imagens", "videos", "audio", ".entregas.json"), n)

    def test_conversa_sem_projeto_pergunta_antes_de_baixar(self):
        self.projeto("Outro")
        cid = conversas.criar()
        antes = self.todos_os_arquivos()
        st, _, corpo = self.pedir("/api/midia/baixar", "POST",
                                  corpo={"conversa": cid, "url": self.base + "/video.mp4"})
        self.assertEqual(st, 409)
        d = json.loads(corpo)
        self.assertTrue(d["precisa_destino"])
        self.assertTrue(d["projetos"])
        self.assertEqual(self.todos_os_arquivos(), antes)                 # nada foi gravado
        # a pasta da conversa NÃO serve de destino
        st, _, corpo = self.pedir("/api/conversas/%s/destino" % cid, "POST",
                                  corpo={"pasta": conversas.dir_conversa(cid)})
        self.assertEqual(st, 400)
        # escolhe um projeto: aí baixa para ele
        pid = d["projetos"][0]["id"]
        st, _, corpo = self.pedir("/api/conversas/%s/destino" % cid, "POST", corpo={"projeto": pid})
        self.assertEqual(st, 200)
        st, _, corpo = self.pedir("/api/midia/baixar", "POST",
                                  corpo={"conversa": cid, "url": self.base + "/video.mp4"})
        self.assertEqual(st, 200)
        self.assertTrue(os.path.realpath(json.loads(corpo)["caminho"]).startswith(
            os.path.realpath(projetos.dir_projeto(pid)) + os.sep))

    def test_pasta_escolhida_vira_destino_e_raiz(self):
        cid = conversas.criar()
        pasta = os.path.join(self.tmp, "Jobs", "Escolhido")
        os.makedirs(pasta)
        with mock.patch.object(midia, "_temporaria", lambda p: False), \
                mock.patch.object(midia, "escolher_pasta", lambda *a: pasta):
            st, _, corpo = self.pedir("/api/conversas/%s/destino" % cid, "POST", corpo={"escolher": True})
            self.assertEqual(st, 200, corpo)
            st, _, corpo = self.pedir("/api/midia/baixar", "POST",
                                      corpo={"conversa": cid, "url": self.base + "/png-sem-extensao"})
            self.assertEqual(st, 200, corpo)
            c = json.loads(corpo)["caminho"]
            self.assertEqual(os.path.dirname(os.path.realpath(c)),
                             os.path.join(os.path.realpath(pasta), "media", "imagens"))
            midia.esquecer_raizes()
            self.assertTrue(midia.permitido(c))


# ====================================================================== contexto
class Contexto(unittest.TestCase):

    def test_regra_da_pasta_vai_no_contexto(self):
        with mock.patch.object(conversa.adobe, "estado", side_effect=RuntimeError("sem adobe")):
            t = conversa._contexto_ambiente(None)
        self.assertIn(conversa.REGRA_PASTA, t)
        self.assertIn("Nunca em pasta temporária, Downloads ou fora do projeto", conversa.REGRA_PASTA)
        self.assertIn("Antes de importar no Premiere", conversa.REGRA_PASTA)

    def test_regra_da_legenda_vai_no_contexto(self):
        with mock.patch.object(conversa.adobe, "estado", side_effect=RuntimeError("sem adobe")):
            t = conversa._contexto_ambiente(None)
        self.assertIn(conversa.REGRA_LEGENDA, t)
        r = conversa.REGRA_LEGENDA
        for trecho in ("pr_legenda_nativa_criar", "pr_legendas_mogrt_aplicar", "pr_extendscript",
                       "seq.createCaptionTrack(item,0)", "(item,0,3)", "(item)", "LF",
                       "pasta do projeto", "Nunca use insertClip com .srt",
                       "o que não existe é LER legenda nativa"):
            self.assertIn(trecho, r)


if __name__ == "__main__":
    unittest.main()
