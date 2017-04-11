import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_midpoints

# Read the parameter values
# 0: Lijnenbestand
# 1: Id veld van lijnenbestand
# 2: Lijst met velden (copy_fields)
# 3: Doelbestand

input_fl = arcpy.GetParameterAsText(0)
copy_velden = [str(f) for f in arcpy.GetParameter(1)]
output_file = arcpy.GetParameterAsText(2)

# Testwaarden voor test zonder GUI:
# input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Test_kwaliteit.shp')
# copy_velden = ['hydro_code', 'datum_km', '[ver_eind]']
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#     
# output_file = os.path.join(test_dir, 'test_midpunten.shp')


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Over te nemen velden = ' + str(copy_velden))
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# voorbereiden data typen en inlezen data
print 'Bezig met voorbereiden van de data...'

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
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                  point in line] for line in geom]},
                    'properties': properties})

collection.writerecords(records)

# aanroepen tool
print 'Bezig met uitvoeren van get_midpoints..'

point_col = get_midpoints(collection, copy_velden)

# wegschrijven tool resultaat
print 'Bezig met het genereren van het doelbestand...'
spatial_reference = arcpy.Describe(input_fl).spatialReference


output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_velden:
        arcpy.AddField_management(output_fl, field.name, field.type, 
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, 
                                  field.required, field.domain)
        
dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for field in fields:
        if field.name in copy_velden:
            row.setValue(field.name, p['properties'].get(field.name, None))
            
    dataset.insertRow(row)

add_result_to_display(output_fl, output_name)

print 'Gereed'
