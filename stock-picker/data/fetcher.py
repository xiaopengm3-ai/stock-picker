"""akshare 统一数据获取封装 — 限流、重试、降级到缓存."""
import hashlib
import json
import logging
import time
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


class DataFetcher:
    """akshare 调用封装，提供统一的错误处理和缓存降级."""

    def __init__(self, cache_dir: str = "./data/cache", timeout: int = 30, retry: int = 1):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retry = retry
        self._failure_count: dict[str, int] = {}

    def _cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        raw = json.dumps({"f": func_name, "a": args, "k": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()

    def _read_cache(self, cache_key: str, ttl_seconds: int) -> pd.DataFrame | None:
        path = self.cache_dir / f"{cache_key}.parquet"
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if age > ttl_seconds:
            return None
        return pd.read_parquet(path)

    def _write_cache(self, cache_key: str, df: pd.DataFrame):
        path = self.cache_dir / f"{cache_key}.parquet"
        df.to_parquet(path, index=True)

    def fetch(self, func, *args, ttl_seconds: int = 86400, **kwargs) -> pd.DataFrame:
        """调用 akshare 函数，自动缓存、重试和降级.

        Args:
            func: akshare 函数对象
            ttl_seconds: 缓存有效期（秒）
        Returns:
            pandas DataFrame
        Raises:
            RuntimeError: 所有尝试失败
        """
        func_name = getattr(func, "__name__", str(func))
        cache_key = self._cache_key(func_name, args, kwargs)

        # 1. 读缓存
        cached = self._read_cache(cache_key, ttl_seconds)
        if cached is not None:
            log.debug(f"缓存命中: {func_name}")
            return cached

        # 2. 调用 akshare（含重试）
        last_error = None
        for attempt in range(self.retry + 1):
            try:
                log.debug(f"调用: {func_name} (attempt {attempt + 1})")
                df = func(*args, **kwargs)
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    raise ValueError(f"{func_name} 返回空数据")
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                self._write_cache(cache_key, df)
                self._failure_count[func_name] = 0
                return df
            except Exception as e:
                last_error = e
                log.warning(f"{func_name} 失败 (attempt {attempt + 1}): {e}")
                if attempt < self.retry:
                    time.sleep(2)

        # 3. 降级：返回过期缓存
        path = self.cache_dir / f"{cache_key}.parquet"
        if path.exists():
            log.warning(f"{func_name} 降级使用过期缓存")
            return pd.read_parquet(path)

        # 4. 完全失败
        self._failure_count[func_name] = self._failure_count.get(func_name, 0) + 1
        raise RuntimeError(f"{func_name} 获取数据失败: {last_error}")

    def too_many_failures(self, threshold: int = 3) -> bool:
        return any(c >= threshold for c in self._failure_count.values())


_fetcher: DataFetcher | None = None


def get_fetcher(cache_dir: str = "./data/cache", timeout: int = 30, retry: int = 1) -> DataFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = DataFetcher(cache_dir, timeout, retry)
    return _fetcher
