# names: Filip Skalka, Mark Jansen
# student numbers: 14635011, 500831327
# group name: sapphire agama of wealth
# description: we go through both files compute the average
# of cwnd/rtt for the matching timestamps in both files

import sys
import matplotlib.pyplot as plt
import numpy as np


matching_timestamps = []
frac = []


if __name__ == "__main__":
    filename_cwnd = sys.argv[1]
    filename_rtt = sys.argv[2]
    time = []
    bytes = []
    with open(filename_cwnd, 'r') as file:
        lines_1 = file.readlines()[1:]
        with open(filename_rtt, 'r') as file2:
            lines_2 = file2.readlines()[1:]
            i, j = 0, 0
            while i < len(lines_1) and j < len(lines_2):
                if float(lines_1[i].split(" ")[0]) == float(lines_2[j].split(" ")[0]):
                    if float(lines_2[j].split(" ")[0]) != 0:
                        frac.append(float(lines_1[i].split(" ")[1]) /
                                    float(lines_2[j].split(" ")[1]))
                        matching_timestamps.append(float(lines_1[i].split(" ")[0]))
                    i += 1
                elif float(lines_1[i].split(" ")[0]) > float(lines_2[j].split(" ")[0]):
                    j += 1
                elif float(lines_1[i].split(" ")[0]) < float(lines_2[j].split(" ")[0]):
                    i += 1

    plt.figure(figsize=(12, 8))
    plt.xlabel('time [ms]')
    plt.ylabel('cwnd / rtt')
    plt.xticks(ticks=np.linspace(start=0.01, stop=504, num=15))
    plt.yticks(ticks=np.linspace(start=0.01, stop=3.550e5, num=15))
    plt.scatter(matching_timestamps, frac, s=1, alpha=0.1, c='red', label='cwnd/rtt')
    average = sum(frac) / len(frac)
    print(f'Average CWND/RTT: {average}')
    plt.show()
