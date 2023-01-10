# names: Filip Skalka, Mark Jansen
# student numbers: 14635011, 500831327
# group name: sapphire agama of wealth
# description: we go through both files, find the second fast recovery
# take the value of cwnd from right before it, compute the average rtt
# and find the actual average of cwnd/rtt for matching timestamps

import sys

matching_timestamps = []
frac = []
mss = 340

estimated_average = None
fast_recovery_counter = 0
W = None
rtts = []

if __name__ == "__main__":
    filename_cwnd = sys.argv[1]
    filename_rtt = sys.argv[2]
    with open(filename_cwnd, 'r') as file:
        lines_1 = file.readlines()[1:]
        with open(filename_rtt, 'r') as file2:
            lines_2 = file2.readlines()[1:]
            i, j = 0, 0
            while i < len(lines_1) and j < len(lines_2):
                if float(lines_1[i - 1].split(" ")[1]) / 2 >= float(lines_1[i].split(" ")[1]):
                    i += 1
                    fast_recovery_counter += 1
                    if fast_recovery_counter == 2:
                        W = float(lines_1[i - 1].split(" ")[1])
                if float(lines_1[i].split(" ")[0]) == float(lines_2[j].split(" ")[0]):
                    if float(lines_2[j].split(" ")[1]) != 0:
                        frac.append(float(lines_1[i].split(" ")[1]) /
                                    float(lines_2[j].split(" ")[1]))
                        matching_timestamps.append(float(lines_1[i].split(" ")[0]))
                    i += 1

                elif float(lines_1[i].split(" ")[0]) > float(lines_2[j].split(" ")[0]):
                    rtts.append(float(lines_2[j].split(" ")[1]))
                    j += 1

                elif float(lines_1[i].split(" ")[0]) < float(lines_2[j].split(" ")[0]):
                    i += 1

    average = sum(frac) / len(frac)
    average_rtt = sum(rtts) / len(rtts)
    print(f'Average CWND/RTT: {average}')
    print(f'Approximated average is: {0.75 * W / average_rtt}')
