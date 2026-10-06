"""
Roda os testes JS da Conversa (testes/js/) pelo node, dentro da suíte Python
— assim `python -m pytest testes/` (ou unittest) cobre a tela também.

- conversa-ui.test.js: markdown seguro, rótulos em português, menu "/" e "@",
  fila, painel de tarefas, /custo e conversas antigas abrindo na tela nova.
- conversa-ui-dom.test.js: o mesmo componente no DOM (jsdom da banca do Tools
  PRO, se existir na máquina): teclado do menu, fila visível, Esc, ↑.
- conversa-ui-midia-dom.test.js (0.22.1): prévia de imagem/vídeo/áudio,
  lightbox, "Colocar na timeline" só com clique, entrega remota baixando para
  o projeto, barra do topo com Histórico/+ Nova/renomear/apagar.
"""

import os
import shutil
import subprocess
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node não está instalado nesta máquina")
class ConversaUI(unittest.TestCase):

    def rodar(self, arquivo):
        r = subprocess.run([NODE, "--test", "--test-force-exit",
                            os.path.join(RAIZ, "testes", "js", arquivo)],
                           capture_output=True, text=True, timeout=180, cwd=RAIZ)
        saida = "\n".join(l for l in (r.stdout + r.stderr).splitlines()
                          if not l.startswith('{"type"'))
        self.assertEqual(r.returncode, 0, saida[-4000:])
        self.assertIn("# fail 0", saida)
        return saida

    def test_pecas_puras(self):
        self.assertIn("# pass 24", self.rodar("conversa-ui.test.js"))

    def test_no_dom(self):
        self.rodar("conversa-ui-dom.test.js")

    def test_midia_e_historico_no_dom(self):
        # prévia das entregas, lightbox, "Colocar na timeline", barra do topo
        # e histórico (0.22.1). Sem jsdom na máquina, o node marca "skipped".
        saida = self.rodar("conversa-ui-midia-dom.test.js")
        if "# skipped 0" in saida:
            self.assertIn("# pass 9", saida)


if __name__ == "__main__":
    unittest.main()
