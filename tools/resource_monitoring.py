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

cpu_use = []
ram_use = []
t = []

p = subprocess.Popen(["sh", f'{ROOT_PATH}/scripts/tests/{script}'])

while p.poll() is None:
    t0 = datetime.now()
    cpu = np.array(psutil.cpu_percent(percpu=True))
    ram = psutil.virtual_memory().percent
    n = 1
    while (datetime.now() - t0).total_seconds() < 0.05:
        cpu += np.array(psutil.cpu_percent(percpu=True))
        ram += psutil.virtual_memory().percent
        n += 1
    # time.sleep(0.01)
    t.append(t0)
    cpu_use.append(cpu / n)
    ram_use.append(ram / n)

cpu_use = np.array(cpu_use)

xfmt = md.DateFormatter('%H:%M:%S')
_, ax = plt.subplots()

ax.plot(t, cpu_use[:, 0], label="CPU 1")
ax.plot(t, cpu_use[:, 1], label="CPU 2")
ax.plot(t, cpu_use[:, 2], label="CPU 3")
ax.plot(t, cpu_use[:, 3], label="CPU 4")

ax.set_xlabel("Time")
ax.set_ylabel("CPU use (%)")
ax.set_title("CPU use during build request")
ax.xaxis.set_major_formatter(xfmt)
ax.legend()
plt.show()

_, ax = plt.subplots()

ax.plot(t, ram_use)
ax.set_xlabel("Time")
ax.set_ylabel("RAM use (%)")
ax.set_title("RAM use during build request")
ax.xaxis.set_major_formatter(xfmt)
plt.show()
