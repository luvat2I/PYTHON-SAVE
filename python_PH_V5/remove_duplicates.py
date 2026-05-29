def remove_duplicates(file1, file2, output_file):
    # Read contents of both files
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

    # Combine lines from both files
    all_lines = lines1 + lines2

    # Remove duplicates while preserving order
    unique_lines = []
    seen = set()
    for line in all_lines:
        line = line.strip()
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    # Write unique lines to the output file
    with open(output_file, 'w') as out_f:
        for line in unique_lines:
            out_f.write(line + '\n')

    print(f"Unique lines have been written to {output_file}")

def extract_non_duplicates(file1, file2, output_file):
    # Read contents of both files
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        lines1 = set(f1.read().splitlines())
        lines2 = set(f2.read().splitlines())

    # Find lines that are in one file but not in the other
    unique_to_file1 = lines1 - lines2
    unique_to_file2 = lines2 - lines1

    # Combine unique lines
    all_unique_lines = unique_to_file1.union(unique_to_file2)

    # Write unique lines to the output file
    with open(output_file, 'w') as out_f:
        for line in sorted(all_unique_lines):
            out_f.write(line + '\n')

    print(f"Non-duplicate lines have been written to {output_file}")
    print(f"Lines unique to {file1}: {len(unique_to_file1)}")
    print(f"Lines unique to {file2}: {len(unique_to_file2)}")
    print(f"Total non-duplicate lines: {len(all_unique_lines)}")
