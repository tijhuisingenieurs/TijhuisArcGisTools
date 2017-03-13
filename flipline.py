import sys
import os.path
from collections import OrderedDict

import arcpy
from addresulttodisplay import add_result_to_display


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))


from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import flip_lines

    
# Read the parameter values
# 0: Lijnenbestand
# 2: Doelbestand
input_fl = arcpy.GetParameterAsText(0)
output_file = arcpy.GetParameterAsText(1)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
# 
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit.shp')
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#  
# output_file = os.path.join(test_dir, 'test_flip.shp')


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Doelbestand = ' + str(output_file))


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
arcpy.AddMessage('Bezig met uitvoeren van get_flipped_line...')

flipped_line_col = flip_lines(collection)

# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)


output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POLYLINE', 
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name.lower() not in ['shape', 'fid', 'id']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

for l in flipped_line_col:
    row = dataset.newRow()
    mline = arcpy.Array()
    for line_part in l['geometry']['coordinates']:
        array = arcpy.Array()
        for p in line_part:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)

        mline.add(array)

    row.Shape = mline

    for field in fields:
        if field.name.lower() not in ['shape', 'fid']:
            row.setValue(field.name, l['properties'].get(field.name, None))

    dataset.insertRow(row)       

add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')
