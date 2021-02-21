import numpy as np
import time as systime

import ndpulsecount

if __name__ == '__main__':
    counter = ndpulsecount.PulseCounter()
    counter.purge_memory()

    for a in range(500):
        counts = counter.get_counts(timeout=1)
        if a % 100 == 0:
            print(counts)

    counter.close()

