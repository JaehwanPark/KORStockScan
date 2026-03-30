#!/usr/bin/env python3
import re
import sys

with open('src/engine/kiwoom_sniper_condition.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function handle_watching_state
start = -1
for i, line in enumerate(lines):
    if line.strip().startswith('def handle_watching_state'):
        start = i
        break
if start == -1:
    print("Function not found")
    sys.exit(1)

# Find the line where the execution part begins (line containing "# 🎯 매수 실행 공통 로직")
# We'll search from start onward.
exec_start = -1
for i in range(start, len(lines)):
    if '# 🎯 매수 실행 공통 로직' in lines[i]:
        exec_start = i
        break
if exec_start == -1:
    print("Execution start not found")
    sys.exit(1)

print(f"Function start line: {start}")
print(f"Execution start line: {exec_start}")

# The decision block is from start to exec_start-1 (excluding the line with the comment)
decision_lines = lines[start:exec_start]

# We'll create a nested function with these lines, but need to modify returns.
# We'll add a new function definition before the decision block.
# Let's just output the decision block with modifications for demonstration.
# Instead we'll generate a new block that replaces the entire function from start to exec_start-1 with a nested function.
# But we need to keep the original function signature and docstring.
# Let's extract the signature and docstring lines (up to the line containing 'global LAST_AI_CALL_TIMES')
# Actually we need to keep the outer function's initial lines (signature, docstring, global) and then insert nested function.
# This is complex; we'll just output the decision block with modified returns for manual review.
# Let's write to a file.

def modify_return(line):
    # If line is a return statement (with nothing else), replace with return dict
    stripped = line.strip()
    if stripped == 'return':
        return '        return {"is_trigger": False, "skip_reason": "early return"}'
    # If line is 'return' with comment, we need to handle.
    # For simplicity, we'll just replace.
    if stripped.startswith('return'):
        # Keep the rest of line after return? Might be return with value? Not in decision block.
        # We'll assume empty return.
        return '        return {"is_trigger": False, "skip_reason": "early return"}'
    return line

# Indent decision lines by 4 spaces (since nested function will be inside outer function)
# Actually we will later decide.
# Let's just print.
for i, line in enumerate(decision_lines):
    sys.stdout.write(f"{i+start}: {line}")

sys.stdout.write("\n---\n")
print("Now we need to write the nested function.")