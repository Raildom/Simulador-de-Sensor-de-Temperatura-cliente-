# ============================================================
#  historico.py  -  Historico local de leituras
# ============================================================

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, List
from config import MAX_ITENS_HISTORICO


@dataclass
class Registro:
    """Representa uma leitura armazenada no historico local."""
    uuid:        str
    sensor_id:   str
    temperatura: float
    status:      str              # vem do servidor (ou local em caso de falha)
    timestamp:   str
    enviado:     bool = True      # False = falha de rede
    erro:        str  = ""


class Historico:
    """
    Mantem as ultimas MAX_ITENS_HISTORICO leituras em memoria.
    Thread-safe para leitura; gravacao deve ocorrer na thread principal.
    """

    def __init__(self) -> None:
        self._itens: Deque[Registro] = deque(maxlen=MAX_ITENS_HISTORICO)

    # ------------------------------------------------------------------
    def adicionar(
        self,
        leitura:   dict,
        status:    str,
        enviado:   bool = True,
        erro:      str  = "",
    ) -> Registro:
        reg = Registro(
            uuid        = leitura["id"],
            sensor_id   = leitura["sensor_id"],
            temperatura = leitura["temperatura"],
            status      = status,
            timestamp   = leitura.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            enviado     = enviado,
            erro        = erro,
        )
        self._itens.appendleft(reg)   # mais recente no topo
        return reg

    # ------------------------------------------------------------------
    def itens(self) -> List[Registro]:
        """Retorna copia da lista, mais recente primeiro."""
        return list(self._itens)

    # ------------------------------------------------------------------
    def total(self) -> int:
        return len(self._itens)

    # ------------------------------------------------------------------
    def contagens(self) -> dict:
        """Retorna {Normal: n, Alerta: n, Critico: n, Falha: n}."""
        totais = {"Normal": 0, "Alerta": 0, "Critico": 0, "Falha": 0}
        for r in self._itens:
            if not r.enviado:
                totais["Falha"] += 1
            else:
                totais[r.status] = totais.get(r.status, 0) + 1
        return totais
