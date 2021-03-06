import abc
import collections
import maps.utils as utils
from maps.fixedkeymap import FixedKeyMap

class NamedFixedKeyMapMeta(abc.ABCMeta):
    '''Returns a new :class:`maps.FixedKeyMap` subclass named ``typename``. The new
    subclass is used to create :py:class:`dict`-like objects that have fields
    accessible by attribute lookup as well as being indexable by name and iterable.
    Instances of the subclass also have a helpful docstring (with typename and
    field_names) and a helpful __repr__() method which lists the mapping contents
    in a name=value format.

    ``field_names`` can be a sequence of strings such as ``['x', 'y']``.

    Any valid Python identifier may be used for a fieldname except for names
    starting with an underscore. Valid identifiers consist of letters, digits,
    and underscores but do not start with a digit or underscore and cannot be a
    keyword such as class, for, return, global, pass, or raise.

    This metaclass injects 3 methods into the subclass:
    ``__getattr__``, ``__setattr__``, and ``__repr__``.

    1. ``__getattr__`` attempts to retrieve attributes from an instance's
    underlying ``_data`` dictionary, raising :py:exc:`AttributeError`
    if the attribute is not found.

    2. ``__setattr__`` attempts to set the value for the specified attribute, but
    raises :py:exc:`TypeError` if the attribute is not part of the
    fixed key set. If the attribute name has a leading underscore, these checks
    are skipped and the value is set normally.

    3. ``__repr__`` simply replaces ``FixedKeyMap`` with the name of the instantiated
    class.

    :func:`maps.namedfixedkey` provides a convenient alias for calling this metaclass.

    :param str typename: Name for the new class
    :param iterable fields: Names for the fields of the new class
    :raises ValueError: if the type name or field names provided are not properly formatted
    :return: Newly created subclass of :class:`maps.FixedKeyMap`
    '''

    @staticmethod
    def _getattr(self, name):
        '''Retrieves attribute by name.

        :param str name: Name of the desired attribute
        :raises AttributeError: if an attribute with the specified name cannot be found
        :return: Desired attribute
        '''
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                "'{}' object has no attribute {!r}".format(type(self).__name__, name))

    @staticmethod
    def _setattr(self, name, value):
        '''Sets the value for the specified attribute if the attribute name is
        part of the fixed key set.

        :raises TypeError: if the attribute name is not part of the fixed key set
        '''
        if name.startswith('_'):
            super(type(self), self).__setattr__(name, value)
        elif name in self._data:
            self._data[name] = value
        else:
            raise TypeError(
                "'{}' object does not support new attribute assignment".format(type(self).__name__))

    @staticmethod
    def _repr(self): # pragma: no cover
        kwargs = ', '.join('{}={!r}'.format(key, value) for key, value in self.items())
        return '{}({})'.format(type(self).__name__, kwargs)

    def __new__(cls, typename, fields=[]):
        fields = tuple(fields)
        # validate names
        for name in (typename,) + fields:
            utils._validate_name(name)
        utils._validate_fields(fields)

        cls._fields = fields

        docstring = '''{typename}: A key-value mapping with a fixed set of keys
        whose items are accessible via bracket-notation (i.e. ``__getitem__``
        and ``__setitem__``). Though the set of keys is immutable, the
        corresponding values can be edited. Has fields ({fields})

        :param args: Position arguments in the same form as the :py:class:`dict` constructor.
        :param kwargs: Keyword arguments in the same form as the :py:class:`dict` constructor.
        '''.format(typename=typename, fields=cls._fields)

        methods = {
            '__doc__': docstring,
            '__getattr__': NamedFixedKeyMapMeta._getattr,
            '__repr__': NamedFixedKeyMapMeta._repr,
            '__setattr__': NamedFixedKeyMapMeta._setattr}

        # handle custom __init__
        template = '\n'.join([
            'def __init__(self, {args}):',
            '    super(type(self), self).__init__()',
            '    self._data = collections.OrderedDict({kwargs})'])
        args = ', '.join(fields)
        kwargs = ', '.join(['{0}={0}'.format(i) for i in fields])
        namespace = {'collections': collections}
        exec(template.format(args=args, kwargs=kwargs), namespace)
        methods['__init__'] = namespace['__init__']

        return type.__new__(cls, typename, (FixedKeyMap,), methods)

    def __init__(cls, typename, fields=[]):
        super(type(cls), cls).__init__(cls)
