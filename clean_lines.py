import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))


import arcpy
from addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.clean import connect_lines

# Read the parameter values
# 0: Lijnenbestand
# 1: Split de lijnen op connecties
# 2: Doelbestand

input_line_fl = arcpy.GetParameterAsText(0)
split_on_connections = arcpy.GetParameter(1)
output_file = arcpy.GetParameterAsText(2)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
# input_line_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'real_line_example.shp')
# split_on_lines = True
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
# output_file = os.path.join(test_dir, 'cleaned.shp')


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
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)

    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                  point in line] for line in geom]},
                    'properties': properties})

line_col.writerecords(records)

# aanroepen tool
print 'Bezig met uitvoeren van cleanen van lijnen'

connect_lines(line_col,
              split_line_at_connection=split_on_connections)

# wegschrijven tool resultaat
print 'Bezig met het genereren van het doelbestand...'
spatial_reference = arcpy.Describe(input_line_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)

# copy fields from input
for field in fields:
    if field.name.lower() not in ['shape', 'fid', 'id']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

# add additional fields with output of tool
arcpy.AddField_management(output_fl, 'link_start', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'link_end', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'link_loc', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'part', 'integer', field_is_nullable=True)

dataset = arcpy.InsertCursor(output_fl)

for l in line_col.filter():
    row = dataset.newRow()

    mline = arcpy.Array()
    for sub_line in l['geometry']['coordinates']:
        array = arcpy.Array()
        for p in sub_line:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)

        mline.add(array)

    row.Shape = mline

    for field in fields:
        if field.name.lower() not in ['shape', 'fid', 'id']:
            row.setValue(field.name, l['properties'].get(field.name, None))

    for extra in ['link_start', 'link_end', 'link_loc']:
        print extra
        print l['properties'].get(extra, [])
        value = ','.join([str(v) for v in l['properties'].get(extra, [])])

        row.setValue(extra, value)

    row.setValue('part', l['properties'].get('part', None))

    dataset.insertRow(row)

add_result_to_display(output_fl, output_name)

print 'Gereed'
