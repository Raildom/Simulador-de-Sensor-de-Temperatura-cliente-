# ============================================================
#  gui.py  -  Interface grafica Tkinter
# ============================================================

import queue
import tkinter as tk
from tkinter import ttk, font as tkfont

import api_client
import sensor as modulo_sensor
from historico import Historico
from config import (
    ID_SENSOR, SERVIDOR_URL, INTERVALO_ENVIO_MS,
    LIMITE_ALERTA, LIMITE_CRITICO, MAX_ITENS_HISTORICO,
)

# -- Paleta de cores --------------------------------------------------------
CORES = {
    "fundo":           "#0f1117",
    "painel":          "#1a1d27",
    "borda":           "#2a2d3e",
    "texto":           "#e2e8f0",
    "texto_fraco":     "#64748b",
    "destaque":        "#38bdf8",
    "Normal":          "#22c55e",
    "Alerta":          "#f59e0b",
    "Critico":         "#ef4444",
    "Falha":           "#7c3aed",
    "fundo_cabecalho": "#141720",
    "linha_par":       "#1a1d27",
    "linha_impar":     "#1e2130",
}

ICONE_STATUS = {"Normal": "[OK]", "Alerta": "[!]", "Critico": "[X]", "Falha": "[F]"}


# -- Classe principal -------------------------------------------------------

