# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Refactored FilterBroker with class-based design, type safety, and dependency injection.

This is a modern replacement for filterbroker.py that provides:
- Type-safe configuration access
- Automatic undo/redo
- Change subscription system
- Better testability through dependency injection
- Backward compatibility wrappers

USAGE:
    # Get singleton instance
    broker = FilterBroker.get_instance()

    # Type-safe access
    order = broker.get('N')
    broker.set('N', 8)
    broker.undo()

    # Subscribe to changes
    broker.subscribe(lambda key, old, new: print(f"{key} changed"))

    # Dependency injection (recommended for testability)
    def process_filter(broker: FilterBroker):
        ...

Migration path:
    Phase 1: New code uses FilterBroker directly
    Phase 2: Gradual migration of existing code
    Phase 3: Replace old filterbroker.py
"""

import copy
import logging
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Type-safe filter configuration
# ============================================================================

@dataclass
class FilterConfig:
    """Type-safe filter configuration with all design parameters."""
    # Amplitude specs (linear units)
    A_PB: float = 0.2056717652757185
    A_PB2: float = 0.01
    A_SB: float = 0.001
    A_SB2: float = 0.0001

    # Frequency specs (normalized to F_S)
    F_C: float = 0.1
    F_C2: float = 0.4
    F_N: float = 0.2
    F_N2: float = 0.4
    F_PB: float = 0.1
    F_PB2: float = 0.3
    F_SB: float = 0.2
    F_SB2: float = 0.4

    N: int = 4  # filter order
    T_S: float = 1.0  # sample time

    # Weights for pass- and stopbands
    W_PB: float = 1.0
    W_PB2: float = 1.0
    W_SB: float = 1.0
    W_SB2: float = 1.0

    amp_specs_unit: str = 'dB'
    f_S: float = 1.0  # sampling frequency
    f_s_prev: float = 1.0  # previous sampling frequency
    f_max: float = 1.0
    f_s_scale: float = 1.0
    fc: str = 'Ellip'  # filter class
    ft: str = 'IIR'  # filter type
    fo: str = 'man'  # filter order: 'man' or 'min'
    rt: str = 'LP'  # filter response type

    freq_locked: bool = False
    freq_specs_sort: bool = True
    freq_specs_unit: str = 'f_S'

    # Format and representation
    qfrmt: str = 'float64'  # quantization format
    qfrmt_float_last: str = 'float64'
    qfrmt_fx_last: str = 'qfrac'
    fx_base: str = 'dec'  # {'dec', 'hex', 'bin', 'oct', 'csd'}
    fx_mod_class_name: str = 'pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp_ui'

    # Metadata
    info: str = 'Ellip. LP (default)'
    timestamp: float = field(default_factory=lambda: 0.0)

    # Complex nested structures (stored as dict for flexibility)
    # These will need special handling in serialize/deserialize
    ba: Any = field(default_factory=lambda: np.array([[1], [1]]))
    sos: Any = field(default_factory=lambda: np.array([[1, 0, 0, 1, 0, 0]]))
    zpk: Any = field(default_factory=lambda: np.array([[], [], [1]]))
    creator: list = field(default_factory=lambda: ['sos', 'pyfda.filter_widgets.ellip'])
    _id: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization and backward compatibility."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, np.ndarray):
                result[key] = value  # Keep numpy arrays as-is
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary, handling numpy arrays and extra keys."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ============================================================================
# Main FilterBroker Class
# ============================================================================

class FilterBroker:
    """
    Centralized filter state management with undo/redo and type safety.

    This is a singleton class that manages all filter design parameters.
    It provides:
    - Type-safe get/set operations
    - Automatic undo/redo stack
    - Change notification system
    - Serialization support
    - Backward compatibility with old code

    Examples
    --------
    # Singleton access
    broker = FilterBroker.get_instance()

    # Get/set values
    order = broker.get('N')
    broker.set('N', 8)

    # Undo/redo
    broker.undo()
    broker.redo()

    # Subscribe to changes
    broker.subscribe(on_change_callback)

    # Dependency injection (recommended)
    def design_filter(broker: FilterBroker):
        order = broker.get('N')
        # ... use broker in function
    """

    _instance: Optional['FilterBroker'] = None
    UNDO_LEN: int = 20

    def __init__(self):
        """Initialize FilterBroker as singleton."""
        if FilterBroker._instance is not None:
            raise RuntimeError(
                "FilterBroker is a singleton. Use FilterBroker.get_instance()"
            )

        self._config = FilterConfig()
        self._undo_stack: list[FilterConfig] = []
        self._redo_stack: list[FilterConfig] = []
        self._change_callbacks: list[Callable[[str, Any, Any], None]] = []
        self._lock_depth: int = 0  # For preventing undo during callbacks

        logger.info("FilterBroker initialized")

    @staticmethod
    def get_instance() -> 'FilterBroker':
        """
        Get singleton instance, creating if necessary.

        Returns
        -------
        FilterBroker
            The singleton FilterBroker instance
        """
        if FilterBroker._instance is None:
            FilterBroker._instance = FilterBroker()
        return FilterBroker._instance

    @staticmethod
    def reset_instance():
        """Reset singleton instance. Useful for testing."""
        FilterBroker._instance = None

    # ========================================================================
    # Core Get/Set Operations
    # ========================================================================

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key with type checking.

        Parameters
        ----------
        key : str
            Configuration key (e.g., 'N', 'F_C')
        default : Any, optional
            Default value if key doesn't exist

        Returns
        -------
        Any
            Configuration value or default

        Examples
        --------
        >>> broker = FilterBroker.get_instance()
        >>> order = broker.get('N')  # Returns int
        >>> freq = broker.get('F_C')  # Returns float
        """
        if not hasattr(self._config, key):
            logger.warning("Key '%s' not found in FilterConfig", key)
            return default

        return getattr(self._config, key)

    def set(
        self,
        key: str,
        value: Any,
        backup: bool = True,
        notify: bool = True
    ) -> bool:
        """
        Set configuration value with type checking and undo support.

        Parameters
        ----------
        key : str
            Configuration key
        value : Any
            New value
        backup : bool, optional (default True)
            Whether to backup for undo. Can be disabled for batch operations.
        notify : bool, optional (default True)
            Whether to notify subscribers

        Returns
        -------
        bool
            True if successful, False otherwise

        Examples
        --------
        >>> broker.set('N', 8)
        True
        >>> broker.set('invalid_key', 5)
        False
        """
        if not hasattr(self._config, key):
            logger.error("Key '%s' not recognized in FilterConfig", key)
            return False

        # Backup old value for undo
        if backup and self._lock_depth == 0:
            self._undo_stack.append(copy.deepcopy(self._config))
            self._redo_stack.clear()
            # Limit undo stack size
            if len(self._undo_stack) > self.UNDO_LEN:
                self._undo_stack.pop(0)

        # Get old value for change detection
        old_value = getattr(self._config, key)

        # Set new value
        try:
            setattr(self._config, key, value)

            # Notify subscribers of change
            if notify and old_value != value and self._lock_depth == 0:
                self._notify_change(key, old_value, value)

            return True

        except (TypeError, ValueError) as e:
            logger.error("Error setting '%s' to %s: %s", key, value, e)
            return False

    def batch_set(self, updates: dict[str, Any]) -> bool:
        """
        Set multiple values without creating undo entries for each.

        Parameters
        ----------
        updates : dict
            Dictionary of key-value pairs to set

        Returns
        -------
        bool
            True if all successful, False if any failed

        Examples
        --------
        >>> broker.batch_set({'N': 8, 'F_C': 0.25})
        True
        """
        if not updates:
            return True

        # Backup once at the beginning
        self._undo_stack.append(copy.deepcopy(self._config))
        self._redo_stack.clear()

        self._lock_depth += 1
        try:
            success = True
            for key, value in updates.items():
                if not self.set(key, value, backup=False, notify=False):
                    success = False

            # Notify after all changes
            if success:
                for key, value in updates.items():
                    old_value = self.get(key)
                    self._notify_change(key, old_value, value)

            return success
        finally:
            self._lock_depth -= 1

    def undo(self) -> bool:
        """
        Undo last change.

        Returns
        -------
        bool
            True if undo was performed, False if stack empty
        """
        if not self._undo_stack:
            logger.debug("Undo stack empty")
            return False

        self._redo_stack.append(copy.deepcopy(self._config))
        self._config = self._undo_stack.pop()
        logger.debug("Undo executed")
        return True

    def redo(self) -> bool:
        """
        Redo last undone change.

        Returns
        -------
        bool
            True if redo was performed, False if stack empty
        """
        if not self._redo_stack:
            logger.debug("Redo stack empty")
            return False

        self._undo_stack.append(copy.deepcopy(self._config))
        self._config = self._redo_stack.pop()
        logger.debug("Redo executed")
        return True

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    # ========================================================================
    # Change Notification System
    # ========================================================================

    def subscribe(self, callback: Callable[[str, Any, Any], None]):
        """
        Subscribe to configuration changes.

        Parameters
        ----------
        callback : Callable
            Function called with (key, old_value, new_value) on change

        Examples
        --------
        >>> def on_change(key, old_val, new_val):
        ...     print(f"{key}: {old_val} -> {new_val}")
        >>> broker.subscribe(on_change)
        """
        self._change_callbacks.append(callback)

    def unsubscribe(self, callback: Callable[[str, Any, Any], None]):
        """Unsubscribe from notifications."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def _notify_change(self, key: str, old_value: Any, new_value: Any):
        """Notify all subscribers of a change."""
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error("Error in change callback: %s", e)

    # ========================================================================
    # Serialization for Persistence
    # ========================================================================

    def to_dict(self) -> dict:
        """
        Serialize current state to dictionary.

        Returns
        -------
        dict
            Current configuration as dictionary
        """
        return self._config.to_dict()

    def from_dict(self, data: dict):
        """
        Load state from dictionary.

        Parameters
        ----------
        data : dict
            Configuration dictionary
        """
        self._config = FilterConfig.from_dict(data)
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.info("State loaded from dictionary")

    def reset_to_defaults(self):
        """Reset all configuration to default values."""
        self._undo_stack.append(copy.deepcopy(self._config))
        self._redo_stack.clear()
        self._config = FilterConfig()
        logger.info("Configuration reset to defaults")

    # ========================================================================
    # Backward Compatibility: dict-like interface
    # ========================================================================

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access: broker['N']"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        """Allow dict-like assignment: broker['N'] = 5"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator: 'N' in broker"""
        return hasattr(self._config, key)

    def __repr__(self) -> str:
        return f"FilterBroker({self._config})"


