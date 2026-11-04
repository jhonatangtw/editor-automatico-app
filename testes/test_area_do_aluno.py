"""
Área do aluno (0.21.0): login por código, "Minhas aulas" e atualizador com o
servidor primeiro e o GitHub de reserva.

Tudo com HTTP FALSO — nenhuma chamada sai desta máquina, nenhum instalador é
aberto, nada é gravado fora de uma pasta temporária (sessao.json e a pasta de
código da atualização leve são redirecionados).

    .venv/bin/python -m unittest discover -s testes -v
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import atualizacao, codigo, conta  # noqa: E402

SERVIDOR = conta.SERVIDOR
GH = "https://github.com/jhonatangtw/editor-automatico-app/releases/latest/download/"
DL = "https://editorblackbelt.com.br/api/download/abc?u=u1&e=1&t=ff"


# ---------------------------------------------------------------- HTTP falso

class _Resp(io.BytesIO):
    def __init__(self, corpo, status=200, cab=None):
        super().__init__(corpo)
        self.status = status
        self.headers = cab or {"Content-Length": str(len(corpo))}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class FakeHTTP:
    """Roteia por URL exata (ou pelo caminho, sem query). Valor:
    bytes/dict -> 200; (status, dict) -> HTTPError; Exception -> levanta."""

    def __init__(self, rotas):
        self.rotas = rotas
        self.pedidos = []

    def __call__(self, req, timeout=None, context=None):
        url = req.full_url if hasattr(req, "full_url") else req
        corpo = getattr(req, "data", None)
        cab = {k.lower(): v for k, v in getattr(req, "header_items", lambda: [])()}
        self.pedidos.append({"url": url, "metodo": req.get_method(),
                             "corpo": json.loads(corpo) if corpo else None, "cab": cab})
        r = self.rotas.get(url)
        if r is None:
            r = self.rotas.get(url.split("?")[0])
        if r is None:
            raise urllib.error.URLError("rota não simulada: " + url)
        if isinstance(r, Exception):
            raise r
        if isinstance(r, tuple):
            st, d = r
            raise urllib.error.HTTPError(url, st, "x", {}, io.BytesIO(json.dumps(d).encode()))
        if isinstance(r, dict):
            r = json.dumps(r).encode()
        return _Resp(r)

    def para(self, trecho):
        return [p for p in self.pedidos if trecho in p["url"]]


class Base(unittest.TestCase):
    """sessao.json e ~/.editorblackbelt/app vão para uma pasta temporária."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ea-teste-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        app_dir = os.path.join(self.tmp, "app")
        for alvo, nome, valor in (
                (conta, "PASTA", self.tmp),
                (conta, "ARQUIVO", os.path.join(self.tmp, "sessao.json")),
                (codigo, "BASE", app_dir),
                (codigo, "PONTEIRO", os.path.join(app_dir, "ativo.json")),
                (codigo, "MARCA", os.path.join(app_dir, "tentando.flag"))):
            p = mock.patch.object(alvo, nome, valor)
            p.start()
            self.addCleanup(p.stop)

    def usar_http(self, rotas):
        f = FakeHTTP(rotas)
        p = mock.patch("urllib.request.urlopen", f)
        p.start()
        self.addCleanup(p.stop)
        return f

    def sessao(self, **d):
        with open(conta.ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(d, f)

    def lida(self):
        with open(conta.ARQUIVO, encoding="utf-8") as f:
            return json.load(f)


# ---------------------------------------------------------------- login por código

class LoginPorCodigo(Base):

    def test_pedir_codigo_manda_email_e_devolve_frase_neutra(self):
        h = self.usar_http({SERVIDOR + "/api/entrar/codigo":
                            {"ok": True, "msg": "qualquer coisa do servidor"}})
        r = conta.pedir_codigo("  Aluno@Exemplo.com ")
        self.assertTrue(r["ok"])
        self.assertEqual(r["msg"], conta.MSG_CODIGO)
        self.assertIn("Se houver um acesso", r["msg"])
        p = h.para("/api/entrar/codigo")[0]
        self.assertEqual(p["metodo"], "POST")
        self.assertEqual(p["corpo"], {"email": "Aluno@Exemplo.com"})

    def test_pedir_codigo_mesma_resposta_com_e_sem_conta(self):
        # o servidor responde igual; o app não pode criar diferença
        self.usar_http({SERVIDOR + "/api/entrar/codigo": {"ok": True, "msg": "x"}})
        a = conta.pedir_codigo("tem@conta.com")
        b = conta.pedir_codigo("nao@existe.com")
        self.assertEqual(a, b)

    def test_pedir_codigo_email_invalido_nem_chama(self):
        h = self.usar_http({})
        r = conta.pedir_codigo("sem-arroba")
        self.assertFalse(r["ok"])
        self.assertEqual(h.pedidos, [])

    def test_pedir_codigo_offline(self):
        self.usar_http({SERVIDOR + "/api/entrar/codigo": urllib.error.URLError("sem rede")})
        r = conta.pedir_codigo("a@b.com")
        self.assertFalse(r["ok"])
        self.assertTrue(r["offline"])
        self.assertIn("Não consegui falar com o servidor", r["msg"])

    def test_verificar_grava_mesma_sessao_e_reusa_impressao(self):
        self.sessao(bb_digital="m-dopainel123", outra_chave="do painel")
        h = self.usar_http({SERVIDOR + "/api/entrar/verificar": {
            "ok": True, "token": "tok-novo", "trocar_senha": True,
            "usuario": {"nome": "Ana", "email": "a@b.com", "admin": False}}})
        r = conta.entrar_com_codigo("a@b.com", "123 456")
        self.assertEqual(r, {"ok": True, "nome": "Ana", "email": "a@b.com"})
        corpo = h.para("/api/entrar/verificar")[0]["corpo"]
        self.assertEqual(corpo["codigo"], "123456")
        self.assertEqual(corpo["impressao"], "m-dopainel123")   # não queima vaga
        self.assertEqual(corpo["email"], "a@b.com")
        self.assertIn("apelido", corpo)
        s = self.lida()
        self.assertEqual(s["bb_acesso_token"], "tok-novo")
        self.assertEqual(s["bb_acesso_nome"], "Ana")
        self.assertEqual(s["bb_acesso_adm"], "0")
        self.assertEqual(s["outra_chave"], "do painel")          # não apaga o do painel
        self.assertEqual(s["bb_digital"], "m-dopainel123")

    def test_verificar_mesmo_formato_do_login_com_senha(self):
        resposta = {"ok": True, "token": "t1", "usuario": {"nome": "Bia", "email": "b@c.com", "admin": True}}
        self.usar_http({SERVIDOR + "/api/entrar/verificar": resposta,
                        SERVIDOR + "/api/login": resposta})
        a = conta.entrar_com_codigo("b@c.com", "000111")
        sa = self.lida()
        os.remove(conta.ARQUIVO)
        b = conta.entrar("b@c.com", "senha")
        sb = self.lida()
        self.assertEqual(a, b)
        for k in ("bb_acesso_token", "bb_acesso_nome", "bb_acesso_adm"):
            self.assertEqual(sa[k], sb[k])

    def test_codigo_errado_nao_grava_token(self):
        self.sessao(bb_digital="m-x")
        self.usar_http({SERVIDOR + "/api/entrar/verificar": (401, {
            "ok": False, "msg": "Código inválido ou expirado. Peça um novo.", "motivo": "codigo_invalido"})})
        r = conta.entrar_com_codigo("a@b.com", "999999")
        self.assertFalse(r["ok"])
        self.assertIn("Código inválido", r["msg"])
        self.assertNotIn("bb_acesso_token", self.lida())

    def test_codigo_com_digitos_a_menos_nem_chama(self):
        h = self.usar_http({})
        r = conta.entrar_com_codigo("a@b.com", "12345")
        self.assertFalse(r["ok"])
        self.assertEqual(h.pedidos, [])

    def test_resposta_ok_sem_token_nao_vira_login(self):
        self.usar_http({SERVIDOR + "/api/entrar/verificar": {"ok": True}})
        r = conta.entrar_com_codigo("a@b.com", "123456")
        self.assertFalse(r["ok"])


# ---------------------------------------------------------------- Minhas aulas

class MinhasAulas(Base):

    def test_passe_usa_bearer_e_devolve_url(self):
        self.sessao(bb_acesso_token="tok-app")
        url = "https://editorblackbelt.com.br/entrar/passe?c=" + "a" * 64
        h = self.usar_http({SERVIDOR + "/api/passe": {"ok": True, "url": url, "codigo": "a" * 64}})
        r = conta.passe()
        self.assertEqual(r, {"ok": True, "url": url})
        p = h.para("/api/passe")[0]
        self.assertEqual(p["metodo"], "POST")
        self.assertEqual(p["cab"]["authorization"], "Bearer tok-app")

    def test_passe_sem_token_nem_chama(self):
        h = self.usar_http({})
        r = conta.passe()
        self.assertEqual(r["motivo"], "sem_sessao")
        self.assertEqual(h.pedidos, [])

    def test_passe_sessao_expirada(self):
        self.sessao(bb_acesso_token="velho")
        self.usar_http({SERVIDOR + "/api/passe": (401, {"ok": False, "msg": "Sessão inválida. Entre de novo.",
                                                        "motivo": "sem_sessao"})})
        r = conta.passe()
        self.assertFalse(r["ok"])
        self.assertEqual(r["motivo"], "sem_sessao")
        self.assertIn("expirou", r["msg"])

    def test_passe_offline(self):
        self.sessao(bb_acesso_token="t")
        self.usar_http({SERVIDOR + "/api/passe": urllib.error.URLError("timed out")})
        r = conta.passe()
        self.assertEqual(r["motivo"], "offline")
        self.assertIn("internet", r["msg"])

    def test_passe_rota_ausente(self):
        self.sessao(bb_acesso_token="t")
        self.usar_http({SERVIDOR + "/api/passe": (404, {"ok": False, "msg": "Rota não encontrada."})})
        self.assertEqual(conta.passe()["motivo"], "indisponivel")

    def test_passe_url_nao_https_e_recusada(self):
        self.sessao(bb_acesso_token="t")
        self.usar_http({SERVIDOR + "/api/passe": {"ok": True, "url": "http://outro/x"}})
        self.assertFalse(conta.passe()["ok"])

    def test_botao_abre_navegador_padrao(self):
        import app
        url = "https://editorblackbelt.com.br/entrar/passe?c=" + "b" * 64
        with mock.patch.object(app.conta, "passe", return_value={"ok": True, "url": url}), \
             mock.patch.object(app.webbrowser, "open", return_value=True) as abre:
            r = app.abrir_aulas()
        abre.assert_called_once_with(url)
        self.assertTrue(r["ok"])
        self.assertNotIn("url", r)          # o link de uso único não volta para a tela

    def test_botao_repassa_erro_sem_abrir(self):
        import app
        erro = {"ok": False, "motivo": "offline", "msg": "Sem conexão com o servidor agora."}
        with mock.patch.object(app.conta, "passe", return_value=erro), \
             mock.patch.object(app.webbrowser, "open") as abre:
            r = app.abrir_aulas()
        abre.assert_not_called()
        self.assertEqual(r, erro)


# ---------------------------------------------------------------- atualizador

def _zip_codigo(versao, **extra):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("app.py", "print('novo')\n")
        z.writestr("nucleo/__init__.py", "")
        z.writestr("web/index.html", "<!doctype html>")
        z.writestr("version.json", json.dumps(dict(version=versao, **extra)))
    return b.getvalue()


def _sha(b):
    return hashlib.sha256(b).hexdigest()


class Atualizador(Base):
    LOCAL = {"version": "0.21.0", "repo": "jhonatangtw/editor-automatico-app",
             "asset_mac": "EditorAutomatico.dmg", "asset_win": "EditorAutomatico-Instalador.exe",
             "asset_mac_intel": "EditorAutomatico-Intel.dmg"}

    def setUp(self):
        super().setUp()
        for alvo, nome, valor in ((atualizacao, "local", lambda: dict(self.LOCAL)),
                                  (atualizacao, "_so_servidor", lambda: "mac"),
                                  (atualizacao.so, "abrir", mock.MagicMock(return_value=True))):
            p = mock.patch.object(alvo, nome, valor)
            p.start()
            self.addCleanup(p.stop)
        self.abrir = atualizacao.so.abrir
        self.rota_srv = SERVIDOR + "/api/atualizacao/editor-automatico"

    def gh(self, versao="0.21.0", **extra):
        return {GH + "version.json": dict(self.LOCAL, version=versao, **extra)}

    def srv(self, **d):
        base = {"ok": True, "version": "0.22.0", "notes": "do servidor", "sha256": "a" * 64,
                "sig": None, "size": 10, "so": "universal", "url": DL}
        base.update(d)
        return {self.rota_srv: base}

    # ---- conferir

    def test_sem_sessao_nem_pergunta_ao_servidor(self):
        h = self.usar_http(self.gh("0.21.1"))
        r = atualizacao.conferir()
        self.assertEqual(h.para("/api/atualizacao"), [])
        self.assertNotEqual(r.get("fonte"), "servidor")
        self.assertTrue(r["tem_nova"])
        self.assertEqual(r["ultima"], "0.21.1")

    def test_sem_sessao_resultado_identico_ao_github(self):
        self.usar_http(self.gh("0.21.1", codigo="codigo.zip", codigo_sha256="c" * 64))
        self.assertEqual(atualizacao.conferir(), atualizacao.conferir_github())

    def test_servidor_primeiro_com_bearer_e_so(self):
        self.sessao(bb_acesso_token="tok")
        h = self.usar_http(dict(self.srv(), **self.gh()))
        r = atualizacao.conferir()
        p = h.para("/api/atualizacao")[0]
        self.assertEqual(p["metodo"], "GET")
        self.assertEqual(p["cab"]["authorization"], "Bearer tok")
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(p["url"]).query)
        self.assertEqual(q["so"], ["mac"])
        self.assertEqual(r["fonte"], "servidor")
        self.assertEqual(r["ultima"], "0.22.0")
        self.assertEqual(r["modo"], "codigo")
        self.assertEqual(r["url_codigo"], DL)
        self.assertEqual(r["codigo_sha256"], "a" * 64)
        self.assertEqual(h.para("github.com"), [])          # nem precisou do GitHub

    def test_servidor_instalador_por_sistema(self):
        self.sessao(bb_acesso_token="tok")
        self.usar_http(self.srv(so="mac"))
        r = atualizacao.conferir()
        self.assertEqual(r["modo"], "instalador")
        self.assertEqual(r["sha256"], "a" * 64)
        self.assertTrue(r["asset"].endswith(".dmg"))

    def _cai_no_github(self, rota_srv):
        self.sessao(bb_acesso_token="tok")
        rotas = self.gh("0.21.3")
        if rota_srv is not None:
            rotas[self.rota_srv] = rota_srv
        h = self.usar_http(rotas)
        r = atualizacao.conferir()
        self.assertNotEqual(r.get("fonte"), "servidor")
        self.assertEqual(r["ultima"], "0.21.3")
        self.assertTrue(h.para("github.com"))
        return r

    def test_reserva_quando_servidor_sem_build(self):
        self._cai_no_github({"ok": True, "version": None})

    def test_reserva_quando_sessao_recusada(self):
        self._cai_no_github((401, {"ok": False, "motivo": "sem_sessao"}))

    def test_reserva_quando_sem_acesso(self):
        self._cai_no_github((403, {"ok": False, "motivo": "sem_acesso"}))

    def test_reserva_quando_servidor_fora(self):
        self._cai_no_github(urllib.error.URLError("sem rede"))

    def test_reserva_quando_servidor_5xx_sem_json(self):
        self._cai_no_github(urllib.error.HTTPError("x", 503, "x", {}, io.BytesIO(b"<html>")))

    def test_reserva_quando_rota_nao_existe(self):
        self._cai_no_github(None)

    def test_reserva_quando_falta_sha256(self):
        self._cai_no_github(self.srv(sha256=None)[self.rota_srv])

    def test_reserva_quando_url_fora_do_dominio(self):
        self._cai_no_github(self.srv(url="https://evil.example/x.zip")[self.rota_srv])

    def test_reserva_quando_url_sem_https(self):
        self._cai_no_github(self.srv(url="http://editorblackbelt.com.br/x")[self.rota_srv])

    def test_reserva_quando_versao_do_servidor_nao_e_mais_nova(self):
        self._cai_no_github(self.srv(version="0.21.0")[self.rota_srv])

    def test_reserva_quando_instalador_de_outro_sistema(self):
        self._cai_no_github(self.srv(so="windows")[self.rota_srv])

    # ---- o que o servidor ao vivo tem hoje: instaladores 0.20.2, sem sig

    def _servidor_ao_vivo(self):
        return self.srv(version="0.20.2", so="mac", sig=None, notes="", sha256="b" * 64)[self.rota_srv]

    def test_servidor_com_versao_mais_velha_nao_rebaixa(self):
        r = self._cai_no_github(self._servidor_ao_vivo())
        self.assertNotEqual(r["ultima"], "0.20.2")

    def test_servidor_com_versao_mais_velha_e_github_em_dia(self):
        self.sessao(bb_acesso_token="tok")
        rotas = self.gh("0.21.0")
        rotas[self.rota_srv] = self._servidor_ao_vivo()
        self.usar_http(rotas)
        r = atualizacao.conferir()
        self.assertFalse(r["tem_nova"])
        self.assertIsNone(r.get("erro"))
        destino = os.path.join(self.tmp, "Downloads")
        b = atualizacao.baixar(destino_dir=destino)
        self.assertTrue(b.get("nada"))                    # não baixa nem abre nada
        self.abrir.assert_not_called()
        self.assertFalse(os.path.exists(destino) and os.listdir(destino))

    def test_servidor_mesma_versao_nao_reinstala(self):
        with mock.patch.dict(self.LOCAL, {"version": "0.20.2"}):
            r = self._cai_no_github(self._servidor_ao_vivo())
        self.assertNotEqual(r.get("fonte"), "servidor")

    def test_sem_sig_vale_o_sha256_como_no_github(self):
        # sig ausente não bloqueia nem relaxa nada: quem decide é o sha256
        self.sessao(bb_acesso_token="tok")
        dmg = b"instalador-sem-sig" * 50
        self.usar_http(dict(self.srv(so="mac", sig=None, sha256=_sha(dmg)), **{DL: dmg}))
        r = atualizacao.baixar(destino_dir=os.path.join(self.tmp, "Downloads"))
        self.assertEqual(r["fonte"], "servidor")
        self.abrir.assert_called_once()

    # ---- atualização leve pelo servidor

    def test_leve_pelo_servidor_confere_sha_e_instala(self):
        self.sessao(bb_acesso_token="tok")
        z = _zip_codigo("0.22.0")
        self.usar_http(dict(self.srv(sha256=_sha(z)), **{DL: z}))
        r = atualizacao.atualizar_codigo()
        self.assertTrue(r["ok"])
        self.assertEqual(r["fonte"], "servidor")
        with open(codigo.PONTEIRO, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["versao"], "0.22.0")

    def test_leve_sha_errado_nao_instala_e_cai_no_github(self):
        self.sessao(bb_acesso_token="tok")
        z_srv = _zip_codigo("0.22.0")
        z_gh = _zip_codigo("0.21.5")
        rotas = dict(self.srv(sha256="0" * 64), **{DL: z_srv})
        rotas.update(self.gh("0.21.5", codigo="codigo.zip", codigo_sha256=_sha(z_gh)))
        rotas[GH + "codigo.zip"] = z_gh
        self.usar_http(rotas)
        r = atualizacao.atualizar_codigo()
        self.assertNotEqual(r.get("fonte"), "servidor")
        with open(codigo.PONTEIRO, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["versao"], "0.21.5")   # o do GitHub, não o adulterado

    def test_leve_sha_errado_e_github_em_dia_mostra_o_erro(self):
        self.sessao(bb_acesso_token="tok")
        z = _zip_codigo("0.22.0")
        rotas = dict(self.srv(sha256="0" * 64), **{DL: z})
        rotas.update(self.gh("0.21.0"))
        self.usar_http(rotas)
        with self.assertRaises(RuntimeError) as c:
            atualizacao.atualizar_codigo()
        self.assertIn("sha256", str(c.exception))
        self.assertFalse(os.path.exists(codigo.PONTEIRO))

    def test_leve_que_precisa_instalador_nao_entra(self):
        self.sessao(bb_acesso_token="tok")
        z = _zip_codigo("0.22.0", precisa_instalador=True)
        rotas = dict(self.srv(sha256=_sha(z)), **{DL: z})
        rotas.update(self.gh("0.21.0"))
        self.usar_http(rotas)
        with self.assertRaises(RuntimeError):
            atualizacao.atualizar_codigo()
        self.assertFalse(os.path.exists(codigo.PONTEIRO))

    def test_leve_pelo_github_continua_igual_sem_sessao(self):
        z = _zip_codigo("0.21.2")
        rotas = self.gh("0.21.2", codigo="codigo.zip", codigo_sha256=_sha(z))
        rotas[GH + "codigo.zip"] = z
        h = self.usar_http(rotas)
        r = atualizacao.atualizar_codigo()
        self.assertTrue(r["ok"])
        self.assertEqual(h.para("/api/atualizacao"), [])

    # ---- instalador pelo servidor

    def test_instalador_pelo_servidor_confere_e_abre(self):
        self.sessao(bb_acesso_token="tok")
        dmg = b"\x00dmg-falso" * 100
        self.usar_http(dict(self.srv(so="mac", sha256=_sha(dmg)), **{DL: dmg}))
        destino = os.path.join(self.tmp, "Downloads")
        r = atualizacao.baixar(destino_dir=destino)
        self.assertEqual(r["fonte"], "servidor")
        with open(r["arquivo"], "rb") as f:
            self.assertEqual(f.read(), dmg)
        self.abrir.assert_called_once_with(r["arquivo"])
        self.assertFalse(any(n.endswith(".parcial") for n in os.listdir(destino)))

    def test_instalador_adulterado_e_apagado_e_nao_abre(self):
        self.sessao(bb_acesso_token="tok")
        rotas = dict(self.srv(so="mac", sha256="0" * 64), **{DL: b"adulterado"})
        rotas.update(self.gh("0.21.0"))
        self.usar_http(rotas)
        destino = os.path.join(self.tmp, "Downloads")
        with self.assertRaises(RuntimeError):
            atualizacao.baixar(destino_dir=destino)
        self.abrir.assert_not_called()
        self.assertEqual(os.listdir(destino), [])


if __name__ == "__main__":
    unittest.main()
