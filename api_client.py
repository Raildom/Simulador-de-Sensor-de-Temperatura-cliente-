# ============================================================
#  api_client.py  -  Comunicacao HTTP com o servidor
# ============================================================

import json
import threading
import urllib.request
import urllib.error
from typing import Callable
from config import SERVER_URL, REQUEST_TIMEOUT


# --------------------------------------------------------------------------
# Tipos de callback esperados pela GUI
# --------------------------------------------------------------------------
# on_success(resposta: dict)      -> chamado quando o servidor responde 2xx
# on_error(mensagem: str)         -> chamado em falha de rede / resposta invalida
# --------------------------------------------------------------------------


def enviar_leitura(
    leitura: dict,
    on_success: Callable[[dict], None],
    on_error:   Callable[[str],  None],
) -> None:
    """
    Envia *leitura* (dict) ao servidor via POST JSON em uma thread separada,
    evitando bloquear a GUI.  Os callbacks sao invocados na thread de rede;
    a GUI deve usar `after()` ou filas para atualizar widgets com seguranca.
    """
    thread = threading.Thread(
        target=_post_worker,
        args=(leitura, on_success, on_error),
        daemon=True,
    )
    thread.start()


# --------------------------------------------------------------------------
# Worker interno (roda em thread separada)
# --------------------------------------------------------------------------

def _post_worker(
    leitura: dict,
    on_success: Callable[[dict], None],
    on_error:   Callable[[str],  None],
) -> None:
    payload = json.dumps(leitura).encode("utf-8")
    req = urllib.request.Request(
        url=SERVER_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept":        "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                on_error(f"Resposta invalida do servidor: {raw[:120]}")
                return
            on_success(data)

    except urllib.error.HTTPError as exc:
        # Tenta extrair mensagem de erro do corpo da resposta
        try:
            corpo = exc.read().decode("utf-8")
            detalhes = json.loads(corpo).get("erro", corpo)
        except Exception:
            detalhes = str(exc)
        on_error(f"HTTP {exc.code}: {detalhes}")

    except urllib.error.URLError as exc:
        on_error(f"Servidor inacessivel - {exc.reason}")

    except TimeoutError:
        on_error("Tempo-limite da requisicao esgotado.")

    except Exception as exc:
        on_error(f"Erro inesperado: {exc}")
