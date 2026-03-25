#!/usr/bin/env python3
import sys
import os

def extract_added_lines(patch_file):
    with open(patch_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    i = 0
    while i < len(lines) and not lines[i].startswith('@@'):
        i += 1
    if i >= len(lines):
        return []
    i += 1  # skip header
    added = []
    while i < len(lines) and not lines[i].startswith('@@'):
        line = lines[i]
        if line.startswith('+') and not line.startswith('++'):
            added.append(line[1:])
        i += 1
    return added

def find_insert_position(original_lines):
    # locate the line "    return price" that is after get_target_price_up
    # we can search for the function definition and then find the return
    for idx, line in enumerate(original_lines):
        if line.strip().startswith('def get_target_price_up'):
            # find the return line within the same indentation
            for j in range(idx, len(original_lines)):
                if original_lines[j].strip() == 'return price':
                    return j  # line index (0-based)
    # fallback: find any line with "return price"
    for idx, line in enumerate(original_lines):
        if line.rstrip() == '    return price':
            return idx
    return len(original_lines) - 1

def main():
    original_path = 'src/utils/kiwoom_utils.py'
    patch_path = 'etc/kiwoom_utils_realtime.patch'
    
    with open(original_path, 'r', encoding='utf-8') as f:
        original = f.readlines()
    
    added = extract_added_lines(patch_path)
    if not added:
        print("No added lines extracted")
        sys.exit(1)
    
    insert_pos = find_insert_position(original)
    print(f"Inserting after line {insert_pos+1}: {original[insert_pos].rstrip()}")
    # Ensure we don't duplicate the three lines already present.
    # The added lines already include the new functions, but we need to ensure
    # we don't duplicate the blank line after return price.
    # We'll insert after the line, adding a blank line before new functions.
    new_lines = original[:insert_pos+1] + ['\n'] + added + original[insert_pos+1:]
    
    # backup
    import shutil
    shutil.copy2(original_path, original_path + '.bak')
    with open(original_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Applied patch to {original_path}")

if __name__ == '__main__':
    main()