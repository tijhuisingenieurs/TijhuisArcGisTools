import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand
# 1: Vaste waarde voor afstand (default_distance)
# 2: Veld met afstand (distance_field)
# 3: Maximale representative lengte (representative_length)
# 4: Veld met maximale representatieve lengte (representative_field)
# 4: Punt in elk hydrovak (all_lines)
# 5: Lijst met velden (copy_fields)
# 6: Doelbestand voor punten

input_fl = arcpy.GetParameterAsText(0)
fixed_distance = arcpy.GetParameter(1)
distance_field = arcpy.GetParameterAsText(2)
representative_length = arcpy.GetParameter(3)
representative_field = arcpy.GetParameterAsText(4)
all_lines = arcpy.GetParameter(5)
copy_fields = [str(f) for f in arcpy.GetParameter(6)]
output_file = arcpy.GetParameterAsText(7)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#
# input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Test_kwaliteit.shp')
# selectie = 'FALSE'
# distance_field = None
# fixed_distance = 100.0
# restlength = True
#
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#
# output_file = os.path.join(test_dir, 'test_punten.shp')

# Testwaarden voor test zonder GUI:
# input_fl = "C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_a3_puntenoplijnenafstand\\test_line.shp"
# selectie = 'FALSE'
# distance_field = None
# fixed_distance = 50
# representative_length = 75
#
# test_dir = "C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_a3_puntenoplijnenafstand"
# output_file = os.path.join(test_dir, 'test_punten.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Afstand vaste waarde = ' + str(fixed_distance))
arcpy.AddMessage('Afstand uit veld = ' + str(distance_field))
arcpy.AddMessage('Maximale representatieve lengte = ' + str(representative_length))
arcpy.AddMessage('Representatieve lengte uit veld = ' + str(representative_field))
arcpy.AddMessage('Over te nemen velden = ' + str(copy_fields))
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# validatie ontvangen parameters
if distance_field is None and fixed_distance is None:
    raise ValueError('Geen afstand opgegeven')

if fixed_distance <= 0 and (distance_field is None or distance_field == ''):
    raise ValueError('Geen geldige afstand opgegeven. Afstand: ' + fixed_distance)

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

collection = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_fl)
fields = arcpy.ListFields(input_fl)
point = arcpy.Point()

# vullen collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection.writerecords(records)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_points_on_line...')

point_col = get_points_on_line(collection,
                               copy_fields,
                               distance_field=distance_field,
                               fixed_distance=fixed_distance,
                               max_repr_length=representative_length,
                               rep_field=representative_field,
                               all_lines=all_lines)

# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_fields:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point
        
    for field in fields:
        if field.name in copy_fields:
            row.setValue(field.name, p['properties'].get(field.name, None))        

    dataset.insertRow(row)
 
add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')
