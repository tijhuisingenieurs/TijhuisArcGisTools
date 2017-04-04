import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand
# 1: Veld met afstand (distance_field)
# 2: Vaste waarde voor afstand (default_distance)
# 3: Veld met offset afstand aan het begin (min_offset_start_field)
# 4: Vaste waarde voor offset afstand aan het begin (min_default_offset_start)
# 5: Extra punt in restlengte zetten (restlength)
# 6: Lijst met velden (copy_fields)
# 7: Doelbestand voor punten

input_fl = arcpy.GetParameterAsText(0)
distance_veld = arcpy.GetParameterAsText(1)
default_afstand = arcpy.GetParameter(2)
offset_start_veld = arcpy.GetParameter(3)
default_offset_start = arcpy.GetParameter(4)
restlength = arcpy.GetParameter(5)
copy_velden = [str(f) for f in arcpy.GetParameter(6)]
output_file = arcpy.GetParameterAsText(7)


# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#  
# input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Test_kwaliteit.shp')
# selectie = 'FALSE'
# distance_veld = None
# default_afstand = 100.0
# offset_start_veld = None
# default_offset_start = 20.0
# restlength = True
# copy_velden = ['hydro_code', 'datum_km', '[ver_eind]']
#    
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#     
# output_file = os.path.join(test_dir, 'test_punten.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Afstand uit veld = ' + str(distance_veld))
arcpy.AddMessage('Afstand vaste waarde = ' + str(default_afstand))
arcpy.AddMessage('Offset begin uit veld = ' + str(offset_start_veld))
arcpy.AddMessage('Offset begin vaste waarde = ' + str(default_offset_start))
arcpy.AddMessage('Restlengte extra punt geven = ' + str(restlength))
arcpy.AddMessage('Over te nemen velden = ' + str(copy_velden))
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# validatie ontvangen parameters
if distance_veld is None and default_afstand is None:
    raise ValueError('Geen afstand opgegeven')

if default_afstand < 0 and (distance_veld is None or distance_veld == ''):
    raise ValueError('Geen geldige afstand opgegeven')

if default_offset_start < 0 and (offset_start_veld is None or offset_start_veld == ''):
    raise ValueError('Negatieve start offset opgegeven')

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

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
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection.writerecords(records)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_points_on_line...')

point_col = get_points_on_line(collection, 
                               copy_velden, 
                               distance_field=distance_veld,
                               min_default_offset_start=default_offset_start,
                               default_distance=default_afstand,
                               min_offset_start_field=offset_start_veld,
                               use_rest = restlength)

# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_velden:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

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

arcpy.AddMessage('Gereed')
