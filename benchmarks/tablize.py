# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- reST tables writer tool
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   MIT License
# :Copyright: © 2017, 2018 Lele Gaifax
#

# Assume we did::
#
#  pytest --benchmark-json=comparison.json --compare-other-engines benchmarks/
#
# Read back that JSON outcome and produce three reST tables summarizing the
# comparison.
#

from collections import defaultdict, namedtuple
import sys

import rapidjson


Benchmark = namedtuple('Benchmark', 'group, name, contender')


class Comparison:
    COMPARE_FIELD = 'min'  # one of min, max, mean, median...

    def __init__(self, contenders, benchmarks):
        self.contenders = contenders
        self.timings = {}
        self.load_data(benchmarks)

    def load_data(self, benchmarks):
        for bm in benchmarks:
            group = bm['group']
            desc = bm['name'].split('[', 1)[1][:-1]
            contender, name = desc.split('-')
            if contender in self.contenders:
                bmark = Benchmark(group, name, contender)
                self.timings[bmark] = bm['stats'][self.COMPARE_FIELD]

    def normalize_and_summarize(self, group):
        table = defaultdict(dict)
        for bmark, timing in self.timings.items():
            if bmark.group == group:
                table[bmark.name][bmark.contender] = timing

        normalized = {}
        sums = defaultdict(float)
        by = self.contenders[0]
        for name, values in table.items():
            for c in self.contenders:
                sums[c] += values[c]
            normalized[name] = [values[c] / values[by] for c in self.contenders]

        normalized_sum = [sums[c] / sums[by] for c in self.contenders]

        return normalized, normalized_sum

    def tabulate(self, group, headers):
        normalized, sum = self.normalize_and_summarize(group)

        nc = len(self.contenders)
        widths = [max((len(n)+4 for n in normalized))] + \
                 [max((len(h) for h in headers))] * nc

        cells = ['-' * (width+2) for width in widths]
        seprow = '+' + '+'.join(cells) + '+'

        cells = ['=' * (width+2) for width in widths]
        headseprow = '+' + '+'.join(cells) + '+'

        cells = [' {:^%d} ' % width for width in widths]
        rowfmt = '|' + '|'.join(cells) + '|'

        print(seprow)
        print(rowfmt.format(*([group] + [headers[i]
                                         for i, c in enumerate(self.contenders)])))
        print(headseprow)

        def printrow(name, row):
            best = min(row)
            fvalues = [('**%.2f**' if v==best else '%.2f') % v for v in row]
            print(rowfmt.format(*([name] + fvalues)))
            print(seprow)

        for n in sorted(normalized):
            printrow(n, normalized[n])

        printrow('overall', sum)


def dumps_and_loads(benchmarks):
    contenders = ('rapidjson_f',
                  'rapidjson_c',
                  'rapidjson_nn_f',
                  'rapidjson_nn_c',
                  'ujson',
                  'simplejson',
                  'stdlib json',
                  'yajl')
    s_headers = (r'``dumps()``\ [1]_',
                 r'``Encoder()``\ [2]_',
                 r'``dumps(n)``\ [3]_',
                 r'``Encoder(n)``\ [4]_',
                 r'ujson\ [5]_',
                 r'simplejson\ [6]_',
                 r'stdlib\ [7]_',
                 r'yajl\ [8]_')
    d_headers = (r'``loads()``\ [9]_',
                 r'``Decoder()``\ [10]_',
                 r'``loads(n)``\ [11]_',
                 r'``Decoder(n)``\ [12]_',
                 r'ujson',
                 r'simplejson',
                 r'stdlib',
                 r'yajl')

    assert len(contenders) == len(s_headers) == len(d_headers)

    footnotes = [
        '.. [1] ``rapidjson.dumps()``',
        '.. [2] ``rapidjson.Encoder()``',
        '.. [3] ``rapidjson.dumps(number_mode=NM_NATIVE)``',
        '.. [4] ``rapidjson.Encoder(number_mode=NM_NATIVE)``',
        '.. [5] `ujson 1.35 <https://pypi.python.org/pypi/ujson/1.35>`__',
        '.. [6] `simplejson 3.13.2 <https://pypi.python.org/pypi/simplejson/3.13.2>`__',
        '.. [7] Python %d.%d.%d standard library ``json``' % sys.version_info[:3],
        '.. [8] `yajl 0.3.5 <https://pypi.python.org/pypi/yajl/0.3.5>`__',
        '.. [9] ``rapidjson.loads()``',
        '.. [10] ``rapidjson.Decoder()``',
        '.. [11] ``rapidjson.loads(number_mode=NM_NATIVE)``',
        '.. [12] ``rapidjson.Decoder(number_mode=NM_NATIVE)``']

    comparison = Comparison(contenders, benchmarks)
    comparison.tabulate('serialize', s_headers)
    print()
    comparison.tabulate('deserialize', d_headers)
    return footnotes


def ascii_vs_utf8(benchmarks):
    engines = (('rapidjson', 'rj'),
               ('ujson', 'uj'),
               ('simplejson', 'sj'),
               ('stdlib json', 'json'))
    contenders = ['%s %s' % (e[0], k) for e in engines for k in ('ascii', 'utf8')]
    i = 12
    s_headers = []
    footnotes = []
    for e in engines:
        i += 1
        s_headers.append(r'``%s ascii``\ [%d]_' % (e[1], i))
        footnotes.append('.. [%d] ``%s.dumps(ensure_ascii=True)``' % (i, e[0]))
        i += 1
        s_headers.append(r'``%s utf8``\ [%d]_' % (e[1], i))
        footnotes.append('.. [%d] ``%s.dumps(ensure_ascii=False)``' % (i, e[0]))

    comparison = Comparison(contenders, benchmarks)
    comparison.tabulate('serialize', s_headers)
    return footnotes


def main():
    import sys

    if len(sys.argv) > 1:
        fname = sys.argv[1]
    else:
        fname = 'comparison.json'

    with open(fname) as f:
        benchmarks = rapidjson.loads(f.read())['benchmarks']

    footnotes = []

    footnotes.extend(dumps_and_loads(benchmarks))
    print()
    footnotes.extend(ascii_vs_utf8(benchmarks))

    print()
    for fn in footnotes:
        print(fn)


if __name__ == '__main__':
    main()
