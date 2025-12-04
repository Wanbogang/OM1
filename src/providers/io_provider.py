import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .singleton import singleton


@dataclass
class Input:
    input: str
    timestamp: Optional[float] = None


@singleton
class IOProvider:
    """
    Thread-safe singleton for managing IO state and timing data.
    """

    def __init__(self):
        self._lock: threading.Lock = threading.Lock()

        # Input storage
        self._inputs: Dict[str, Input] = {}
        self._input_timestamps: Dict[str, float] = {}

        # LLM related state
        self._llm_prompt: Optional[str] = None

        # Mode transition state
        self._mode_transition_input: Optional[str] = None

        # Dynamic variables (backward compatibility)
        self._variables: Dict[str, Any] = {}

    # =========================
    # INPUTS
    # =========================

    def add_input(
        self, key: str, value: str, timestamp: Optional[float] = None
    ) -> None:
        with self._lock:
            self._inputs[key] = Input(input=value, timestamp=timestamp)
            if timestamp is not None:
                self._input_timestamps[key] = timestamp

    def remove_input(self, key: str) -> None:
        with self._lock:
            self._inputs.pop(key, None)
            self._input_timestamps.pop(key, None)

    def get_input(self, key: str) -> Optional[Input]:
        with self._lock:
            return self._inputs.get(key)

    @property
    def inputs(self) -> Dict[str, Input]:
        return self._inputs

    def clear_inputs(self) -> None:
        with self._lock:
            self._inputs.clear()
            self._input_timestamps.clear()

    # =========================
    # TIMESTAMPS (FULL BACKWARD COMPATIBILITY)
    # =========================

    def set_input_timestamp(self, key: str, timestamp: float) -> None:
        with self._lock:
            self._input_timestamps[key] = timestamp
            if key in self._inputs:
                self._inputs[key].timestamp = timestamp
            else:
                self._inputs[key] = Input(input="", timestamp=timestamp)

    def get_input_timestamp(self, key: str) -> Optional[float]:
        with self._lock:
            return self._input_timestamps.get(key)

    # ✅ BACKWARD COMPATIBILITY
    def add_input_timestamp(self, key: str, timestamp: float) -> None:
        self.set_input_timestamp(key, timestamp)

    # =========================
    # LLM PROMPT
    # =========================

    @property
    def llm_prompt(self) -> Optional[str]:
        return self._llm_prompt

    @llm_prompt.setter
    def llm_prompt(self, prompt: Optional[str]) -> None:
        self._llm_prompt = prompt

    def set_llm_prompt(self, prompt: str) -> None:
        with self._lock:
            self._llm_prompt = prompt

    def get_llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    def clear_llm_prompt(self) -> None:
        with self._lock:
            self._llm_prompt = None

    # =========================
    # MODE TRANSITION
    # =========================

    def set_mode_transition_input(self, value: str) -> None:
        with self._lock:
            self._mode_transition_input = value

    def get_mode_transition_input(self) -> Optional[str]:
        with self._lock:
            return self._mode_transition_input

    def clear_mode_transition_input(self) -> None:
        with self._lock:
            self._mode_transition_input = None

    # =========================
    # FUSER TIME PROPERTIES
    # =========================

    @property
    def t_last_input(self) -> Optional[float]:
        if not self._input_timestamps:
            return None
        return max(self._input_timestamps.values())

    @property
    def dt_last_input(self) -> Optional[float]:
        if self.t_last_input is None:
            return None
        return time.time() - self.t_last_input

    # =========================
    # THREAD SAFETY HELPERS
    # =========================

    @contextmanager
    def locked(self):
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()
