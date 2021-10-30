import subprocess
import os

COMPILER_PATH = "/home/wasp97/Downloads/micropython/mpy-cross/mpy-cross"

files = [file for file in os.listdir() if file.endswith(".py") and not file == "compiler.py"]

print(f"Compiling files {len(files)}...")
for file in files:
	print(f"Compiling {file}...")
	response = subprocess.run(f"{COMPILER_PATH} {file} -o {file.replace('.py', '.mpy')}", shell=True)
	if response.stdout is not None:
		raise ValueError(response.stdout)
print("Done.")
