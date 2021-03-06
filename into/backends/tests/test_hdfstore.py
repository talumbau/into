
from into.backends.hdfstore import discover
from contextlib import contextmanager
from into.utils import tmpfile
from into.chunks import chunks
from into import into, append, convert, resource, discover
import datashape
import pandas as pd
from datetime import datetime
import numpy as np
import os

df = pd.DataFrame([['a', 1, 10., datetime(2000, 1, 1)],
                   ['ab', 2, 20., datetime(2000, 2, 2)],
                   ['abc', 3, 30., datetime(2000, 3, 3)],
                   ['abcd', 4, 40., datetime(2000, 4, 4)]],
                   columns=['name', 'a', 'b', 'time'])


@contextmanager
def file(df):
    with tmpfile('.hdf5') as fn:
        f = pd.HDFStore(fn)
        f.put('/data', df, format='table', append=True)

        try:
            yield fn, f, f.get_storer('/data')
        finally:
            f.close()


def test_discover():
    with file(df) as (fn, f, dset):
        assert str(discover(dset)) == str(discover(df))
        assert str(discover(f)) == str(discover({'data': df}))


def test_discover():
    with tmpfile('hdf5') as fn:
        df.to_hdf(fn, '/a/b/data')
        df.to_hdf(fn, '/a/b/data2')
        df.to_hdf(fn, '/a/data')

        hdf = pd.HDFStore(fn)

        assert discover(hdf) == discover({'a': {'b': {'data': df, 'data2': df},
                                                'data': df}})


def eq(a, b):
    if isinstance(a, pd.DataFrame):
        a = into(np.ndarray, a)
    if isinstance(b, pd.DataFrame):
        b = into(np.ndarray, b)
    c = a == b
    if isinstance(c, np.ndarray):
        c = c.all()
    return c


def test_chunks():
    with file(df) as (fn, f, dset):
        c = convert(chunks(pd.DataFrame), dset)
        assert eq(convert(np.ndarray, c), df)


def test_resource_no_info():
    with tmpfile('.hdf5') as fn:
        assert isinstance(resource('hdfstore://' + fn), pd.HDFStore)


def test_resource_of_dataset():
    with tmpfile('.hdf5') as fn:
        ds = datashape.dshape('{x: int32, y: 3 * int32}')
        r = resource('hdfstore://'+fn+'::/x', dshape=ds)
        assert r


def test_append():
    with file(df) as (fn, f, dset):
        append(dset, df)
        append(dset, df)
        assert discover(dset).shape == (len(df) * 3,)


def test_into_resource():
    with tmpfile('.hdf5') as fn:
        d = into('hdfstore://' + fn + '::/x', df)
        assert discover(d) == discover(df)
        assert eq(into(pd.DataFrame, d), df)


def test_convert_pandas():
    with file(df) as (fn, f, dset):
        assert eq(convert(pd.DataFrame, dset), df)


def test_convert_chunks():
    with file(df) as (fn, f, dset):
        c = convert(chunks(pd.DataFrame), dset, chunksize=len(df) / 2)
        assert len(list(c)) == 2
        assert eq(convert(pd.DataFrame, c), df)


def test_append_chunks():
    with file(df) as (fn, f, dset):
        append(dset, chunks(pd.DataFrame)([df, df]))

        assert discover(dset).shape[0] == len(df) * 3


def test_append_other():
    with tmpfile('.hdf5') as fn:
        x = into(np.ndarray, df)
        dset = into('hdfstore://'+fn+'::/data', x)
        assert discover(dset) == discover(x)


def test_fixed_shape():
    with tmpfile('.hdf5') as fn:
        df.to_hdf(fn, 'foo')
        r = resource('hdfstore://'+fn+'::/foo')
        assert isinstance(r.shape, list)
        assert discover(r).shape == (len(df),)


def test_fixed_convert():
    with tmpfile('.hdf5') as fn:
        df.to_hdf(fn, 'foo')
        r = resource('hdfstore://'+fn+'::/foo')
        assert eq(convert(pd.DataFrame, r), df)
