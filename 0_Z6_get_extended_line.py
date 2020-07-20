###########################################################################
####### 0_Z6 Lijn verlengen (extra punten toevoegen aan uiteinden) ########
###########################################################################

import os.path
import sys
import logging
import arcpy

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import get_extended_line   

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

# Read the parameter values
# input_fl = './testdata/input/Testdata_watergangen.shp'
# length_m = 2.0
# length_perc = None
# length_field = None
# length_side = 'einde'
# output_file = './testdata/output/0_z6_output.shp'

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand lijnen = ' + str(input_fl))
arcpy.AddMessage('Verlenging in meters = ' + str(length_m))
arcpy.AddMessage('Verlenging in percentage tov huidige lengte = ' + str(length_perc))
arcpy.AddMessage('Verlenging op basis van nieuwe lengte in veld = ' + str(length_field))
arcpy.AddMessage('Verlenging ten opzicht van zijde = ' + str(length_side))
arcpy.AddMessage('Doelbestand verlengde lijnen = ' + str(output_file))

# validatie ontvangen parameters
target = 'fixed_extension'

if length_m > 0.0 and ((length_perc > 0.0 and length_perc is not None) or (length_field != '' and length_field is not None)):
    raise ValueError('Zowel verlening in meters als, percentage en/of veld opgegeven... Kies 1 methode voor scaling.')

if length_m == None or length_m == 0.0:
    if (length_perc is None or length_perc == 0.0) and (length_field is None or length_field == ''):
        raise ValueError('Geen nieuwe lengte opgegeven')
    
    if length_perc > 0.0 and length_field is not None and length_field != '' :
        raise ValueError('Zowel percentage als veld opgegeven... Kies 1 methode voor scaling.')

test_cursor = arcpy.SearchCursor(input_fl)
for row in test_cursor:
    geom = row.getValue('SHAPE')
    parts = geom.partCount
    if parts > 1:
        raise TypeError('Multipart geometrie aangeboden... tool werkt alleen voor singlepart geometrie')

if length_field != '' and length_field is not None:
    target = 'field'
if length_perc > 0.0 and length_perc is not None:
    target = 'percentage'


# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

if length_side == 'einde':
    extend_point = 'end'
if length_side == 'begin':
    extend_point = 'begin'
if length_side != 'begin' and length_side != 'einde':
    extend_point = 'both'

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

arcpy.AddMessage('Bezig met uitvoeren van get_extended_line...')
line_col = get_extended_line(input_col, target_length_field, extend_point)

# wegschrijven tool resultaat scaled line
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
