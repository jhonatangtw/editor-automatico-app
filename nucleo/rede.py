"""
Fazer o HTTPS funcionar em máquina que não é a de quem construiu o app.

O defeito, encontrado no Mac de um aluno: TODA chamada HTTPS do app respondia
`SSL: CERTIFICATE_VERIFY_FAILED` — versão do plugin, aviso de atualização,
login, download. Parecia problema de rede dele; não era.

O Python guarda o caminho do pacote de certificados que existia na máquina onde
ele foi COMPILADO. Aqui isso é `/opt/homebrew/etc/openssl@3/cert.pem`, um
caminho do Homebrew; no runner do CI é outro. Na máquina do aluno — que não tem
Homebrew — esse arquivo simplesmente não existe, então não há autoridade
certificadora nenhuma e qualquer `https://` falha na verificação.

⚠️ É invisível para quem desenvolve: no `.venv` do Homebrew funciona sempre. Só
aparece no app empacotado, na máquina de quem não instalou nada.

O conserto é `SSL_CERT_FILE` apontando para um pacote que EXISTE ali. A ordem
tenta o que viaja dentro do app primeiro, e só então o do sistema:

  1. `certifi` — vai empacotado, então está garantido em qualquer máquina;
  2. `/etc/ssl/cert.pem` — existe em todo macOS, mesmo sem Homebrew;
  3. o padrão do Python — no Windows ele lê a loja de certificados do sistema,
     que já funciona (por isso o Windows nunca deu este erro).
"""

import os
import ssl

_escolhido = None


def _candidatos():
    try:
        import certifi
        yield "certifi", certifi.where()
    except Exception:
        pass
    for p in ("/etc/ssl/cert.pem",                    # macOS, sempre existe
              "/usr/local/etc/openssl@3/cert.pem",
              "/opt/homebrew/etc/openssl@3/cert.pem",
              "/etc/pki/tls/certs/ca-bundle.crt"):
        yield "sistema", p


def preparar():
    """Chame UMA vez, no arranque, antes de qualquer HTTPS."""
    global _escolhido
    if _escolhido:
        return _escolhido

    atual = os.environ.get("SSL_CERT_FILE")
    if atual and os.path.isfile(atual):
        _escolhido = {"fonte": "ambiente", "arquivo": atual}
        return _escolhido

    # o caminho embutido no Python só serve se o arquivo estiver LÁ
    padrao = ssl.get_default_verify_paths().openssl_cafile
    if padrao and os.path.isfile(padrao):
        _escolhido = {"fonte": "python", "arquivo": padrao}
        return _escolhido

    for fonte, caminho in _candidatos():
        if caminho and os.path.isfile(caminho):
            os.environ["SSL_CERT_FILE"] = caminho
            _escolhido = {"fonte": fonte, "arquivo": caminho}
            return _escolhido

    _escolhido = {"fonte": "nenhuma", "arquivo": None}
    return _escolhido


def contexto():
    preparar()
    return ssl.create_default_context()


def explicar(erro):
    """Transforma o erro de certificado em algo que se possa agir.

    "CERTIFICATE_VERIFY_FAILED" não diz a ninguém o que fazer, e mandou um aluno
    procurar problema na internet dele."""
    if "CERTIFICATE_VERIFY" not in str(erro):
        return str(erro)
    d = preparar()
    if d["arquivo"]:
        return ("A conexão segura falhou mesmo com os certificados em %s. Se você "
                "está numa rede de empresa com filtro, ela pode estar no meio da "
                "conexão." % d["arquivo"])
    return ("Este computador está sem o pacote de certificados que o app usa para "
            "falar com a internet com segurança. Atualize o app — a versão nova "
            "leva o pacote junto.")
