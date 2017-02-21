import sys
import os.path
from collections import OrderedDict

import arcpy
from .addresulttodisplay import add_result_to_display


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))


from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import flip_lines

    
# Read the parameter values
# 0: lijnenbestand
# 1: gebruik alleen geselecteerde features (boolean)
# 3: Doelmap voor doelbestand
# 4: Doelbestand voor punten

# input_fl = arcpy.GetParameterAsText(0)
# selectie = arcpy.GetParameter(1)
# output_dir = arcpy.GetParameterAsText(2)
# output_name = arcpy.GetParameterAsText(3)

# Testwaarden voor test zonder GUI:
input_fl = 'C:\\Users\\annemieke\\Desktop\\TIJDELIJK\\1. GIS zaken\\Test_kwaliteit.shp'
selectie = 'FALSE'
output_dir = 'C:\\Users\\annemieke\\Desktop\\TIJDELIJK\\1. GIS zaken\\'
output_name = 'test_flipped_line'

# Print ontvangen input naar console
print 'Ontvangen parameters:'
print 'Lijnenbestand = ', input_fl
print 'Gebruik selectie = ', str(selectie)
print 'Bestandslocatie voor output = ', str(output_dir)
print 'Bestandsnaam voor output = ', str(output_name)


# voorbereiden data typen en inlezen data
print 'Bezig met voorbereiden van de data...'

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
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection.writerecords(records)

# aanroepen tool
print 'Bezig met uitvoeren van get_flipped_line...'

flipped_line = flip_lines(collection)

# wegschrijven tool resultaat
print 'Bezig met het genereren van het doelbestand...'
spatial_reference = arcpy.Describe(input_fl).spatialReference

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POLYLINE', 
                                                spatial_reference=spatial_reference)

# ToDo: velden ophalen uit output collection op basis van copy_fields
for field in fields:
    if field.name.lower() not in ['shape', 'fid', 'id']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

for record in records:
    row = dataset.newRow()
    mline = arcpy.Array()
    for line_part in record['geometry']['coordinates']:
        array = arcpy.Array()
        for p in line_part:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)

        mline.add(array)

    row.Shape = mline
    # arcpy.geometries.Polyline(line, spatial_reference)

    for field in fields:
        if field.name.lower() not in ['shape', 'fid', 'id']:
            row.setValue(field.name, record['properties'].get(field.name, None))

    dataset.insertRow(row)       

display_name = output_name
add_result_to_display(output_fl, display_name)
    
print 'Gereed'
