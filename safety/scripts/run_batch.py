import subprocess
import sys


def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Command: {cmd}")
    print("Output:")
    print(result.stdout)
    if result.returncode != 0:
        description = result.stderr.strip()
        if len(description) > 200:
            description = description[:200] + "..."
        print(f"Error Description: {description}")
    print("---")


if __name__ == "__main__":
    try:
        with open("commands.txt") as f:
            commands = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("commands.txt not found. Please create a file with one command per line.")
        sys.exit(1)
    for cmd in commands:
        run_command(cmd)
