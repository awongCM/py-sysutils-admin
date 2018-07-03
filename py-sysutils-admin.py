# My first sysadmin memory monitoring usage!
import os 
import psutil

for proc in psutil.process_iter():
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
