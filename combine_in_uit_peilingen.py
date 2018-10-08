import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from gistools.tools.combine_peilingen import combine_peilingen, convert_to_metfile, results_dict_to_csv
from gistools.utils.conversion_tools import get_float

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
# 13: Take width waterway from inpeiling or uitpeiling
# 14: Doelbestand voor metfile
# 15: Doelbestand non-scaled uitpeilingen
 
input_inpeilingen = arcpy.GetParameterAsText(0)
order_in = arcpy.GetParameterAsText(1)
loc_in = arcpy.GetParameterAsText(2)
input_uitpeilingen = arcpy.GetParameterAsText(3)
order_uit = arcpy.GetParameterAsText(4)
loc_uit = arcpy.GetParameterAsText(5)
link_table = arcpy.GetParameterAsText(6)
project = arcpy.GetParameterAsText(7)
order = arcpy.GetParameterAsText(8)
scale_threshold = float(arcpy.GetParameter(9))/100
scale_bank_distance = arcpy.GetParameter(10)
level_peiling = arcpy.GetParameterAsText(11)
shore_peiling = arcpy.GetParameterAsText(12)
width_peiling = arcpy.GetParameterAsText(13)
ID_peiling = arcpy.GetParameterAsText(14)
output_file = arcpy.GetParameterAsText(15)
output_unscaled = arcpy.GetParameterAsText(16)

# input_inpeilingen = "K:\Tekeningen Amersfoort\\2018\TI18082 Inmeten baggerprofielen 2017 Wetterskip\Tekening\Bewerkingen\Verwerking\Cluster04\Metfile_Fryslan\TI18082_Metfile_voor_vastebodem.met"
# order_in = "z1z2"
# loc_in = "Eerste plaats"
# input_uitpeilingen = "K:\Projecten\\2018\TI18082 Inmeten baggerprofielen 2017 - WF\Rapport\Cluster04\TI18082_Cluster04_nog_combineren_WIT_Opmaak.met"
# order_uit = "z1z2"
# loc_uit = "Eerste plaats"
# link_table = "K:\Tekeningen Amersfoort\\2018\TI18082 Inmeten baggerprofielen 2017 Wetterskip\Tekening\Bewerkingen\Verwerking\Cluster04\Resultaat_Metfiles\Z1Z2\TI18082_04_Koppeltabel.csv"
# project = "TI18082,Uipeiling_Combi_Cluster04_2018"
# order = "z2z1"
# scale_threshold = 99.0/100.0
# scale_bank_distance = False
# level_peiling = "Uitpeiling"
# shore_peiling = "Uitpeiling"
# width_peiling = "Uitpeiling"
# ID_peiling = "Uitpeiling"
# output_file = "K:\Algemeen\\1_GIS\GEHEIM\Uitpeilingen_ws\TI178082_combi.met"
# output_unscaled = "K:\Algemeen\\1_GIS\GEHEIM\Uitpeilingen_ws\TI18082_nietbehandeldeuitpeilingen.shp"

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
arcpy.AddMessage('Watergang breedte meenemen van = ' + str(width_peiling))
arcpy.AddMessage('Doelbestand metfile = ' + str(output_file))
arcpy.AddMessage('Doelbestand niet behandelde uitpeilingen ' + str(output_unscaled))

# Define name for output results csv
output_name = os.path.basename(output_file).split('.')[0]
output_name_results = output_name + '_processingResults.csv'
output_dir = os.path.dirname(output_file)
results_path = os.path.join(output_dir, output_name_results)

# Process input data
arcpy.AddMessage('Bezig met combineren van de peilingen...')
id_peiling = 1 if ID_peiling == "Uitpeiling" else 0
combined_points, results_list, unscaled_points = combine_peilingen(input_inpeilingen, input_uitpeilingen, order_in,
                                                                   order_uit, loc_in, loc_uit, link_table,
                                                                   width_peiling, id_peiling, scale_threshold,
                                                                   scale_bank_distance)

# Generate metfile
arcpy.AddMessage('Bezig met genereren van metfile...')
results_list = convert_to_metfile(combined_points, project, output_file, results_list, order=order,
                                  level_peiling=level_peiling, shore_peiling=shore_peiling)
results_dict_to_csv(results_list, results_path)

# Generate shapefile with unscaled points
if unscaled_points:
    arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

    output_name = os.path.basename(output_unscaled).split('.')[0]
    output_dir = os.path.dirname(output_unscaled)

    output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                    spatial_reference=28992)

    # Add the fields
    arcpy.AddField_management(output_fl, 'prof_ids', "TEXT")
    arcpy.AddField_management(output_fl, 'datum', "TEXT")
    arcpy.AddField_management(output_fl, 'code', "TEXT")
    arcpy.AddField_management(output_fl, 'tekencode', "TEXT")
    arcpy.AddField_management(output_fl, 'volgnr', "TEXT")
    arcpy.AddField_management(output_fl, 'afstand', "DOUBLE")
    arcpy.AddField_management(output_fl, 'x_coord', "DOUBLE")
    arcpy.AddField_management(output_fl, 'y_coord', "DOUBLE")
    arcpy.AddField_management(output_fl, '_bk_wp', "DOUBLE")
    arcpy.AddField_management(output_fl, '_bk_nap', "DOUBLE")
    arcpy.AddField_management(output_fl, '_ok_wp', "DOUBLE")
    arcpy.AddField_management(output_fl, '_ok_nap', "DOUBLE")

    # Start filling the shapefile with the new points (new geometry and same properties as input file)
    dataset = arcpy.InsertCursor(output_fl)

    for p in unscaled_points.filter():
        arcpy.AddMessage('meetpunt: ' + str(p['properties']['prof_ids']) + ' ' + str(p['properties']['volgnr']))
        arcpy.AddMessage('geometrie: ' + str(p['geometry']['coordinates']))

        point = arcpy.Point()
        point.X = p['geometry']['coordinates'][0]
        point.Y = p['geometry']['coordinates'][1]

        row = dataset.newRow()
        row.Shape = point

        for field in ['prof_ids', 'datum', 'code', 'tekencode']:
            row.setValue(field, p['properties'].get(field, ''))

        for field in ['volgnr', 'afstand', 'x_coord', 'y_coord', '_bk_wp', '_bk_nap', '_ok_wp', '_ok_nap']:
            value = get_float(p['properties'].get(field, ''))
            row.setValue(field, value)

        dataset.insertRow(row)

    # Add results to display
    add_result_to_display(output_fl, output_name)


arcpy.AddMessage('Gereed')
