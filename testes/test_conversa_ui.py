"""
Roda os testes JS da Conversa (testes/js/) pelo node, dentro da suíte Python
— assim `python -m pytest testes/` (ou unittest) cobre a tela também.

- conversa-ui.test.js: markdown seguro, rótulos em português, menu "/" e "@",
  fila, painel de tarefas, /custo e conversas antigas abrindo na tela nova.
- conversa-ui-dom.test.js: o mesmo componente no DOM (jsdom da banca do Tools
  PRO, se existir na máquina): teclado do menu, fila visível, Esc, ↑.
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
        self.assertIn("# pass 21", self.rodar("conversa-ui.test.js"))

    def test_no_dom(self):
        self.rodar("conversa-ui-dom.test.js")


if __name__ == "__main__":
    unittest.main()
