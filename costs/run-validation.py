import glob
import subprocess
import sys
import os

results = open('mixed-programs/results.csv', 'w+')

gnuplot_filename = 'mixed-programs/render.gnuplot'
gnuplot = open(gnuplot_filename, 'w+')

gnuplot.write('''set output "mixed-programs/costs.png"
set datafile separator ","
set term png size 1400,900 small
set termoption enhanced
set ylabel "run-time (s)"
set xlabel "cost"
set xrange [0:*]
set yrange [0:*]
plot "mixed-programs/results.csv" using 1:2 with points
''')
gnuplot.close()

counter = 0
for fn in glob.glob('mixed-programs/*.clvm'):

    print('%04d: %s' % (counter, fn))
    counter += 1
    # the filename is expected to be in the form:
    # name "-" value_size "-" num_calls
    env = open(fn[:-4] + 'env').read()
    output = subprocess.check_output(['brun', '--backend=rust', '-c', '--quiet', '--time', fn, env])
    output = output.decode('ascii').split('\n', 5)[:-1]

    counters = {}
    for o in output:
        if ':' in o:
            key, value = o.split(':')
            counters[key.strip()] = value.strip()
        elif '=' in o:
            key, value = o.split('=')
            counters[key.strip()] = value.strip()

    line = counters['cost'] + ',' + counters['run_program'] + '\n'
    results.write(line)
    results.flush()

results.close()
os.system('gnuplot %s' % gnuplot_filename)
