from dataclasses import dataclass, field
from typing import Dict, List, Optional
import threading
import pandas as pd

@dataclass
class CircuitBreaker:
    drawdown_limit: float = 15.0
    max_error_rate: float = 0.4
    enabled: bool = True
    max_error_count: int = 5
    current_drawdown: float = 0.0
    error_count: int = 0
    total_checks: int = 1
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def update(self, current_drawdown: float, error_rate: float) -> bool:
        with self._lock:
            self.current_drawdown = max(0.0, float(current_drawdown))
            self.total_checks += 1
            
            if error_rate > self.max_error_rate:
                self.error_count += 1
            else:
                self.error_count = max(0, self.error_count - 1)

            if not self.enabled:
                return False

            if self.current_drawdown >= self.drawdown_limit or self.error_count >= self.max_error_count:
                return True

            return False

    def is_open(self) -> bool:
        with self._lock:
            return self.current_drawdown >= self.drawdown_limit or self.error_count >= self.max_error_count

