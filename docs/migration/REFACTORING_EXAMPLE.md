# Filterbroker Refactoring Example

## Problem with Current Approach

Your current `filterbroker.py` uses module-level globals:
```python
# Current code
from pyfda import filterbroker as fb
value = fb_get('N')
fb_set('N', 5)
```

**Issues:**
- Global state makes unit testing difficult
- No type safety—type errors caught at runtime only
- Tight coupling throughout codebase
- Hard to serialize/persist state
- No IDE autocomplete for valid keys
- Thread-unsafe

## Proposed Solution: Class-Based with Backward Compatibility

### Step 1: Create FilterBroker Class (New File)

Create `pyfda/filterbroker_v2.py` with a class-based design:

```python
# filterbroker_v2.py (new file - side by side with current filterbroker.py)
"""
New class-based FilterBroker with type safety and dependency injection.
Designed to coexist with current implementation during migration.
"""
import copy
import logging
from typing import Any, Callable
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)

# ============================================================================
# Type-safe configuration using dataclass (lightweight alternative to Pydantic)
# ============================================================================

@dataclass
class FilterConfig:
    """Type-safe filter configuration with documentation."""
    # Amplitude specs (linear units)
    a_pb: float = 0.2056717652757185
    a_pb2: float = 0.01
    a_sb: float = 0.001
    a_sb2: float = 0.0001
    
    # Frequency specs (normalized to F_S)
    f_c: float = 0.1
    f_c2: float = 0.4
    F_N: float = 0.2
    F_N2: float = 0.4
    f_pb: float = 0.1
    f_pb2: float = 0.3
    f_sb: float = 0.2
    f_sb2: float = 0.4
    
    N: int = 4  # filter order
    T_S: float = 1.0  # sample time
    
    # Weights
    w_pb: float = 1.0
    W_PB2: float = 1.0
    w_sb: float = 1.0
    W_SB2: float = 1.0
    
    amp_specs_unit: str = 'dB'
    
    # ... add other fields as needed
    _id: list = field(default_factory=list)
    creator: list = field(default_factory=lambda: ['sos', 'pyfda.filter_widgets.ellip'])
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {k: v for k, v in self.__dict__.items()}
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary."""
        # Filter to only valid dataclass fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ============================================================================
# Main FilterBroker Class - Singleton Pattern
# ============================================================================

class FilterBroker:
    """
    Centralized filter state management with undo/redo and type safety.
    
    Usage:
        broker = FilterBroker()
        broker.get('N')  # type-safe, with validation
        broker.set('N', 5)
        broker.undo()
        
    For dependency injection:
        def process_filter(broker: FilterBroker):
            order = broker.get('N')
            ...
    """
    _instance = None
    UNDO_LEN = 20
    
    def __init__(self):
        """Initialize FilterBroker as singleton."""
        if FilterBroker._instance is not None:
            raise RuntimeError("FilterBroker is a singleton. Use FilterBroker.get_instance()")
        
        self._config = FilterConfig()
        self._undo_stack: list[FilterConfig] = []
        self._redo_stack: list[FilterConfig] = []
        self._change_callbacks: list[Callable] = []
        self._lock_depth = 0  # For preventing undo during callbacks
        
        logger.info("FilterBroker initialized")
    
    @staticmethod
    def get_instance() -> 'FilterBroker':
        """Get singleton instance, creating if necessary."""
        if FilterBroker._instance is None:
            FilterBroker._instance = FilterBroker()
        return FilterBroker._instance
    
    # ========================================================================
    # Core Get/Set Operations (Compatible with existing fb_get/fb_set)
    # ========================================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key with type checking.
        
        Parameters
        ----------
        key : str
            Configuration key (e.g., 'N', 'f_c')
        default : Any
            Default value if key doesn't exist
        
        Returns
        -------
        Any
            Configuration value or default
        """
        if not hasattr(self._config, key):
            logger.warning(f"Key '{key}' not found in FilterConfig")
            return default
        
        return getattr(self._config, key)
    
    def set(self, key: str, value: Any, backup: bool = True) -> bool:
        """
        Set configuration value with type checking and undo support.
        
        Parameters
        ----------
        key : str
            Configuration key
        value : Any
            New value
        backup : bool
            Whether to backup for undo
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not hasattr(self._config, key):
            logger.error(f"Key '{key}' not recognized in FilterConfig")
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
            if old_value != value and self._lock_depth == 0:
                self._notify_change(key, old_value, value)
            
            return True
        except (TypeError, ValueError) as e:
            logger.error(f"Type error setting '{key}': {e}")
            return False
    
    def undo(self) -> bool:
        """Undo last change."""
        if not self._undo_stack:
            logger.debug("Undo stack empty")
            return False
        
        self._redo_stack.append(copy.deepcopy(self._config))
        self._config = self._undo_stack.pop()
        logger.debug("Undo executed")
        return True
    
    def redo(self) -> bool:
        """Redo last undone change."""
        if not self._redo_stack:
            logger.debug("Redo stack empty")
            return False
        
        self._undo_stack.append(copy.deepcopy(self._config))
        self._config = self._redo_stack.pop()
        logger.debug("Redo executed")
        return True
    
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
        """
        self._change_callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from notifications."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_change(self, key: str, old_value: Any, new_value: Any):
        """Notify all subscribers of a change."""
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
    
    # ========================================================================
    # Serialization for Persistence
    # ========================================================================
    
    def to_dict(self) -> dict:
        """Serialize current state to dictionary."""
        return self._config.to_dict()
    
    def from_dict(self, data: dict):
        """Load state from dictionary."""
        self._config = FilterConfig.from_dict(data)
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.info("State loaded from dictionary")
    
    # ========================================================================
    # Backward Compatibility: dict-like interface for old code
    # ========================================================================
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access: broker['N']"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        """Allow dict-like assignment: broker['N'] = 5"""
        self.set(key, value)
    
    def __repr__(self) -> str:
        return f"FilterBroker({self._config})"


# ============================================================================
# Legacy Wrapper Functions for Backward Compatibility
# ============================================================================

def fb_get(*key_list) -> Any:
    """
    Backward compatible wrapper for old fb_get() calls.
    
    NEW CODE should use:
        broker = FilterBroker.get_instance()
        broker.get('N')
    
    OLD CODE continues to work:
        fb_get('N')
    """
    broker = FilterBroker.get_instance()
    if len(key_list) == 0:
        return broker.to_dict()
    elif len(key_list) == 1:
        return broker.get(key_list[0])
    else:
        logger.warning("fb_get with nested keys deprecated. Use FilterBroker directly.")
        return None


def fb_set(*key_list, backup: bool = True, new_key: bool = False) -> int:
    """
    Backward compatible wrapper for old fb_set() calls.
    
    NEW CODE should use:
        broker = FilterBroker.get_instance()
        broker.set('N', 5)
    
    OLD CODE continues to work:
        fb_set('N', 5)
    """
    broker = FilterBroker.get_instance()
    if len(key_list) < 2:
        logger.error("fb_set requires at least 2 arguments")
        return -1
    
    key = key_list[0]
    value = key_list[1]
    
    success = broker.set(key, value, backup=backup)
    return 0 if success else -1
```

