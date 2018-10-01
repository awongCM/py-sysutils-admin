from __future__ import print_function
import os 
from psutil import(cpu_percent, virtual_memory, __version__, process_iter)
import psutil
import time

psutil_version = __version__
cpu_percent = cpu_percent()
system_memory= virtual_memory()
system_memory_in_gb = virtual_memory()[0]/2.**30

print(psutil_version) # Psutil version
print("#-------------------#")
print("#-------------------#")
print(cpu_percent) #CPU Percent
print(system_memory) #Virtual Memory
print("#-------------------#")
print("#-------------------#")
print('Memory (in GB): ', system_memory_in_gb)

# Process Monitor
def process_monitor():
  for proc in process_iter():
    try:
      pinfo = {
        "pid": proc.ppid(),
        "name": proc.name(),
        "username": proc.username(),
        "create_time": proc.create_time(),
        "cpu_times": proc.cpu_times(),
        "memory_usage_percent": proc.memory_percent()
      }
    except psutil.NoSuchProcess:
      pass
    else:
      print(pinfo)

# Disk monitor
def disk_monitor():
  statvfs = os.statvfs('/')
  print(statvfs.f_frsize * statvfs.f_blocks) # Size of filesystem in bytes
  print(statvfs.f_frsize * statvfs.f_bfree)  # Actual number of bytes
  print(statvfs.f_frsize * statvfs.f_bavail) # Number of free bytes that ordinary users

# Network monitor
def network_monitor():
  
  old_value = 0

  while True:
    new_value = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

    if old_value:
      sent_sat(new_value - old_value)

    old_value = new_value

    time.sleep(1)


def convert_to_gbit(value):
  return value/1024./1024./1024.*8      

def sent_sat(value):
  print ("%0.3f" % convert_to_gbit(value))


# Main Program starts
def main():
  print("Available options")
  print("======= c - cpu and memory =========")
  print("======= n - network  =========")
  print("======= d - disk =========")

  monitor_type = input("Enter your monitoring type: ")

  if monitor_type == 'c':
    process_monitor()
  elif monitor_type == 'n':
    network_monitor()
  elif monitor_type == 'd':
    disk_monitor()
  else:
    print('Program ends here')

main()