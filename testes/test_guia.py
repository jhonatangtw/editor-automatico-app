"""
Guia de comandos: nada inventado. Cada ferramenta ou skill que um comando diz
usar precisa EXISTIR — no plugin Tools PRO, nas ferramentas do app ou nas
skills que vão no pacote. E o documento .md precisa bater com a tela.
"""

import importlib.util
import json
import os
import re
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
LOCAIS = {"FFmpeg", "Whisper", "etapas do app"}
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
        conhecido = TOOLSPRO | app | skills | LOCAIS
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

    def test_documento_bate_com_a_tela(self):
        spec = importlib.util.spec_from_file_location("gerar_guia", os.path.join(RAIZ, "gerar-guia.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        with open(os.path.join(RAIZ, "web", "GUIA-DE-COMANDOS.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), m.markdown(guia()),
                             "rode: python3 gerar-guia.py")


if __name__ == "__main__":
    unittest.main()
