import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.tools.combine_peilingen import combine_peilingen
from gistools.utils.metfile_generator import export_points_to_metfile

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: Metfile inpeilingen
# 1: Metfile uitpeilingen
# 2: Link tabel
# 3: Project naam
# 4: Volgorde slib-vaste bodem
# 5: Schaaldrempel
# 5: Oeverpunten meeschalen
# 6: Doelbestand voor metfile
 
input_inpeilingen = arcpy.GetParameterAsText(0)
input_uitpeilingen = arcpy.GetParameterAsText(1)
link_table = arcpy.GetParameterAsText(2)
project = arcpy.GetParameterAsText(3)
order = arcpy.GetParameterAsText(4)
scale_threshold = arcpy.GetParameter(5)/100
scale_bank_distance = arcpy.GetParameter(6)
output_file = arcpy.GetParameterAsText(7)

# input_inpeilingen = "C:\Users\eline\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\Inpeiling.met"
# input_uitpeilingen = "C:\Users\eline\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\Uitpeiling.met"
# link_table = "C:\Users\eline\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\linkTable.csv"
# project = "Project,test"
# order = "z2z1"
# scale_threshold = 0.01
# scale_bank_distance = False
# output_file = "C:\Users\eline\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\Output.met"

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Shapefile = ' + str(input_inpeilingen))
arcpy.AddMessage('Shapefile = ' + str(input_uitpeilingen))
arcpy.AddMessage('Project = ' + str(link_table))
arcpy.AddMessage('Project = ' + str(project))
arcpy.AddMessage('Doelbestand metfile = ' + str(output_file))

# Process input data
combined_points = combine_peilingen(input_inpeilingen, input_uitpeilingen, link_table, scale_threshold,
                                    scale_bank_distance)

# Generate metfile
arcpy.AddMessage('Bezig met genereren van metfile...')
export_points_to_metfile(combined_points, project, output_file, 1, "combined_peilingen", order)

arcpy.AddMessage('Gereed')
