import os
import tempfile
import pytest
import sys
print("sys.path: " + str(sys.path))
sys.path.insert(0, sys.path[0] + '/../src')
import application