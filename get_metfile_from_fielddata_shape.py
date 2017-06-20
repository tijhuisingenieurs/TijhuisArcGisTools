import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.metfile_generator import export_points_to_metfile

# Read the parameter values
# 0: shapefile met velddata als punten
# 1: Doelbestand voor metfile

# input_fl = arcpy.GetParameterAsText(0)
# output_file = arcpy.GetParameterAsText(1)

# Testwaarden voor test zonder GUI:
import tempfile
import shutil
 
input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'metfile_punten.shp')
test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
if os.path.exists(test_dir):
    # empty test directory
    shutil.rmtree(test_dir)
os.mkdir(test_dir)
      
output_file = os.path.join(test_dir, 'test_metfile.csv')


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Shapefile = ' + input_fl)
arcpy.AddMessage('Doelbestand metfile = ' + str(output_file))


# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met lezen van puntdata...')

point_col = MemCollection(geometry_type='Point')
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

    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                    'properties': properties})

point_col.writerecords(records)

# Genereren metfile
arcpy.AddMessage('Bezig met genereren van metfile...')

metfile = export_points_to_metfile(point_col, output_file)

arcpy.AddMessage('Gereed')
