# names: Filip Skalka, Mark Jansen
# student numbers: 14635011, 500831327
# group name: sapphire agama of wealth
# description: algorithm detects congestion control
# phases for TcpNewReno. We then make a plot for cwnd and time
# including the points when there is a transition
# to a different phase or a timeout

import sys
import matplotlib.pyplot as plt
import numpy as np
from math import inf

slow_start = True
congestion_aviodance = False
fast_recovery = False
timeouts_times = []
timeouts_bytes = []
transitions_times = []
transitions_bytes = []
threshold = inf
mss = 964


def is_fast_recovery(entry1, entry2):
    return -mss < entry1 // 2 - entry2 < mss and not fast_recovery


def is_slow_start(entry1, start_value):
    return entry1 == start_value and not slow_start


def is_congestion_avoidance(entry1, entry2):
    if entry1 > 0:
        succesiveWindow = (mss / entry1 * mss + entry1)
        checkBool = entry1 > threshold and not congestion_aviodance
        checkBool_2 = round(succesiveWindow) - entry2 == 1 and not congestion_aviodance
        if checkBool or checkBool_2:
            return True
    return False


def is_time_out(entry1):
    if entry1 == mss:
        return True
    return False


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
    start_value = min(bytes[1:])
    print(f"Transition at {time[0]} to slow start. Value of cwnd: {bytes[0]}.")
    transitions_times.append(time[0])
    transitions_bytes.append(bytes[0])
    for i in range(1, len(time)):
        if is_time_out(bytes[i]):
            print(f"Timeout at {time[i - 1]}. Value of cwnd: {bytes[i - 1]}.")
            timeouts_times.append(time[i])
            timeouts_bytes.append(bytes[i])

        if is_slow_start(bytes[i], start_value):
            slow_start = True
            congestion_aviodance = False
            fast_recovery = False
            threshold = bytes[i-1] // 2
            print(f"Transition at {time[i]} to slow start. Value of cwnd: {bytes[i]}.")
            transitions_times.append(time[i])
            transitions_bytes.append(bytes[i])
        elif is_congestion_avoidance(bytes[i - 1], bytes[i]):
            slow_start = False
            congestion_aviodance = True
            fast_recovery = False
            strToPrint = f"Transition at {time[i - 1]} to congestion avoidance."
            strToPrint += f" Value of cwnd: {bytes[i - 1]}."
            print(strToPrint)
            transitions_times.append(time[i-1])
            transitions_bytes.append(bytes[i-1])
        elif is_fast_recovery(bytes[i-1], bytes[i]):
            fast_recovery = True
            slow_start = False
            congestion_aviodance = False
            threshold = bytes[i-1] // 2
            print(f"Transition at {time[i]} to fast recovery. Value of cwnd: {bytes[i]}.")
            transitions_times.append(time[i])
            transitions_bytes.append(bytes[i])
        else:
            continue

    plt.xticks(ticks=np.linspace(start=0.01, stop=max(time), num=15))
    plt.yticks(ticks=np.linspace(start=0.01, stop=max(bytes), num=15))
    plt.scatter(time, bytes, s=1, alpha=0.5, label="cwnd")
    plt.scatter(timeouts_times, timeouts_bytes, marker='.',
                color='red', alpha=0.5, s=700, label="timeouts")
    plt.scatter(transitions_times, transitions_bytes, marker='.',
                color='black', s=175, label="transition")
    plt.legend(loc="upper right")
    plt.show()
