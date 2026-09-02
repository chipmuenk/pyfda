# -*- coding: utf-8 -*-
"""
Unit tests for the refactored FilterBroker.

Demonstrates improved testability of class-based design.
"""

import pytest
from docs.migration.filterbroker_v2 import FilterBroker, FilterConfig


class TestFilterConfig:
    """Test the FilterConfig dataclass."""
    
    def test_default_values(self):
        """Test that default values are initialized correctly."""
        config = FilterConfig()
        assert config.N == 4
        assert config.f_c == 0.1
        assert config.f_S == 1.0
    
    def test_to_dict(self):
        """Test serialization to dict."""
        config = FilterConfig()
        config.N = 8
        data = config.to_dict()
        
        assert data['N'] == 8
        assert 'f_c' in data
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {'N': 12, 'f_c': 0.25, 'f_S': 2.0}
        config = FilterConfig.from_dict(data)
        
        assert config.N == 12
        assert config.f_c == 0.25
        assert config.f_S == 2.0


class TestFilterBrokerBasics:
    """Test basic FilterBroker functionality."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_singleton(self):
        """Test that FilterBroker is a singleton."""
        broker1 = FilterBroker.get_instance()
        broker2 = FilterBroker.get_instance()
        assert broker1 is broker2
    
    def test_get_set(self):
        """Test basic get/set operations."""
        broker = FilterBroker.get_instance()
        
        # Test set and get
        assert broker.set('N', 8) is True
        assert broker.get('N') == 8
        
        # Test multiple sets
        assert broker.set('f_c', 0.25) is True
        assert broker.get('f_c') == 0.25
        
        # Original value unchanged
        assert broker.get('N') == 8
    
    def test_get_nonexistent_key(self):
        """Test getting nonexistent key."""
        broker = FilterBroker.get_instance()
        
        result = broker.get('nonexistent_key')
        assert result is None
        
        result = broker.get('nonexistent_key', default=42)
        assert result == 42
    
    def test_set_invalid_key(self):
        """Test setting invalid key."""
        broker = FilterBroker.get_instance()
        
        assert broker.set('invalid_key', 5) is False
    
    def test_dict_like_access(self):
        """Test dict-like access interface."""
        broker = FilterBroker.get_instance()
        
        # __setitem__
        broker['N'] = 10
        assert broker['N'] == 10
        
        # __contains__
        assert 'N' in broker
        assert 'invalid' not in broker


class TestUndoRedo:
    """Test undo/redo functionality."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_simple_undo(self):
        """Test basic undo functionality."""
        broker = FilterBroker.get_instance()
        
        broker.set('N', 5)
        broker.set('N', 10)
        
        assert broker.get('N') == 10
        assert broker.undo() is True
        assert broker.get('N') == 5
    
    def test_simple_redo(self):
        """Test basic redo functionality."""
        broker = FilterBroker.get_instance()
        
        broker.set('N', 5)
        broker.undo()
        
        assert broker.get('N') == 4  # default value
        assert broker.redo() is True
        assert broker.get('N') == 5
    
    def test_undo_empty_stack(self):
        """Test undo with empty stack."""
        broker = FilterBroker.get_instance()
        
        assert broker.undo() is False
    
    def test_redo_empty_stack(self):
        """Test redo with empty stack."""
        broker = FilterBroker.get_instance()
        
        assert broker.redo() is False
    
    def test_can_undo_redo(self):
        """Test can_undo() and can_redo()."""
        broker = FilterBroker.get_instance()
        
        assert broker.can_undo() is False
        assert broker.can_redo() is False
        
        broker.set('N', 8)
        assert broker.can_undo() is True
        assert broker.can_redo() is False
        
        broker.undo()
        assert broker.can_undo() is False
        assert broker.can_redo() is True
    
    def test_undo_stack_limit(self):
        """Test that undo stack respects size limit."""
        broker = FilterBroker.get_instance()
        
        # Fill undo stack beyond limit
        for i in range(FilterBroker.UNDO_LEN + 5):
            broker.set('N', i, backup=True)
        
        # Stack should be limited
        assert len(broker._undo_stack) <= FilterBroker.UNDO_LEN
    
    def test_set_clears_redo_stack(self):
        """Test that setting a value clears redo stack."""
        broker = FilterBroker.get_instance()
        
        broker.set('N', 5)
        broker.set('N', 10)
        broker.undo()
        
        assert broker.can_redo() is True
        
        broker.set('N', 15)  # This should clear redo stack
        
        assert broker.can_redo() is False


