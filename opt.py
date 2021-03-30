import numpy as np
import subprocess, os, shutil
from dragonfly import load_config, maximize_function

CONF_FILE_TEMPLATE = 'ml-perf-harness.conf.template'
CONF_FILE = 'ml-perf.harness.conf'
LOC = 'conf_files'
it = 0

def objective(arr, domain=None, default_vals=None, return_std=False, n_iter=None):
    '''Objective function used by bayes opt
    Responsible for:
    1. Taking array input from dragonfly and transforming to dict
    2. Use dict to write new conf file
    3. Run ml-perf-harness to run workload and print metric to stdout
    4. Parse stdout to get objective value
    '''

    assert(len(arr)==len(domain))

    global it
    it += 1

    arr = [val[0] for val in arr] #since dragonfly wraps each val with dim=1 by default

    params = {a['name']:b for (a,b) in zip(domain, arr)} #convert array to dict

    write_config(outfile=CONF_FILE, templatefile=CONF_FILE_TEMPLATE, params=params, default_vals=default_vals)

    valid = check_config()

    if not valid:
        raise ValueError("Configuration is not valid")

    if not n_iter:
        o = subprocess.run(['bash', 'ml-perf-harness.sh', '-t', 'seq-disk-perf.sh'], capture_output=True)
    else:
        o = subprocess.run(['bash', 'ml-perf-harness.sh', '-t', 'seq-disk-perf.sh', '-n', str(n_iter)], capture_output=True)
    
    o = [float(i) for i in o.stdout.decode('utf-8').split('\n') if len(i) > 0]

    shutil.copyfile(CONF_FILE, f'{LOC}/{CONF_FILE}.{it}')
    
    if return_std:
        return np.mean(o), np.std(o)

    return np.mean(o)

def write_config(outfile='settings.conf', templatefile=None, default_vals = {}, params = {}):
    '''write passed config values to file
    '''
    #read data from template file
    with open(templatefile, 'r') as f:
        lines = f.readlines()

    #fill in vars from params and write to outfile
    with open(outfile, 'w') as f:
        for l in lines:
            if l.find('{')==-1:
                print(l.rstrip("\n"), file=f)

            elif l.find('{')>-1: #bayesopt params
                l_split = l.split('=')
                key = l_split[0]
                print(f'{key}={params.get(key, default_vals.get(key, -999))}', file=f)

            else:
                #should never enter here but protection for future changes
                raise ValueError(f"ERROR: {l}")

def check_config():
    '''ensure written config is valid
    '''
    o = subprocess.run(['bash', 'ml-perf-harness.sh', '-c'], capture_output=True)
    o = o.stdout.decode('utf-8')
    
    if o.find('Configuration is valid')>-1:
        return True
    return False

def read_vars(filename, vals={}):
    '''read var values from file
    '''
    with open(filename) as f:
        lines = f.readlines()
        for l in lines:
            try:    
                k,v = l.rstrip('\n').split('=')
                if k[0]!='#': #uncommented line
                    if v[0]=='$': #variable defined before
                        v = vals.get(v[1:], v)
                    vals[k] = v 
            except:
                continue
    return vals

def scan_loop(n_iter=None):
    vars_to_loop = [{'name': 'READ_AHEAD_KB', 'type': 'int', 'min': 0, 'max': 3, 'step_size': 1, 'dim': 1}]

    vals_limits = read_vars('limits.sh')
    vals_default = read_vars('default.conf', vals=vals_limits)

    results = {}
    for var in vars_to_loop:
        domain = [var]

        objective_partial = lambda x: objective(x, domain=domain, default_vals=vals_default, return_std=True, n_iter=n_iter)
        
        results[var['name']] = {}

        for x in np.arange(var['min'], var['max'], var['step_size']):
            metric_mean, metric_std = objective_partial([[x]])
            results[var['name']][x] = (metric_mean, metric_std)
            print(x, metric_mean, metric_std)

    return results

def optimization_loop(capital=10):
    vals_limits = read_vars('limits.sh')
    vals = read_vars('ml-perf-harness.conf', vals=vals_limits)

    vals_default = read_vars('default.conf', vals=vals_limits)

    domain = [
                #{'name': 'READ_LAT_NSEC', 'type': 'int', 'min': 0, 'max': 100000000, 'dim': 1},
                #{'name': 'WRITE_LAT_NSEC', 'type': 'int', 'min': 0, 'max': 100000000, 'dim': 1},
                #{'name': 'NR_REQUESTS', 'type': 'int', 'min': 4, 'max': 10000, 'dim': 1}, #queue depth
                #{'name': 'MAX_SECTORS_KB', 'type': 'int', 'min': 128, 'max': 1280, 'dim': 1}, #max IO size sent to device
                {'name': 'READ_AHEAD_KB', 'type': 'int', 'min': 0, 'max': 10000, 'dim': 1}, #amount of IO to read ahead into cache
                #{'name': 'WBT_LAT_USEC', 'type': 'int', 'min': 0, 'max': 10000, 'dim': 1}, #target latency for reads. throttle writes otherwise
                #{'name': 'DIRTY_RATIO', 'type': 'int', 'min': 0, 'max': 100, 'dim': 1},
                #{'name': 'DIRTY_BACKGROUND_RATIO', 'type': 'int', 'min': 0, 'max': 100, 'dim': 1},
                #{'name': 'SWAPPINESS', 'type': 'int', 'min': 0, 'max': 100, 'dim': 1},
            ]
    
    config = load_config({'domain': domain})

    objective_partial = lambda x: objective(x, domain=domain, default_vals=vals_default)
    

    if not os.path.exists(LOC):    
        os.makedirs(LOC)

    val, point, history = maximize_function(objective_partial, config.domain, capital, config=config)
    
    return val, point, history

