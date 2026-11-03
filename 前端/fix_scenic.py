import os
import subprocess

js_path = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js\scenic.js"

with open(js_path, 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the broken quote pattern
# Find: ','' + spot.name + '')
# This creates: '') which JS parser sees as empty string + )
# Fix: ',\\' + escapedName + '\\')
import re

# Replace the problematic onclick strings
# Pattern 1: setDriveDest
old1 = "onclick=\"setDriveDest(' + spot.longitude + ',' + spot.latitude + ','' + spot.name + '')\""
new1 = "onclick=\"setDriveDest(' + spot.longitude + ',' + spot.latitude + ',\\' + (spot.name||'').replace(/'/g,'') + '\\')\""
c = c.replace(old1, new1)

# Pattern 2: addToTspList
old2 = "onclick=\"addToTspList(' + spot.longitude + ',' + spot.latitude + ','' + spot.name + '')\""
new2 = "onclick=\"addToTspList(' + spot.longitude + ',' + spot.latitude + ',\\' + (spot.name||'').replace(/'/g,'') + '\\')\""
c = c.replace(old2, new2)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(c)

# Verify
r = subprocess.run(['node', '--check', js_path], capture_output=True, text=True)
if r.returncode == 0:
    print('OK - scenic.js syntax valid')
else:
    # Find the actual error
    for line in r.stderr.split('\n'):
        if 'SyntaxError' in line:
            print(f'ERROR: {line.strip()}')
            break

    # Show the error line
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if 'SyntaxError' in r.stderr and str(i+1) in r.stderr:
            print(f'  Line {i+1}: {line[:100]}')
            break
