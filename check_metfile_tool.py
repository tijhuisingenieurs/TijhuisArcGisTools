import os.path
import sys
import logging
import arcpy
from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.tools.check_metfile import check_metfile

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: metfile bestand
# 1: resultatenbestand

input_fl = arcpy.GetParameterAsText(0)
output_fl = arcpy.GetParameterAsText(1)

check_metfile(input_fl, output_fl)