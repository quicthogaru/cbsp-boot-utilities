# --------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause-Clear
# --------------------------------------------------------------------



__prog__        = "Clean Hex file"
__version__     = "1.0"
__description__ = "Clean Hex file"
                    


def clean_hex_file(input_file):
    with open(input_file, 'r') as file:
        content = file.read()
    
    # Remove '0x', '{', '}', and commas
    cleaned_content = content.replace("0x", "").replace(",", "").replace("{", "").replace("}", "")
    
    with open(input_file, 'w') as file:
        file.write(cleaned_content)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python clean_hex_file.py <input_file>")
    else:
        input_file = sys.argv[1]
        clean_hex_file(input_file)