# -*- coding: utf-8 -*-
"""
Migration Guide: Updating existing code from old to new FilterBroker.

This file shows concrete before/after examples for migrating code from
the module-level global dictionary approach to the new class-based FilterBroker.
"""

# ============================================================================
# EXAMPLE 1: Simple Filter Widget
# ============================================================================

# --- BEFORE (Old filterbroker.py)
"""
from pyfda import filterbroker as fb

class OldFilterWidget:
    def get_filter_order(self):
        # Tightly coupled to global state
        return fb.fb_get('N')
    
    def set_filter_specs(self, order, freq):
        fb.fb_set('N', order)
        fb.fb_set('F_C', freq)
    
    def undo_last_change(self):
        fb.restore_fil()
    
    def redo_last_change(self):
        # Note: Old code doesn't have redo, only undo!
        pass
"""

# --- AFTER (New filterbroker_v2.py)
from pyfda.filterbroker_v2 import FilterBroker

class NewFilterWidget:
    """Dependency-injected version - much easier to test."""
    
    def __init__(self, broker: FilterBroker = None):
        # Can inject a mock broker for testing
        self.broker = broker or FilterBroker.get_instance()
    
    def get_filter_order(self) -> int:
        return self.broker.get('N')
    
    def set_filter_specs(self, order: int, freq: float) -> bool:
        # Batch operation = single undo entry
        return self.broker.batch_set({'N': order, 'F_C': freq})
    
    def undo_last_change(self) -> bool:
        return self.broker.undo()
    
    def redo_last_change(self) -> bool:
        return self.broker.redo()


# --- Testing the difference

# Old approach: Very hard to test (global state interference)
"""
def test_old_widget():
    widget = OldFilterWidget()
    result = widget.get_filter_order()
    # Problem: What if another test changed fb.fil[0]['N']?
    # Test is not isolated!
    assert result == 4  # Might fail due to global state
"""

# New approach: Easy to test (dependency injection)

from unittest.mock import MagicMock

def test_new_widget():
    # Create mock broker
    mock_broker = MagicMock(spec=FilterBroker)
    mock_broker.get.return_value = 8
    
    # Test widget with mock
    widget = NewFilterWidget(broker=mock_broker)
    result = widget.get_filter_order()
    
    # Isolated test!
    assert result == 8
    mock_broker.get.assert_called_once_with('N')


# ============================================================================
# EXAMPLE 2: Complex Filter Designer
# ============================================================================

# --- BEFORE (Old approach)

"""
from pyfda import filterbroker as fb

class OldFilterDesigner:
    def design_lowpass(self):
        order = fb.fb_get('N')
        freq = fb.fb_get('F_C')

        # Design filter
        ba = self._compute_coefficients(order, freq)
        
        # Store results in global dict
        fb.fb_set('ba', ba)
        fb.backup_fil()  # Manual backup
    
    def undo_design(self):
        fb.restore_fil()
    
    def _compute_coefficients(self, order, freq):
        # Complex computation...
        return np.array([[1], [1]])
"""

# --- AFTER (New approach)

from typing import Optional
import numpy as np

class NewFilterDesigner:
    """
    Type-safe, testable filter designer with change notifications.
    """
    
    def __init__(self, broker: FilterBroker = None):
        self.broker = broker or FilterBroker.get_instance()
        # Subscribe to design changes for live updates
        self.broker.subscribe(self._on_param_changed)
    
    def design_lowpass(self) -> bool:
        """Design lowpass filter with current parameters."""
        try:
            order = self.broker.get('N')
            freq = self.broker.get('F_C')
            
            if not self._validate_params(order, freq):
                return False
            
            # Design filter
            ba = self._compute_coefficients(order, freq)
            
            # Store result (automatic backup)
            return self.broker.set('ba', ba)
        
        except Exception as e:
            print(f"Design error: {e}")
            return False
    
    def undo_design(self) -> bool:
        """Undo last design change."""
        return self.broker.undo()
    
    def redo_design(self) -> bool:
        """Redo last undone design."""
        return self.broker.redo()
    
    def _validate_params(self, order: int, freq: float) -> bool:
        """Validate design parameters."""
        return 1 <= order <= 100 and 0 < freq < 0.5
    
    def _compute_coefficients(self, order: int, freq: float) -> np.ndarray:
        """Complex computation..."""
        return np.array([[1], [1]])
    
    def _on_param_changed(self, key: str, old_val, new_val):
        """Called when any filter parameter changes."""
        if key in ['N', 'F_C', 'ft', 'rt']:
            print(f"Parameter {key} changed: {old_val} -> {new_val}")
            # Could trigger automatic redesign here
            # self.design_lowpass()


# Testing new designer is straightforward

def test_new_designer():
    # Create mock broker
    mock_broker = MagicMock(spec=FilterBroker)
    mock_broker.get.side_effect = lambda key: {
        'N': 8,
        'F_C': 0.25
    }.get(key)
    mock_broker.set.return_value = True

    designer = NewFilterDesigner(broker=mock_broker)
    success = designer.design_lowpass()
    
    assert success
    # Verify parameters were retrieved
    assert mock_broker.get.call_count >= 2
    # Verify result was stored
    mock_broker.set.assert_called_once()


# ============================================================================
# EXAMPLE 3: Multiple Filter Storage
# ============================================================================

