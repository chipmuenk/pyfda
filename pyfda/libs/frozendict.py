# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create an immutable dictionary for the filter tree. The eliminates the risk
that a filter design routine inadvertedly modifies the dict e.g. via
a shallow copy. Used by filterbroker.py and filter_tree_builder.py

Taken from http://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be
"""
#------------- For FrozenOrderedDict --------------------
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from functools import reduce
import operator
from typing import Any
# ----------------------------------------------------------

def col(i: int) -> property:
    """
    Create a property that returns the tuple element at index `i`.

    This helper is used by `Item` to expose the first and second tuple elements
    as named attributes, `key` and `value`.

    Parameters
    ----------
    i: int
        The index of the tuple element to expose.

    Returns
    -------
    property
        A property object that retrieves the tuple element at the given index.

    Usage
    -----
        key = col(0)   # Accesses the first element of the tuple
        value = col(1) # Accesses the second element of the tuple
    """
    g = tuple.__getitem__
    @property
    def _col(self) -> Any:
        return g(self, i)
    return _col

#--------------------------------------------------------------------------
def freeze_hierarchical(hier_dict: Any) -> Any | 'FrozenDict':
    """
    Recursively convert a dictionary and its nested dictionaries to FrozenDict.

    Parameters
    ----------
    hier_dict: dict or any
        The object to freeze. If the object is a dict, nested dicts are
        converted recursively to FrozenDict instances.

    Returns
    -------
    FrozenDict or any
        FrozenDict: If the input is a dict.
        Any: The input unchanged if it is not a dict.
    """
    if isinstance(hier_dict, dict):
        for k in hier_dict:
            if isinstance(hier_dict[k], dict):
                hier_dict[k] = freeze_hierarchical(hier_dict[k])
        return FrozenDict(hier_dict)

    return hier_dict


class Item(tuple):
    """
    Immutable container for a key/value pair stored inside a FrozenDict.

    The `Item` object behaves like a tuple of length two, but its hash is based
    solely on the key, and comparisons against non-Item objects compare only the
    keys.

    Designed for storing key-value pairs inside a FrozenDict, which itself is a subclass
    of frozenset.

    WARNING: Do not use this class for any other purpose!!!!

    The __hash__ is overloaded to return the hash of only the key.

    __eq__ is overloaded so that normally it only checks whether the Item's key is equal
    to the other object, HOWEVER, if the other object itself is an instance of Item, it
    checks BOTH the key and value for equality.

    This has the consequence that the __eq__ operator violates a fundamental property of
    mathematics. That property, which says that a == b and b == c implies a == c, does not
    hold for this object.

    Here's a demonstration:

        >>> x = Item(('a',4))
        >>> y = Item(('a',5))
        >>> hash('a')
        >>> 194817700
        >>> hash(x)
        >>> 194817700
        >>> hash(y)
        >>> 194817700
        >>> 'a' == x
        >>> True
        >>> 'a' == y
        >>> True
        >>> x == y
        >>> False
    """
    # __slots__ is a special class attribute in Python that tells the interpreter which instance
    # attributes are allowed. It
    # - prevents creation of a per-instance __dict__
    # - restricts instances to only the declared attribute names
    # - can save memory for many instances
    # - can slightly speed up attribute access
    #
    # The empty __slots__ = () declaration means that no new attributes can be assigned to
    # instances, keeping them as minimal as possible. This is appropriate for an immutable data
    # structure like FrozenDict.
    __slots__ = ()
    key, value = col(0), col(1)

    def __hash__(self) -> int:
        """Return the hash of the item's key."""
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """
        Compare the item with another object.

        If the other object is also an Item, compare both key and value. Otherwise,
        compare only the key to the other object.
        """
        if isinstance(other, Item):
            return tuple.__eq__(self, other)
        return self.key == other

    def __ne__(self, other: Any) -> bool:
        """Test whether this Item is not equal to another object."""
        return not self.__eq__(other)

    def __str__(self) -> str:
        """Return a human-readable string representation of the Item."""
        return f'{self[0]!r}: {self[1]!r}'

    def __repr__(self) -> str:
        """Return the canonical representation of the Item."""
        return f'Item(({self[0]!r}, {self[1]!r}))'

