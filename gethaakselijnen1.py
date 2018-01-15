import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from utils.addresulttodisplay import add_result_to_display

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: lijnenbestand
# 1: puntenbestand
# 2: Vaste waarde voor lengte haakselijn (default_length)
# 3: Veld met lengte haakselijn (length_field)
# 4: Doelbestand voor haakse lijnen

input_fl = arcpy.GetParameterAsText(0)
input_points = arcpy.GetParameterAsText(1)
fixed_length = arcpy.GetParameter(2)
length_field = arcpy.GetParameterAsText(3)
output_file = arcpy.GetParameterAsText(4)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit.shp')
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Lijnen_Bedum_singlepart.shp')
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'TI17034_Trajectenshape_aaenmaas_2017.shp')
# input_points = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit_punten.shp')
# selectie = 'FALSE'
# length_field = None
# fixed_length = 15
# copy_fields = ['HYDRO_CODE', 'DATUM_KM', 'VER_EIND']
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#
# output_file =  os.path.join(test_dir, 'test_haakselijnen.shp')

# Print ontvangen input to console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Puntenbestand = ' + input_points)
arcpy.AddMessage('Lengte haakse lijn uit veld = ' + str(length_field))
arcpy.AddMessage('Lengte haakse lijn vaste waarde = ' + str(fixed_length))
arcpy.AddMessage('Bestandsnaam voor output haakse lijnen = ' + str(output_file))

# Validation of received parameters
if length_field is None and length_field is None:
    raise ValueError('Geen lengte opgegeven')

if fixed_length < 0 and length_field is None:
    raise ValueError('Geen geldige lengte opgegeven')

# Preparation of data types and reading of parameters
arcpy.AddMessage('Bezig met voorbereiden van de data...')

# Fill line collection
collection = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_fl)
fields = arcpy.ListFields(input_fl)
point = arcpy.Point()

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

# Fill point collection
point_col = MemCollection(geometry_type='MultiPoint')
records = []
rows = arcpy.SearchCursor(input_points)
fields = arcpy.ListFields(input_points)
point = arcpy.Point()

for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)

    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                    'properties': properties})

point_col.writerecords(records)

copy_fields = []
for field in fields:
    if field.name.lower() not in ['fid', 'shape']:
        copy_fields.append(field.name.lower())

# Perform tool
haakselijn_col = get_haakselijnen_on_points_on_line(collection,
                                                    point_col,
                                                    copy_fields,
                                                    length_field=length_field,
                                                    default_length=fixed_length)

# Write result tool 'haakselijnen'
arcpy.AddMessage('Bezig met het genereren van het doelbestand met haakse lijnen...')

spatial_reference = arcpy.Describe(input_fl).spatialReference
output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir,
                                                output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_fields:
        arcpy.AddField_management(output_fl, field.name, field.type,
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable,
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

# Haakselijn_col bevat enkel LineStrings, geen MultiLineStrings, nalopen line_parts is dus niet nodig...
for l in haakselijn_col.filter():
    row = dataset.newRow()
    mline = arcpy.Array()
    array = arcpy.Array()
    for p in l['geometry']['coordinates']:
        point.X = p[0]
        point.Y = p[1]
        array.add(point)

    mline.add(array)

    row.Shape = mline

    for field in fields:
        if field.name in copy_fields:
            row.setValue(field.name, l['properties'].get(field.name, None))

    dataset.insertRow(row)

add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')