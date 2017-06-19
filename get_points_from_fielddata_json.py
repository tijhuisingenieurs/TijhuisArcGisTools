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
print 'Bezig met uitvoeren van json_handler..'

point_col, project_dict, profile_dict = fielddata_to_memcollection(input_fl)

# wegschrijven tool resultaat

print 'Bezig met het genereren van het doelbestand...'
# spatial_reference = arcpy.spatialReference(28992)


output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=28992)


keys = point_col[0]['properties'].keys()

for key in ['profiel', 'volgnr', 'ids', 'code', 'method']:
    arcpy.AddField_management(output_fl, key, "TEXT")
for key in ['z', 'accuracy'] :
    arcpy.AddField_management(output_fl, key, "float")

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for key in ['profiel', 'volgnr', 'ids', 'code', 'method', 'z', 'accuracy']:
        row.setValue(key, p['properties'].get(key, None))
                
    dataset.insertRow(row)

# add_result_to_display(output_fl, output_name)

# genereren csv data
print 'Bezig met het genereren van csv bestanden...'

project_csv = os.path.join(output_dir, (output_name +'_project.csv'))
with open(project_csv, 'wb') as csvfile1:
    
    fieldnames = ['project_id', 'project']
    writer = csv.DictWriter(csvfile1, fieldnames=fieldnames)
    
    writer.writeheader()
    for project_id in project_dict:
        writer.writerow({'project_id': project_id, 'project': project_dict[project_id]})


profiel_csv = os.path.join(output_dir,(output_name + '_profiel.csv'))
with open(profiel_csv, 'wb') as csvfile2:
    
    fieldnames = ['pro_id', 'profiel', 'project']
    writer = csv.DictWriter(csvfile2, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in profile_dict:
        writer.writerow({'pro_id': row ,'profiel': profile_dict[row]['profiel'], 'project': profile_dict[row]['project']})

print 'Gereed'
