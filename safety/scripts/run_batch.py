import shlex
import subprocess
import sys


def run_command(cmd):
    args = shlex.split(cmd) if isinstance(cmd, str) else cmd
    result = subprocess.run(args, shell=False, capture_output=True, text=True)  # noqa: S603
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
