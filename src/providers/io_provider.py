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
        self._inputs: Dict[str, str] = {}
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

    @property
    def inputs(self) -> Dict[str, Input]:
        with self._lock:
            result: Dict[str, Input] = {}
            for name, value in self._inputs.items():
                result[name] = Input(
                    input=value,
                    timestamp=self._input_timestamps.get(name),
                )
            return result

    def add_input(
        self, key: str, value: str, timestamp: Optional[float] = None
    ) -> None:
        with self._lock:
            self._inputs[key] = value
            if timestamp is not None:
                self._input_timestamps[key] = timestamp
            else:
                self._input_timestamps[key] = time.time()

    def remove_input(self, key: str) -> None:
        with self._lock:
            self._inputs.pop(key, None)
            self._input_timestamps.pop(key, None)

    def add_input_timestamp(self, key: str, timestamp: float) -> None:
        with self._lock:
            self._input_timestamps[key] = timestamp

    def get_input_timestamp(self, key: str) -> Optional[float]:
        with self._lock:
            return self._input_timestamps.get(key)

    # =========================
    # ✅ LLM PROMPT (FULL PROPERTY SUPPORT)
    # =========================

    @property
    def llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    @llm_prompt.setter
    def llm_prompt(self, value: Optional[str]) -> None:
        with self._lock:
            self._llm_prompt = value

    def set_llm_prompt(self, value: Optional[str]) -> None:
        with self._lock:
            self._llm_prompt = value

    def get_llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    def clear_llm_prompt(self) -> None:
        with self._lock:
            self._llm_prompt = None

    # =========================
    # MODE TRANSITION
    # =========================

    def add_mode_transition_input(self, input_text: str) -> None:
        with self._lock:
            if self._mode_transition_input is None:
                self._mode_transition_input = input_text
            else:
                self._mode_transition_input += " " + input_text

    @contextmanager
    def mode_transition_input(self):
        try:
            with self._lock:
                current_input = self._mode_transition_input
            yield current_input
        finally:
            self.delete_mode_transition_input()

    def get_mode_transition_input(self) -> Optional[str]:
        with self._lock:
            return self._mode_transition_input

    def delete_mode_transition_input(self) -> None:
        with self._lock:
            self._mode_transition_input = None

    # =========================
    # DYNAMIC VARIABLES
    # =========================

    def add_dynamic_variable(self, key: str, value: Any) -> None:
        with self._lock:
            self._variables[key] = value

    def get_dynamic_variable(self, key: str) -> Any:
        with self._lock:
            return self._variables.get(key)
