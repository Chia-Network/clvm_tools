import glob
import subprocess
import sys
import os

open_files = {}

dry_run = False

def get_file(folder, name):
    full_path = os.path.join(folder, 'results-%s.csv' % name)
    if full_path in open_files: return open_files[full_path]

    if dry_run: f = 1
    else: f = open(full_path, 'a')
    open_files[full_path] = f

    if dry_run: return f

    f.write('#cost,assemble_from_ir,to_sexp_f,run_program,multiplier\n')
    return f

counter = 0

force_run = '--force' in sys.argv

for directory in glob.glob('test-programs/*'):
    existing_results = []
    for r in glob.glob(directory + '/*.csv'):
        existing_results.append(os.path.split(r)[1].split('-')[1])

    for fn in glob.glob('test-programs/%s/*.clvm' % os.path.split(directory)[1]):

        # if we have a csv file for this run already, skip running it again
        dry_run = not force_run and os.path.split(fn)[1].split('-')[0] in existing_results

        if not dry_run:
            print('%04d: %s' % (counter, fn))
        counter += 1
        # the filename is expected to be in the form:
        # name "-" value_size "-" num_calls
        if not dry_run:
            env = open(fn[:-4] + 'env').read()
            output = subprocess.check_output(['brun', '--backend=rust', '-c', '--quiet', '--time', fn, env])
            output = output.decode('ascii').split('\n', 5)[:-1]

            counters = {}
            for o in output:
                try:
                    if ':' in o:
                        key, value = o.split(':')
                        counters[key.strip()] = value.strip()
                    elif '=' in o:
                        key, value = o.split('=')
                        counters[key.strip()] = value.strip()
                except BaseException as e:
                    print(e)
                    print('ERROR parsing: %s' % o)
            print(counters)

        folder, fn = os.path.split(fn)
        name_components = fn.split('-')
        f = get_file(folder, '-'.join(name_components[0:-1]))
        if not dry_run:
            line = counters['cost'] + ',' + \
                counters['assemble_from_ir'] + ',' + \
                counters['to_sexp_f'] + ',' + \
                counters['run_program'] + ',' + \
                name_components[-1].split('.')[0] + '\n'
            f.write(line)

    gnuplot_filename = '%s/render-timings.gnuplot' % folder
    gnuplot = open(gnuplot_filename, 'w+')

    gnuplot.write('''set output "%s/timings.png"
set datafile separator ","
set term png size 1400,900 small
set termoption enhanced
set ylabel "run-time (s)"
set xlabel "number of ops"
set xrange [0:*]
set yrange [0:0.3]
''' % directory)

    color = 0
    gnuplot.write('plot ')
    count = len(open_files)
    for n,v in open_files.items():
        cont = ', \\'
        if color + 1 == count: cont = ''
        name = n.split('results-')[1].split('.csv')[0]
        gnuplot.write('"%s" using 5:4 with points lc %d title "%s"%s\n' % (n, color, name, cont))
        color += 1
        if not isinstance(v, int): v.close()

    gnuplot.close()
    open_files = {}
    os.system('gnuplot %s' % gnuplot_filename)
