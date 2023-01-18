#!/usr/bin/python3

import psutil
import subprocess
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
import time
from datetime import datetime

ROOT_PATH = str(Path(__file__).parent.parent)

script = "build-datacube.sh"

print(psutil.cpu_percent(percpu=True))

cpu_use = []
t = [datetime.now()]
cpu_use.append(psutil.cpu_percent(percpu=True))
p = subprocess.Popen(["sh", f'{ROOT_PATH}/scripts/tests/{script}'])

while p.poll() is None:
    time.sleep(1)
    t.append(datetime.now())
    cpu_use.append(psutil.cpu_percent(percpu=True))

cpu_use = np.array(cpu_use)

xfmt = md.DateFormatter('%H:%M:%S')
_, ax = plt.subplots(2, 2)

ax[0, 0].plot(t, cpu_use[:, 0])
ax[0, 0].set_xlabel("Time")
ax[0, 0].set_ylabel("CPU use (%)")
ax[0, 0].set_title("CPU 1")
ax[0, 0].xaxis.set_major_formatter(xfmt)

ax[0, 1].plot(t, cpu_use[:, 1])
ax[0, 1].set_xlabel("Time")
ax[0, 1].set_ylabel("CPU use (%)")
ax[0, 1].set_title("CPU 2")
ax[0, 1].xaxis.set_major_formatter(xfmt)

ax[1, 0].plot(t, cpu_use[:, 2])
ax[1, 0].set_xlabel("Time")
ax[1, 0].set_ylabel("CPU use (%)")
ax[1, 0].set_title("CPU 3")
ax[1, 0].xaxis.set_major_formatter(xfmt)

ax[1, 1].plot(t, cpu_use[:, 3])
ax[1, 1].set_xlabel("Time")
ax[1, 1].set_ylabel("CPU use (%)")
ax[1, 1].set_title("CPU 4")
ax[1, 1].xaxis.set_major_formatter(xfmt)

plt.show()
