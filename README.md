# pytest-bench
[![PyPi Version](https://pypip.in/v/pytest-bench/badge.png)](https://pypi.python.org/pypi/pytest-bench)
![PyPi Downloads](https://pypip.in/d/pytest-bench/badge.png)
> Benchmark utility that plugs into pytest.

## Installation

1. **pytest-bench** can be installed using `pip` or `easy_install`.

   ```sh
   pip install pytest-bench
   ```

## Usage

```python
from pytest import mark
import operator

@mark.bench('operator.eq')
def test_eq():
    assert operator.eq(1, 1)
```

Now when `py.test --bench` is run it will benchmark the execution of the `operator.eq` method.

## License

Unless otherwise noted, all files contained within this project are liensed under the MIT opensource license. See the included file LICENSE or visit [opensource.org][] for more information.

[opensource.org]: http://opensource.org/licenses/MIT
