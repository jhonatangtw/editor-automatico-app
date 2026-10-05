"""
Guia de comandos: nada inventado. Cada ferramenta ou skill que um comando diz
usar precisa EXISTIR — no plugin Tools PRO, nas ferramentas do app ou nas
skills que vão no pacote. E o documento .md precisa bater com a tela.
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# as 44 ferramentas do registro do Tools PRO (js/mcp/registry.js, plugin 1.9.x)
TOOLSPRO = {
    "pr_zoom_info", "pr_zoom_aplicar", "pr_zoom_limpar", "pr_organizar_info", "pr_organizar_analisar",
    "pr_organizar_aplicar", "pr_organizar_desfazer", "pr_autoclip_info", "pr_autoclip", "pr_marcadores_info",
    "pr_marcadores_listar", "pr_marcadores_criar", "pr_marcadores_apagar", "pr_midia_info", "pr_midia_listar",
    "pr_midia_importar", "pr_timeline_colocar", "ae_organizar_info", "ae_organizar_analisar",
    "ae_organizar_aplicar", "ae_smoothify_info", "ae_smoothify", "ae_smoothify_limpar_expressoes",
    "pr_projeto_salvar", "pr_sequencias_listar", "pr_sequencia_ativar", "pr_timeline_selecionar",
    "pr_timeline_listar", "pr_timeline_remover", "pr_timeline_mudo", "pr_copiar_info", "pr_copiar_atributos",
    "pr_smoothify_info", "pr_smoothify", "pr_smoothify_resetar", "pr_anypaste_info", "pr_anypaste",
    "ae_legendas_info", "ae_legendas_importar", "ae_legendas_limpar", "ae_titulos_info", "ae_titulos_inserir",
    "pr_extendscript", "ae_extendscript",
}
LOCAIS = {"FFmpeg", "Whisper", "etapas do app", "pastas do computador"}
# as contas que o PRÓPRIO aluno conecta na aba Contas
CONTAS = {"Higgsfield", "ElevenLabs", "HeyGen", "MiniMax"}
REGISTRO = os.path.expanduser("~/Documents/03_Apps/Editor Black Belt/src-toolspro/js/mcp/registry.js")


def guia():
    with open(os.path.join(RAIZ, "web", "guia.json"), encoding="utf-8") as f:
        return json.load(f)


def comandos():
    for gr in guia()["grupos"]:
        for c in gr["comandos"]:
            yield gr, c


class Guia(unittest.TestCase):

    def test_tudo_que_o_guia_cita_existe(self):
        from nucleo import mcp_servidor
        app = {f["name"] for f in mcp_servidor.FERRAMENTAS}
        skills = {n for n in os.listdir(os.path.join(RAIZ, "skills"))
                  if os.path.isdir(os.path.join(RAIZ, "skills", n))}
        conhecido = TOOLSPRO | app | skills | LOCAIS | CONTAS
        faltam = ["%s → %s" % (c["titulo"], u) for _, c in comandos() for u in c["usa"] if u not in conhecido]
        self.assertEqual(faltam, [])

    @unittest.skipUnless(os.path.isfile(REGISTRO), "código do Tools PRO não está nesta máquina")
    def test_lista_do_tools_pro_bate_com_o_registro(self):
        with open(REGISTRO, encoding="utf-8") as f:
            nomes = set(re.findall(r"nome:\s*'([a-z_]+)'", f.read()))
        self.assertEqual(TOOLSPRO - nomes, set(), "ferramenta citada que o plugin não tem mais")

    def test_ferramenta_do_tools_pro_e_so_no_claude(self):
        # o ChatGPT (Codex) recebe as ferramentas do APP, não as do plugin
        errados = [c["titulo"] for _, c in comandos()
                   if any(u in TOOLSPRO for u in c["usa"]) and c["ia"] != "Claude"]
        self.assertEqual(errados, [])

    def test_cada_comando_esta_completo(self):
        for gr, c in comandos():
            for campo in ("titulo", "comando", "faz", "quando", "precisa", "ia", "usa"):
                self.assertTrue(c.get(campo), "%s / %s sem %s" % (gr["titulo"], c.get("titulo"), campo))
            self.assertIn(c["ia"], guia()["legenda_ia"])
            self.assertIn(c.get("nivel"), ("rápido", "completo"), c["titulo"])

    def test_documento_bate_com_a_tela(self):
        spec = importlib.util.spec_from_file_location("gerar_guia", os.path.join(RAIZ, "gerar-guia.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        with open(os.path.join(RAIZ, "web", "GUIA-DE-COMANDOS.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), m.markdown(guia()),
                             "rode: python3 gerar-guia.py")


# ------------------------------------------------------------ busca do guia
# A busca vive no app.js (é o navegador que filtra). O teste recorta o trecho
# marcado e roda no node, contra o guia.json de verdade — testar uma cópia em
# Python provaria a cópia, não o que o aluno usa.
NODE = shutil.which("node")


def _rodar_busca(consultas):
    with open(os.path.join(RAIZ, "web", "app.js"), encoding="utf-8") as f:
        js = f.read()
    ini = js.index("// ---- busca do guia")
    fim = js.index("// ---- fim da busca do guia")
    programa = js[ini:fim] + """
