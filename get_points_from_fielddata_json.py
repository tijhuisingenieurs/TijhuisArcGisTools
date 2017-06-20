import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.json_handler import fielddata_to_memcollection

# Read the parameter values
# 0: JSON bestand met velddata
# 1: Doelbestand voor punten

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

point_col, project_dict, profile_dict, json_dict = fielddata_to_memcollection(input_fl)

# wegschrijven tool resultaat

arcpy.AddMessage('Bezig met het genereren van het doelbestand...')
# spatial_reference = arcpy.spatialReference(28992)


output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=28992)


keys = point_col[0]['properties'].keys()

for key in ['pro_id', 'profiel', 'volgnr', 'project', 'datetime', 'code',  'method']:
    arcpy.AddField_management(output_fl, key, "TEXT")
for key in ['z', 'accuracy', 'distance'] :
    arcpy.AddField_management(output_fl, key, "DOUBLE")

arcpy.AddField_management(output_fl, 'x_coord', "DOUBLE")
arcpy.AddField_management(output_fl, 'y_coord', "DOUBLE")
arcpy.AddField_management(output_fl, 'polelength', "TEXT")  
arcpy.AddField_management(output_fl, 'lonelength', "TEXT")  
arcpy.AddField_management(output_fl, 'alt_acc', "TEXT")  
arcpy.AddField_management(output_fl, 'dis_source', "TEXT") 
arcpy.AddField_management(output_fl, 'dis_acc', "TEXT")
arcpy.AddField_management(output_fl, 'lowerlevel', "TEXT")  
arcpy.AddField_management(output_fl, 'low_lv_src', "TEXT")  
arcpy.AddField_management(output_fl, 'low_lv_acc', "TEXT")  
arcpy.AddField_management(output_fl, 'low_lv_unt', "TEXT")  
arcpy.AddField_management(output_fl, 'upperlevel', "TEXT")  
arcpy.AddField_management(output_fl, 'upp_lv_src', "TEXT")  
arcpy.AddField_management(output_fl, 'upp_lv_acc', "TEXT")  
arcpy.AddField_management(output_fl, 'upp_lv_unt', "TEXT") 
       

dataset = arcpy.InsertCursor(output_fl)


for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for key in ['pro_id', 'profiel', 'volgnr', 'project', 'datetime', 'code', 'method', 'distance', 'z', 'accuracy']:
        row.setValue(key, p['properties'].get(key, None))
    
    # distance gaat nog niet goed -> komt er als geheel getal uit, ongeacht keuze type veld...
    
    x_coord = round(point.X,3)
    y_coord = round(point.Y,3)
    
    arcpy.AddMessage('Coordinates: ' + str(x_coord) + '...' + str(y_coord))
    
    row.setValue('x_coord', x_coord)
    row.setValue('y_coord', y_coord)
    row.setValue('polelength',p['properties'].get('pole_length', None))
    row.setValue('lonelength',p['properties'].get('l_one_length', None))    
    row.setValue('alt_acc',p['properties'].get('altitude_accuracy', None))
    row.setValue('dis_source',p['properties'].get('distance_source', None))
    row.setValue('dis_acc',p['properties'].get('distance_accuracy', None))
    row.setValue('lowerlevel',p['properties'].get('lower_level', None))    
    row.setValue('low_lv_src',p['properties'].get('lower_level_source', None))
    row.setValue('low_lv_acc',p['properties'].get('lower_level_accuracy', None))
    row.setValue('low_lv_unt',p['properties'].get('lower_level_unit', None))
    row.setValue('upperlevel',p['properties'].get('upper_level', None))
    row.setValue('upp_lv_src',p['properties'].get('upper_level_source', None))
    row.setValue('upp_lv_acc',p['properties'].get('upper_level_accuracy', None))
    row.setValue('upp_lv_unt',p['properties'].get('upper_level_unit', None))
    
    
    dataset.insertRow(row)

# add_result_to_display(output_fl, output_name)


        

print 'Gereed'