# --- BEFORE (Old approach with fil[0]...fil[9])
"""
from pyfda import filterbroker as fb

class OldMultiFilterManager:
    def save_current_filter(self, slot: int):
        # Have to copy entire dict manually
        fb.fil[slot] = copy.deepcopy(fb.fil[0])
    
    def load_filter(self, slot: int):
        # Restore to current
        fb.fil[0] = copy.deepcopy(fb.fil[slot])
    
    def compare_filters(self, slot1: int, slot2: int):
        return fb.fil[slot1] == fb.fil[slot2]
"""

# --- AFTER (New approach)
from typing import Dict
import copy

class NewMultiFilterManager:
    """Manage multiple filter designs with easy save/load."""
    
    def __init__(self, broker: FilterBroker = None):
        self.broker = broker or FilterBroker.get_instance()
        self.filters: Dict[int, dict] = {}
        self.current_slot = 0
    
    def save_current_filter(self, slot: int):
        """Save current filter to slot."""
        self.filters[slot] = self.broker.to_dict()
        print(f"Filter saved to slot {slot}")
    
    def load_filter(self, slot: int) -> bool:
        """Load filter from slot."""
        if slot not in self.filters:
            print(f"Slot {slot} is empty")
            return False
        
        self.broker.from_dict(self.filters[slot])
        self.current_slot = slot
        print(f"Filter loaded from slot {slot}")
        return True
    
    def compare_filters(self, slot1: int, slot2: int) -> bool:
        """Compare two saved filters."""
        if slot1 not in self.filters or slot2 not in self.filters:
            return False
        return self.filters[slot1] == self.filters[slot2]
    
    def list_saved_filters(self):
        """List all saved filter slots."""
        return sorted(self.filters.keys())
    
    def clear_filter(self, slot: int):
        """Delete filter from slot."""
        if slot in self.filters:
            del self.filters[slot]


# ============================================================================
# EXAMPLE 4: GUI Integration with Callbacks
# ============================================================================

# --- BEFORE (Old approach - manual updates)

"""
from pyfda import filterbroker as fb

class OldFilterUI:
    def __init__(self, ui_manager):
        self.ui = ui_manager

    def on_order_changed(self, new_order):
        fb.fb_set('N', new_order)
        # Manually update all dependent UI elements
        self.ui.update_freq_response()
        self.ui.update_filter_plot()
        self.ui.update_coefficients_table()
    
    def on_frequency_changed(self, new_freq):
        fb.fb_set('F_C', new_freq)
        # Manually update all dependent UI elements again
        self.ui.update_freq_response()
        self.ui.update_filter_plot()
"""

# --- AFTER (New approach - event-driven)

class UIManager:
    """Mock UI manager."""
    def update_freq_response(self):
        pass

    def update_filter_plot(self):
        pass
    
    def update_coefficients_table(self):
        pass


class NewFilterUI:
    """Event-driven UI that automatically updates on changes."""

    def __init__(self, ui_manager: UIManager, broker: FilterBroker = None):
        self.ui = ui_manager
        self.broker = broker or FilterBroker.get_instance()
        
        # Subscribe to ALL parameter changes
        self.broker.subscribe(self._on_filter_param_changed)
    
    def on_order_changed(self, new_order: int):
        """Called when user changes filter order."""
        self.broker.set('N', new_order)
        # No manual update calls needed!
    
    def on_frequency_changed(self, new_freq: float):
        """Called when user changes frequency."""
        self.broker.set('F_C', new_freq)
        # No manual update calls needed!
    
    def _on_filter_param_changed(self, key: str, old_val, new_val):
        """
        Automatically called by broker when ANY parameter changes.
        Updates all dependent UI elements.
        """
        # Update dependent UI elements
        self.ui.update_freq_response()
        self.ui.update_filter_plot()
        self.ui.update_coefficients_table()
        
        print(f"UI updated due to {key} change: {old_val} -> {new_val}")


# ============================================================================
# MIGRATION CHECKLIST
# ============================================================================

"""
When migrating from old to new FilterBroker:

STEP 1: Update imports
  OLD: from pyfda import filterbroker as fb
  NEW: from pyfda.filterbroker_v2 import FilterBroker

STEP 2: Get broker instance
  OLD: (globals, no instance)
  NEW: broker = FilterBroker.get_instance()

STEP 3: Replace fb_get/fb_set calls
  OLD: value = fb.fb_get('N')
  NEW: value = broker.get('N')
  
  OLD: fb.fb_set('N', 5)
  NEW: broker.set('N', 5)

STEP 4: Replace undo/redo calls
  OLD: fb.backup_fil() / fb.restore_fil()
  NEW: (automatic, or broker.undo() / broker.redo())

STEP 5: Add dependency injection where possible
  OLD: class Widget:
           def __init__(self):
               pass
  
  NEW: class Widget:
           def __init__(self, broker: FilterBroker = None):
               self.broker = broker or FilterBroker.get_instance()

STEP 6: Add tests using mock brokers
  NEW: Create tests with MagicMock(spec=FilterBroker)

STEP 7: (Optional) Use subscription system for automatic updates
  NEW: broker.subscribe(lambda key, old, new: self.update_ui())

PRIORITY MIGRATION ORDER:

1. Modules that are most tested (easier to validate changes)
2. Widget classes (separate state from UI logic)
3. Filter design algorithms
4. Main application entry points last
"""
