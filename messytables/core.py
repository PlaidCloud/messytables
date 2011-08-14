from itertools import izip_longest

from messytables.util import skip_n
from messytables.ordereddict import OrderedDict

class Cell(object):
    """ A cell is the basic value type. It always has a ``value`` (that
    may be ``None`` and may optionally also have a type and column name
    associated with it. """

    def __init__(self, value, column=None, type=None):
        if type is None:
            from messytables.types import StringType
            type = StringType()
        self.value = value
        self.column = column
        self.column_autogenerated = False
        self.type = type

    def __repr__(self):
        if self.column is not None:
            return "<Cell(%s=%s:%s>" % (self.column, 
                    self.type, self.value)
        return "<Cell(%r:%s>" % (self.type, self.value)

    @property
    def empty(self):
        """ Stringify the value and check that it has a length. """
        if self.value is None:
            return True
        value = self.value
        if not isinstance(value, basestring):
            value = unicode(value)
        if len(value.strip()):
            return False
        return True


class TableSet(object):
    """ A table set is used for data formats in which multiple tabular
    objects are bundeled. This might include relational databases and 
    workbooks used in spreadsheet software (Excel, LibreOffice). """

    @classmethod
    def from_fileobj(cls, fileobj):
        """ The primary way to instantiate is through a file object 
        pointer. This means you can stream a table set directly off 
        a web site or some similar source. """
        pass

    @property
    def tables(self):
        """ Return a listing of tables in the ``TableSet``. Each table
        has a name. """
        pass


class RowSet(object):
    typed = False
    
    _column_types = None
    column_headers = None
    row_offset = None

    def set_column_types(self, types):
        self.typed = True
        self._column_types = types

    def get_column_types(self):
        return self._column_types

    column_types = property(get_column_types, set_column_types)

    def apply_types(self, row):
        """ Apply the column types set on the instance to the
        current row, attempting to cast each cell to the specified
        type. """
        if self.column_types is None:
            return row
        for cell, type in izip_longest(row, self.column_types):
            try:
                cell.value = type.cast(cell.value)
                cell.type = type
            except:
                pass
        return row

    def apply_headers(self, row):
        """ Add column names to the cells in a row_set. If no 
        header is defined, use an autogenerated name. """
        _row = []
        pairs = izip_longest(row, self.column_headers)
        for i, (cell, header) in enumerate(pairs):
            if cell is None:
                cell = Cell(None)
            cell.column = header
            if cell.column is None or not len(cell.column):
                cell.column = "column_%d" % i
                cell.column_autogenerated = True
            _row.append(cell)
        return _row

    def __iter__(self):
        """ Apply several filters to the row data. """
        rows = self.raw()
        if self.row_offset is not None:
            rows = skip_n(rows, self.row_offset)
        for row in rows:
            if self.column_types is not None:
                row = self.apply_types(row)
            if self.column_headers is not None:
                row = self.apply_headers(row)
            yield row

    def dicts(self):
        if not self.column_headers:
            raise TypeError("No column headers are defined!")
        for row in self:
            yield OrderedDict([(c.column, c.value) for c in row])

    def __repr__(self):
        return "RowSet(%s)" % self.name

