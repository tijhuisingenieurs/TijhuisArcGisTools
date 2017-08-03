import os.path
import sys
import logging
import arcpy

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import get_scaled_line   

# Read the parameter values
# 0: Lijnenbestand
# 1: Verlenging in meters
# 2: Verlenging in % huidige lengte
# 3: Veld met nieuwe lengte
# 4: Te verlengen zijde
# 5: Doelbestand

input_fl = arcpy.GetParameterAsText(0)
length_m = arcpy.GetParameter(1)
length_perc = arcpy.GetParameter(2)
length_field = arcpy.GetParameterAsText(3)
length_side = arcpy.GetParameterAsText(4)
output_file = arcpy.GetParameterAsText(5)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#     
# length_m = 2.0
# length_perc = None
# length_field = None
# length_side = 'einde'
#    
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit.shp')
# create_new_file = True
# test_dir = os.path.join(tempfile.gettempdir(), 'lengte_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#   
# output_file = os.path.join(test_dir, 'test_verlengd.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand lijnen = ' + str(input_fl))
arcpy.AddMessage('Verlenging in meters = ' + str(length_m))
arcpy.AddMessage('Verlenging in percentage tov huidige lengte = ' + str(length_perc))
arcpy.AddMessage('Verlenging op basis van nieuwe lengte in veld = ' + str(length_field))
arcpy.AddMessage('Verlenging ten opzicht van zijde = ' + str(length_field))
arcpy.AddMessage('Doelbestand verlengde lijnen = ' + str(output_file))

# validatie ontvangen parameters
target = 'fixed_extension'

if length_m <> 0.0 and ((length_perc <> 0.0 and length_perc is not None) or (length_field <> '' and length_field is not None)):
    raise ValueError('Zowel verlening in meters als, percentage en/of veld opgegeven... Kies 1 methode voor scaling.')

elif length_m == None or length_m == 0.0:
    if (length_perc is None or length_perc == 0.0) and (length_field is None or length_field == ''):
        raise ValueError('Geen nieuwe lengte opgegeven')
    
    if length_perc <> 0.0 and length_field is not None and length_field <> '' :
        raise ValueError('Zowel percentage als veld opgegeven... Kies 1 methode voor scaling.')

elif length_field <> '' and length_field is not None:
    target = 'field'
elif length_perc <> 0.0 and length_perc is not None:
    target = 'percentage'
else:
    target = 'fixed_extension'

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

if length_side == 'einde':
    scale_point_perc = 0
elif length_side == 'begin':
    scale_point_perc = 1
else:
    scale_point_perc = 0.5
    
# arcpy.AddMessage('Omzetten bronbestand lijnen naar singel part shape...')
# input_dir_sp = os.path.dirname(output_file)
# input_name_sp = os.path.basename(input_fl).split('.')[0]
# input_fl_sp = arcpy.MultipartToSinglepart_management(input_fl, os.path.join(input_dir_sp,input_name_sp + '_sp' ))

input_fl_sp = input_fl

input_col = MemCollection(geometry_type='Linestring')
records = []
rows = arcpy.SearchCursor(input_fl_sp)
fields = arcpy.ListFields(input_fl_sp)
point = arcpy.Point()

# vullen collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
    
    if target == 'fixed_extension':
        properties['new_length'] = geom.length + length_m
        target_length_field = 'new_length'
        
    elif target == 'percentage':
        properties['new_length'] = geom.length * (1 + (length_perc/100))
        target_length_field = 'new_length'
    else:
        target_length_field = str(length_field)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

input_col.writerecords(records)

arcpy.AddMessage('Bezig met uitvoeren van get_scaled_line...')
line_col = get_scaled_line(input_col, target_length_field, scale_point_perc)

# wegschrijven tool resultaat haakselijnen
arcpy.AddMessage('Bezig met het genereren van het doelbestand met verlengde lijnen...')

spatial_reference = arcpy.Describe(input_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, 
                                                 output_name, 'POLYLINE', 
                                                 spatial_reference=spatial_reference)

for field in fields:
    if field.name.lower() not in ['shape', 'id', 'fid']:
        arcpy.AddField_management(output_fl, field.name, field.type, 
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, 
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

# Haakselijn_col bevat enkel LineStrings, geen MultiLineStrings, nalopen line_parts is dus niet nodig...
for l in line_col.filter():
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
        if field.name.lower() not in ['shape', 'id', 'fid']:
            row.setValue(field.name, l['properties'].get(field.name, None))
    
    dataset.insertRow(row)

add_result_to_display(output_fl, output_name) 

arcpy.AddMessage('Gereed')