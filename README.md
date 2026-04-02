# Cliente – Monitor de Temperatura

Camada de cliente do sistema distribuído de monitoramento de sensores.  
Interface gráfica em **Tkinter**, comunicação HTTP sem dependências externas.

## Estrutura de arquivos

```
client/
├── main.py        # Ponto de entrada – execute este arquivo
├── config.py      # Todas as configurações (URL, limiares, intervalo)
├── sensor.py      # Geração de leituras simuladas e avaliação local de status
├── api_client.py  # Envio HTTP assíncrono ao servidor (thread separada)
├── history.py     # Armazenamento em memória do histórico local
└── gui.py         # Interface gráfica Tkinter
```

## Pré-requisitos

- Python 3.8 ou superior  
- Apenas bibliotecas da stdlib (`tkinter`, `uuid`, `urllib`, `threading`, `queue`)

## Configuração

Abra `config.py` e ajuste:

| Variável | Padrão | Descrição |
|---|---|---|
| `SERVER_HOST` | `127.0.0.1` | IP ou hostname do servidor Flask |
| `SERVER_PORT` | `5000` | Porta do servidor |
| `SENSOR_ID` | `SENSOR-01` | Identificador deste sensor |
| `SEND_INTERVAL_MS` | `3000` | Intervalo de envio automático (ms) |
| `THRESHOLD_ALERTA` | `10.0` | °C mínimo para status Alerta |
| `THRESHOLD_CRITICO` | `15.0` | °C mínimo para status Crítico |

## Execução

```bash
cd client
python main.py
```

## Funcionalidades da GUI

| Elemento | Descrição |
|---|---|
| Display central | Temperatura atual colorida por status |
| **ENVIAR LEITURA** | Envia uma leitura manualmente |
| **AUTO** | Liga/desliga envio periódico automático |
| **LIMPAR HISTÓRICO** | Apaga registros da tabela local |
| Contadores | Totais acumulados por status (Normal / Alerta / Crítico / Falha) |
| Tabela | Histórico das últimas 50 leituras com UUID, timestamp e status |
| Barra inferior | Log da última operação realizada |

## Comportamento offline

Se o servidor estiver inacessível, a leitura é marcada como **Falha** no histórico local com o status estimado localmente, e a GUI exibe a mensagem de erro na barra inferior.  O cliente **nunca trava** aguardando resposta.

## Formato JSON enviado ao servidor

```json
{
  "id":          "550e8400-e29b-41d4-a716-446655440000",
  "sensor_id":   "SENSOR-01",
  "temperatura": 12.47,
  "timestamp":   "2024-06-01T14:32:10"
}
```

## Formato JSON esperado do servidor

```json
{
  "status_logico": "Alerta"
}
```
