import numpy as np
import subprocess


def objective(**kwargs):
    #check_config()
    write_config(**kwargs)

    o = subprocess.run(['bash', 'test.sh', '>', 'OUTPUT'], capture_output=True)
    o = [float(i) for i in o.stdout.decode('utf-8').split('\n') if len(i) > 0]

    return np.mean(o)

def write_config(outfile='settings.conf', **kwargs):
    with open(outfile, 'w') as f:
        print(kwargs['val'], file=f)

def check_config():
    o = subprocess.run(['bash', 'test.sh', '>', 'OUTPUT'], capture_output=True)

print(objective(val=3))