class Aplicacao(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Monitor de Temperatura  |  {ID_SENSOR}")
        self.configure(bg=CORES["fundo"])
        self.minsize(760, 580)
        self.resizable(True, True)

        self._historico   = Historico()
        self._fila: queue.Queue = queue.Queue()   # comunicacao entre threads
        self._auto_ativo  = False
        self._tarefa_auto = None                  # id do `after` em execucao

        self._criar_fontes()
        self._criar_interface()
        self._processar_fila()   # inicia polling da fila de callbacks

    # -- Fontes ----------------------------------------------------------------

    def _criar_fontes(self) -> None:
        self.fonte_titulo  = tkfont.Font(family="Courier", size=15, weight="bold")
        self.fonte_rotulo  = tkfont.Font(family="Courier", size=10)
        self.fonte_grande  = tkfont.Font(family="Courier", size=36, weight="bold")
        self.fonte_status  = tkfont.Font(family="Courier", size=14, weight="bold")
        self.fonte_mono    = tkfont.Font(family="Courier", size=9)
        self.fonte_botao   = tkfont.Font(family="Courier", size=10, weight="bold")

    # -- Layout principal ------------------------------------------------------

    def _criar_interface(self) -> None:
        # -- cabecalho ----------------------------------------------------------
        cabecalho = tk.Frame(self, bg=CORES["fundo_cabecalho"], pady=10)
        cabecalho.pack(fill="x")
        tk.Label(
            cabecalho, text="< MONITOR DE SENSOR >",
            font=self.fonte_titulo, bg=CORES["fundo_cabecalho"], fg=CORES["destaque"],
        ).pack(side="left", padx=20)
        tk.Label(
            cabecalho, text=f"id: {ID_SENSOR}   servidor: {SERVIDOR_URL}",
            font=self.fonte_mono, bg=CORES["fundo_cabecalho"], fg=CORES["texto_fraco"],
        ).pack(side="right", padx=20)

        # -- linha de separacao -------------------------------------------------
        tk.Frame(self, bg=CORES["borda"], height=1).pack(fill="x")

        # -- painel central (temperatura + controles) -------------------------
        centro = tk.Frame(self, bg=CORES["fundo"])
        centro.pack(fill="x", padx=20, pady=14)

        self._criar_painel_temperatura(centro)
        self._criar_controles(centro)

        # -- painel de estatisticas ---------------------------------------------
        self._criar_barra_estatisticas()

        # -- tabela historico ---------------------------------------------------
        tk.Frame(self, bg=CORES["borda"], height=1).pack(fill="x")
        self._criar_tabela_historico()

        # -- barra de status ----------------------------------------------------
        self._criar_barra_status()

    # -- Painel de temperatura -------------------------------------------------

    def _criar_painel_temperatura(self, pai: tk.Frame) -> None:
        painel = tk.Frame(pai, bg=CORES["painel"], bd=0, relief="flat")
        painel.pack(side="left", padx=(0, 14), ipadx=20, ipady=10)

        tk.Label(painel, text="TEMPERATURA ATUAL",
                 font=self.fonte_mono, bg=CORES["painel"], fg=CORES["texto_fraco"]).pack()

        self._rotulo_temp = tk.Label(
            painel, text="--.- C",
            font=self.fonte_grande, bg=CORES["painel"], fg=CORES["texto"],
        )
        self._rotulo_temp.pack()

        self._rotulo_status = tk.Label(
            painel, text="- aguardando -",
            font=self.fonte_status, bg=CORES["painel"], fg=CORES["texto_fraco"],
        )
        self._rotulo_status.pack(pady=(0, 4))

        tk.Label(
            painel,
            text=f"Normal < {LIMITE_ALERTA}C  |  "
                 f"Alerta >= {LIMITE_ALERTA}C  |  "
                 f"Critico >= {LIMITE_CRITICO}C",
            font=self.fonte_mono, bg=CORES["painel"], fg=CORES["texto_fraco"],
        ).pack()

    # -- Controles -------------------------------------------------------------

    def _criar_controles(self, pai: tk.Frame) -> None:
        controles = tk.Frame(pai, bg=CORES["fundo"])
        controles.pack(side="left", fill="both", expand=True)

        # botao enviar manual
        self._btn_enviar = tk.Button(
            controles,
            text=">  ENVIAR LEITURA",
            font=self.fonte_botao,
            bg=CORES["destaque"], fg=CORES["fundo"],
            activebackground="#7dd3fc", activeforeground=CORES["fundo"],
            relief="flat", cursor="hand2", pady=10, padx=20,
            command=self._enviar_manual,
        )
        self._btn_enviar.pack(fill="x", pady=(0, 8))

        # botao envio automatico
        self._btn_auto = tk.Button(
            controles,
            text=f"[T]  AUTO  (a cada {INTERVALO_ENVIO_MS//1000}s)",
            font=self.fonte_botao,
            bg=CORES["borda"], fg=CORES["texto"],
            activebackground=CORES["texto_fraco"], activeforeground=CORES["texto"],
            relief="flat", cursor="hand2", pady=10, padx=20,
            command=self._alternar_auto,
        )
        self._btn_auto.pack(fill="x", pady=(0, 8))

        # botao limpar historico
        tk.Button(
            controles,
            text="[-]  LIMPAR HISTORICO",
            font=self.fonte_botao,
            bg=CORES["borda"], fg=CORES["texto_fraco"],
            activebackground=CORES["texto_fraco"], activeforeground=CORES["texto"],
            relief="flat", cursor="hand2", pady=6, padx=20,
            command=self._limpar_historico,
        ).pack(fill="x")

    # -- Barra de estatisticas -------------------------------------------------

    def _criar_barra_estatisticas(self) -> None:
        barra = tk.Frame(self, bg=CORES["painel"], pady=8)
        barra.pack(fill="x", padx=20, pady=(0, 8))

        self._rotulos_estatisticas: dict[str, tk.Label] = {}
        for status in ("Normal", "Alerta", "Critico", "Falha"):
            coluna = tk.Frame(barra, bg=CORES["painel"])
            coluna.pack(side="left", expand=True)

            tk.Label(
                coluna, text=ICONE_STATUS.get(status, "") + " " + status,
                font=self.fonte_rotulo, bg=CORES["painel"],
                fg=CORES[status],
            ).pack()

            rotulo = tk.Label(
                coluna, text="0",
                font=tkfont.Font(family="Courier", size=18, weight="bold"),
                bg=CORES["painel"], fg=CORES[status],
            )
            rotulo.pack()
            self._rotulos_estatisticas[status] = rotulo

    # -- Tabela de historico ----------------------------------------------------

    def _criar_tabela_historico(self) -> None:
        container = tk.Frame(self, bg=CORES["fundo"])
        container.pack(fill="both", expand=True, padx=20, pady=(8, 0))

        tk.Label(
            container, text="HISTORICO LOCAL",
            font=self.fonte_mono, bg=CORES["fundo"], fg=CORES["texto_fraco"],
        ).pack(anchor="w")

        colunas = ("data_hora", "temperatura", "status", "uuid")
        self._tabela = ttk.Treeview(
            container, columns=colunas, show="headings", height=10,
        )

        larguras = {"data_hora": 140, "temperatura": 100, "status": 90, "uuid": 310}
        titulos  = {"data_hora": "Data/Hora", "temperatura": "Temp (C)",
                    "status": "Status", "uuid": "UUID"}
        for coluna in colunas:
            self._tabela.heading(coluna, text=titulos[coluna])
            self._tabela.column(coluna, width=larguras[coluna], anchor="center")

        # barra de rolagem
        barra_rolagem = ttk.Scrollbar(container, orient="vertical", command=self._tabela.yview)
        self._tabela.configure(yscrollcommand=barra_rolagem.set)
        self._tabela.pack(side="left", fill="both", expand=True)
        barra_rolagem.pack(side="right", fill="y")

        # tags de cor por status
        self._tabela.tag_configure("Normal",  foreground=CORES["Normal"])
        self._tabela.tag_configure("Alerta",  foreground=CORES["Alerta"])
        self._tabela.tag_configure("Critico", foreground=CORES["Critico"])
        self._tabela.tag_configure("Falha",   foreground=CORES["Falha"])

        # estilo geral da tabela
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("Treeview",
                         background=CORES["linha_par"],
                         fieldbackground=CORES["linha_par"],
                         foreground=CORES["texto"],
                         rowheight=24,
                         font=self.fonte_mono)
        estilo.configure("Treeview.Heading",
                         background=CORES["fundo_cabecalho"],
                         foreground=CORES["destaque"],
                         font=self.fonte_mono)
        estilo.map("Treeview", background=[("selected", CORES["borda"])])

    # -- Barra de status inferior ----------------------------------------------

    def _criar_barra_status(self) -> None:
        barra = tk.Frame(self, bg=CORES["fundo_cabecalho"], pady=4)
        barra.pack(fill="x", side="bottom")
        self._rotulo_log = tk.Label(
            barra, text="Pronto.",
            font=self.fonte_mono, bg=CORES["fundo_cabecalho"], fg=CORES["texto_fraco"],
            anchor="w",
        )
        self._rotulo_log.pack(fill="x", padx=10)

    # -- Acoes -----------------------------------------------------------------

    def _enviar_manual(self) -> None:
        self._disparar_leitura()

    def _alternar_auto(self) -> None:
        self._auto_ativo = not self._auto_ativo
        if self._auto_ativo:
            self._btn_auto.config(
                bg=CORES["Normal"], fg=CORES["fundo"],
                text=f"[S]  PARAR AUTO  (a cada {INTERVALO_ENVIO_MS//1000}s)",
            )
            self._loop_automatico()
        else:
            if self._tarefa_auto:
                self.after_cancel(self._tarefa_auto)
                self._tarefa_auto = None
            self._btn_auto.config(
                bg=CORES["borda"], fg=CORES["texto"],
                text=f"[T]  AUTO  (a cada {INTERVALO_ENVIO_MS//1000}s)",
            )

    def _loop_automatico(self) -> None:
        if not self._auto_ativo:
            return
        self._disparar_leitura()
        self._tarefa_auto = self.after(INTERVALO_ENVIO_MS, self._loop_automatico)

    def _limpar_historico(self) -> None:
        self._historico = Historico()
        for item in self._tabela.get_children():
            self._tabela.delete(item)
        self._atualizar_estatisticas()
        self._registrar_log("Historico limpo.")

    # -- Envio de leitura ------------------------------------------------------

    def _disparar_leitura(self) -> None:
        leitura = modulo_sensor.gerar_leitura()
        status_previo = modulo_sensor.status_local(leitura["temperatura"])

        # feedback imediato na interface
        self._atualizar_display(leitura["temperatura"], status_previo)
        self._registrar_log(f"Enviando  UUID={leitura['id'][:8]}...  "
                            f"temp={leitura['temperatura']}C")

        api_client.enviar_leitura(
            leitura,
            ao_sucesso=lambda resp: self._fila.put(("ok",    leitura, resp)),
            ao_erro   =lambda msg:  self._fila.put(("erro",  leitura, msg)),
        )

    # -- Processamento da fila (thread-safe para Tkinter) -----------------------

    def _processar_fila(self) -> None:
        try:
            while True:
                evento = self._fila.get_nowait()
                tipo, leitura, dado = evento

                if tipo == "ok":
                    status   = dado.get("status_logico", "Normal")
                    temp     = leitura["temperatura"]
                    self._atualizar_display(temp, status)
                    reg = self._historico.adicionar(leitura, status, enviado=True)
                    self._registrar_log(f"[OK] Recebido  status={status}  "
                                        f"UUID={reg.uuid[:8]}...")
                else:
                    # falha de rede - usa status local
                    status = modulo_sensor.status_local(leitura["temperatura"])
                    reg = self._historico.adicionar(
                        leitura, status, enviado=False, erro=dado
                    )
                    self._registrar_log(f"[ERRO] Falha ao enviar: {dado}")

                self._adicionar_linha(reg)
                self._atualizar_estatisticas()

        except queue.Empty:
            pass
        finally:
            self.after(100, self._processar_fila)

    # -- Auxiliares de interface ------------------------------------------------

    def _atualizar_display(self, temperatura: float, status: str) -> None:
        cor = CORES.get(status, CORES["texto"])
        self._rotulo_temp.config(
            text=f"{temperatura:+.2f} C",
            fg=cor,
        )
        icone = ICONE_STATUS.get(status, "")
        self._rotulo_status.config(
            text=f"{icone}  {status}",
            fg=cor,
        )

    def _adicionar_linha(self, reg) -> None:
        tag = reg.status if reg.enviado else "Falha"
        temp_str = f"{reg.temperatura:+.2f}"
        status_str = reg.status if reg.enviado else f"Falha ({reg.status})"
        
        # Remove a linha mais antiga se atingiu o limite
        filhos = self._tabela.get_children()
        if len(filhos) >= MAX_ITENS_HISTORICO:
            self._tabela.delete(filhos[-1])  # remove a ultima (mais antiga)
        
        self._tabela.insert(
            "", 0,
            values=(reg.data_hora, temp_str, status_str, reg.uuid),
            tags=(tag,),
        )

    def _atualizar_estatisticas(self) -> None:
        contagens = self._historico.contagens()
        for status, rotulo in self._rotulos_estatisticas.items():
            rotulo.config(text=str(contagens.get(status, 0)))

    def _registrar_log(self, mensagem: str) -> None:
        self._rotulo_log.config(text=mensagem)
