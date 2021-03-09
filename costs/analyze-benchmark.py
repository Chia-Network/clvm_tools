import glob
from numpy import linalg
from numpy import array
from numpy import inner
import os

def to_float_list(l):
    ret = []
    for s in l:
        ret.append(float(s))
    return ret

def linear_regression_no_outliers(ops, runtime):
    num_points = len(ops)

    # we want to remove the 5% worst points
    for counter in range(num_points // 20):
        m, c = linalg.lstsq(ops, runtime)[0]
        # find the point farthest from the line defined by x*m+c
        # and remove it
        worst = -1
        dist = 0
        for i in range(len(ops)):
            f = ops[i][0] * m + c
            d = abs(f - runtime[i])
            if d > dist:
                worst = i
                dist = d

        if worst >= 0:
            del ops[worst]
            del runtime[worst]

    # now, run the regression analysis on the cleaned-up points
    return linalg.lstsq(ops, runtime)[0]

for directory in glob.glob('test-programs/*'):
    gnuplot_filename = os.path.join(directory, 'render-trends.gnuplot')
    gnuplot = open(gnuplot_filename, 'w+')

    gnuplot.write('''set output "%s/timing-trends.png"
set term png size 1400,900 small
set termoption enhanced
set ylabel "run-time (s)"
set xlabel "number of ops"
set xrange [0:3000]
set yrange [0:0.02]
set datafile separator ","
plot ''' % directory)

    print('microseconds per operation')
    color = 0
    for fn in glob.glob('test-programs/%s/results-*.csv' % os.path.split(directory)[1]):
        r = open(fn, 'r')

        ops = []
        runtime = []

        for l in r:
            if l.startswith('#'): continue
            l = l.split(',')
            runtime.append(float(l[3]))
            ops.append([float(l[4]), 1.])

        m, c = linear_regression_no_outliers(ops, runtime)

        name = fn.split('results-')[1].split('.csv')[0]
        print('%30s: %.20f (%f)' % (name, m * 1000000, c * 1000000))

        gnuplot.write('x*%.20f+%.20f title "%s" lc %d, \\\n' % (m, c, name, color))
        color += 1

    gnuplot.write('y=0\n')
    gnuplot.close()
    os.system('gnuplot %s 2>/dev/null' % gnuplot_filename)
