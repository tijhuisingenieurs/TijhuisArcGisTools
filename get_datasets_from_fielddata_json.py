import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.json_handler import fielddata_to_memcollections
from gistools.utils.csv_generator import export_memcollection_to_csv

# Read the parameter values
# 0: JSON bestand met velddata
# 1: Doelbestand voor lijnen

# input_fl = arcpy.GetParameterAsText(0)
# output_file = arcpy.GetParameterAsText(1)



# Testwaarden voor test zonder GUI:
import tempfile
import shutil
 
input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'projectdata.json')
test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
if os.path.exists(test_dir):
    # empty test directory
    shutil.rmtree(test_dir)
os.mkdir(test_dir)
      
output_file = os.path.join(test_dir, 'test_json.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('JSON-bestand = ' + input_fl)
arcpy.AddMessage('Doelbestand = ' + str(output_file))


# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van json_handler..')

point_col, line_col, ttlr_col = fielddata_to_memcollections(input_fl)

# wegschrijven tool resultaat
output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

arcpy.AddMessage('Bezig met het genereren van het doelbestand profiellijnen...')
# spatial_reference = arcpy.spatialReference(28992)

#  specific file name and data
output_name_lines = output_name + '_lines'
output_fl_lines = arcpy.CreateFeatureclass_management(output_dir, output_name_lines, 'POLYLINE',
                                                spatial_reference=28992)


arcpy.AddField_management(output_fl_lines, 'pk', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'project', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'ids', "TEXT")
arcpy.AddField_management(output_fl_lines, 'wpeil', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'wpeil_bron', "TEXT")
arcpy.AddField_management(output_fl_lines, 'hpeil', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'lpeil', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'lpeil_afw', "TEXT")
arcpy.AddField_management(output_fl_lines, 'rpeil', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'rpeil_afw', "TEXT")
arcpy.AddField_management(output_fl_lines, 'opm', "TEXT")
arcpy.AddField_management(output_fl_lines, 'geom_bron', "TEXT")

arcpy.AddField_management(output_fl_lines, 'gps_width ', "TEXT")
arcpy.AddField_management(output_fl_lines, 'h_width ', "TEXT")

arcpy.AddField_management(output_fl_lines, 'aantal_1', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'aantal_22L', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'aantal_99', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'aantal_22R', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'aantal_2', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'aantal_gps', "INTEGER")
arcpy.AddField_management(output_fl_lines, 'aantal_hand', "INTEGER")

arcpy.AddField_management(output_fl_lines, 'min_z_afw', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'gem_z_afw', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'max_z_afw', "DOUBLE")

arcpy.AddField_management(output_fl_lines, 'methode', "TEXT")  
arcpy.AddField_management(output_fl_lines, 'datum', "TEXT")  
arcpy.AddField_management(output_fl_lines, 'min_datumt', "TEXT") 
arcpy.AddField_management(output_fl_lines, 'max_datumt', "TEXT") 
arcpy.AddField_management(output_fl_lines, 'min_l1_len', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'max_l1_len', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'min_stok', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'max_stok', "DOUBLE")
       

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
        row.setValue(field, l['properties'].get(field, 99999)) 
    
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

dataset = arcpy.InsertCursor(output_fl_ttlr)

for p in ttlr_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for field in fields_ttlr:
        row.setValue(field, l['properties'].get(field, 99999)) 
    

    dataset.insertRow(row)


arcpy.AddMessage('Bezig met het genereren van het csv-bestand met metingen...')

output_name_meting = output_name + '_metingen.csv'
csv_metingen = export_memcollection_to_csv(point_col, output_name_meting)


# add_result_to_display(output_fl_lines, output_name_lines)
# add_result_to_display(output_fl_ttlr, output_name_ttlr)

        

print 'Gereed'