class TestBatchSet:
    """Test batch set operations."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_batch_set(self):
        """Test setting multiple values at once."""
        broker = FilterBroker.get_instance()
        
        updates = {'N': 8, 'f_c': 0.25, 'f_S': 2.0}
        assert broker.batch_set(updates) is True
        
        assert broker.get('N') == 8
        assert broker.get('f_c') == 0.25
        assert broker.get('f_S') == 2.0
    
    def test_batch_set_creates_single_undo(self):
        """Test that batch_set creates only one undo entry."""
        broker = FilterBroker.get_instance()
        
        updates = {'N': 8, 'f_c': 0.25}
        broker.batch_set(updates)
        
        # Undo should restore both values
        broker.undo()
        assert broker.get('N') == 4  # default
        assert broker.get('f_c') == 0.1  # default


class TestSubscriptions:
    """Test change notification system."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_subscription_notification(self):
        """Test that subscribers are notified of changes."""
        broker = FilterBroker.get_instance()
        changes = []
        
        def track_change(key, old_val, new_val):
            changes.append((key, old_val, new_val))
        
        broker.subscribe(track_change)
        broker.set('N', 8)
        
        assert len(changes) == 1
        assert changes[0] == ('N', 4, 8)
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers."""
        broker = FilterBroker.get_instance()
        changes1 = []
        changes2 = []
        
        def track1(key, old, new):
            changes1.append((key, old, new))
        
        def track2(key, old, new):
            changes2.append((key, old, new))
        
        broker.subscribe(track1)
        broker.subscribe(track2)
        broker.set('N', 8)
        
        assert len(changes1) == 1
        assert len(changes2) == 1
    
    def test_unsubscribe(self):
        """Test unsubscribing from notifications."""
        broker = FilterBroker.get_instance()
        changes = []
        
        def track_change(key, old_val, new_val):
            changes.append((key, old_val, new_val))
        
        broker.subscribe(track_change)
        broker.set('N', 8)
        assert len(changes) == 1
        
        broker.unsubscribe(track_change)
        broker.set('N', 10)
        assert len(changes) == 1  # No new change
    
    def test_no_notification_on_same_value(self):
        """Test that setting same value doesn't notify."""
        broker = FilterBroker.get_instance()
        changes = []
        
        def track_change(key, old_val, new_val):
            changes.append((key, old_val, new_val))
        
        broker.subscribe(track_change)
        broker.set('N', 4)  # Set to same value
        
        assert len(changes) == 0


class TestSerialization:
    """Test save/load functionality."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_to_dict(self):
        """Test serialization to dict."""
        broker = FilterBroker.get_instance()
        broker.set('N', 12)
        broker.set('f_c', 0.25)
        
        data = broker.to_dict()
        
        assert data['N'] == 12
        assert data['f_c'] == 0.25
        assert 'f_S' in data
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        broker1 = FilterBroker.get_instance()
        broker1.set('N', 12)
        broker1.set('f_c', 0.25)
        
        # Save state
        data = broker1.to_dict()
        
        # Reset and load
        FilterBroker.reset_instance()
        broker2 = FilterBroker.get_instance()
        broker2.from_dict(data)
        
        assert broker2.get('N') == 12
        assert broker2.get('f_c') == 0.25
    
    def test_reset_to_defaults(self):
        """Test resetting to default values."""
        broker = FilterBroker.get_instance()
        broker.set('N', 12)
        broker.set('f_c', 0.25)
        
        broker.reset_to_defaults()
        
        assert broker.get('N') == 4
        assert broker.get('f_c') == 0.1
        
        # Can undo the reset
        assert broker.undo() is True
        assert broker.get('N') == 12


class TestBackwardCompatibility:
    """Test legacy wrapper functions."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_fb_get_legacy(self):
        """Test legacy fb_get function."""
        from docs.migration.filterbroker_v2 import fb_get
        
        result = fb_get('N')
        assert result == 4  # default value
    
    def test_fb_set_legacy(self):
        """Test legacy fb_set function."""
        from docs.migration.filterbroker_v2 import fb_set
        
        result = fb_set('N', 8)
        assert result == 0  # success
        
        broker = FilterBroker.get_instance()
        assert broker.get('N') == 8
    
    def test_fb_get_without_args(self):
        """Test fb_get without arguments returns dict."""
        from docs.migration.filterbroker_v2 import fb_get
        
        data = fb_get()
        assert isinstance(data, dict)
        assert 'N' in data


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Reset broker before each test."""
        FilterBroker.reset_instance()
    
    def test_set_without_backup(self):
        """Test set with backup=False."""
        broker = FilterBroker.get_instance()
        
        broker.set('N', 8, backup=False)
        
        assert broker.get('N') == 8
        assert broker.can_undo() is False
    
    def test_set_without_notify(self):
        """Test set with notify=False."""
        broker = FilterBroker.get_instance()
        changes = []
        
        def track_change(key, old_val, new_val):
            changes.append((key, old_val, new_val))
        
        broker.subscribe(track_change)
        broker.set('N', 8, notify=False)
        
        assert len(changes) == 0
        assert broker.get('N') == 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
