"""
Skills que viajam no app: o instalador (versão, idempotência, cópia do aluno
intocada, backup fora da pasta de skills, Claude + Codex) e a AUDITORIA do
retrato que vai no pacote (nenhum segredo, caminho pessoal ou cliente).

Tudo em pasta temporária: nada encosta em ~/.claude nem em ~/.codex.

    .venv/bin/python -m unittest discover -s testes -v
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import skills  # noqa: E402

RETRATO = os.path.join(RAIZ, "skills")


def escrever(p, texto):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(texto)


def ler(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


class Instalador(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ea-skills-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.retrato = os.path.join(self.tmp, "retrato")
        for nome in ("alfa", "beta"):
            escrever(os.path.join(self.retrato, nome, "SKILL.md"),
                     "---\nname: %s\ndescription: skill %s\n---\n# %s\n" % (nome, nome, nome))
            escrever(os.path.join(self.retrato, nome, "scripts", "x.py"), "print(1)\n")
        self.claude = os.path.join(self.tmp, "home", ".claude", "skills")
        self.codex = os.path.join(self.tmp, "home", ".codex", "skills")
        self.backup = os.path.join(self.tmp, "home", ".editorblackbelt", "skills-anteriores")
        for nome, valor in (("DESTINO", self.claude), ("DESTINO_CODEX", self.codex),
                            ("BACKUP", self.backup), ("_raiz", lambda: self.retrato)):
            p = mock.patch.object(skills, nome, valor)
            p.start()
            self.addCleanup(p.stop)
        # sem Codex por padrão: nem pasta, nem comando
        p = mock.patch.object(skills.shutil, "which", return_value=None)
        p.start()
        self.addCleanup(p.stop)

    def acoes(self, r, para="claude"):
        return {f["skill"]: f["acao"] for f in r["feitos"] if f["para"] == para}

    def test_instala_o_que_falta_com_marca_de_versao(self):
        r = skills.instalar()
        self.assertEqual(self.acoes(r), {"alfa": "instalada", "beta": "instalada"})
        m = json.loads(ler(os.path.join(self.claude, "alfa", skills.MARCA)))
        self.assertEqual(m["hash"], skills.hash_pasta(os.path.join(self.retrato, "alfa")))
        self.assertEqual(skills.situacao("alfa", self.claude), "em_dia")
        self.assertEqual(skills.estado()["faltam"], [])

    def test_idempotente(self):
        skills.instalar()
        antes = {n: skills.hash_pasta(os.path.join(self.claude, n)) for n in ("alfa", "beta")}
        marca = ler(os.path.join(self.claude, "alfa", skills.MARCA))
        r = skills.instalar()
        self.assertEqual(set(self.acoes(r).values()), {"já estava em dia"})
        self.assertEqual(r["novas"], 0)
        self.assertEqual(ler(os.path.join(self.claude, "alfa", skills.MARCA)), marca)
        for n, h in antes.items():
            self.assertEqual(skills.hash_pasta(os.path.join(self.claude, n)), h)
        self.assertFalse(os.path.exists(self.backup))

    def test_retrato_novo_atualiza_o_que_e_nosso(self):
        skills.instalar()
        escrever(os.path.join(self.retrato, "alfa", "SKILL.md"), "---\nname: alfa\n---\nversão 2\n")
        self.assertEqual(skills.estado()["atualizar"], ["alfa"])
        r = skills.instalar()
        self.assertEqual(self.acoes(r)["alfa"], "atualizada")
        self.assertIn("versão 2", ler(os.path.join(self.claude, "alfa", "SKILL.md")))
        self.assertFalse(os.path.exists(self.backup))      # era nossa e intacta: sem backup

    def test_copia_mexida_pelo_aluno_nao_e_tocada(self):
        skills.instalar()
        meu = os.path.join(self.claude, "alfa", "SKILL.md")
        escrever(meu, "minha versão\n")
        escrever(os.path.join(self.retrato, "alfa", "SKILL.md"), "versão 2 do app\n")
        self.assertEqual(skills.situacao("alfa", self.claude), "do_usuario")
        r = skills.instalar()
        self.assertEqual(self.acoes(r)["alfa"], "mantida (cópia sua)")
        self.assertEqual(ler(meu), "minha versão\n")
        self.assertEqual(r["mantidas"], 1)
        self.assertFalse(os.path.exists(self.backup))

    def test_reinstalar_guarda_a_do_aluno_fora_da_pasta_de_skills(self):
        skills.instalar()
        escrever(os.path.join(self.claude, "alfa", "SKILL.md"), "minha versão\n")
        r = skills.instalar(substituir=True)
        f = [x for x in r["feitos"] if x["skill"] == "alfa"][0]
        self.assertEqual(f["acao"], "substituída")
        self.assertTrue(f["anterior"].startswith(self.backup))
        self.assertEqual(ler(os.path.join(f["anterior"], "SKILL.md")), "minha versão\n")
        # nada de alfa.anterior-* ao lado: o Claude veria duas skills com o mesmo nome
        self.assertEqual(sorted(os.listdir(self.claude)), ["alfa", "beta"])
        self.assertEqual(skills.situacao("alfa", self.claude), "em_dia")

    def test_pasta_sem_marca_diferente_e_do_dono(self):
        # máquina do autor: a skill instalada é a FONTE, sem a nossa marca
        escrever(os.path.join(self.claude, "alfa", "SKILL.md"), "fonte do autor\n")
        r = skills.instalar()
        self.assertEqual(self.acoes(r)["alfa"], "mantida (cópia sua)")
        self.assertEqual(ler(os.path.join(self.claude, "alfa", "SKILL.md")), "fonte do autor\n")
        self.assertFalse(os.path.exists(os.path.join(self.claude, "alfa", skills.MARCA)))

    def test_pasta_sem_marca_identica_passa_a_ser_nossa(self):
        shutil.copytree(os.path.join(self.retrato, "alfa"), os.path.join(self.claude, "alfa"))
        r = skills.instalar()
        self.assertEqual(self.acoes(r)["alfa"], "já estava em dia")
        self.assertTrue(os.path.isfile(os.path.join(self.claude, "alfa", skills.MARCA)))

    def test_uso_da_skill_nao_a_faz_parecer_mexida(self):
        skills.instalar()
        escrever(os.path.join(self.claude, "alfa", "scripts", "__pycache__", "x.cpython-314.pyc"), "lixo")
        escrever(os.path.join(self.claude, "alfa", ".DS_Store"), "lixo")
        self.assertEqual(skills.situacao("alfa", self.claude), "em_dia")

    def test_codex_recebe_as_mesmas_skills_quando_existe(self):
        os.makedirs(os.path.dirname(self.codex))
        r = skills.instalar()
        self.assertEqual(self.acoes(r, "codex"), {"alfa": "instalada", "beta": "instalada"})
        self.assertTrue(os.path.isfile(os.path.join(self.codex, "beta", "SKILL.md")))
        self.assertIn(self.codex, r["destinos"])

    def test_sem_codex_nao_cria_pasta_dele(self):
        skills.instalar()
        self.assertFalse(os.path.exists(os.path.dirname(self.codex)))


# ---------------------------------------------------------------- o retrato que vai no app

# Independente do limpar-skills.py de propósito: se alguém afrouxar a limpeza,
# este teste continua barrando.
PROIBIDO = {
    "caminho pessoal": r"/Users/|C:\\\\Users\\\\|jhonwill|~/Documents/|~/Library/CloudStorage|/Volumes/|hw-creative",
    "chave ou token": (r"sk-[A-Za-z0-9_-]{16,}|sk-ant-|AKIA[0-9A-Z]{12}|AIza[0-9A-Za-z_-]{20,}|ghp_[A-Za-z0-9]{20,}"
                       r"|xox[abprs]-|hf_[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"
                       r"|Bearer [A-Za-z0-9._-]{20,}"
                       r"|(?i:api[_-]?key|secret|token|password)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_\-]{12,}"),
    "link interno": r"(?i)drive\.google|docs\.google|frame\.io|slack\.com|monday\.com|notion\.so|hostinger",
    "casa ou cliente": (r"\bH&W\b|HW Publishing|hw-publishing|LeafTide|Leaftide|CardioFlush|MemoFlow|LinfaFlow"
                        r"|GlucoJaro|Ameripel|\bJhon\b|Jhonatan|jhonatangtw|\bMarcelo\b"),
}


# A MESMA exceção do limpar-skills.py: o primeiro nome do autor do curso é a
# vitrine da skill do Reels — só a palavra exata, só dentro daquela pasta.
PERMITIDO = {"editor-de-reels-do-jhon": {"casa ou cliente": r"Jhon"}}


def permitido(rel, tipo, trecho):
    pad = PERMITIDO.get(rel.split(os.sep)[0], {}).get(tipo)
    return bool(pad and re.fullmatch(pad, trecho))


class RetratoDoPacote(unittest.TestCase):

    def arquivos(self):
        for d, subs, arqs in os.walk(RETRATO):
            subs[:] = [s for s in subs if s != "__pycache__"]
            for a in arqs:
                yield os.path.join(d, a)

    def test_nenhum_segredo_caminho_pessoal_ou_cliente(self):
        achados = []
        for p in self.arquivos():
            try:
                t = ler(p)
            except (UnicodeDecodeError, OSError):
                continue
            for tipo, pad in PROIBIDO.items():
                for m in re.finditer(pad, t):
                    if permitido(os.path.relpath(p, RETRATO), tipo, m.group(0)):
                        continue
                    achados.append("%s:%d [%s] %s" % (os.path.relpath(p, RETRATO),
                                   t.count("\n", 0, m.start()) + 1, tipo, m.group(0)[:50]))
        self.assertEqual(achados, [], "\n".join(achados))

    def test_skills_pessoais_ficam_fora(self):
        for nome in ("motion-viral-jhon1", "gemini-omni", "cortar-aula", "painel-hw-edicao", "replicador-hw"):
            self.assertFalse(os.path.exists(os.path.join(RETRATO, nome)), nome)
        self.assertFalse(os.path.exists(os.path.join(RETRATO, "hooks-meat-hook", "referencia")))

    def test_skill_mestra_e_as_pedidas_estao_no_pacote(self):
        for nome in ("skill-black-belt", "blackbelt-omni", "editor-automatico-de-broll", "hooks-meat-hook",
                     "motion-omni-vsl", "vibe-motion", "photorealism-prompts", "video-prompt-builder",
                     "motion-design", "clone-ad-validado", "plataforma-ia-higgsfield", "boas-praticas-black-belt"):
            self.assertTrue(os.path.isfile(os.path.join(RETRATO, nome, "SKILL.md")), nome)

    def test_cada_skill_tem_skill_md_com_o_nome_da_pasta(self):
        for nome in os.listdir(RETRATO):
            p = os.path.join(RETRATO, nome)
            if not os.path.isdir(p):
                continue
            cab = ler(os.path.join(p, "SKILL.md")).split("---")[1]
            self.assertRegex(cab, r"(?m)^name:\s*%s\s*$" % re.escape(nome))

    def test_fonte_json_bate_com_o_conteudo(self):
        fonte = json.loads(ler(os.path.join(RETRATO, "FONTE.json")))
        pastas = sorted(n for n in os.listdir(RETRATO) if os.path.isdir(os.path.join(RETRATO, n)))
        self.assertEqual(sorted(fonte["skills"]), pastas)
        for n in pastas:
            self.assertEqual(fonte["skills"][n], skills.hash_pasta(os.path.join(RETRATO, n)), n)


class SkillsNovas(unittest.TestCase):
    """As três que levam o que se aprendeu nas sessões: cada uma com a regra que a justifica."""

    def ler_skill(self, nome):
        return ler(os.path.join(RETRATO, nome, "SKILL.md"))

    def test_plataforma_nunca_pede_a_chave(self):
        t = self.ler_skill("plataforma-ia-higgsfield")
        self.assertIn("SUA_CHAVE_AQUI", t)
        self.assertIn("variável de ambiente", t)
        prompt = ler(os.path.join(RETRATO, "plataforma-ia-higgsfield", "references", "prompt-de-design.md"))
        self.assertIn("Nunca coloque a minha chave de API dentro do código", prompt)

    def test_clone_pede_aprovacao_e_prova_lip_sync_sem_correlacao(self):
        t = self.ler_skill("clone-ad-validado")
        for trecho in ("Aprovação antes de cada gasto", "Avatar IV", "F0", "Nunca sobra imagem da pessoa antiga",
                       "silêncio", "Nunca reprove por correlação"):
            self.assertIn(trecho, t)
        for s in ("f0_voz.py", "tts_elevenlabs.py", "encaixar_voz.py", "offset_audio.py", "qc_lipsync.py",
                  "folha_original_x_clone.py"):
            self.assertTrue(os.path.isfile(os.path.join(RETRATO, "clone-ad-validado", "scripts", s)), s)
            self.assertIn(s, t)

    def test_tts_le_a_chave_so_do_ambiente(self):
        t = ler(os.path.join(RETRATO, "clone-ad-validado", "scripts", "tts_elevenlabs.py"))
        self.assertIn('os.environ.get("ELEVENLABS_API_KEY"', t)
        self.assertNotIn(".env", t.replace("os.environ", ""))

    def test_boas_praticas_tem_as_sete_ferramentas(self):
        t = self.ler_skill("boas-praticas-black-belt")
        for secao in ("## Higgsfield", "## HeyGen", "## ElevenLabs", "## HyperFrames", "## Premiere / Tools PRO",
                      "## ffmpeg / Whisper", "## QC", "## Conferir um job"):
            self.assertIn(secao, t)
        self.assertGreater(t.count("- Sintoma:"), 30)


class AuditoriaDaSkillDoReels(unittest.TestCase):
    """A exceção do nome é estreita: só "Jhon", só na pasta da skill do Reels."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("limpar_skills", os.path.join(RAIZ, "limpar-skills.py"))
        self.ls = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ls)
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def escrever(self, rel, texto):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(texto)

    def test_nome_do_autor_passa_so_na_skill_do_reels(self):
        self.escrever("editor-de-reels-do-jhon/SKILL.md", "---\nname: editor-de-reels-do-jhon\n---\nO Reels do Jhon.\n")
        self.escrever("outra/SKILL.md", "Estilo do Jhon.\n")
        achados = self.ls.auditar(self.tmp)
        self.assertEqual([(a[0].split(os.sep)[0], a[3]) for a in achados], [("outra", "Jhon")])

    def test_o_resto_continua_barrado_dentro_dela(self):
        self.escrever("editor-de-reels-do-jhon/SKILL.md",
                      "Jhonatan\n/Users/fulano/x\njhonatangtw\nLeafTide\n")
        tipos = sorted(a[2] for a in self.ls.auditar(self.tmp))
        self.assertEqual(tipos, ["caminho pessoal", "casa ou cliente", "casa ou cliente", "casa ou cliente"])

    def test_sincronizar_so_leva_skill_marcada_como_pronta(self):
        with open(os.path.join(RAIZ, "sincronizar-skills.sh"), encoding="utf-8") as f:
            sh = f.read()
        self.assertIn("editor-de-reels-do-jhon", sh)
        self.assertIn('"$ALUNOS/$s/.pronta"', sh)
        self.assertIn("--exclude '.pronta'", sh)


if __name__ == "__main__":
    unittest.main()
