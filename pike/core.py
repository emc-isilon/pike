#
# Copyright (c) 2013-2020, Dell Inc. or its subsidiaries.
# All rights reserved.
# See file LICENSE for licensing information.
#
# Module Name:
#
#        core.py
#
# Abstract:
#
#        Core API
#
# Authors: Brian Koropoff (brian.koropoff@emc.com)
#          Masen Furer (masen.furer@dell.com)
#

"""
Core Pike infrastructure
"""

from builtins import hex
from builtins import str
from builtins import object
import array
from binascii import hexlify
import struct

from future.utils import with_metaclass


class BufferOverrun(Exception):
    """Buffer overrun exception"""

    def __init__(self, cursor, request, boundary):
        self.cursor = cursor
        self.request = request
        self.boundary = boundary

    @property
    def message(self):
        return "{} is {} bound {} in {!r}\nPacket buffer: {!r}".format(
            self.request,
            "below lower" if self.request < self.boundary else "above upper",
            self.boundary,
            self.cursor,
            hexlify(self.cursor.array),
        )

    def __str__(self):
        return self.message


class Cursor(object):
    """
    Byte array cursor

    Represents a position within a byte array.

    encode_* operations write data at the current position
    and advance it by the number of bytes written.

    decode_* operations read data at the current position,
    advance it by the number of bytes read, and return
    the result.

    Cursors support in-place addition and subtraction (+=,-=) of
    integer values to manually adjust position, as well
    as ordinary addition and subtraction, which return a new
    cursor without modifiying the original.

    Ordinary subtraction of two cursors will yield the
    difference between their positions as an integer.
    ==, !=, <, <=, >, and >= operators will also work to
    compare positions.  The results will only be meaningful
    for cursors referencing the same underlying array.

    For a given cursor, cursor.hole.encode_* will perform
    the same operation as cursor.encode_*, but will return
    a hole object.  Calling this hole object with the same
    type of arguments as the original encode method will
    overwrite the original value.  This mechanism is useful
    for backpatching values into fields that aren't known until
    later, such as internal packet lengths and offsets or
    checksum fields.  For example::

        hole = cursor.hole.encode_uint32le(0)
        # Encode rest of packet
        ...
        # Overwrite value with calculated checksum
        hole(sum)

    Cursors support slicing to extract sections
    of the underlying array.  For example::

        # Extract array slice between cur1 and cur2
        subarray = cur1[:cur2]

    Cursors also support establishing boundaries outside of which
    decoding will raise exceptions::

        with cur.bounded(startcur, endcur):
            # Within this block, attempts to decode data outside of
            # the range starting with startcur (inclusive) and ending
            # with endcur (exclusive) will raise BufferOverrun().
            # If the start and end paremeters are numbers rather than
            # other cursors, they will be taken to be relative to
            # cur itself.
            ...

    @ivar array: Array referenced by cursor
    @ivar offset: Offset within the array
    @ivar bounds: Pair of lower and upper bound on offset
    """

    def __init__(self, arr, offset, bounds=(None, None)):
        """
        Create a L{Cursor} for the given array
        at the given offset.

        @type arr: array.array('B', ...)
        @param arr: The array
        @type offset: number
        @param offset: The offset from the start of the array
        @param bounds: A pair of a lower and upper bound on valid offsets
        """

        self.array = arr
        self.offset = offset
        self.bounds = bounds
        self.hole = Cursor.Hole(self)

    def __eq__(self, o):
        return self.array is o.array and self.offset == o.offset

    def __ne__(self, o):
        return not (self == o)

    def __lt__(self, o):
        assert self.array is o.array
        return self.offset < o.offset

    def __gt__(self, o):
        assert self.array is o.array
        return self.offset > o.offset

    def __le__(self, o):
        assert self.array is o.array
        return self.offset <= o.offset

    def __ge__(self, o):
        assert self.array is o.array
        return self.offset >= o.offset

    def __add__(self, o):
        return Cursor(self.array, self.offset + o, self.bounds)

    def __sub__(self, o):
        if isinstance(o, Cursor):
            assert self.array is o.array
            return self.offset - o.offset
        else:
            return Cursor(self.array, self.offset - o, self.bounds)

    def __iadd__(self, o):
        self.offset += o
        return self

    def __isub__(self, o):
        self.offset -= o
        return self

    def _getindex(self, ind):
        if ind is None:
            return None
        elif isinstance(ind, Cursor):
            assert self.array is ind.array
            return ind.offset
        else:
            return self.offset + ind

    def __getitem__(self, index):
        if isinstance(index, slice):
            start = self._getindex(index.start if index.start else 0)
            stop = self._getindex(index.stop)
            step = index.step

            self._check_bounds(start, stop)
            return self.array.__getitem__(slice(start, stop, step))
        else:
            self._check_bounds(index, index + 1)
            return self.array.__getitem__(index)

    def __repr__(self):
        return (
            "Cursor("
            + object.__repr__(self.array)
            + ","
            + repr(self.offset)
            + ","
            + repr(self.bounds)
            + ")"
        )

    def copy(self):
        """ Create copy of cursor. """
        return Cursor(self.array, self.offset, self.bounds)

    def _expand_to(self, size):
        cur_size = len(self.array)
        if size > cur_size:
            self.array.extend([0] * (size - cur_size))

    def encode_bytes(self, val):
        """ Encode bytes.  Accepts byte arrays, strings, and integer lists."""
        size = len(val)
        self._expand_to(self.offset + size)
        self.array[self.offset : self.offset + size] = array.array("B", val)
        self.offset += size

    def encode_struct(self, fmt, *args):
        size = struct.calcsize(fmt)
        self._expand_to(self.offset + size)
        struct.pack_into(fmt, self.array, self.offset, *args)
        self.offset += size

    def encode_uint8be(self, val):
        self.encode_struct(">B", val)

    def encode_uint16be(self, val):
        self.encode_struct(">H", val)

    def encode_uint32be(self, val):
        self.encode_struct(">L", val)

    def encode_uint64be(self, val):
        self.encode_struct(">Q", val)

    def encode_uint8le(self, val):
        self.encode_struct("<B", val)

    def encode_uint16le(self, val):
        self.encode_struct("<H", val)

    def encode_uint32le(self, val):
        self.encode_struct("<L", val)

    def encode_uint64le(self, val):
        self.encode_struct("<Q", val)

    def encode_int64le(self, val):
        self.encode_struct("<q", val)

    def encode_utf16le(self, val):
        self.encode_bytes(str(val).encode("utf-16le"))

    def trunc(self):
        self._expand_to(self.offset)
        del self.array[self.offset :]

    def _check_bounds(self, start, end):
        lower = self.bounds[0] if self.bounds[0] is not None else 0
        upper = self.bounds[1] if self.bounds[1] is not None else len(self.array)

        if start < lower:
            raise BufferOverrun(self, start, lower)
        if end > upper:
            raise BufferOverrun(self, end, upper)

    def decode_bytes(self, size):
        self._check_bounds(self.offset, self.offset + size)
        result = self.array[self.offset : self.offset + size]
        self.offset += size
        return result

    def decode_struct(self, fmt):
        size = struct.calcsize(fmt)
        self._check_bounds(self.offset, self.offset + size)
        result = struct.unpack_from(fmt, self.array, self.offset)
        self.offset += size
        return result

    def decode_uint8be(self):
        return self.decode_struct(">B")[0]

    def decode_uint16be(self):
        return self.decode_struct(">H")[0]

    def decode_uint32be(self):
        return self.decode_struct(">L")[0]

    def decode_uint64be(self):
        return self.decode_struct(">Q")[0]

    def decode_uint8le(self):
        return self.decode_struct("<B")[0]

    def decode_uint16le(self):
        return self.decode_struct("<H")[0]

    def decode_uint32le(self):
        return self.decode_struct("<L")[0]

    def decode_int32le(self):
        return self.decode_struct("<l")[0]

    def decode_uint64le(self):
        return self.decode_struct("<Q")[0]

    def decode_int64le(self):
        return self.decode_struct("<q")[0]

    def decode_utf16le(self, size):
        return self.decode_bytes(size).tobytes().decode("utf-16le")

    def align(self, base, val):
        assert self.array is base.array
        rem = (self.offset - base.offset) % val
        if rem != 0:
            self.offset += val - rem

    def seekto(self, o, lowerbound=None, upperbound=None):
        assert self.array is o.array
        if lowerbound is not None and o < lowerbound:
            raise BufferOverrun(self, o, lowerbound)
        if upperbound is not None and o > upperbound:
            raise BufferOverrun(self, o, upperbound)
        self.offset = o.offset

    def advanceto(self, o, bound=None):
        self.seekto(o, self, bound)

    def reverseto(self, o, bound=None):
        self.seekto(o, bound, self)

    @property
    def lowerbound(self):
        lower = self.bounds[0] if self.bounds[0] is not None else 0
        return Cursor(self.array, lower, self.bounds)

    @property
    def upperbound(self):
        upper = self.bounds[1] if self.bounds[1] is not None else len(self.array)
        return Cursor(self.array, upper, self.bounds)

    def bounded(self, lower, upper):
        # Allow cursors to be used as bounds (the preferred idiom)
        if isinstance(lower, Cursor):
            assert self.array is lower.array
            lower = lower.offset
        else:
            lower = cur.offset + lower
        if isinstance(upper, Cursor):
            assert self.array is upper.array
            upper = upper.offset
        else:
            upper = cur.offset + upper

        # Don't let new bounds escape current bounds
        self._check_bounds(lower, upper)

        return Cursor.Bounds(self, lower, upper)

    class Hole(object):
        def __init__(self, cur):
            self.cur = cur

        def __getattr__(self, attr):
            if hasattr(self.cur.__class__, attr):
                f = getattr(self.cur.__class__, attr)
                if callable(f):
                    copy = self.cur.copy()

                    def f2(*args, **kwargs):
                        offset = copy.offset
                        f(copy, *args, **kwargs)
                        copy.offset = offset

                    def f1(*args, **kwargs):
                        f(self.cur, *args, **kwargs)
                        return f2

                    return f1
                else:
                    raise AttributeError
            else:
                raise AttributeError

    class Bounds(object):
        def __init__(self, cur, lower, upper):
            self.cur = cur
            self.bounds = (lower, upper)

        def __enter__(self):
            self.oldbounds = self.cur.bounds
            self.cur.bounds = self.bounds
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.cur.bounds = self.oldbounds


