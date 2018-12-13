import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging
import arcpy
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))
logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

from gistools.tools.calculate_slibaanwas_tool import GetProfielMiddelpunt, Createbuffer,\
    GetSlibaanwas, WriteListtoCollection

# Read the parameter values
# 0: Meetpunten inpeiling (shapefile)
# 1: Meetpunten uitpeiling (shapefile)
# 2: Folder doelbestand en bestandsnaam
# 3: afstand waarbinnen een uitpeiling wordt gezocht(buffer radius)
# 4: waarde voor het maximale verschil in breedte toegestaan
# 5: waarde voor het maximale verschil in waterpeil toegestaan

input_inpeil = arcpy.GetParameterAsText(0)
input_uitpeil = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)
zoekafstand = arcpy.GetParameter(3)
tolerantie_breedte = arcpy.GetParameter(4)
tolerantie_wp = arcpy.GetParameter(5)

arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bestand inpeiling = ' + input_inpeil)
arcpy.AddMessage('Bestand uitpeiling = ' + input_uitpeil)
arcpy.AddMessage('Output bestand = ' + output_file)
arcpy.AddMessage('Inlezen data...')

# ------------- Spul om de functie zonder arcgis aan te roepen
# print('Start tool')
# print('Inlezen data...')
#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
#input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_201800216_points.shp'
#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_20170215_kortlang_points.shp'

#input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_20170215_points.shp'

# input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all\\20180718_IBA_meetjaar_2_points.shp'
# input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all\\20181108_IBA_meetjaar_1_points.shp'

# zoekafstand = 5
# input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slib_error_meetjaar2_0101.shp'
# input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slib_error_meetjaar1_0101.shp'
#
# output_folder = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all'
# ------------------

# Aanroepen functies voor berekening slib:
arcpy.AddMessage('Middelpunten genereren...')
point_col_in, point_col_uit, point_col_mid_in, point_col_mid_uit, profiel_namen_in, profiel_namen_uit = \
    GetProfielMiddelpunt(input_inpeil, input_uitpeil)

arcpy.AddMessage('Middelpunten gegenereerd')
arcpy.AddMessage('Buffer creeren...')

buffer_mid_in = Createbuffer(point_col_mid_in, zoekafstand)
arcpy.AddMessage('Buffer gecreeerd')
arcpy.AddMessage('Slibaanwas berekenen...')

t = time.time()
in_uit_combi, info_list = GetSlibaanwas(point_col_in,point_col_uit,point_col_mid_uit,buffer_mid_in,
                                        tolerantie_breedte, tolerantie_wp)
elapsed = time.time() - t
# print('Slibaanwas berekend')
# print('TIJD: ', elapsed)

# Wegschrijven gegevens in shapefile
arcpy.AddMessage('Resultaat in shapefile wegschrijven...')
WriteListtoCollection(output_file, in_uit_combi, info_list)
arcpy.AddMessage('Resultaat weggeschreven')
arcpy.AddMessage('klaar')
