import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_perc
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand
# 1: Veld met percentage (perc_field)
# 2: Vaste waarde voor percentage (default_perc)
# 3: Lijst met velden (copy_fields)
# 4: Doelbestand voor punten

input_fl = arcpy.GetParameterAsText(0)
percentage_veld = arcpy.GetParameterAsText(1)
default_percentage = arcpy.GetParameter(2)
copy_velden = [str(f) for f in arcpy.GetParameter(3)]
output_file = arcpy.GetParameterAsText(4)


# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#  
# input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Test_kwaliteit.shp')
# selectie = 'FALSE'
# percentage_veld = None
# default_percentage = 10.0
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
arcpy.AddMessage('Percentage uit veld = ' + str(percentage_veld))
arcpy.AddMessage('Percentage vaste waarde = ' + str(default_percentage))
arcpy.AddMessage('Over te nemen velden = ' + str(copy_velden))
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# validatie ontvangen parameters
if percentage_veld is None and default_percentage is None:
    raise ValueError('Geen afstand opgegeven')

if default_percentage < 0 and (percentage_veld is None or percentage_veld == ''):
    raise ValueError('Geen geldige afstand opgegeven')

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
arcpy.AddMessage('Bezig met uitvoeren van get_points_on_perc...')

point_col = get_points_on_perc(collection, 
                               copy_velden, 
                               perc_field=percentage_veld,
                               default_perc=default_percentage)

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