class BadPacket(Exception):
    pass


class FrameMeta(type):
    def __new__(mcs, name, bases, dict):
        # Inherit _register from bases
        dict["_register"] = []
        for base in bases:
            if hasattr(base, "_register"):
                dict["_register"] += base._register

        # Inherit field_blacklist from bases
        if "field_blacklist" in dict:
            for base in bases:
                if hasattr(base, "field_blacklist"):
                    dict["field_blacklist"] += base.field_blacklist

        result = type.__new__(mcs, name, bases, dict)

        # Register class in appropriate tables
        for (table, keyattrs) in result._register:
            if all(hasattr(result, a) for a in keyattrs):
                key = [getattr(result, a) for a in keyattrs]
                if len(key) == 1:
                    key = key[0]
                else:
                    key = tuple(key)
                table[key] = result

        return result


class Frame(with_metaclass(FrameMeta)):
    field_blacklist = ["fields", "parent", "start", "end"]
    LOG_CHILDREN_COUNT = False  # Include len(children) in __repr__
    LOG_CHILDREN_EXPAND = False  # Include c._log_str for all children

    def __init__(self, parent, context=None):
        object.__setattr__(self, "fields", [])
        self.parent = parent
        self._context = context

    def __len__(self):
        return len(self.children)

    def __getitem__(self, key):
        return self.children[key]

    def __iter__(self):
        return self.children.__iter__()

    def __setattr__(self, name, value):
        if (
            not name.startswith("_")
            and name not in self.fields
            and name not in self.field_blacklist
        ):
            self.fields.append(name)
        object.__setattr__(self, name, value)

    def __str__(self):
        return self._str(1)

    @staticmethod
    def _value_str(value):
        if isinstance(value, array.array) and value.typecode == "B":
            return "0x" + "".join("%.2x" % b for b in value)
        else:
            return str(value)

    def _str(self, indent):
        res = self.__class__.__name__
        for field in self.fields:
            value = getattr(self, field)
            if value is not None:
                if isinstance(value, Frame):
                    valstr = value._str(indent + 1)
                else:
                    valstr = self._value_str(value)
                res += "\n" + "  " * indent + field + ": " + valstr
        for child in self.children:
            valstr = child._str(indent + 1)
            res += "\n" + "  " * indent + valstr
        return res

    def _log_str_expand_children(self):
        """
        return a list of _log_str output for all children
        """
        return [c._log_str() for c in self.children]

    def _log_str_count_children(self):
        """
        return a list containing a string count of children wrapped in
        parentheses
        """
        if self.children:
            return ["({})".format(len(self.children))]
        return []

    def _log_str_children(self):
        """
        return a list of string components summarizing the children
        """
        components = []
        if self.LOG_CHILDREN_COUNT:
            components.extend(self._log_str_count_children())
        if self.LOG_CHILDREN_EXPAND:
            components.extend(self._log_str_expand_children())
        return components

    def _log_str(self):
        """
        Short description used for logging. Should provide basic context and be
        under 100 characters
        """
        components = [type(self).__name__]
        components.extend(self._log_str_children())
        return " ".join(components)

    def _encode_pre(self, cur):
        self.start = cur.copy()

    def _encode_post(self, cur):
        self.end = cur.copy()

    def _decode_pre(self, cur):
        self.start = cur.copy()

    def _decode_post(self, cur):
        self.end = cur.copy()

    @property
    def context(self):
        if self._context is not None:
            return self._context
        elif self.parent is not None:
            return self.parent.context
        else:
            return None

    @property
    def children(self):
        return self._children() if hasattr(self, "_children") else []

    def encode(self, cur):
        self._encode_pre(cur)
        self._encode(cur)
        self._encode_post(cur)

    def decode(self, cur):
        self._decode_pre(cur)
        self._decode(cur)
        self._decode_post(cur)

    def serialize(self):
        self.buf = array.array("B")
        cursor = Cursor(self.buf, 0)
        self.encode(cursor)
        return self.buf

    def parse(self, arr):
        cursor = Cursor(arr, 0)
        self.decode(cursor)
        self.buf = arr

    def next_sibling(self):
        children = self.parent.children
        index = children.index(self) + 1
        return children[index] if index < len(children) else None

    def prev_sibling(self):
        children = self.parent.children
        index = children.index(self) - 1
        return children[index] if index >= 0 else None

    def is_last_child(self):
        children = self.parent.children
        return children.index(self) == len(children) - 1


