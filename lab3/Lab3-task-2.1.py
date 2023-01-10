# names: Filip Skalka, Mark Jansen
# student numbers: 14635011, 500831327
# group name: sapphire agama of wealth
# description: we plot the cwnd and time

import sys
import matplotlib.pyplot as plt
import numpy as np


if __name__ == "__main__":
    filename = sys.argv[1]
    time = []
    bytes = []
    with open(filename, 'r') as file:
        lines = file.readlines()[1:]
        for line in lines:
            time.append(float(line.split(" ")[0]))
            bytes.append(float(line.split(" ")[1]))
    plt.figure(figsize=(12, 8))
    plt.xlabel('time [ms]')
    plt.ylabel('congestion window size segments')
    plt.xticks(ticks=np.linspace(start=0.01, stop=241, num=15))
    plt.yticks(ticks=np.linspace(start=0.01, stop=170000, num=15))
    plt.scatter(time, bytes, s=1, alpha=0.1)
    plt.show()
