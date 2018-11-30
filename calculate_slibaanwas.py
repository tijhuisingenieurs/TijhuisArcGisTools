import os.path
import sys
import logging
import arcpy
from utils.arcgis_logging import setup_logging
import arcpy
import time
from utils.addresulttodisplay import add_result_to_display
from gistools.tools.combine_peilingen import combine_peilingen, convert_to_metfile, results_dict_to_csv
from gistools.utils.conversion_tools import get_float

from gistools.tools.calculate_slibaanwas_tool import GetProfielMiddelpunt, Createbuffer,\
    GetSlibaanwas, WriteListtoCollection

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

#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
#input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'


input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_201800216_points.shp'
#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_20170215_kortlang_points.shp'

input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_20170215_points.shp'

input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all\\20180718_IBA_meetjaar_2_points.shp'
input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all\\20181108_IBA_meetjaar_1_points.shp'
output_folder = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all'

# Aanroepen functies voor berekening slib:
point_col_in, point_col_uit, point_col_mid_in, point_col_mid_uit, profiel_namen_in, profiel_namen_uit = \
    GetProfielMiddelpunt(input_inpeil, input_uitpeil)
buffer_mid_in = Createbuffer(point_col_mid_in)
t = time.time()
in_uit_combi, info_list = GetSlibaanwas(point_col_in,point_col_uit,point_col_mid_uit,buffer_mid_in)
elapsed = time.time() - t

print('TIJD: ', elapsed)

# Wegschrijven gegevens in shapefile
WriteListtoCollection(output_folder, in_uit_combi, info_list)