class Register(object):
    def __init__(self, table, *keyattrs):
        self.table = table
        self.keyattrs = keyattrs

    def __call__(self, cls):
        assert issubclass(cls, Frame)
        cls._register.append((self.table, self.keyattrs))
        return cls


class EnumMeta(type):
    def __new__(mcs, cname, bases, idict):
        nametoval = {}
        valtoname = {}
        misc = {}

        for (name, val) in idict.items():
            if name[0].isupper():
                nametoval[name] = val
                valtoname[val] = name
            else:
                misc[name] = val

        cls = type.__new__(mcs, cname, bases, misc)
        cls._nametoval = nametoval
        cls._valtoname = valtoname

        return cls

    def __getattribute__(cls, name):
        nametoval = type.__getattribute__(cls, "_nametoval")
        if name in nametoval:
            return cls(nametoval[name])
        else:
            return type.__getattribute__(cls, name)


class Enum(with_metaclass(EnumMeta, int)):
    """
    Enumeration abstract base

    An Enum subclasses long in order to ensure that instances
    are a member of a well-defined enumeration of values,
    provide introspection into the allowed values and their names,
    and provide symbolic string forms of values.

    You should generally subclass one of L{ValueEnum} or L{FlagEnum}.
    """

    @classmethod
    def items(cls):
        """
        Returns a list of (name,value) pairs for allowed enumeration values.
        """
        return iter(cls._nametoval.items())

    @classmethod
    def names(cls):
        """
        Returns a list of names of allowed enumeration values.
        """
        return list(cls._nametoval.keys())

    @classmethod
    def values(cls):
        """
        Returns a list of allowed enumeration values.
        """
        return list(cls._nametoval.values())

    @classmethod
    def import_items(cls, dictionary):
        """
        Import enumeration values into dictionary

        This method is intended to allow importing enumeration
        values from an L{Enum} subclass into the root of a module,
        and should be invoked as::

            SomeEnumClass.import_items(globals())
        """
        dictionary.update((name, cls(value)) for (name, value) in cls.items())

    @classmethod
    def validate(cls, value):
        """
        Validate value as valid for enumeration.

        This must be implemented in subclasses of L{Enum}
        (but not L{ValueEnum} or L{FlagEnum}, which provide it).
        It should raise a ValueError on failure.
        """
        raise NotImplementedError()

    def __new__(cls, value=0):
        """
        Constructor.

        Creates a new Enum instance from an ordinary number,
        validating that is is valid for the particular
        enumeration.
        """
        cls.validate(value)
        return super(Enum, cls).__new__(cls, value)

    def __repr__(self):
        # Just return string form
        return str(self)


