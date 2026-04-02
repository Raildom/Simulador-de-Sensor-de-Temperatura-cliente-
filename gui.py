# ============================================================
#  gui.py  -  Interface grafica Tkinter
# ============================================================

import queue
import tkinter as tk
from tkinter import ttk, font as tkfont

import api_client
import sensor as sensor_mod
from history import Historico
from config import (
    SENSOR_ID, SERVER_URL, SEND_INTERVAL_MS,
    THRESHOLD_ALERTA, THRESHOLD_CRITICO,
)

# -- Paleta de cores --------------------------------------------------------
CORES = {
    "bg":          "#0f1117",
    "panel":       "#1a1d27",
    "border":      "#2a2d3e",
    "text":        "#e2e8f0",
    "muted":       "#64748b",
    "accent":      "#38bdf8",
    "Normal":      "#22c55e",
    "Alerta":      "#f59e0b",
    "Critico":     "#ef4444",
    "Falha":       "#7c3aed",
    "header_bg":   "#141720",
    "row_even":    "#1a1d27",
    "row_odd":     "#1e2130",
}

STATUS_EMOJI = {"Normal": "[OK]", "Alerta": "[!]", "Critico": "[X]", "Falha": "[F]"}


# -- Classe principal -------------------------------------------------------

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"Monitor de Temperatura  |  {SENSOR_ID}")
        self.configure(bg=CORES["bg"])
        self.minsize(760, 580)
        self.resizable(True, True)

        self._historico   = Historico()
        self._queue: queue.Queue = queue.Queue()   # comunicacao entre threads
        self._auto_ativo  = False
        self._auto_job    = None                   # id do `after` em execucao

        self._build_fonts()
        self._build_ui()
        self._poll_queue()   # inicia polling da fila de callbacks

    # -- Fontes ----------------------------------------------------------------

    def _build_fonts(self) -> None:
        self.f_title   = tkfont.Font(family="Courier", size=15, weight="bold")
        self.f_label   = tkfont.Font(family="Courier", size=10)
        self.f_big     = tkfont.Font(family="Courier", size=36, weight="bold")
        self.f_status  = tkfont.Font(family="Courier", size=14, weight="bold")
        self.f_mono    = tkfont.Font(family="Courier", size=9)
        self.f_btn     = tkfont.Font(family="Courier", size=10, weight="bold")

    # -- Layout principal ------------------------------------------------------

    def _build_ui(self) -> None:
        # -- cabecalho ----------------------------------------------------------
        hdr = tk.Frame(self, bg=CORES["header_bg"], pady=10)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="< SENSOR MONITOR >",
            font=self.f_title, bg=CORES["header_bg"], fg=CORES["accent"],
        ).pack(side="left", padx=20)
        tk.Label(
            hdr, text=f"id: {SENSOR_ID}   servidor: {SERVER_URL}",
            font=self.f_mono, bg=CORES["header_bg"], fg=CORES["muted"],
        ).pack(side="right", padx=20)

        # -- linha de separacao -------------------------------------------------
        tk.Frame(self, bg=CORES["border"], height=1).pack(fill="x")

        # -- painel central (temperatura + controles) -------------------------
        centro = tk.Frame(self, bg=CORES["bg"])
        centro.pack(fill="x", padx=20, pady=14)

        self._build_temp_panel(centro)
        self._build_controls(centro)

        # -- painel de estatisticas ---------------------------------------------
        self._build_stats_bar()

        # -- tabela historico ---------------------------------------------------
        tk.Frame(self, bg=CORES["border"], height=1).pack(fill="x")
        self._build_history_table()

        # -- barra de status ----------------------------------------------------
        self._build_status_bar()

    # -- Painel de temperatura -------------------------------------------------

    def _build_temp_panel(self, parent: tk.Frame) -> None:
        panel = tk.Frame(parent, bg=CORES["panel"], bd=0, relief="flat")
        panel.pack(side="left", padx=(0, 14), ipadx=20, ipady=10)

        tk.Label(panel, text="TEMPERATURA ATUAL",
                 font=self.f_mono, bg=CORES["panel"], fg=CORES["muted"]).pack()

        self._lbl_temp = tk.Label(
            panel, text="--.- C",
            font=self.f_big, bg=CORES["panel"], fg=CORES["text"],
        )
        self._lbl_temp.pack()

        self._lbl_status = tk.Label(
            panel, text="- aguardando -",
            font=self.f_status, bg=CORES["panel"], fg=CORES["muted"],
        )
        self._lbl_status.pack(pady=(0, 4))

        tk.Label(
            panel,
            text=f"Normal < {THRESHOLD_ALERTA}C  |  "
                 f"Alerta >= {THRESHOLD_ALERTA}C  |  "
                 f"Critico >= {THRESHOLD_CRITICO}C",
            font=self.f_mono, bg=CORES["panel"], fg=CORES["muted"],
        ).pack()

    # -- Controles -------------------------------------------------------------

    def _build_controls(self, parent: tk.Frame) -> None:
        ctrl = tk.Frame(parent, bg=CORES["bg"])
        ctrl.pack(side="left", fill="both", expand=True)

        # botao enviar manual
        self._btn_enviar = tk.Button(
            ctrl,
            text=">  ENVIAR LEITURA",
            font=self.f_btn,
            bg=CORES["accent"], fg=CORES["bg"],
            activebackground="#7dd3fc", activeforeground=CORES["bg"],
            relief="flat", cursor="hand2", pady=10, padx=20,
            command=self._enviar_manual,
        )
        self._btn_enviar.pack(fill="x", pady=(0, 8))

        # botao envio automatico
        self._btn_auto = tk.Button(
            ctrl,
            text=f"[T]  AUTO  (a cada {SEND_INTERVAL_MS//1000}s)",
            font=self.f_btn,
            bg=CORES["border"], fg=CORES["text"],
            activebackground=CORES["muted"], activeforeground=CORES["text"],
            relief="flat", cursor="hand2", pady=10, padx=20,
            command=self._toggle_auto,
        )
        self._btn_auto.pack(fill="x", pady=(0, 8))

        # botao limpar historico
        tk.Button(
            ctrl,
            text="[-]  LIMPAR HISTORICO",
            font=self.f_btn,
            bg=CORES["border"], fg=CORES["muted"],
            activebackground=CORES["muted"], activeforeground=CORES["text"],
            relief="flat", cursor="hand2", pady=6, padx=20,
            command=self._limpar_historico,
        ).pack(fill="x")

    # -- Barra de estatisticas -------------------------------------------------

    def _build_stats_bar(self) -> None:
        bar = tk.Frame(self, bg=CORES["panel"], pady=8)
        bar.pack(fill="x", padx=20, pady=(0, 8))

        self._stat_labels: dict[str, tk.Label] = {}
        for status in ("Normal", "Alerta", "Critico", "Falha"):
            col = tk.Frame(bar, bg=CORES["panel"])
            col.pack(side="left", expand=True)

            tk.Label(
                col, text=STATUS_EMOJI.get(status, "") + " " + status,
                font=self.f_label, bg=CORES["panel"],
                fg=CORES[status],
            ).pack()

            lbl = tk.Label(
                col, text="0",
                font=tkfont.Font(family="Courier", size=18, weight="bold"),
                bg=CORES["panel"], fg=CORES[status],
            )
            lbl.pack()
            self._stat_labels[status] = lbl

    # -- Tabela de historico ----------------------------------------------------

    def _build_history_table(self) -> None:
        wrapper = tk.Frame(self, bg=CORES["bg"])
        wrapper.pack(fill="both", expand=True, padx=20, pady=(8, 0))

        tk.Label(
            wrapper, text="HISTORICO LOCAL",
            font=self.f_mono, bg=CORES["bg"], fg=CORES["muted"],
        ).pack(anchor="w")

        cols = ("timestamp", "temperatura", "status", "uuid")
        self._tree = ttk.Treeview(
            wrapper, columns=cols, show="headings", height=10,
        )

        larguras = {"timestamp": 140, "temperatura": 100, "status": 90, "uuid": 310}
        titulos  = {"timestamp": "Data/Hora", "temperatura": "Temp (C)",
                    "status": "Status", "uuid": "UUID"}
        for c in cols:
            self._tree.heading(c, text=titulos[c])
            self._tree.column(c, width=larguras[c], anchor="center")

        # scrollbar
        sb = ttk.Scrollbar(wrapper, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # tags de cor por status
        self._tree.tag_configure("Normal",  foreground=CORES["Normal"])
        self._tree.tag_configure("Alerta",  foreground=CORES["Alerta"])
        self._tree.tag_configure("Critico", foreground=CORES["Critico"])
        self._tree.tag_configure("Falha",   foreground=CORES["Falha"])

        # estilo geral da tabela
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
                         background=CORES["row_even"],
                         fieldbackground=CORES["row_even"],
                         foreground=CORES["text"],
                         rowheight=24,
                         font=self.f_mono)
        style.configure("Treeview.Heading",
                         background=CORES["header_bg"],
                         foreground=CORES["accent"],
                         font=self.f_mono)
        style.map("Treeview", background=[("selected", CORES["border"])])

    # -- Barra de status inferior ----------------------------------------------

    def _build_status_bar(self) -> None:
        bar = tk.Frame(self, bg=CORES["header_bg"], pady=4)
        bar.pack(fill="x", side="bottom")
        self._lbl_log = tk.Label(
            bar, text="Pronto.",
            font=self.f_mono, bg=CORES["header_bg"], fg=CORES["muted"],
            anchor="w",
        )
        self._lbl_log.pack(fill="x", padx=10)

    # -- Acoes -----------------------------------------------------------------

    def _enviar_manual(self) -> None:
        self._disparar_leitura()

    def _toggle_auto(self) -> None:
        self._auto_ativo = not self._auto_ativo
        if self._auto_ativo:
            self._btn_auto.config(
                bg=CORES["Normal"], fg=CORES["bg"],
                text=f"[S]  PARAR AUTO  (a cada {SEND_INTERVAL_MS//1000}s)",
            )
            self._auto_loop()
        else:
            if self._auto_job:
                self.after_cancel(self._auto_job)
                self._auto_job = None
            self._btn_auto.config(
                bg=CORES["border"], fg=CORES["text"],
                text=f"[T]  AUTO  (a cada {SEND_INTERVAL_MS//1000}s)",
            )

    def _auto_loop(self) -> None:
        if not self._auto_ativo:
            return
        self._disparar_leitura()
        self._auto_job = self.after(SEND_INTERVAL_MS, self._auto_loop)

    def _limpar_historico(self) -> None:
        self._historico = Historico()
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._atualizar_stats()
        self._log("Historico limpo.")

    # -- Envio de leitura ------------------------------------------------------

    def _disparar_leitura(self) -> None:
        leitura = sensor_mod.gerar_leitura()
        status_prev = sensor_mod.status_local(leitura["temperatura"])

        # feedback imediato na UI
        self._atualizar_display(leitura["temperatura"], status_prev)
        self._log(f"Enviando  UUID={leitura['id'][:8]}...  "
                  f"temp={leitura['temperatura']}C")

        api_client.enviar_leitura(
            leitura,
            on_success=lambda resp: self._queue.put(("ok",    leitura, resp)),
            on_error  =lambda msg:  self._queue.put(("erro",  leitura, msg)),
        )

    # -- Polling da fila (thread-safe para Tkinter) -----------------------------

    def _poll_queue(self) -> None:
        try:
            while True:
                evento = self._queue.get_nowait()
                tipo, leitura, dado = evento

                if tipo == "ok":
                    status   = dado.get("status_logico", "Normal")
                    temp     = leitura["temperatura"]
                    self._atualizar_display(temp, status)
                    reg = self._historico.adicionar(leitura, status, enviado=True)
                    self._log(f"[OK] Recebido  status={status}  "
                              f"UUID={reg.uuid[:8]}...")
                else:
                    # falha de rede - usa status local
                    status = sensor_mod.status_local(leitura["temperatura"])
                    reg = self._historico.adicionar(
                        leitura, status, enviado=False, erro=dado
                    )
                    self._log(f"[ERRO] Falha ao enviar: {dado}")

                self._adicionar_linha(reg)
                self._atualizar_stats()

        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_queue)

    # -- Helpers de UI ---------------------------------------------------------

    def _atualizar_display(self, temperatura: float, status: str) -> None:
        cor = CORES.get(status, CORES["text"])
        self._lbl_temp.config(
            text=f"{temperatura:+.2f} C",
            fg=cor,
        )
        emoji = STATUS_EMOJI.get(status, "")
        self._lbl_status.config(
            text=f"{emoji}  {status}",
            fg=cor,
        )

    def _adicionar_linha(self, reg) -> None:
        tag = reg.status if reg.enviado else "Falha"
        temp_str = f"{reg.temperatura:+.2f}"
        status_str = reg.status if reg.enviado else f"Falha ({reg.status})"
        self._tree.insert(
            "", 0,
            values=(reg.timestamp, temp_str, status_str, reg.uuid),
            tags=(tag,),
        )

    def _atualizar_stats(self) -> None:
        contagens = self._historico.contagens()
        for status, lbl in self._stat_labels.items():
            lbl.config(text=str(contagens.get(status, 0)))

    def _log(self, msg: str) -> None:
        self._lbl_log.config(text=msg)