const g = JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'));
const consultas = JSON.parse(process.argv[2]);
const idx = [];
for (const gr of g.grupos) for (const c of gr.comandos) idx.push([c.titulo, indiceGuia(gr, c)]);
const r = { norm: {}, achados: {} };
for (const q of consultas) {
  r.norm[q] = normalizarBusca(q);
  r.achados[q] = idx.filter(([, i]) => casaBusca(i, q)).map(([t]) => t);
}
process.stdout.write(JSON.stringify(r));
"""
    out = subprocess.run([NODE, "-e", programa, os.path.join(RAIZ, "web", "guia.json"),
                          json.dumps(consultas)], capture_output=True, text=True, timeout=30)
    if out.returncode:
        raise AssertionError(out.stderr)
    return json.loads(out.stdout)


@unittest.skipUnless(NODE, "node não está instalado nesta máquina")
class BuscaDoGuia(unittest.TestCase):

    def test_sem_acento_acha_o_que_tem_acento(self):
        # o defeito da gravação: "silencio" não achava nada, só "silêncio"
        r = _rodar_busca(["silencio", "silêncio", "SILÊNCIO", "Silencio"])
        com = r["achados"]["silêncio"]
        self.assertIn("Cortar o silêncio de uma aula (corte suave)", com)
        for q in ("silencio", "SILÊNCIO", "Silencio"):
            self.assertEqual(r["achados"][q], com, q)

    def test_acento_na_busca_acha_texto_sem_acento(self):
        # e o contrário: digitar com acento o que o guia escreve sem
        r = _rodar_busca(["prómpt", "prompt"])
        self.assertTrue(r["achados"]["prompt"])
        self.assertEqual(r["achados"]["prómpt"], r["achados"]["prompt"])

    def test_cedilha_e_til(self):
        r = _rodar_busca(["organizacao de job", "webinario", "preco"])
        self.assertTrue(r["achados"]["organizacao de job"])
        self.assertIn("Slides de webinário pela fala", r["achados"]["webinario"])
        self.assertIn("Trocar o preço numa VSL de upsell", r["achados"]["preco"])

    def test_espaco_sobrando_nao_atrapalha(self):
        r = _rodar_busca(["  corte   suave  ", "corte suave", "suave\tcorte"])
        self.assertEqual(r["norm"]["  corte   suave  "], "corte suave")
        self.assertTrue(r["achados"]["corte suave"])
        self.assertEqual(r["achados"]["  corte   suave  "], r["achados"]["corte suave"])
        # palavra fora de ordem continua achando
        self.assertEqual(r["achados"]["suave\tcorte"], r["achados"]["corte suave"])

    def test_procura_em_titulo_descricao_ferramenta_e_comando(self):
        g = guia()
        gr = g["grupos"][0]
        c = gr["comandos"][0]
        trecho_cmd = " ".join(c["comando"].split()[3:6])
        consultas = [gr["descricao"].split(":")[0], c["faz"].split(".")[0][:30],
                     c["usa"][0], trecho_cmd, c["precisa"][0][:20]]
        r = _rodar_busca(consultas)
        for q in consultas:
            self.assertIn(c["titulo"], r["achados"][q], q)

    def test_hifen_opcional(self):
        r = _rodar_busca(["broll", "b-roll"])
        self.assertTrue(r["achados"]["b-roll"])
        self.assertEqual(set(r["achados"]["b-roll"]) - set(r["achados"]["broll"]), set())

    def test_busca_vazia_mostra_tudo_e_lixo_nao_acha_nada(self):
        total = sum(len(gr["comandos"]) for gr in guia()["grupos"])
        r = _rodar_busca(["", "   ", "xyzzyqwv"])
        self.assertEqual(len(r["achados"][""]), total)
        self.assertEqual(len(r["achados"]["   "]), total)
        self.assertEqual(r["achados"]["xyzzyqwv"], [])


# o guia vai para todo aluno: nada de cliente, produto, pessoa, job ou máquina
PRIVADO = re.compile(
    r"/Users/|C:\\\\Users|jhonwill|~/Documents/|drive\.google|docs\.google|frame\.io|claude\.ai/"
    r"|\bH&W\b|HW Publishing|hw-publishing|LeafTide|Leaftide|CardioFlush|CardioClear|MemoFlow|LinfaFlow|Lymphoria"
    r"|GlucoJaro|VitaRenew|VigorBoost|SlimSoda|Ameripel|Iron Heart|Profit Publishers|AI Loophole"
    r"|\b(?:Jhon|Jhonatan|Bifi|Marcelo|Roque|Gustavo|Ericles|Diogo|Pedro|Jonas|Mia|Jason|Robert|Sarah|Nina|Gupta|Rogan|Rhonda)\b"
    r"|\b\d{2,3}_[A-Z]{2}\b|\[\d{6}\]|R\$ ?\d")


class GuiaSemDadoPrivado(unittest.TestCase):

    def test_json_e_documento_sem_cliente_pessoa_job_ou_caminho(self):
        for nome in ("guia.json", "GUIA-DE-COMANDOS.md"):
            with open(os.path.join(RAIZ, "web", nome), encoding="utf-8") as f:
                t = f.read()
            achados = sorted({m.group(0) for m in PRIVADO.finditer(t)})
            self.assertEqual(achados, [], nome)


if __name__ == "__main__":
    unittest.main()
