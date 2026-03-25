#!/usr/bin/env python3
import sys
import os

def apply_patch(original_file, patch_file):
    with open(original_file, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
    with open(patch_file, 'r', encoding='utf-8') as f:
        patch_lines = f.readlines()
    
    # parse unified diff header
    i = 0
    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
        i += 1
    if i >= len(patch_lines):
        print("No hunk found")
        return None
    header = patch_lines[i]
    # extract old start, old length, new start, new length
    import re
    match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', header)
    if not match:
        print("Invalid header")
        return None
    old_start = int(match.group(1))
    old_len = int(match.group(2))
    new_start = int(match.group(3))
    new_len = int(match.group(4))
    # lines after header are the hunk content
    i += 1
    hunk_lines = []
    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
        hunk_lines.append(patch_lines[i])
        i += 1
    
    # separate old and new lines
    old_hunk = []
    new_hunk = []
    for line in hunk_lines:
        if line.startswith(' '):
            old_hunk.append(line[1:])
            new_hunk.append(line[1:])
        elif line.startswith('-'):
            old_hunk.append(line[1:])
        elif line.startswith('+'):
            new_hunk.append(line[1:])
        else:
            # empty line? ignore
            pass
    
    # verify old_hunk matches original lines at old_start-1
    original_slice = original_lines[old_start-1:old_start-1+old_len]
    if original_slice != old_hunk:
        print("Context mismatch. Expected:")
        print(repr(old_hunk))
        print("Got:")
        print(repr(original_slice))
        # try to find matching context by scanning
        print("Attempting to locate context...")
        for idx in range(len(original_lines) - len(old_hunk) + 1):
            if original_lines[idx:idx+len(old_hunk)] == old_hunk:
                print(f"Found at line {idx+1}")
                old_start = idx + 1
                break
        else:
            print("Could not locate context, aborting")
            return None
    
    # replace old lines with new lines
    new_lines = original_lines[:old_start-1] + new_hunk + original_lines[old_start-1+old_len:]
    return new_lines

if __name__ == '__main__':
    original = 'src/utils/kiwoom_utils.py'
    patch = 'etc/kiwoom_utils_realtime.patch'
    new_lines = apply_patch(original, patch)
    if new_lines is None:
        sys.exit(1)
    # backup original
    import shutil
    shutil.copy2(original, original + '.bak')
    with open(original, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Applied patch to {original}")