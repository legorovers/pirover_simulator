import sys, os

try:
    sys.path.index(os.getcwd())
except ValueError:
    sys.path.append(os.getcwd())
    
print(os.getcwd())
