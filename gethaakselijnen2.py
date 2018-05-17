import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from utils.addresulttodisplay import add_result_to_display

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: lijnenbestand
# 1: Vaste waarde voor afstand (default_distance)
# 2: Veld met afstand (distance_field)
# 3: Maximale representatieve lengte van een profiel (representative_length)
# 4: In elk hydrovak een profiel? (all_lines)
# 5: Vaste waarde voor lengte haakselijn (default_length)
# 6: Veld met lengte haakselijn (length_field)
# 7: Lijst met velden (copy_fields)
# 8: Doelbestand voor haakse lijnen

input_fl = arcpy.GetParameterAsText(0)
fixed_distance = arcpy.GetParameter(1)
distance_field = arcpy.GetParameterAsText(2)
representative_length = arcpy.GetParameter(3)
all_lines = arcpy.GetParameter(4)
fixed_length = arcpy.GetParameter(5)
length_field = arcpy.GetParameterAsText(6)
copy_fields = [str(f) for f in arcpy.GetParameter(7)]
output_file = arcpy.GetParameterAsText(8)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit.shp')
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Lijnen_Bedum_singlepart.shp')
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'TI17034_Trajectenshape_aaenmaas_2017.shp')
# input_points = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit_punten.shp')
# selectie = 'FALSE'
# distance_field = None
# fixed_distance = 10.0
# length_field = None
# fixed_length = 15
# representative_length = True
# copy_fields = ['HYDRO_CODE', 'DATUM_KM', 'VER_EIND']
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#    
# output_file =  os.path.join(test_dir, 'test_haakselijnen.shp')

# Print input to console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Afstand vaste waarde = ' + str(fixed_distance))
arcpy.AddMessage('Afstand uit veld = ' + str(distance_field))
arcpy.AddMessage('Maximale representatieve lengte van een profiel = ' + str(representative_length))
arcpy.AddMessage('In elk hydrovak een profiel = ' + str(all_lines))
arcpy.AddMessage('Lengte haakse lijn vaste waarde = ' + str(fixed_length))
arcpy.AddMessage('Lengte haakse lijn uit veld = ' + str(length_field))
arcpy.AddMessage('Over te nemen velden = ' + str(copy_fields))
arcpy.AddMessage('Bestandsnaam voor output haakse lijnen = ' + str(output_file))

# Validation received parameters
if distance_field is None and fixed_distance is None:
    raise ValueError('Geen afstand opgegeven')
    
if fixed_distance < 0 and distance_field is None:
    raise ValueError('Geen geldige afstand opgegeven')
    
if length_field is None and fixed_length is None:
    raise ValueError('Geen lengte opgegeven')

if fixed_length < 0 and length_field is None:
    raise ValueError('Geen geldige lengte opgegeven')

# Preparation of data types and input
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

# Call tool to create points
arcpy.AddMessage('Bezig met uitvoeren van get_points_on_line...')

point_col = get_points_on_line(collection,
                               copy_fields,
                               distance_field=distance_field,
                               fixed_distance=fixed_distance,
                               max_repr_length=representative_length,
                               all_lines=all_lines)

# Call tool to create haakse lijnen
haakselijn_col = get_haakselijnen_on_points_on_line(collection,
                                                    point_col,
                                                    copy_fields,
                                                    length_field=length_field,
                                                    default_length=fixed_length,
                                                    source="lines")

# Write point results
arcpy.AddMessage('Bezig met het genereren van het doelbestand met punten...')
spatial_reference = arcpy.Describe(input_fl).spatialReference
output_name_points = os.path.basename(output_file).split('.')[0] + '_intersectiepunten'
output_dir_points = os.path.dirname(output_file)

output_fl_points = arcpy.CreateFeatureclass_management(output_dir_points, output_name_points, 'POINT',
                                                       spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_fields and field.name.lower() not in ['id']:
        arcpy.AddField_management(output_fl_points, field.name, field.type,
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable,
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl_points)

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

add_result_to_display(output_fl_points, output_name_points)

# Write line results
arcpy.AddMessage('Bezig met het genereren van het doelbestand met haakse lijnen...')

output_name_haakselijn = os.path.basename(output_file).split('.')[0]
output_dir_haakselijn = os.path.dirname(output_file)

output_fl_haakselijnen = arcpy.CreateFeatureclass_management(output_dir_haakselijn,
                                                             output_name_haakselijn, 'POLYLINE',
                                                             spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_fields:
        arcpy.AddField_management(output_fl_haakselijnen, field.name, field.type, 
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, 
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl_haakselijnen)

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

add_result_to_display(output_fl_haakselijnen, output_name_haakselijn)

arcpy.AddMessage('Gereed')
