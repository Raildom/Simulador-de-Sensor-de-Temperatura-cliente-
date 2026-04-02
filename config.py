# ============================================================
#  config.py  -  Configuracoes centrais do cliente
# ============================================================

# --- Servidor -----------------------------------------------------------
SERVER_HOST = "127.0.0.1"   # Altere para o IP/hostname do servidor real
SERVER_PORT = 5000
SERVER_URL  = f"http://{SERVER_HOST}:{SERVER_PORT}/leitura"

# Tempo-limite (segundos) para cada requisicao HTTP
REQUEST_TIMEOUT = 5

# --- Sensor -------------------------------------------------------------
SENSOR_ID       = "SENSOR-01"
TEMP_MIN        = 0.0     # C minimo gerado
TEMP_MAX        = 100.0      # C maximo gerado
SEND_INTERVAL_MS = 3000     # intervalo automatico de envio (ms)

# --- Regras de status (espelhadas localmente para exibicao imediata) ----
THRESHOLD_ALERTA   = 30.0   # C  ->  Alerta
THRESHOLD_CRITICO  = 60.0   # C  ->  Critico

# --- Historico local ----------------------------------------------------
MAX_HISTORY_ITEMS = 10      # linhas exibidas na tabela
