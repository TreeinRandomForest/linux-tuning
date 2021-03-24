import numpy as np
import subprocess
from dragonfly import load_config, maximize_function

CONF_FILE_TEMPLATE = 'ml-perf-harness.conf.template'
CONF_FILE = 'ml-perf.harness.conf'

def objective(arr, domain=None, default_vals=None):
    '''Objective function used by bayes opt
    Responsible for:
    1. Taking array input from dragonfly and transforming to dict
    2. Use dict to write new conf file
    3. Run ml-perf-harness to run workload and print metric to stdout
    4. Parse stdout to get objective value
    '''

    assert(len(arr)==len(domain))

    arr = [val[0] for val in arr] #since dragonfly wraps each val with dim=1 by default

    params = {a['name']:b for (a,b) in zip(domain, arr)} #convert array to dict

    write_config(outfile=CONF_FILE, templatefile=CONF_FILE_TEMPLATE, params=params, default_vals=default_vals)

    valid = check_config()

    if not valid:
        raise ValueError("Configuration is not valid")

    o = subprocess.run(['bash', 'ml-perf-harness.sh', '-t', 'seq-disk-perf.sh'], capture_output=True)
    o = [float(i) for i in o.stdout.decode('utf-8').split('\n') if len(i) > 0]

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

def optimization_loop(capital=10):
    vals_limits = read_vars('limits.sh')
    vals = read_vars('ml-perf-harness.conf', vals=vals_limits)

    vals_default = read_vars('default.conf', vals=vals_limits)

    domain = [{'name': 'MAX_SECTORS_KB', 'type': 'int', 'min': 1, 'max': 256, 'dim': 1},
            ]
    
    def objective_temp(x):
        return -(x[0]-100)**2


    config = load_config({'domain': domain})

    objective_partial = lambda x: objective(x, domain=domain, default_vals=vals_default)
    
    val, point, history = maximize_function(objective_partial, config.domain, capital, config=config)

    return val, point, history

