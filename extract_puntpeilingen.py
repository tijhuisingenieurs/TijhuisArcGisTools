import logging
import os.path
import sys

import arcpy

from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))
from gistools.utils.collection import MemCollection
from gistools.tools.extract_puntpeilingen import extract_puntpeilingen

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

# ------------------------- TEST WITHOUT GUI ---------------------------
# input_points = "K:\Algemeen\\1_GIS\GEHEIM\Puntpeilingen_naar_metfile\TI18070_Leusden_Puntpeiling_voor_metfile.shp"
# reeks = "Leusden, Puntpeilingen"
# output_file = "K:\Algemeen\\1_GIS\GEHEIM\Puntpeilingen_naar_metfile\TI18070_Leusden_metfile.met"

# -------------------------------------------------------------------------

# Obtaining parameters from the user
input_points = arcpy.GetParameterAsText(0)
reeks = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)

# Send received input to the console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand punten = ' + input_points)
arcpy.AddMessage('Doelbestand snapped punten = ' + output_file)

# Prepare data types and read data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

# Initialize point collection
point_col = MemCollection(geometry_type='MultiPoint')
records = []
rows = arcpy.SearchCursor(input_points)
fields = arcpy.ListFields(input_points)
point = arcpy.Point()

oid_fieldname = fields[0].name

# Fill the point collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = {}
    for field in fields:
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

    records.append({'geometry': {'type': 'Point',
                                  'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                     'properties': properties})

point_col.writerecords(records)

extract_puntpeilingen(point_col, output_file, reeks)

arcpy.AddMessage('Gereed')
