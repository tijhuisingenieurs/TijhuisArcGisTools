###########################################################################
####################### 0_a3 Snap punten op lijnen ########################
###########################################################################

import logging
import os.path
import sys
import arcpy

from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.collection import MemCollection
from gistools.tools.snap_points_to_line import snap_points_to_line

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: lijnenbestand
# 1: puntenbestand
# 2: Doelbestand voor snapped punten
# 3: Tolerantie
# 4: Unsnapped punten behouden

# Obtaining parameters from the user
input_lines = arcpy.GetParameterAsText(0)
input_points = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)
tolerance = arcpy.GetParameter(3)
keep_unsnapped_points = arcpy.GetParameter(4)

# Test script without ArcMAP
# input_lines = './testdata/input/Testdata_watergangen.shp'
# input_points = './testdata/input/Testdata_snap_punten_op_lijn.shp'
# output_file = './testdata/output/0_a3_output.shp'
# tolerance = 10.0
# keep_unsnapped_points = True

# Send received input to the console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand lijnen = ' + input_lines)
arcpy.AddMessage('Bronbestand punten = ' + input_points)
arcpy.AddMessage('Doelbestand snapped punten = ' + output_file)
arcpy.AddMessage('Tolerantie = ' + str(tolerance))
arcpy.AddMessage('Unsnapped punten behouden = ' + str(keep_unsnapped_points))

# Prepare data types and read data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

# Initialize line collection
line_col = MemCollection(geometry_type='MultiLinestring')
records1 = []
rows1 = arcpy.SearchCursor(input_lines)
fields1 = arcpy.ListFields(input_lines)
point = arcpy.Point()

# Fill the line collection
for row in rows1:
    geom = row.getValue('SHAPE')
    properties = {}
    for field in fields1:
        if field.name.lower() != 'shape':
            if isinstance(field.name, unicode):
                key = field.name.encode('utf-8')
            else:
                key = field.name
            if isinstance(row.getValue(field.name), unicode):
                value = row.getValue(field.name).encode('utf-8')
            else:
                value = row.getValue(field.name)
            properties[key] = value

    records1.append({'geometry': {'type': 'MultiLineString',
                                  'coordinates': [[(point.X, point.Y) for
                                                   point in line] for line in geom]},
                     'properties': properties})

line_col.writerecords(records1)

# Initialize point collection
point_col = MemCollection(geometry_type='MultiPoint')
records2 = []
rows2 = arcpy.SearchCursor(input_points)
fields2 = arcpy.ListFields(input_points)
point = arcpy.Point()

oid_fieldname = fields2[0].name

# Fill the point collection
for row in rows2:
    geom = row.getValue('SHAPE')
    properties = {}
    for field in fields2:
        if field.name.lower() != 'shape':
            if isinstance(field.name, unicode):
                key = field.name.encode('utf-8')
            else:
                key = field.name
            if isinstance(row.getValue(field.name), unicode):
                value = row.getValue(field.name).encode('utf-8')
            else:
                value = row.getValue(field.name)
            properties[key] = value

    records2.append({'geometry': {'type': 'Point',
                                  'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                     'properties': properties})

point_col.writerecords(records2)

# Perform the snap function
arcpy.AddMessage('Bezig met het snappen van de punten...')
snapped_points_col = snap_points_to_line(line_col, point_col, tolerance, keep_unsnapped_points)

# Write results, create a new shapefile
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')
spatial_reference = arcpy.Describe(input_points).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

# Add the fields from the input points to the new shapefile (excluding ID and geometry fields)
for field in fields2:
    if field.editable and field.baseName.lower() not in ['shape', 'id', 'fid']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required,
                                  field.domain)

# Start filling the shapefile with the new points (new geometry and same properties as input file)
dataset = arcpy.InsertCursor(output_fl)

for p in snapped_points_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point

    for field in fields2:
        if field.editable and field.baseName.lower() not in ['shape', 'fid']:
            row.setValue(field.name, p['properties'].get(field.name, None))

    dataset.insertRow(row)

# Add results to display
add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')
