"""
Voz — ElevenLabs, e só ela.

Decisão do usuário (17/08/2026): **não usar o gerador de voz do MiniMax.**
A ElevenLabs é a única porta de voz do app.

⚠️ Isso é sobre VOZ, não sobre o MiniMax inteiro: o **MiniMax Hailuo segue no
catálogo de motores de vídeo** (`gerar.MOTORES_VIDEO`) e é a escolha certa para
transição de imagem inicial para final. Cortar o MiniMax por engano tiraria um
motor de vídeo que o app usa.

Isso conversa com a trava do b-roll: no Seedance o app já força
`generate_audio: false`, porque áudio de IA embutido no b-roll briga com a voz
do avatar e não separa depois. As duas regras dizem a mesma coisa por caminhos
diferentes — som neste app vem da ElevenLabs ou do bruto, de mais lugar nenhum.

Convenção da casa: voz americana.
"""

import json
import os
import urllib.error
import urllib.request

from . import chaves, projetos

BASE = "https://api.elevenlabs.io/v1"

# eleven_multilingual_v2 segura PT-BR e EN com a mesma voz; o v3 ainda não está
# liberado para todas as contas, então o padrão é o que funciona em qualquer uma.
MODELO = "eleven_multilingual_v2"


class SemChave(RuntimeError):
    pass


class Falhou(RuntimeError):
    pass


def _chave():
    k = chaves.ler("elevenlabs")
    if not k:
        raise SemChave("Conecte a ElevenLabs na aba Contas — é a única fonte de "
                       "voz deste app.")
    return k


def _pedir(rota, corpo=None, binario=False, metodo=None):
    req = urllib.request.Request(
        BASE + rota,
        data=json.dumps(corpo).encode("utf-8") if corpo is not None else None,
        method=metodo or ("POST" if corpo is not None else "GET"),
        headers={"xi-api-key": _chave(), "Content-Type": "application/json",
                 "Accept": "audio/mpeg" if binario else "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read() if binario else json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = ""
        try:
            detalhe = e.read().decode("utf-8", "replace")[:250]
        except Exception:
            pass
        if e.code in (401, 403):
            raise Falhou("A ElevenLabs recusou a chave. Confira na aba Contas.")
        if e.code == 422:
            raise Falhou("A ElevenLabs recusou o pedido: " + detalhe)
        if e.code == 429:
            raise Falhou("Limite da ElevenLabs atingido. Espere e tente de novo.")
        raise Falhou("ElevenLabs respondeu HTTP %d. %s" % (e.code, detalhe))
    except Exception as e:
        raise Falhou("Não consegui falar com a ElevenLabs: " + str(e))


def vozes():
    """As vozes da conta. A tela mostra para o usuário escolher antes de gerar."""
    d = _pedir("/voices")
    saida = []
    for v in d.get("voices", []):
        rot = v.get("labels") or {}
        saida.append({
            "id": v.get("voice_id"),
            "nome": v.get("name"),
            "sotaque": rot.get("accent", ""),
            "genero": rot.get("gender", ""),
            "idade": rot.get("age", ""),
            "uso": rot.get("use_case", ""),
            "amostra": v.get("preview_url"),
            # convenção da casa: voz americana
            "recomendada": (rot.get("accent") or "").lower() in ("american", "us"),
        })
    saida.sort(key=lambda x: (not x["recomendada"], x["nome"] or ""))
    return saida


def assinatura():
    """Quanto sobra de caractere — é o 'saldo' da ElevenLabs."""
    try:
        d = _pedir("/user")
        s = d.get("subscription") or {}
        usado, teto = s.get("character_count"), s.get("character_limit")
        return {"usado": usado, "teto": teto,
                "sobra": (teto - usado) if (usado is not None and teto) else None,
                "plano": s.get("tier")}
    except Exception:
        return None


def orcamento_voz(texto):
    """A ElevenLabs cobra por CARACTERE, não por chamada. Dizer isso antes evita
    o susto de gerar uma VSL inteira e queimar a cota do mês."""
    n = len(texto or "")
    a = assinatura()
    return {
        "caracteres": n,
        "sobra": (a or {}).get("sobra"),
        "suficiente": (a is None) or (a.get("sobra") is None) or (a["sobra"] >= n),
        "plano": (a or {}).get("plano"),
    }


def falar(pid, texto, voice_id, nome="voz.mp3", estabilidade=0.5, similaridade=0.75):
    """Gera o áudio e grava no projeto.

    A copy vai INTEIRA e sem reescrita: a etapa 2 já validou esse texto contra a
    fala real, e mexer nele aqui invalidaria a validação."""
    if not (texto or "").strip():
        raise Falhou("Sem texto para narrar.")
    if not voice_id:
        raise Falhou("Escolha uma voz antes.")

    audio = _pedir("/text-to-speech/" + voice_id, corpo={
        "text": texto,
        "model_id": MODELO,
        "voice_settings": {"stability": estabilidade,
                           "similarity_boost": similaridade},
    }, binario=True)

    pasta = projetos.caminho(pid, "audio")
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, nome)
    tmp = destino + ".parte"
    with open(tmp, "wb") as f:
        f.write(audio)
    os.replace(tmp, destino)
    return {"arquivo": destino, "caracteres": len(texto), "voz": voice_id,
            "modelo": MODELO}
