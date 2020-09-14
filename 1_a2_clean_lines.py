import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
import logging
from utils.arcgis_logging import setup_logging

from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.clean import connect_lines

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: Lijnenbestand
# 1: Split de lijnen op connecties
# 2: Buffer (around vertex in m)
# 3: Doelbestand

input_line_fl = arcpy.GetParameterAsText(0)
split_on_connections = arcpy.GetParameter(1)
buffer_value = arcpy.GetParameter(2)
output_file = arcpy.GetParameterAsText(3)

# Read the parameter values
# input_line_fl = './testdata/input/Testdata_watergangen.shp'
# split_on_connections = True
# buffer_value = 2
# output_file = './testdata/output/1_a2.shp'

# voorbereiden data typen en inlezen data
log.info('Bezig met voorbereiden van de data...')

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
log.info('Bezig met uitvoeren van cleanen van lijnen')

arcpy.AddMessage('Bezig met uitvoeren van cleanen van lijnen')

new_lines = connect_lines(line_col, buffer_value,
              split_line_at_connection=split_on_connections)

# wegschrijven tool resultaat

log.info('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_line_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)

# copy fields from input
for field in fields:
    if field.editable and field.type.lower() not in ['geometry']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

# add additional fields with output of tool
arcpy.AddField_management(output_fl, 'part', 'integer', field_is_nullable=True)

dataset = arcpy.InsertCursor(output_fl)

for l in new_lines:
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
        if field.editable and field.type.lower() not in ['geometry']:
            log.debug("field: %s, type: %s, editable: %s, value: %s",
                      field.name,
                      field.type,
                      field.editable,
                      l['properties'].get(field.name, None))
            row.setValue(field.name, l['properties'].get(field.name, field.defaultValue))

    row.setValue('part', l['properties'].get('part', None))

    dataset.insertRow(row)

arcpy.DeleteField_management(output_file, ["Id"])

add_result_to_display(output_fl, output_name)

log.info('Gereed')

