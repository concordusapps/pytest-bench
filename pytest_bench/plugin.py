# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division
import os
from timeit import timeit
from functools import wraps


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--bench', action='store_true',
                    help="Perform benchmarks on marked test cases.")


def pytest_configure(config):
    if config.option.bench:
        config.pluginmanager.register(BenchmarkController(config), '_bench')


class Benchmark(object):

    def __init__(self, item, iterations, function, *args, **kwargs):
        #! The collected item from pytest.
        self.item = item

        #! The number of iterations to run.
        self.iterations = iterations

        #! The function and its arguments.
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @property
    def name(self):
        return '{}::{}::{}'.format(
            os.path.relpath(self.item.module.__file__),
            self.item.cls.__name__,
            self.item.function.__name__)

    def run(self):
        args = self.args
        kwargs = self.kwargs
        function = self.function
        n = timeit(lambda: function(*args, **kwargs), number=self.iterations)
        return n / self.iterations



class BenchmarkController(object):

    def __init__(self, config):
        self.config = config
        self._benchmarks = []

    def pytest_runtest_setup(self, item):
        # Check to see if we need to benchmark any invocations.
        bench = item.keywords.get('bench')
        if bench is None:
            # Nope; nothing to see here.
            return

        # Get the first argument to indicate what method to benchmark.
        name = bench.args[0].split('.')
        iterations = bench.kwargs.get('iterations', 100)

        # Resolve the function name.
        container = item.module
        for segment in name[:-1]:
            container = getattr(container, segment, None)
            if container is None:
                # Mark was invalid; bail.
                return

        # Save the original method.
        self._function = function = getattr(container, name[-1])

        # Create a wrapper method that will store the method.
        @wraps(function)
        def benchmark(*args, **kwargs):
            # Save the invocation of the function to benchmark on teardown.
            self._benchmarks.append(Benchmark(
                item, iterations, function, *args, **kwargs))

            # Run the function initally and save the invocation.
            return function(*args, **kwargs)

        # Replace the function with the benchmark wrapper.
        setattr(container, name[-1], benchmark)

    def pytest_runtest_teardown(self, item):
        # Check to see if we need to benchmark any invocations.
        bench = item.keywords.get('bench')
        if bench is None:
            # Nope; nothing to see here.
            return

        # Get the first argument to indicate what method to benchmark.
        name = bench.args[0].split('.')

        # Resolve the function name.
        container = item.module
        for segment in name[:-1]:
            container = getattr(container, segment, None)
            if container is None:
                # Mark was invalid; bail.
                return

        # Restore the original method.
        setattr(container, name[-1], self._function)

    def pytest_terminal_summary(self, terminalreporter):
        tr = terminalreporter
        tr.write_sep('-', 'benchmark session starts')
        tr.write_line('collected %s items' % len(self._benchmarks))
        tr.write('\n')

        # Format and write out the header.
        header = '{:<100}{:>15}'.format('Benchmark', 'Time (s)')
        tr.write_line('-' * 115)
        tr.write_line(header)
        tr.write_line('-' * 115)

        # Iterate through collected benchmarks.
        for benchmark in list(self._benchmarks):
            # Get and truncate the name.
            name = benchmark.name
            name = name[:92] + (name[92:] and '..')

            # Write out the name.
            tr.write('{:<100}'.format(name))

            # Perform the benchmark.
            elapsed = benchmark.run()

            # Write out the elapsed.
            tr.write_line('{:>15.8f}'.format(elapsed))