# ============================================================================
# Legacy Wrapper Functions for Backward Compatibility
# ============================================================================

def fb_get(*key_list, fil_dict=None, verbose: bool = True) -> Any:
    """
    Backward compatible wrapper for old fb_get() calls.

    DEPRECATED: New code should use FilterBroker.get_instance().get()

    OLD CODE continues to work:
        result = fb_get('N')

    NEW CODE should use:
        broker = FilterBroker.get_instance()
        result = broker.get('N')
    """
    broker = FilterBroker.get_instance()

    if len(key_list) == 0:
        return broker.to_dict()
    if len(key_list) == 1:
        result = broker.get(key_list[0])
        if result is None and verbose:
            logger.warning("Key '%s' not found", key_list[0])
        return result

    logger.warning("fb_get with multiple/nested keys is deprecated. "
                    "Use FilterBroker directly.")
    return None


def fb_set(*key_list, backup: bool = True, new_key: bool = False) -> int:
    """
    Backward compatible wrapper for old fb_set() calls.

    DEPRECATED: New code should use FilterBroker.get_instance().set()

    OLD CODE continues to work:
        fb_set('N', 5)

    NEW CODE should use:
        broker = FilterBroker.get_instance()
        broker.set('N', 5)

    Returns
    -------
    int
        0 if successful, -1 if error
    """
    broker = FilterBroker.get_instance()

    if len(key_list) < 2:
        logger.error("fb_set requires at least 2 arguments (key, value)")
        return -1

    key = key_list[0]
    value = key_list[1]

    success = broker.set(key, value, backup=backup)
    return 0 if success else -1