### Step 2: Usage Examples

#### **Old Way (Current Code)**
```python
from pyfda import filterbroker as fb

# Direct global access
order = fb.fb_get('N')
fb.fb_set('N', 8)
fb.backup_fil()  # manual undo management
fb.restore_fil()
```

#### **New Way (Recommended)**
```python
from pyfda.filterbroker_v2 import FilterBroker

# Get singleton instance
broker = FilterBroker.get_instance()

# Type-safe access
order = broker.get('N')  # IDE knows valid keys
broker.set('N', 8)  # Automatic undo tracking
broker.undo()
broker.redo()

# Subscribe to changes
def on_filter_changed(key: str, old_val, new_val):
    print(f"Filter {key} changed from {old_val} to {new_val}")

broker.subscribe(on_filter_changed)
```

#### **With Dependency Injection (Best Practice)**
```python
class FilterDesigner:
    """Example of proper dependency injection."""
    
    def __init__(self, broker: FilterBroker):
        self.broker = broker
        # Much easier to test: pass mock broker in tests
    
    def design_filter(self):
        order = self.broker.get('N')
        freq = self.broker.get('f_c')
        # ... design logic ...
        self.broker.set('ba', coefficients)


# Production
designer = FilterDesigner(FilterBroker.get_instance())

# Testing
from unittest.mock import MagicMock
mock_broker = MagicMock()
test_designer = FilterDesigner(mock_broker)
test_designer.design_filter()
mock_broker.set.assert_called()
```

