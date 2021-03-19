import numpy as np
import subprocess
from dragonfly import load_config, maximize_function

def objective(**kwargs):
    valid = check_config()
    if not valid:
        raise ValueError("Configuration is not valid")

    write_config(**kwargs)

    o = subprocess.run(['bash', 'ml-perf-harness.sh', '-t', 'seq-disk-perf.sh'], capture_output=True)
    o = [float(i) for i in o.stdout.decode('utf-8').split('\n') if len(i) > 0]

    return np.mean(o)

def write_config(outfile='settings.conf', **kwargs):
    with open(outfile, 'w') as f:
        print(kwargs['val'], file=f)

def check_config():
    o = subprocess.run(['bash', 'ml-perf-harness.sh', '-c'], capture_output=True)
    o = o.stdout.decode('utf-8')
    
    if o.find('Configuration is valid')>-1:
        return True
    return False

def parse_vars(filename, vals={}):
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
    vals = parse_vars('limits.sh')
    vals = parse_vars('ml-perf-harness.conf', vals=vals)

    domain = {}

    config = load_config({'domain': domain})
    val, point, history = maximize_function(objective, config.domain, capital)

    return val, point, history

print(objective(val=3))
