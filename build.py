import json
import sys

def apply_instructions(file_path, instructions):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    instructions = json.loads(instructions)

    if instructions['Instruct'] == 'paste':
        from_line = instructions['From'] - 1
        code = instructions['Code']
        code_lines = code.split('\n')

        for i, line in enumerate(code_lines):
            lines.insert(from_line + i, line + '\n')

    elif instructions['Instruct'] == 'delete':
        from_line = instructions['From'] - 1
        to_line = instructions['To']

        del lines[from_line:to_line]

    with open(file_path, 'w') as file:
        file.writelines(lines)

def main():
    if len(sys.argv) != 3:
        print("Usage: python build.py <path_to_python_file> <path_to_instructions_json>")
        sys.exit(1)

    file_path = sys.argv[1]
    instructions_path = sys.argv[2]

    with open(instructions_path, 'r') as file:
        instructions = file.read()

    apply_instructions(file_path, instructions)
    print(f"Changes applied to {file_path}")

if __name__ == "__main__":
    main()
