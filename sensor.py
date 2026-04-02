# ============================================================
#  sensor.py  -  Simulacao do sensor de temperatura
# ============================================================

import uuid
import random
from datetime import datetime
from config import SENSOR_ID, TEMP_MIN, TEMP_MAX, THRESHOLD_ALERTA, THRESHOLD_CRITICO


def gerar_leitura() -> dict:
    """
    Gera uma leitura simulada de temperatura.

    Retorna um dict pronto para ser serializado em JSON e enviado ao servidor:
        {
            "id":          str  - UUID unico da requisicao (idempotencia),
            "sensor_id":   str  - identificador do sensor,
            "temperatura": float - valor gerado aleatoriamente,
            "timestamp":   str  - ISO-8601 local,
        }
    """
    temperatura = round(random.uniform(TEMP_MIN, TEMP_MAX), 2)
    return {
        "id":          str(uuid.uuid4()),
        "sensor_id":   SENSOR_ID,
        "temperatura": temperatura,
        "timestamp":   datetime.now().isoformat(timespec="seconds"),
    }


def status_local(temperatura: float) -> str:
    """
    Determina o status com as mesmas regras do servidor.
    Usado para exibicao imediata *antes* da resposta chegar.
    """
    if temperatura >= THRESHOLD_CRITICO:
        return "Critico"
    if temperatura >= THRESHOLD_ALERTA:
        return "Alerta"
    return "Normal"
