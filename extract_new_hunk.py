import sys
import re

with open('etc/kiwoom_utils_realtime.patch', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# find hunk
i = 0
while i < len(lines) and not lines[i].startswith('@@'):
    i += 1
if i >= len(lines):
    sys.exit(1)
header = lines[i]
match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', header)
if not match:
    sys.exit(1)
old_start = int(match.group(1))
old_len = int(match.group(2))
new_start = int(match.group(3))
new_len = int(match.group(4))
i += 1
hunk_lines = []
while i < len(lines) and not lines[i].startswith('@@'):
    hunk_lines.append(lines[i])
    i += 1

new_hunk = []
for line in hunk_lines:
    if line.startswith(' '):
        new_hunk.append(line[1:])
    elif line.startswith('+'):
        new_hunk.append(line[1:])
    elif line.startswith('-'):
        continue
    else:
        # empty line? ignore
        pass

# output
sys.stdout.writelines(new_hunk)