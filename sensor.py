# ============================================================
#  sensor.py  -  Simulacao do sensor de temperatura
# ============================================================

import uuid
import random
from datetime import datetime
from config import ID_SENSOR, TEMP_MIN, TEMP_MAX, LIMITE_ALERTA, LIMITE_CRITICO


def gerar_leitura() -> dict:
    """
    Gera uma leitura simulada de temperatura.

    Retorna um dict pronto para ser serializado em JSON e enviado ao servidor:
        {
            "id":          str  - UUID unico da requisicao (idempotencia),
            "id_sensor":   str  - identificador do sensor,
            "temperatura": float - valor gerado aleatoriamente,
            "data_hora":   str  - ISO-8601 local,
        }
    """
    temperatura = round(random.uniform(TEMP_MIN, TEMP_MAX), 2)
    return {
        "id":          str(uuid.uuid4()),
        "id_sensor":   ID_SENSOR,
        "temperatura": temperatura,
        "data_hora":   datetime.now().isoformat(timespec="seconds"),
    }


def status_local(temperatura: float) -> str:
    """
    Determina o status com as mesmas regras do servidor.
    Usado para exibicao imediata *antes* da resposta chegar.
    """
    if temperatura >= LIMITE_CRITICO:
        return "Critico"
    if temperatura >= LIMITE_ALERTA:
        return "Alerta"
    return "Normal"
