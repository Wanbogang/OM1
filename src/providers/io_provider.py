import threading
from dataclasses import dataclass
from typing import Dict, Optional

from .singleton import singleton


@dataclass
class Input:
    input: str
    timestamp: float


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

        # LLM-related state (RESTORED for backward compatibility)
        self._llm_prompt: Optional[str] = None

        # Mode transition state
        self._mode_transition_input: Optional[str] = None

    # ---------------------------------------------------------------------
    # Input handling
    # ---------------------------------------------------------------------
    def set_input(self, key: str, value: str) -> None:
        with self._lock:
            self._inputs[key] = value

    def get_input(self, key: str) -> Optional[str]:
        with self._lock:
            return self._inputs.get(key)

    def clear_inputs(self) -> None:
        with self._lock:
            self._inputs.clear()
            self._input_timestamps.clear()

    # ---------------------------------------------------------------------
    # Timestamp handling
    # ---------------------------------------------------------------------
    def set_input_timestamp(self, key: str, timestamp: float) -> None:
        with self._lock:
            self._input_timestamps[key] = timestamp

    def get_input_timestamp(self, key: str) -> Optional[float]:
        with self._lock:
            return self._input_timestamps.get(key)

    # ✅ BACKWARD COMPATIBILITY (FIX TEST FAILURE)
    def add_input_timestamp(self, key: str, timestamp: float) -> None:
        """
        Backward-compatible wrapper for older test and plugin code.
        """
        self.set_input_timestamp(key, timestamp)

    # ---------------------------------------------------------------------
    # LLM prompt handling
    # ---------------------------------------------------------------------
    # ✅ BACKWARD COMPATIBILITY (FIX LINT FAILURE)
    def set_llm_prompt(self, prompt: str) -> None:
        """
        Restored for backward compatibility with existing LLM plugins.
        """
        with self._lock:
            self._llm_prompt = prompt

    def get_llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    # ---------------------------------------------------------------------
    # Mode transition handling
    # ---------------------------------------------------------------------
    def set_mode_transition_input(self, value: str) -> None:
        with self._lock:
            self._mode_transition_input = value

    def get_mode_transition_input(self) -> Optional[str]:
        with self._lock:
            return self._mode_transition_input

    def clear_mode_transition_input(self) -> None:
        with self._lock:
            self._mode_transition_input = None
