import subprocess
import sys
import os

if __name__ == "__main__":
    entry = sys.argv[1]
    # subprocess.run(f"dig {ip_address} {hostname}")
    os.system(f"dig {entry}")
