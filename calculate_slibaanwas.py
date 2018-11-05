import os.path
import sys
import logging
import arcpy
from utils.arcgis_logging import setup_logging
import arcpy
from utils.addresulttodisplay import add_result_to_display
from gistools.tools.combine_peilingen import combine_peilingen, convert_to_metfile, results_dict_to_csv
from gistools.utils.conversion_tools import get_float

from gistools.tools.calculate_slibaanwas_tool import GetProfielMiddelpunt

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: Meetpunten inpeiling (shapefile)
# 1: Meetpunten uitpeiling (shapefile)
# 2: Folder doelbestand

# input_inpeil = arcpy.GetParameterAsText(0)
# inpuit_uitpeil = arcpy.GetParameterAsText(1)
# output_folder = arcpy.GetParameterAsText(2)

input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
output_folder = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas'

test = GetProfielMiddelpunt(input_inpeil, input_uitpeil)