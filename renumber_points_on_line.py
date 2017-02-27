import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import tempfile
import shutil
import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.number_points import number_points_on_line

# Read the parameter values
# 0: lijnenbestand
# 1: Id veld van lijnenbestand
# 2: Marge waarbinnen lijnen gecombineerd zijn
# 3: Uitvoerbestand

input_line_fl = arcpy.GetParameterAsText(0)
input_point_fl = arcpy.GetParameterAsText(1)
line_nr_field = arcpy.GetParameterAsText(2)
line_direction_field = arcpy.GetParameterAsText(3)
point_nr_field = arcpy.GetParameterAsText(4)
output_file = arcpy.GetParameterAsText(5)

# Testwaarden voor test zonder GUI:
# input_line_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'real_line_example.shp')
# input_point_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'points_on_real_line_example.shp')
# line_nr_field = 'nr'
# line_direction_field = 'direction'
# point_nr_field = 'nr'
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
# output_file = os.path.join(test_dir, 'renumbered shape.shp')


# voorbereiden data typen en inlezen data
print 'Bezig met voorbereiden van de data...'

line_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_line_fl)
fields = arcpy.ListFields(input_line_fl)
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

line_col.writerecords(records)

point_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_point_fl)
fields = arcpy.ListFields(input_point_fl)
point = arcpy.Point()

# vullen collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom[0].X, geom[0].Y)},
                    'properties': properties})

point_col.writerecords(records)

# aanroepen tool
print 'Bezig met uitvoeren van get_endpoints..'

number_points_on_line(line_col, point_col, line_nr_field, line_direction_field, point_nr_field)

# wegschrijven tool resultaat
print 'Bezig met het genereren van het doelbestand...'
spatial_reference = arcpy.Describe(input_point_fl).spatialReference


output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl, 'nr', 'integer')

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point

    for field in [point_nr_field]:
        row.setValue(field, p['properties'].get(field, None))

    dataset.insertRow(row)

print 'Gereed'
