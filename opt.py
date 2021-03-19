import numpy as np
import subprocess
from dragonfly import load_config, maximize_function

CONF_FILE_TEMPLATE = 'ml-perf-harness.conf.template'
CONF_FILE = 'ml-perf.harness.conf'

def objective(arr, domain=None):
    assert(len(arr)==len(domain))

    kwargs = {a['name']:b for (a,b) in zip(domain, arr)}
    #should also include fixed arguments

    write_config(outfile=CONF_FILE, templatefile=CONF_FILE_TEMPLATE, **kwargs)
    valid = check_config()
    if not valid:
        raise ValueError("Configuration is not valid")

    o = subprocess.run(['bash', 'ml-perf-harness.sh', '-t', 'seq-disk-perf.sh'], capture_output=True)
    o = [float(i) for i in o.stdout.decode('utf-8').split('\n') if len(i) > 0]

    return np.mean(o)

def write_config(outfile='settings.conf', templatefile=None, **kwargs):
    if templatefile is None:    
        with open(outfile, 'w') as f:
            print(kwargs['val'], file=f)

    else:
        with open(templatefile, 'r') as f:
            lines = f.readlines()

        with open(outfile, 'w') as f:            
            for l in lines:
                l_split = l.split('=')

                if l_split[0] in kwargs:
                    print(l.rstrip('\n').replace("{" + l_split[0]+"_VAL}", str(kwargs[l_split[0]])), file=f)
                else:
                    print(l.rstrip('\n'), file=f)

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

