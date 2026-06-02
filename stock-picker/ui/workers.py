"""后台工作线程 — 保持 UI 不卡顿."""
from PyQt6.QtCore import QThread, pyqtSignal


class ScreeningWorker(QThread):
    """选股后台线程."""
    finished = pyqtSignal(object)   # (results, elapsed)
    progress = pyqtSignal(str)       # 进度信息
    error = pyqtSignal(str)          # 错误信息

    def __init__(self, config: dict, date: str | None, top_n: int):
        super().__init__()
        self.config = config
        self.date = date
        self.top_n = top_n

    def run(self):
        try:
            from main import run_screening
            self.progress.emit("正在获取股票列表...")
            results = run_screening(self.config, date=self.date, top_n=self.top_n)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


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
            from main import run_screening
            self.progress.emit(f"回测 {self.start_date} → {self.end_date}...")
            result = run_backtest(
                self.config, self.start_date, self.end_date,
                screening_fn=run_screening, top_n=self.top_n,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
