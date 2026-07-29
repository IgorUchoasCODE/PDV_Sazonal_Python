import pandas as pd
# check what runner_excel used
with open('runner_excel.py', 'r') as f:
    for line in f.readlines():
        if 'read' in line and ('csv' in line or 'excel' in line):
            print(line.strip())
