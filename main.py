# ============================================================
#  principal.py  -  Ponto de entrada do cliente
# ============================================================

from gui import Aplicacao


def principal() -> None:
    app = Aplicacao()
    app.mainloop()


if __name__ == "__main__":
    principal()
