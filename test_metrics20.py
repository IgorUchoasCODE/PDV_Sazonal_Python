with open('runner_excel.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'insert_venda' in line or 'valorVenda' in line:
            print(line.strip())
