# ============================================================
#  config.py  -  Configuracoes centrais do cliente
# ============================================================

# --- Servidor -----------------------------------------------------------
SERVIDOR_HOST = "127.0.0.1"   # Altere para o IP/hostname do servidor real
SERVIDOR_PORTA = 8000
SERVIDOR_URL  = f"http://{SERVIDOR_HOST}:{SERVIDOR_PORTA}/leituras/"

# Tempo-limite (segundos) para cada requisicao HTTP
TEMPO_LIMITE_REQUISICAO = 5

# --- Sensor -------------------------------------------------------------
ID_SENSOR       = "SENSOR-01"
TEMP_MIN        = -10.0     # C minimo gerado
TEMP_MAX        = 40.0      # C maximo gerado
INTERVALO_ENVIO_MS = 3000     # intervalo automatico de envio (ms)

# --- Regras de status (espelhadas localmente para exibicao imediata) ----
LIMITE_ALERTA   = 10.0   # C  ->  Alerta
LIMITE_CRITICO  = 20.0   # C  ->  Critico

# --- Historico local ----------------------------------------------------
MAX_ITENS_HISTORICO = 10      # linhas exibidas na tabela
