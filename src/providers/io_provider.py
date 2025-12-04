import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional

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

        self._inputs: Dict[str, str] = {}
        self._input_timestamps: Dict[str, float] = {}

        self._fuser_system_prompt: Optional[str] = None
        self._fuser_inputs: Optional[str] = None
        self._fuser_available_actions: Optional[str] = None
        self._fuser_start_time: Optional[float] = None
        self._fuser_end_time: Optional[float] = None

        self._llm_prompt: Optional[str] = None
        self._llm_start_time: Optional[float] = None
        self._llm_end_time: Optional[float] = None

        self._mode_transition_input: Optional[str] = None

        self._variables: Dict[str, Any] = {}

    # =========================
    # INPUTS
    # =========================

    @property
    def inputs(self) -> Dict[str, Input]:
        with self._lock:
            return {
                name: Input(input=value, timestamp=self._input_timestamps[name])
                for name, value in self._inputs.items()
            }

    def add_input(
        self, key: str, value: str, timestamp: Optional[float] = None
    ) -> None:
        with self._lock:
            self._inputs[key] = value
            self._input_timestamps[key] = (
                float(timestamp) if timestamp is not None else time.time()
            )

    def remove_input(self, key: str) -> None:
        with self._lock:
            self._inputs.pop(key, None)
            self._input_timestamps.pop(key, None)

    def get_input_timestamp(self, key: str) -> Optional[float]:
        with self._lock:
            return self._input_timestamps.get(key)

    # =========================
    # FUSER DATA
    # =========================

    @property
    def fuser_system_prompt(self) -> Optional[str]:
        with self._lock:
            return self._fuser_system_prompt

    @fuser_system_prompt.setter
    def fuser_system_prompt(self, value: Optional[str]) -> None:
        with self._lock:
            self._fuser_system_prompt = value

    @property
    def fuser_inputs(self) -> Optional[str]:
        with self._lock:
            return self._fuser_inputs

    @fuser_inputs.setter
    def fuser_inputs(self, value: Optional[str]) -> None:
        with self._lock:
            self._fuser_inputs = value

    @property
    def fuser_available_actions(self) -> Optional[str]:
        with self._lock:
            return self._fuser_available_actions

    @fuser_available_actions.setter
    def fuser_available_actions(self, value: Optional[str]) -> None:
        with self._lock:
            self._fuser_available_actions = value

    @property
    def fuser_start_time(self) -> Optional[float]:
        with self._lock:
            return self._fuser_start_time

    @fuser_start_time.setter
    def fuser_start_time(self, value: Optional[float]) -> None:
        with self._lock:
            self._fuser_start_time = value

    @property
    def fuser_end_time(self) -> Optional[float]:
        with self._lock:
            return self._fuser_end_time

    @fuser_end_time.setter
    def fuser_end_time(self, value: Optional[float]) -> None:
        with self._lock:
            self._fuser_end_time = value

    # =========================
    # LLM DATA
    # =========================

    @property
    def llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    @llm_prompt.setter
    def llm_prompt(self, value: Optional[str]) -> None:
        with self._lock:
            self._llm_prompt = value

    def clear_llm_prompt(self) -> None:
        with self._lock:
            self._llm_prompt = None

    @property
    def llm_start_time(self) -> Optional[float]:
        with self._lock:
            return self._llm_start_time

    @llm_start_time.setter
    def llm_start_time(self, value: Optional[float]) -> None:
        with self._lock:
            self._llm_start_time = value

    @property
    def llm_end_time(self) -> Optional[float]:
        with self._lock:
            return self._llm_end_time

    @llm_end_time.setter
    def llm_end_time(self, value: Optional[float]) -> None:
        with self._lock:
            self._llm_end_time = value

    # =========================
    # DYNAMIC VARIABLES
    # =========================

    def add_dynamic_variable(self, key: str, value: Any) -> None:
        with self._lock:
            self._variables[key] = value

    def get_dynamic_variable(self, key: str) -> Any:
        with self._lock:
            return self._variables.get(key)

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
    # GLOBAL RESET
    # =========================

    def clear_all(self) -> None:
        """
        Reset all stored inputs, timestamps, prompts, and variables.
        """
        with self._lock:
            self._inputs.clear()
            self._input_timestamps.clear()
            self._variables.clear()

            self._fuser_system_prompt = None
            self._fuser_inputs = None
            self._fuser_available_actions = None
            self._fuser_start_time = None
            self._fuser_end_time = None

            self._llm_prompt = None
            self._llm_start_time = None
            self._llm_end_time = None

            self._mode_transition_input = None
