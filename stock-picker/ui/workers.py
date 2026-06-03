"""后台工作线程 — 保持 UI 不卡顿."""
import traceback

from PyQt6.QtCore import QThread, pyqtSignal


class ScreeningWorker(QThread):
    """选股后台线程."""
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config: dict, date: str | None, top_n: int):
        super().__init__()
        self.config = config
        self.date = date
        self.top_n = top_n

    def run(self):
        try:
            import main as main_module
            self.progress.emit("正在获取股票列表...")
            results = main_module.run_screening(self.config, date=self.date, top_n=self.top_n)
            self.finished.emit(results)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n\n{tb}")


class BacktestWorker(QThread):
    """回测后台线程."""
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, config: dict, start_date: str, end_date: str, top_n: int):
        super().__init__()
        self.config = config
        self.start_date = start_date
        self.end_date = end_date
        self.top_n = top_n

    def run(self):
        try:
            from backtest import run_backtest
            import main as main_module
            self.progress.emit(f"回测 {self.start_date} → {self.end_date}...")
            result = run_backtest(
                self.config, self.start_date, self.end_date,
                screening_fn=main_module.run_screening, top_n=self.top_n,
            )
            self.finished.emit(result)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"{e}\n\n{tb}")
