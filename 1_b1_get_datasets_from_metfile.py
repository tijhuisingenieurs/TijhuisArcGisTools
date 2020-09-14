import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.xml_handler import import_xml_to_memcollection
from gistools.utils.conversion_tools import get_float

# Read the parameter values
# 0: Metfile
# 1: Volgorde z-waarden
# 2: Locatie te genereren bestanden


input_fl = arcpy.GetParameterAsText(0)
zvalues = arcpy.GetParameterAsText(1)
id_location = arcpy.GetParameterAsText(2)
output_folder = arcpy.GetParameterAsText(3)
generate_lines = arcpy.GetParameterAsText(4)
generate_22points = arcpy.GetParameterAsText(5)
generate_all_points = arcpy.GetParameterAsText(6)


# Testwaarden voor test zonder GUI:
# input_fl = './testdata/input/Testdata_metfile.met'
# zvalues = 'z2z1'
# id_location = "Tweede plaats"
# generate_lines = 'true'
# generate_22points = 'true'
# generate_all_points = 'true'
# output_folder = './testdata/output/1_b1_output/'


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Metfile-bestand = ' + input_fl)
arcpy.AddMessage('Volgorde z-waarden = ' + str(zvalues))
arcpy.AddMessage('Locatie van profiel ID = ' + str(id_location))
arcpy.AddMessage('Bestandsmap voor doelbestanden = ' + str(output_folder))
arcpy.AddMessage('Te genereren bestanden:')
arcpy.AddMessage( 'Profiellijnen  = ' + str(generate_lines))
arcpy.AddMessage( '22 punten  = ' + str(generate_22points))
arcpy.AddMessage( 'Alle meetpunten  = ' + str(generate_all_points))

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van xml-handler..')

point_col, line_col, ttlr_col, records_errors = import_xml_to_memcollection(input_fl, zvalues, id_location)

# wegschrijven tool resultaat
output_name = os.path.basename(input_fl).split('.')[0]
output_name_l =(output_name + '_lines')
output_name_p =(output_name + '_points')
output_name_ttlr = (output_name + '_22_points')
output_dir = output_folder

if generate_lines == 'true':
    arcpy.AddMessage('Bezig met het genereren van het doelbestand met profiellijnen...')
    # spatial_reference = arcpy.spatialReference(28992)

    point = arcpy.Point()
    output_fl_lines = arcpy.CreateFeatureclass_management(output_dir, output_name_l, 'POLYLINE',
                                                    spatial_reference=28992)

    arcpy.AddField_management(output_fl_lines, 'pk', "TEXT")
    arcpy.AddField_management(output_fl_lines, 'ids', "TEXT")
    arcpy.AddField_management(output_fl_lines, 'project_id', "TEXT")
    arcpy.AddField_management(output_fl_lines, 'wpeil', "DOUBLE")
    arcpy.AddField_management(output_fl_lines, 'datum', "TEXT")
    arcpy.AddField_management(output_fl_lines, 'breedte', "DOUBLE")
    arcpy.AddField_management(output_fl_lines, 'xb_prof', "DOUBLE")
    arcpy.AddField_management(output_fl_lines, 'yb_prof', "DOUBLE")
    arcpy.AddField_management(output_fl_lines, 'xe_prof', "DOUBLE")
    arcpy.AddField_management(output_fl_lines, 'ye_prof', "DOUBLE")

    dataset = arcpy.InsertCursor(output_fl_lines)
    fields_lines = next(line_col.filter())['properties'].keys()

    for l in line_col.filter():
        arcpy.AddMessage('profiel: ' + str(l['properties']['ids']))
        arcpy.AddMessage('geometrie: ' + str(l['geometry']['coordinates']))

        mline = arcpy.Array()
        array = arcpy.Array()
        for p in l['geometry']['coordinates']:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)

        mline.add(array)

        row = dataset.newRow()
        row.Shape = mline

        for field in fields_lines:
            row.setValue(field, l['properties'].get(field, ''))

        dataset.insertRow(row)

    add_result_to_display(output_fl_lines, output_name_l)

