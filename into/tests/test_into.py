from into.into import into
from into.utils import tmpfile, filetext

def test_into_convert():
    assert into(list, (1, 2, 3)) == [1, 2, 3]


def test_into_append():
    L = []
    result = into(L, (1, 2, 3))
    assert result == [1, 2, 3]
    assert result is L


def test_into_curry():
    assert callable(into(list))
    data = (1, 2, 3)
    assert into(list)(data) == into(list, data)


def test_into_double_string():
    from into.backends.csv import CSV
    with filetext('alice,1\nbob,2', extension='.csv') as source:
        assert into(list, source) == [('alice', 1), ('bob', 2)]

        with tmpfile('.csv') as target:
            csv = into(target, source)
            assert isinstance(csv, CSV)
            with open(target) as f:
                assert 'alice' in f.read()
