"""Exécution des appels réseau hors du fil de l'interface.

Un appel bloquant dans le fil principal figerait la fenêtre. Chaque appel part
donc dans le pool de fils de Qt, et son résultat revient par un signal, que Qt
délivre dans le fil de l'interface.
"""

import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from app.api import ApiError

logger = logging.getLogger(__name__)


class _Signals(QObject):
    done = Signal(object)
    failed = Signal(str)


class _Task(QRunnable):
    def __init__(self, function, signals: _Signals):
        super().__init__()
        self.function = function
        self.signals = signals

    def run(self):
        try:
            result = self.function()
        except ApiError as exc:
            self._emit(self.signals.failed, exc.message)
        except Exception:
            logger.exception("Erreur inattendue pendant un appel à l'API")
            self._emit(self.signals.failed, "Une erreur inattendue est survenue.")
        else:
            self._emit(self.signals.done, result)

    @staticmethod
    def _emit(signal, value):
        try:
            signal.emit(value)
        except RuntimeError:
            # L'écran qui attendait la réponse a été fermé entre-temps.
            pass


def run_async(owner: QObject, function, on_done, on_error=None) -> None:
    """Exécute `function` en arrière-plan puis appelle `on_done(résultat)` dans le fil de l'interface.

    Les signaux ont `owner` pour parent : si l'écran est détruit avant la réponse,
    ils le sont aussi et aucun rappel ne s'exécute sur un objet disparu.
    """
    signals = _Signals(owner)
    signals.done.connect(on_done)
    if on_error is not None:
        signals.failed.connect(on_error)
    signals.done.connect(signals.deleteLater)
    signals.failed.connect(signals.deleteLater)
    QThreadPool.globalInstance().start(_Task(function, signals))
