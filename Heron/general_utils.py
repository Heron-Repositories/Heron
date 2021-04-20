
import time
import os
import signal

def accurate_delay(delay):
    ''' Function to provide accurate time delay in millisecond
    '''
    target_time = time.perf_counter() + delay/1000
    while time.perf_counter() < target_time:
        pass

def kill_child(child_pid):
    if child_pid is None:
        pass
    else:
        os.kill(child_pid, signal.SIGTERM)