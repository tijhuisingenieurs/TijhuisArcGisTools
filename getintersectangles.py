import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import get_global_intersect_angles
from utils.addresulttodisplay import add_result_to_display

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: lijnenbestand 1
# 1: lijnenbestand 2
# 2: Doelbestand voor intersectiepunten met hoeken

input_fl1 = arcpy.GetParameterAsText(0)
input_fl2 = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)


# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#  
# input_fl1 = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Hoeken_basislijn.shp')
# input_fl2 = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Hoeken_te_bepalen.shp')
#    
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#     
# output_file = os.path.join(test_dir, 'test_hoeken.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand 1 = ' + input_fl1)
arcpy.AddMessage('Lijnenbestand 2 = ' + input_fl2)
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

collection1 = MemCollection(geometry_type='MultiLinestring')
records1 = []
rows1 = arcpy.SearchCursor(input_fl1)
fields1 = arcpy.ListFields(input_fl1)

collection2 = MemCollection(geometry_type='MultiLinestring')
records2 = []
rows2 = arcpy.SearchCursor(input_fl2)
fields2 = arcpy.ListFields(input_fl2)


point = arcpy.Point()

# vullen collection 1 
for row in rows1:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields1:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records1.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection1.writerecords(records1)

# vullen collection 2 
for row in rows2:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields2:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records2.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection2.writerecords(records2)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_points_on_perc...')

point_col = get_global_intersect_angles(collection1, collection2)

# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_fl1).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl, 'crossangle', 'DOUBLE', 8, 2)

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point
        

    row.setValue('crossangle', p['properties'].get('crossangle', None))        

    dataset.insertRow(row)
 
add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')
