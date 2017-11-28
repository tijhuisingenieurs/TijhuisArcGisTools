import logging
import os.path
import sys

import arcpy

from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: lijnenbestand
# 1: puntenbestand
# 2: Doelbestand voor snapped punten
# 3: Tolerantie
# 4: Unsnapped punten behouden

input_lines = arcpy.GetParameterAsText(0)
input_points = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)
tolerance = arcpy.GetParameterAsText(3)
keep_unsnapped_points = arcpy.GetParameterAsText(4)

# Send received input to the console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand lijnen = ' + input_lines)
arcpy.AddMessage('Bronbestand punten = ' + input_points)
arcpy.AddMessage('Doelbestand snapped punten = ' + output_file)
arcpy.AddMessage('Tolerantie = ' + str(tolerance))
arcpy.AddMessage('Unsnapped punten behouden = ' + str(keep_unsnapped_points))

# Prepare data types and read data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

