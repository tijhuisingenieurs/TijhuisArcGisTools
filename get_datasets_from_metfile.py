import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.xml_handler import import_xml_to_memcollection

# Read the parameter values
# 0: Metfile
# 1: Volgorde z-waarden
# 2: Locatie te genereren bestanden

 
# input_fl = arcpy.GetParameterAsText(0)
# zvalues = arcpy.GetParameterAsText(0)
# output_folder = arcpy.GetParameterAsText(1)


# Testwaarden voor test zonder GUI:
import tempfile
import shutil
       
input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Metfile_profielen_generiek.met')
zvalues = 'z1z2'

test_dir = os.path.join(tempfile.gettempdir(), 'import_met_test')
if os.path.exists(test_dir):
    # empty test directory
    shutil.rmtree(test_dir)
os.mkdir(test_dir)
 
output_folder = test_dir           


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Metfile-bestand = ' + input_fl)
arcpy.AddMessage('Volgorde z-waarden = ' + str(zvalues))
arcpy.AddMessage('Bestandsmap voor doelbestanden = ' + str(output_folder))

                                 
# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van xml-handler..')

point_col, line_col, ttlr_col = import_xml_to_memcollection(input_fl, zvalues)

# wegschrijven tool resultaat
output_name = os.path.basename(input_fl).split('.')[0]
output_name_l =(output_name + '_lines')
output_name_p =(output_name + '_points')
output_name_ttlr = (output_name + '_22_points')
output_dir = output_folder

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
# arcpy.AddField_management(output_fl_lines, 'breedte', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'xb_prof', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'yb_prof', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'xe_prof', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'ye_prof', "DOUBLE")

dataset = arcpy.InsertCursor(output_fl_lines)
fields_lines = next(line_col.filter())['properties'].keys()

for l in line_col.filter():
    row = dataset.newRow()
    mline = arcpy.Array()
    array = arcpy.Array()
    for p in l['geometry']['coordinates']:
        point.X = p[0]
        point.Y = p[1]
        array.add(point)

    mline.add(array)

    row.Shape = mline
    
    for field in fields_lines:
        row.setValue(field, l['properties'].get(field, '')) 
    
    dataset.insertRow(row)


arcpy.AddMessage('Bezig met het genereren van het doelbestand met gecorrigeerde meetpunten...')
# spatial_reference = arcpy.spatialReference(28992)

#  specific file name and data
output_fl_points = arcpy.CreateFeatureclass_management(output_dir, output_name_p, 'POINT',
                                                spatial_reference=28992)


dataset = arcpy.InsertCursor(output_fl_points)
fields_points = next(point_col.filter())['properties'].keys()

arcpy.AddField_management(output_fl_points, 'prof_ids', "TEXT")
arcpy.AddField_management(output_fl_points, 'datum', "TEXT")
arcpy.AddField_management(output_fl_points, 'code', "TEXT")
arcpy.AddField_management(output_fl_points, 'tekencode', "TEXT")
arcpy.AddField_management(output_fl_points, 'volgnr', "TEXT")              
# arcpy.AddField_management(output_fl_points, 'afstand', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'x_coord', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'y_coord', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_bk_wp', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_bk_nap', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_ok_wp', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_ok_nap', "DOUBLE")
                    
for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for field in ['prof_ids', 'datum', 'code']:
        row.setValue(field, p['properties'].get(field, '')) 
    
    for field in ['afstand', 'x_coord', 'y_coord', '_bk_wp', '_bk_nap', '_ok_wp', '_ok_nap']:
        value = get_float(p['properties'].get(field, ''))
        row.setValue(field, value)

    dataset.insertRow(row)

  


arcpy.AddMessage('Bezig met het genereren van het doelbestand met 22 punten...')
# spatial_reference = arcpy.spatialReference(28992)

#  specific file name and data
output_name_ttlr = output_name + '_22punten'
output_fl_ttlr = arcpy.CreateFeatureclass_management(output_dir, output_name_ttlr, 'POINT',
                                                spatial_reference=28992)


fields_ttlr = next(ttlr_col.filter())['properties'].keys()

# op volgorde toevoegen en typeren
arcpy.AddField_management(output_fl_ttlr, 'prof_pk', "INTEGER")
arcpy.AddField_management(output_fl_ttlr, 'ids', "TEXT")
arcpy.AddField_management(output_fl_ttlr, 'project_id', "TEXT")
arcpy.AddField_management(output_fl_ttlr, 'code', "TEXT")
# arcpy.AddField_management(output_fl_ttlr, 'afstand', "DOUBLE")

# arcpy.AddField_management(output_fl_ttlr, 'breedte', "DOUBLE")

arcpy.AddField_management(output_fl_ttlr, 'wpeil', "DOUBLE")
arcpy.AddField_management(output_fl_ttlr, 'wpeil_bron', "TEXT")
arcpy.AddField_management(output_fl_ttlr, 'datum', "TEXT")
arcpy.AddField_management(output_fl_ttlr, 'z', "DOUBLE")
arcpy.AddField_management(output_fl_ttlr, 'x_coord', "DOUBLE")
arcpy.AddField_management(output_fl_ttlr, 'y_coord', "DOUBLE")

dataset = arcpy.InsertCursor(output_fl_ttlr)

for p in ttlr_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for field in fields_ttlr:
        row.setValue(field, p['properties'].get(field, '')) 
    

    dataset.insertRow(row)



# add_result_to_display(output_fl_lines, output_name_l)
# add_result_to_display(output_fl_points, output_name_p)
# add_result_to_display(output_fl_ttlr, output_name_ttlr)


print 'Gereed'

