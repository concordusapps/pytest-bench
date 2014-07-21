# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

from functools import wraps
from timeit import default_timer as timer
import gc
import inspect
import math
import os

from termcolor import colored
import colorama
import pytest
import six

from .terminal import get_terminal_size


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--bench', action='store_true',
                    help="Perform benchmarks on marked test cases.")
    group.addoption('--bench-only', action='store_true',
                    help="Perform benchmarks on marked test cases.")
    group.addoption("--bench-disable-gc", action="store_true",
                    default=False,
                    help="Disable GC during benchmarks.")


def pytest_configure(config):
    if config.option.bench:
        config.pluginmanager.register(BenchmarkController(config), '_bench')


class Benchmark(object):

    def __init__(self, item, times):
        #! The collected item from pytest.
        self.item = item

        #! The number of elapsed seconds for each iteration.
        self._times = times

    @property
    def name(self):
        obj = []
        if self.item.cls:
            obj.append(self.item.cls.__name__)

        obj.append(self.item.name)
        return '.'.join(obj)

    @property
    def filename(self):
        return os.path.relpath(self.item.module.__file__)

    @property
    def elapsed(self):
        if self._times:
            return sum(self._times)

    @property
    def min(self):
        if self._times:
            return min(self._times)

    @property
    def max(self):
        if self._times:
            return max(self._times)

    @property
    def mean(self):
        if self._times:
            return sum(self._times) / len(self._times)

    @property
    def median(self):
        if self._times:
            return sorted(self._times)[len(self._times) // 2]

    @property
    def var(self):
        # About math read this: http://legacy.python.org/dev/peps/pep-0450/
        if self._times:
            n = len(self._times)
            ss = sum(x ** 2 for x in self._times) - (sum(self._times) ** 2) / n
            return ss / (n - 1)

    @property
    def stddev(self):
        if self._times:
            return math.sqrt(self.var)


class BenchmarkController(object):

    def __init__(self, config):
        self.config = config
        self._benchmarks = []
        self._item_function = None

    def pytest_runtest_setup(self, item):

        # Check to see if we need to benchmark any invocations.
        bench = item.keywords.get('bench')

        if bench is None:
            # Nope; nothing to see here.

            # Check to see if we can skip this test (requested to /only/ run
            # benchmarks).
            if self.config.option.bench_only:
                raise pytest.skip('no associated benchmark')

            # Just continue to the test.
            return

        # Get the first argument to indicate what method to benchmark.
        expression = bench.args[0]
        iterations = bench.kwargs.get('iterations', 100)

        # Create a wrapper for the test case that applies the benchmark.
        item_function = self._item_function = item.function
        item_function_globals = six.get_function_globals(item_function)
        item_function_argspec = inspect.getargspec(item.function)

        @wraps(item.function)
        def item_function_wrapper(*args, **kwargs):
            # Extract the function from the expression.
            locals_, globals_ = locals(), item_function_globals
            locals_.update(dict(zip(item_function_argspec.args, args)))
            locals_.update(kwargs)
            six.exec_('_function = %s' % expression, globals_, locals_)
            _function = locals_['_function']

            # Initialize benchmark process.
            props = {'times': list()}

            # Create a wrapper for the method to benchmark.
            @wraps(_function)
            def benchmark(*args, **kwargs):
                # nonlocal elapsed, real_iterations
                if self.config.option.bench_disable_gc:
                    gc.collect()
                    gc.disable()
                start = timer()
                result = _function(*args, **kwargs)
                finish = timer()
                if self.config.option.bench_disable_gc:
                    gc.enable()
                props['times'].append(finish - start)
                return result

            # Replace the function with the wrapped function.
            locals_['benchmark'] = benchmark
            six.exec_('%s = benchmark' % expression, globals_, locals_)

            # Attempt to replace it in global scope as well.
            globals_.update(locals_)

            # Get the (unbound) function.
            try:
                locals_['function'] = six.get_method_function(item_function)

            except AttributeError:
                locals_['function'] = item_function

            # Iterate the set number of iterations.
            item.teardown()
            for _ in range(iterations):
                item.setup()
                locals_['args'] = args
                locals_['kwargs'] = kwargs
                six.exec_('function(*args, **kwargs)', globals_, locals_)
                item.teardown()

            # Restore the benchmarked function.
            six.exec_('%s = _function' % expression, globals_, locals_)

            # Construct a Benchmark instance to store the result.
            self._benchmarks.append(Benchmark(item, **props))

        if item.cls is not None:
            setattr(item.cls, item.function.__name__, item_function_wrapper)

        else:
            item.obj = item_function_wrapper

    def pytest_runtest_teardown(self, item):

        # Check to see if we need to handle a benchmark.
        bench = item.keywords.get('bench')
        if bench is None:
            # Nope; nothing to see here.
            return

        if self._item_function is not None:
            # Restore the original item function if we need to.
            if item.cls is not None:
                setattr(item.cls, item.function.__name__,
                        self._item_function)

    def pytest_terminal_summary(self, terminalreporter):
        tr = terminalreporter

        # Ensure terminal output is colored.
        colorama.init()

        # Calculate terminal width and size columns appropriately.
        columns, lines = get_terminal_size()
        time_header_widths = [15, 15, 15, 11]
        name_header_len = columns - sum(time_header_widths)

        # Write session header.
        tr.write_sep('-', 'benchmark summary')
        tr.write_line('collected %s items' % len(self._benchmarks))
        tr.write('\n')

        # Format and write table header.
        header = ('{:<%d}{:>%d}{:>%d}{:>%d}{:>%d}' % tuple([name_header_len] + time_header_widths)). \
            format('Benchmark (time in us)', 'Min', 'Mean', 'Median', 'Stddev')

        tr.write_line('-' * columns)
        tr.write_line(header)
        tr.write_line('-' * columns)

        # Iterate through collected benchmarks.
        for benchmark in list(self._benchmarks):
            # Get and truncate the name.
            name, filename = benchmark.name, benchmark.filename
            allowed_name_len = name_header_len - len(filename) - 4
            name = name[:allowed_name_len] + (name[allowed_name_len:] and '..')

            # Write out the name.
            tr.write(colored(filename + ': ', 'white', attrs=['dark']))
            tr.write(('{:<%d}' % (allowed_name_len + 2)).format(name))

            # Perform the benchmark.
            for tm, width in zip([benchmark.min, benchmark.mean, benchmark.median, benchmark.stddev],
                                 time_header_widths):

                if tm is None:
                    # Write dashes.
                    tr.write(colored(
                        ('{:>%d}' % width).format('----'), 'white', attrs=['dark']))

                else:
                    # Convert to microseconds.
                    tm *= 10 ** 6

                    # Write out the tm.
                    tr.write(colored(
                        ('{:>%d,.2f}' % width).format(tm), 'white', attrs=['bold']))

            tr.write('\n')