### Step 3: Migration Strategy

**Phase 1 (Parallel):**
- Create `filterbroker_v2.py` alongside existing code
- Both work independently
- New code uses v2, old code unchanged

**Phase 2 (Gradual Migration):**
```python
# In existing modules, gradually change:

# FROM:
from pyfda import filterbroker as fb
N = fb.fb_get('N')

# TO:
from pyfda.filterbroker_v2 import FilterBroker
N = FilterBroker.get_instance().get('N')

# OR for better design:
class MyWidget:
    def __init__(self, broker: FilterBroker):
        self.broker = broker
```

**Phase 3 (Refactor Existing):**
Once all code migrated, replace old `filterbroker.py` with v2.

### Step 4: Unit Test Example

```python
# tests/test_filterbroker.py
import pytest
from pyfda.filterbroker_v2 import FilterBroker, FilterConfig

def test_get_set():
    """Test basic get/set operations."""
    broker = FilterBroker()
    
    # Test set and get
    broker.set('N', 8)
    assert broker.get('N') == 8
    
    # Test type mismatch
    result = broker.set('N', 'invalid')
    assert result is False

def test_undo_redo():
    """Test undo/redo functionality."""
    broker = FilterBroker()
    
    broker.set('N', 5)
    broker.set('N', 10)
    
    assert broker.get('N') == 10
    broker.undo()
    assert broker.get('N') == 5
    
    broker.redo()
    assert broker.get('N') == 10

def test_subscription():
    """Test change notifications."""
    broker = FilterBroker()
    changes = []
    
    def track_change(key, old_val, new_val):
        changes.append((key, old_val, new_val))
    
    broker.subscribe(track_change)
    broker.set('N', 6)
    
    assert len(changes) == 1
    assert changes[0] == ('N', 4, 6)

def test_serialization():
    """Test save/load functionality."""
    broker = FilterBroker()
    broker.set('N', 12)
    broker.set('f_c', 0.25)
    
    # Save
    data = broker.to_dict()
    
    # Create new broker and load
    broker2 = FilterBroker()
    broker2.from_dict(data)
    
    assert broker2.get('N') == 12
    assert broker2.get('f_c') == 0.25
```

## Benefits of This Refactoring

| Aspect | Current | Refactored |
|--------|---------|-----------|
| **Type Safety** | None | Full type hints, IDE autocomplete |
| **Testability** | Poor (global state) | Excellent (dependency injection) |
| **Undo/Redo** | Manual | Automatic |
| **Serialization** | Difficult | Built-in `.to_dict()` / `.from_dict()` |
| **Change Tracking** | None | Subscription system |
| **Thread Safety** | No | Easy to add with locks |
| **IDE Support** | No autocomplete | Full autocomplete for keys |
| **Backward Compat** | N/A | Full compatibility wrappers |

## Next Steps

1. Create `filterbroker_v2.py` file
2. Use in new code where possible
3. Add tests gradually
4. Migrate old modules one by one
5. Eventually retire old version