class ValueEnum(Enum):
    """
    Value Enumeration

    Subclass this class to define enumerations of values.
    For example::

        class SomeEnumClass(Enum):
            FOO = 0
            BAR = 1
            BAZ = 2

    Accessing SomeEnumClass.FOO will actually return a SomeEnumClass instance.
    Instances will return their symbolic names when str() is used.
    """

    permissive = False

    @classmethod
    def validate(cls, value):
        if not cls.permissive and value not in cls._valtoname:
            raise ValueError("Invalid %s: %x" % (cls.__name__, value))

    def __str__(self):
        if self in self.__class__._valtoname:
            return self.__class__._valtoname[self]
        else:
            return hex(self)


class FlagEnum(Enum):
    """
    Flag Enumeration

    Subclass this class to define enumerations of flags.
    For example::

        class SomeFlagEnumClass(Enum):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4

    Accessing SomeFlagEnumClass.FOO will actually return a
    SomeFlagEnumClass instance.  Instances may be bitwise-ored
    together.  Instances will return the symbolic names of all
    set flags joined by ' | ' when str() is used.
    """

    @classmethod
    def validate(cls, value):
        remaining = value
        for flag in cls.values():
            if flag & remaining == flag:
                remaining &= ~flag

        if remaining != 0:
            raise ValueError(
                "Invalid %s: 0x%x (remainder 0x%x)" % (cls.__name__, value, remaining)
            )

    def __str__(self):
        names = [
            name
            for (name, flag) in self.items()
            if (flag != 0 and flag & self == flag) or (self == 0 and flag == 0)
        ]

        return " | ".join(names) if len(names) else "0"

    def __or__(self, o):
        return self.__class__(super(FlagEnum, self).__or__(o))

    def __and__(self, o):
        return self.__class__(super(FlagEnum, self).__and__(o))


class Let(object):
    """
    A Let allows for temporarily storing passed arguments in the _settings
    member of a target object for the duration of the contextmanager's scope

    Implementation on a factory class

    class MyThingFactory(object):
        def __init__(self):
            self._settings = {}
        def generate_thing(self):
            # do something here
            new_obj = Thing()
            for k,v in self._settings.iteritems():
                setattr(new_obj, k, v)
            return new_obj
        def let(self, **kwds):
            return Let(self, kwds)

    Calling code that wants to temporarily customize the Thing objects that are
    returned by the factory:

    fac = MyThingFactory()
    with fac.let(this="that", foo="bar"):
        a_thing = fac.generate_thing()
        self.assertEqual(a_thing.this, "that")
    """

    def __init__(self, target, settings_dict):
        self.target = target
        self.settings_dict = settings_dict
        if not hasattr(target, "_settings"):
            target._settings = {}

    def __enter__(self):
        self.backup = dict(self.target._settings)
        self.target._settings.update(self.settings_dict)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.target._settings = self.backup
