from __future__ import print_function
import os 
from psutil import(
  cpu_percent, 
  virtual_memory,  
  process_iter,
  __version__)
import psutil
import time
import sys
from math import ceil


psutil_version = __version__
cpu_percent = cpu_percent()
system_memory= virtual_memory()
system_memory_in_gb = virtual_memory()[0]/2.**30

app_title ='''
Welcome to PySysUtils Admin tool
'''.upper()

print(app_title)

print('Current PSUtil Version: {}'.format(psutil_version)) # Psutil version
print("######-------------------------------------######")
print("######-------------------------------------######")
print("######-------------------------------------######")
print('CPU Percentage(%) in used: {}'.format(cpu_percent)) #CPU Percent
print("######-------------------------------------######")
print("######-------------------------------------######")
print("######-------------------------------------######")
# print(system_memory) #Virtual Memory
print('Total Memory: {}'.format(system_memory.total))
print('Available Memory: {}'.format(system_memory.available))
print('Percent Memory: {}'.format(system_memory.percent))
print('Used Memory: {}'.format(system_memory.used))
print('Free Memory: {}'.format(system_memory.free))
print('Active Memory: {}'.format(system_memory.active))
print('Inactive Memory: {}'.format(system_memory.inactive))
print("######-------------------------------------######")
print("######-------------------------------------######")
print("######-------------------------------------######")
print('Memory: {} GB'.format(system_memory_in_gb))

# Process Monitor
def cpu_mem_monitor():
  for proc in process_iter():
    try:
      pinfo = {
        "pid": proc.ppid(),
        "name": proc.name(),
        "username": proc.username(),
        "create_time": proc.create_time(),
        "cpu_times": proc.cpu_times(),
        "memory_usage_percent": ceil(proc.memory_percent() * 100) / 100.0
      }
      print("Process info", pinfo)
    except:
      print("Oops!", sys.exc_info()[0], "occured",)

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


def check_input(monitor_type):
  if monitor_type == 'c' or monitor_type == 'n' or monitor_type == 'd':
    return True
  else:
    return False

# Main Program starts
def main():
  print("Available options")
  print("======= c - cpu and memory =========")
  print("======= n - network  =========")
  print("======= d - disk =========")

  while True:
    monitor_type = input("Choose your monitoring type: ")
    
    if not check_input(monitor_type):
      print('Incorrect option. Please try again.')
      continue
    else:
      break

  if monitor_type == 'c':
    cpu_mem_monitor()
  elif monitor_type == 'n':
    network_monitor()
  elif monitor_type == 'd':
    disk_monitor()

main()