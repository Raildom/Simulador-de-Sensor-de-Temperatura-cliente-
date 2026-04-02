# ============================================================
#  cliente_api.py  -  Comunicacao HTTP com o servidor
# ============================================================

import json
import threading
import urllib.request
import urllib.error
from typing import Callable
from config import SERVIDOR_URL, TEMPO_LIMITE_REQUISICAO


# --------------------------------------------------------------------------
# Tipos de callback esperados pela GUI
# --------------------------------------------------------------------------
# ao_sucesso(resposta: dict)      -> chamado quando o servidor responde 2xx
# ao_erro(mensagem: str)          -> chamado em falha de rede / resposta invalida
# --------------------------------------------------------------------------


def enviar_leitura(
    leitura: dict,
    ao_sucesso: Callable[[dict], None],
    ao_erro:    Callable[[str],  None],
) -> None:
    """
    Envia *leitura* (dict) ao servidor via POST JSON em uma thread separada,
    evitando bloquear a GUI.  Os callbacks sao invocados na thread de rede;
    a GUI deve usar `after()` ou filas para atualizar widgets com seguranca.
    """
    thread = threading.Thread(
        target=_trabalhador_post,
        args=(leitura, ao_sucesso, ao_erro),
        daemon=True,
    )
    thread.start()


# --------------------------------------------------------------------------
# Trabalhador interno (roda em thread separada)
# --------------------------------------------------------------------------

def _trabalhador_post(
    leitura: dict,
    ao_sucesso: Callable[[dict], None],
    ao_erro:    Callable[[str],  None],
) -> None:
    payload = json.dumps(leitura).encode("utf-8")
    requisicao = urllib.request.Request(
        url=SERVIDOR_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept":        "application/json",
        },
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=TEMPO_LIMITE_REQUISICAO) as resposta:
            bruto = resposta.read().decode("utf-8")
            try:
                dados = json.loads(bruto)
            except json.JSONDecodeError:
                ao_erro(f"Resposta invalida do servidor: {bruto[:120]}")
                return
            ao_sucesso(dados)

    except urllib.error.HTTPError as exc:
        # Tenta extrair mensagem de erro do corpo da resposta
        try:
            corpo = exc.read().decode("utf-8")
            detalhes = json.loads(corpo).get("erro", corpo)
        except Exception:
            detalhes = str(exc)
        ao_erro(f"HTTP {exc.code}: {detalhes}")

    except urllib.error.URLError as exc:
        ao_erro(f"Servidor inacessivel - {exc.reason}")

    except TimeoutError:
        ao_erro("Tempo-limite da requisicao esgotado.")

    except Exception as exc:
        ao_erro(f"Erro inesperado: {exc}")