class FrozenDict(frozenset):
    """
    Behaves in most ways like a regular dictionary, except that it's immutable.
    It differs from other implementations because it doesn't subclass `dict`.
    Instead it subclasses "frozenset" which guarantees immutability.
    FrozenDict instances are created with the same arguments used to initialize
    regular dictionaries and have all the same methods.

        >>> f = FrozenDict(x=3,y=4,z=5)
        >>> f['x']
        >>> 3
        >>> f['a'] = 0
        >>> TypeError: 'FrozenDict' object does not support item assignment

        FrozenDict can accept un-hashable values, but FrozenDict is only hashable
        if its values are hashable.

        >>> f = FrozenDict(x=3, y=4, z=5)
        >>> hash(f)
        >>> 646626455
        >>> g = FrozenDict(x=3,y=4,z=[])
        >>> hash(g)
        >>> TypeError: unhashable type: 'list'

        FrozenDict interacts with dictionary objects as though it were a dict itself:

        >>> original = dict(x=3, y=4, z=5)
        >>> frozen = FrozenDict(x=3, y=4, z=5)
        >>> original == frozen
        >>> True

        FrozenDict supports bi-directional conversions with regular dictionaries:

        >>> original = {'x': 3, 'y': 4, 'z': 5}
        >>> FrozenDict(original)
        >>> FrozenDict({'x': 3, 'y': 4, 'z': 5})
        >>> dict(FrozenDict(original))
        >>> {'x': 3, 'y': 4, 'z': 5}
    """

    __slots__ = ()
    # __slots__ is a special class attribute in Python that tells the interpreter which instance
    # attributes are allowed. See class Item() for more details.

    def __new__(cls, orig: dict | None = None, **kw: Any) -> 'FrozenDict':
        """
        Create a FrozenDict from a mapping or iterable of key/value pairs.

        Parameters
        ----------
        orig: dict or iterable of key/value pairs, optional
            The initial data for the FrozenDict. If not provided, an empty FrozenDict is created.
        **kw: Any
            Additional key/value pairs to include in the FrozenDict. These are merged with `orig`
            if `orig` is provided, or used as the initial data if `orig` is not provided.

        Returns
        -------
        FrozenDict
            A new FrozenDict instance containing the provided key/value pairs.
        """
        if not orig:
            orig = {}
        if kw:
            d = dict(orig, **kw)
            items = map(Item, d.items())
        else:
            try:
                items = map(Item, orig.items())
            except AttributeError:
                items = map(Item, orig)
        return frozenset.__new__(cls, items)

    def __repr__(self) -> str:
        """Return the string representation of the FrozenDict."""
        cls = self.__class__.__name__
        items = frozenset.__iter__(self)
        _repr = ', '.join(map(str, items))
        return f'{cls}({_repr})'

    def __getitem__(self, key: Any) -> Any:
        """Return the value associated with the given key."""
        if key not in self:
            raise KeyError(key)
        diff = self.difference
        item = diff(diff({key}))
        key, value = set(item).pop()
        return value

    def get(self, key: Any, default: Any = None) -> Any:
        """Return the value for key if present, otherwise return default."""
        if key not in self:
            return default
        return self[key]

    def __iter__(self) -> Iterator[Any]:
        """Iterate over the keys of the FrozenDict."""
        items = frozenset.__iter__(self)
        return map(lambda i: i.key, items)

    def keys(self) -> Iterator[Any]:
        """Return an iterator over the mapping keys."""
        items = frozenset.__iter__(self)
        return map(lambda i: i.key, items)

    def values(self) -> Iterator[Any]:
        """Return an iterator over the mapping values."""
        items = frozenset.__iter__(self)
        return map(lambda i: i.value, items)

    def items(self) -> Iterator[tuple[Any, Any]]:
        """Return an iterator over the mapping's key/value pairs."""
        items = frozenset.__iter__(self)
        return map(tuple, items)

    def copy(self) -> 'FrozenDict':
        """Return a shallow copy of the FrozenDict."""
        cls = self.__class__
        items = frozenset.copy(self)
        return frozenset.__new__(cls, items)

    @classmethod
    def fromkeys(cls, keys: Iterable[Any], value: Any) -> 'FrozenDict':
        """Create a FrozenDict from an iterable of keys and a single default value."""
        d = dict.fromkeys(keys, value)
        return cls(d)

    def __hash__(self) -> int:
        """Return a hash based on the frozen set of key/value tuples."""
        kv = tuple.__hash__
        items = frozenset.__iter__(self)
        return hash(frozenset(map(kv, items)))

    def __eq__(self, other: Any) -> bool:
        """Compare this FrozenDict to another mapping or FrozenDict."""
        if not isinstance(other, FrozenDict):
            try:
                other = FrozenDict(other)
            except Exception:  # pylint: disable=broad-exception-caught
                return False
        return frozenset.__eq__(self, other)

    def __ne__(self, other: Any) -> bool:
        """Return True if this FrozenDict is not equal to another mapping or FrozenDict."""
        return not self.__eq__(other)


class FrozenOrderedDict(Mapping):
    """
    Frozen OrderedDict.
    https://github.com/wsmith323/frozenordereddict

    Alternatives
    -------------
    frozendict package by Marco Sulla
    https://github.com/Marco-Sulla/python-frozendict
    pip install frozendict
    """
    __version__ = "1.3.1"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the immutable ordered mapping from the provided arguments."""
        self.__dict = OrderedDict(*args, **kwargs)
        self.__hash = None

    def __getitem__(self, item: Any) -> Any:
        """Return the value for the provided key."""
        return self.__dict[item]

    def __iter__(self) -> Iterator[Any]:
        """Return an iterator over the stored keys."""
        return iter(self.__dict)

    def __len__(self) -> int:
        """Return the number of stored items."""
        return len(self.__dict)

    def __hash__(self) -> int:
        """Compute and cache the hash of the ordered mapping."""
        if self.__hash is None:
            self.__hash = reduce(operator.xor, map(hash, self.__dict.items()), 0)

        return self.__hash

    def __repr__(self) -> str:
        """Return the canonical representation of the FrozenOrderedDict."""
        return f'{self.__class__.__name__}({list(self.__dict.items())!r})'


    def copy(self, *args: Any, **kwargs: Any) -> 'FrozenOrderedDict':
        """Return a shallow copy, optionally updated with provided items."""
        new_dict = self.__dict.copy()

        if args or kwargs:
            new_dict.update(OrderedDict(*args, **kwargs))

        return self.__class__(new_dict)
