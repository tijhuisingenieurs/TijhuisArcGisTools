import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging
import random

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from gistools.tools.combine_peilingen import combine_peilingen, convert_to_metfile, results_dict_to_csv

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: Metfile inpeilingen
# 1: Volgorde slib-vaste bodem inpeiling
# 2: Locatie uniek profiel-ID inpeiling
# 3: Metfile uitpeilingen
# 4: Volgorde slib-vaste bodem uitpeiling
# 5: Locatie uniek profiel-ID uitpeiling
# 6: Link tabel
# 7: Project naam
# 8: Volgorde slib-vaste bodem
# 9: Schaaldrempel
# 10: Oeverpunten meeschalen
# 11: Take waterlevel from inpeiling or uitpeiling
# 12: Take shore points from inpeiling or uitpeiling
# 13: Doelbestand voor metfile
 
input_inpeilingen = arcpy.GetParameterAsText(0)
order_in = arcpy.GetParameterAsText(1)
loc_in = arcpy.GetParameterAsText(2)
input_uitpeilingen = arcpy.GetParameterAsText(3)
order_uit = arcpy.GetParameterAsText(4)
loc_uit = arcpy.GetParameterAsText(5)
link_table = arcpy.GetParameterAsText(6)
project = arcpy.GetParameterAsText(7)
order = arcpy.GetParameterAsText(8)
scale_threshold = arcpy.GetParameter(9)/100
scale_bank_distance = arcpy.GetParameter(10)
level_peiling = arcpy.GetParameterAsText(11)
shore_peiling = arcpy.GetParameterAsText(12)
output_file = arcpy.GetParameterAsText(13)

# input_inpeilingen = "K:\Tekeningen Amersfoort\\2018\TI18082 Inmeten baggerprofielen 2017 Wetterskip\Tekening\Bewerkingen\Data_mug\Metingen Cluster 22 metfiles\In\817001 Cluster 22 geleverd 18012010.met"
# order_in = "z2z1"
# loc_in = "Eerste plaats"
# input_uitpeilingen = "K:\Tekeningen Amersfoort\\2018\TI18082 Inmeten baggerprofielen 2017 Wetterskip\Tekening\Bewerkingen\Data_mug\Metingen Cluster 22 metfiles\Uit\Uit_H11047.22_METfile_2009.met"
# order_uit = "z2z1"
# loc_uit = "Tweede plaats"
# link_table = "K:\Tekeningen Amersfoort\\2018\TI18082 Inmeten baggerprofielen 2017 Wetterskip\Tekening\Bewerkingen\Data_mug\link_tabel.csv"
# project = "Project,test"
# order = "z2z1"
# scale_threshold = 0.05
# scale_bank_distance = False
# level_peiling = "Inpeiling"
# shore_peiling = "Inpeiling"
# output_file = "K:\Tekeningen Amersfoort\\2018\TI18082 Inmeten baggerprofielen 2017 Wetterskip\Tekening\Bewerkingen\Data_mug\TI18082_gecombineerdemetfile_geleverdeData.met"

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Metfile inpeilingen = ' + str(input_inpeilingen))
arcpy.AddMessage('Volgorde slib inpeiling = ' + order_in)
arcpy.AddMessage('Plaats uniek profiel-ID inpeiling = ' + loc_in)
arcpy.AddMessage('Metfile uitpeilingen = ' + str(input_uitpeilingen))
arcpy.AddMessage('Volgorde slib uitpeiling = ' + order_uit)
arcpy.AddMessage('Plaats uniek profiel-ID uitpeiling = ' + loc_uit)
arcpy.AddMessage('Link tabel = ' + str(link_table))
arcpy.AddMessage('Project = ' + str(project))
arcpy.AddMessage('Volgorde slib doelbestand metfile = ' + order)
arcpy.AddMessage('Schaaldrempel = ' + str(scale_threshold))
arcpy.AddMessage('Oevers meeschalen? = ' + str(scale_bank_distance))
arcpy.AddMessage('Waterpeil meenemen van = ' + level_peiling)
arcpy.AddMessage('Oevers meenemen van = ' + shore_peiling)
arcpy.AddMessage('Doelbestand metfile = ' + str(output_file))

# Define name for output results csv
output_name = os.path.basename(output_file).split('.')[0]
output_name_results = output_name + '_processingResults.csv'
output_dir = os.path.dirname(output_file)
results_path = os.path.join(output_dir, output_name_results)

# Process input data
arcpy.AddMessage('Bezig met combineren van de peilingen...')
combined_points, results_list = combine_peilingen(input_inpeilingen, input_uitpeilingen, order_in, order_uit, loc_in,
                                                  loc_uit, link_table, scale_threshold, scale_bank_distance)

# Generate metfile
arcpy.AddMessage('Bezig met genereren van metfile...')
results_list = convert_to_metfile(combined_points, project, output_file, results_list, order=order,
                                  level_peiling=level_peiling, shore_peiling=shore_peiling)
results_dict_to_csv(results_list, results_path)


# ## --------- TEMP ---------- ##
# file_name = "gecombineerde_punten_{0}".format(random.randint(0, 100))
# output_points = arcpy.CreateFeatureclass_management("C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_d3_uitpeilingentool",
#                                                     file_name, 'POINT', spatial_reference=28992)
#
# # op volgorde toevoegen en typeren
# arcpy.AddField_management(output_points, 'prof_ids', "TEXT")
# arcpy.AddField_management(output_points, 'datum', "TEXT")
# arcpy.AddField_management(output_points, 'code', "TEXT")
# arcpy.AddField_management(output_points, 'tekencode', "TEXT")
# arcpy.AddField_management(output_points, 'volgnr', "TEXT")
# arcpy.AddField_management(output_points, 'afstand', "DOUBLE")
# arcpy.AddField_management(output_points, 'x_coord', "DOUBLE")
# arcpy.AddField_management(output_points, 'y_coord', "DOUBLE")
# arcpy.AddField_management(output_points, '_bk_wp', "DOUBLE")
# arcpy.AddField_management(output_points, '_bk_nap', "DOUBLE")
# arcpy.AddField_management(output_points, '_ok_wp', "DOUBLE")
# arcpy.AddField_management(output_points, '_ok_nap', "DOUBLE")
# arcpy.AddField_management(output_points, 'uit_bk_nap', "DOUBLE")
# arcpy.AddField_management(output_points, 'uit_ok_nap', "DOUBLE")
#
# dataset = arcpy.InsertCursor(output_points)
#
# for p in combined_points.filter():
#     arcpy.AddMessage('meetpunt: ' + str(p['properties']['prof_ids']) + ' ' + str(p['properties']['volgnr']))
#     arcpy.AddMessage('geometrie: ' + str(p['geometry']['coordinates']))
#
#     point = arcpy.Point()
#     point.X = p['geometry']['coordinates'][0]
#     point.Y = p['geometry']['coordinates'][1]
#
#     row = dataset.newRow()
#     row.Shape = point
#
#     for field in ['prof_ids', 'datum', 'code', 'tekencode']:
#         row.setValue(field, p['properties'].get(field, ''))
#
#     for field in ['volgnr', 'afstand', 'x_coord', 'y_coord', '_bk_wp', '_bk_nap', '_ok_wp', '_ok_nap', 'uit_bk_nap',
#                   'uit_ok_nap']:
#         value = get_float(p['properties'].get(field, ''))
#         row.setValue(field, value)
#
#     dataset.insertRow(row)

#add_result_to_display(output_points, "gecombineerde_punten")

arcpy.AddMessage('Gereed')
