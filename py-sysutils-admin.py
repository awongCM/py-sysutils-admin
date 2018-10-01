from __future__ import print_function
import os 
from psutil import(cpu_percent, virtual_memory, __version__, process_iter)

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
