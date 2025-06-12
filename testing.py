import psutil
print(psutil.net_io_counters(pernic=False, nowrap=True))