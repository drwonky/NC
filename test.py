import subprocess
import re

output = subprocess.check_output(["/sbin/ifconfig","wlan0"])

print (output)
m = re.search('(addr:)([0-9\.]+)',output)

print (m)

if m is None:
	print ('not found')
else:
	print (m.group(0),m.group(1),m.group(2))

