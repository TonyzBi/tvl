Building extensions:

```bash
rm -rf build && python setup.py build_ext --inplace && pytest -s
```

## TODO

* Some of the stuff in the TvlnvFrameReader constructor should probably be moved to
  a global init function of some variety
