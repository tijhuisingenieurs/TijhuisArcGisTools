import os.path
import sys

import arcpy

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))
from gistools.utils.collection import MemCollection

