"""Fix indentation error in src/training/config.py line 77."""

with open('src/training/config.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 77 (0-indexed 76) - should have 8 spaces, not 4
if lines[76].startswith('    train_config'):
    lines[76] = '        train_config = load_config_file(config_dir, "train.yaml")\n'
    print(f"Fixed line 77: {repr(lines[76])}")
    
    with open('src/training/config.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✓ Fixed indentation in src/training/config.py")
else:
    print(f"Line 77 doesn't match expected pattern: {repr(lines[76])}")