if generate_22points == 'true':
    arcpy.AddMessage('Bezig met het genereren van het doelbestand met 22 punten...')
    # spatial_reference = arcpy.spatialReference(28992)

    #  specific file name and data
    output_fl_ttlr = arcpy.CreateFeatureclass_management(output_dir, output_name_ttlr, 'POINT',
                                                    spatial_reference=28992)


    fields_ttlr = next(ttlr_col.filter())['properties'].keys()

    # op volgorde toevoegen en typeren
    arcpy.AddField_management(output_fl_ttlr, 'prof_pk', "INTEGER")
    arcpy.AddField_management(output_fl_ttlr, 'prof_ids', "TEXT")
    arcpy.AddField_management(output_fl_ttlr, 'project_id', "TEXT")
    arcpy.AddField_management(output_fl_ttlr, 'code', "TEXT")
    arcpy.AddField_management(output_fl_ttlr, 'afstand', "DOUBLE")

    arcpy.AddField_management(output_fl_ttlr, 'breedte', "DOUBLE")

    arcpy.AddField_management(output_fl_ttlr, 'wpeil', "DOUBLE")
    arcpy.AddField_management(output_fl_ttlr, 'wpeil_bron', "TEXT")
    arcpy.AddField_management(output_fl_ttlr, 'datum', "TEXT")
    arcpy.AddField_management(output_fl_ttlr, 'z', "DOUBLE")
    arcpy.AddField_management(output_fl_ttlr, 'x_coord', "DOUBLE")
    arcpy.AddField_management(output_fl_ttlr, 'y_coord', "DOUBLE")

    dataset = arcpy.InsertCursor(output_fl_ttlr)

    for p in ttlr_col.filter():
        arcpy.AddMessage('meetpunt: ' + str(p['properties']['prof_ids']) + ' ' + str(p['properties']['code']))
        arcpy.AddMessage('geometrie: ' + str(p['geometry']['coordinates']))

        point = arcpy.Point()
        point.X = p['geometry']['coordinates'][0]
        point.Y = p['geometry']['coordinates'][1]

        row = dataset.newRow()
        row.Shape = point

        for field in fields_ttlr:
            row.setValue(field, p['properties'].get(field, ''))


        dataset.insertRow(row)

    add_result_to_display(output_fl_ttlr, output_name_ttlr)

if generate_all_points == 'true':
    arcpy.AddMessage('Bezig met het genereren van het doelbestand met gecorrigeerde meetpunten...')
    # spatial_reference = arcpy.spatialReference(28992)

    #  specific file name and data
    output_fl_points = arcpy.CreateFeatureclass_management(output_dir, output_name_p, 'POINT',
                                                    spatial_reference=28992)

    fields_points = next(point_col.filter())['properties'].keys()

    # op volgorde toevoegen en typeren
    arcpy.AddField_management(output_fl_points, 'prof_ids', "TEXT")
    arcpy.AddField_management(output_fl_points, 'datum', "TEXT")
    arcpy.AddField_management(output_fl_points, 'code', "TEXT")
    arcpy.AddField_management(output_fl_points, 'tekencode', "TEXT")
    arcpy.AddField_management(output_fl_points, 'volgnr', "TEXT")
    arcpy.AddField_management(output_fl_points, 'afstand', "DOUBLE")
    arcpy.AddField_management(output_fl_points, 'x_coord', "DOUBLE")
    arcpy.AddField_management(output_fl_points, 'y_coord', "DOUBLE")
    arcpy.AddField_management(output_fl_points, '_bk_wp', "DOUBLE")
    arcpy.AddField_management(output_fl_points, '_bk_nap', "DOUBLE")
    arcpy.AddField_management(output_fl_points, '_ok_wp', "DOUBLE")
    arcpy.AddField_management(output_fl_points, '_ok_nap', "DOUBLE")

    dataset = arcpy.InsertCursor(output_fl_points)

    for p in point_col.filter():
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


    add_result_to_display(output_fl_points, output_name_p)



for e in records_errors:
    arcpy.AddMessage('LET OP:  Profiel ' + str(e.get('Profiel')) + ' -> ' + str(e.get('Error')))

arcpy.AddMessage ('Gereed')

