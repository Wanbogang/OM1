import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from .singleton import singleton


class Input:
    """Input data container with timestamp"""
    
    def __init__(self, input: str, timestamp: Optional[float] = None):
        self.input = input
        self.timestamp = timestamp if timestamp is not None else time.time()


@singleton
class IOProvider:
    """
    Thread-safe singleton for managing IO state and timing data.
    Improvements:
    - Consistent timestamp handling (always float)
    - Consolidated setter methods
    - Added clear_all() for complete state reset
    """

    def __init__(self):
        self._lock: threading.Lock = threading.Lock()

        # Input storage
        self._inputs: Dict[str, Input] = {}
        self._input_timestamps: Dict[str, float] = {}

        # LLM related state
        self._llm_prompt: Optional[str] = None
        self._llm_start_time: Optional[float] = None
        self._llm_end_time: Optional[float] = None

        # Mode transition state
        self._mode_transition_input: Optional[str] = None

        # Fuser system prompt
        self._fuser_system_prompt: Optional[str] = None

        # Dynamic variables (backward compatibility)
        self._variables: Dict[str, Any] = {}

    # =========================
    # INPUTS
    # =========================

    def add_input(
        self, key: str, value: str, timestamp: Optional[float] = None
    ) -> None:
        """Add input with consistent timestamp handling"""
        with self._lock:
            # Ensure timestamp is always set (use current time if not provided)
            ts = timestamp if timestamp is not None else time.time()
            self._inputs[key] = Input(input=value, timestamp=ts)
            self._input_timestamps[key] = ts

    def remove_input(self, key: str) -> None:
        with self._lock:
            self._inputs.pop(key, None)
            self._input_timestamps.pop(key, None)

    def get_input(self, key: str) -> Optional[Input]:
        with self._lock:
            return self._inputs.get(key)

    @property
    def inputs(self) -> Dict[str, Input]:
        """Returns copy of inputs dict for thread safety"""
        with self._lock:
            return self._inputs.copy()

    def clear_inputs(self) -> None:
        with self._lock:
            self._inputs.clear()
            self._input_timestamps.clear()

    # =========================
    # TIMESTAMPS
    # =========================

    def set_input_timestamp(self, key: str, timestamp: float) -> None:
        """Set timestamp for an input key"""
        with self._lock:
            self._input_timestamps[key] = timestamp
            if key in self._inputs:
                self._inputs[key].timestamp = timestamp
            else:
                # Create placeholder input if key doesn't exist
                self._inputs[key] = Input(input="", timestamp=timestamp)

    def get_input_timestamp(self, key: str) -> Optional[float]:
        with self._lock:
            return self._input_timestamps.get(key)

    # Backward compatibility alias
    def add_input_timestamp(self, key: str, timestamp: float) -> None:
        """Alias for set_input_timestamp (backward compatibility)"""
        self.set_input_timestamp(key, timestamp)

    # =========================
    # LLM PROMPT
    # =========================

    @property
    def llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    @llm_prompt.setter
    def llm_prompt(self, prompt: Optional[str]) -> None:
        with self._lock:
            self._llm_prompt = prompt

    def set_llm_prompt(self, prompt: str) -> None:
        """Set LLM prompt (method style for explicit calls)"""
        with self._lock:
            self._llm_prompt = prompt

    def get_llm_prompt(self) -> Optional[str]:
        with self._lock:
            return self._llm_prompt

    def clear_llm_prompt(self) -> None:
        with self._lock:
            self._llm_prompt = None

    # =========================
    # LLM TIMING
    # =========================

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

    def set_llm_start_time(self, timestamp: float) -> None:
        """Set LLM start time"""
        with self._lock:
            self._llm_start_time = timestamp

    def set_llm_end_time(self, timestamp: float) -> None:
        """Set LLM end time"""
        with self._lock:
            self._llm_end_time = timestamp

    def get_llm_start_time(self) -> Optional[float]:
        with self._lock:
            return self._llm_start_time

    def get_llm_end_time(self) -> Optional[float]:
        with self._lock:
            return self._llm_end_time

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
    # FUSER SYSTEM PROMPT
    # =========================

    def set_fuser_system_prompt(self, prompt: str) -> None:
        """Set fuser system prompt"""
        with self._lock:
            self._fuser_system_prompt = prompt

    def get_fuser_system_prompt(self) -> Optional[str]:
        with self._lock:
            return self._fuser_system_prompt

    def clear_fuser_system_prompt(self) -> None:
        with self._lock:
            self._fuser_system_prompt = None

    # =========================
    # FUSER TIME PROPERTIES
    # =========================

    @property
    def t_last_input(self) -> Optional[float]:
        """Get timestamp of most recent input"""
        with self._lock:
            if not self._input_timestamps:
                return None
            return max(self._input_timestamps.values())

    @property
    def dt_last_input(self) -> Optional[float]:
        """Get time elapsed since last input"""
        t_last = self.t_last_input
        if t_last is None:
            return None
        return time.time() - t_last

    # =========================
    # STATE MANAGEMENT
    # =========================

    def clear_all(self) -> None:
        """Clear all state (new method for complete reset)"""
        with self._lock:
            self._inputs.clear()
            self._input_timestamps.clear()
            self._llm_prompt = None
            self._llm_start_time = None
            self._llm_end_time = None
            self._mode_transition_input = None
            self._fuser_system_prompt = None
            self._variables.clear()

    # =========================
    # THREAD SAFETY HELPERS
    # =========================

    @contextmanager
    def locked(self):
        """Context manager for thread-safe operations"""
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()
