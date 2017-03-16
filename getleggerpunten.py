import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import get_leggerprofiel
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand
# 1: id van lijn
# 2: objectnaam
# 3; veld met waterpeil
# 4: veld met waterdiepte
# 5: veld met breedte_wa
# 6: veld met bodemhoogte
# 7: veld met bodembreedte
# 8: veld met talud_l
# 9: veld met talud_r
# 10: veld met peiljaar
# 11: doelbestand

input_fl = arcpy.GetParameterAsText(0)
line_id_field = arcpy.GetParameterAsText(1)
name_field = arcpy.GetParameterAsText(2)
waterpeil_field = arcpy.GetParameterAsText(3)
waterdiepte_field = arcpy.GetParameterAsText(4)
breedte_wa_field = arcpy.GetParameterAsText(5)
bodemhoogte_field = arcpy.GetParameterAsText(6)
bodembreedte_field = arcpy.GetParameterAsText(7)
talud_l_field = arcpy.GetParameterAsText(8)
talud_r_field = arcpy.GetParameterAsText(9)
peiljaar_field = arcpy.GetParameterAsText(10)
output_file = arcpy.GetParameterAsText(11)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
# 
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_legger.shp')
# 
# line_id_field = 'FID'
# name_field = 'Hydro_code'
# waterpeil_field = 'Waterpeil'
# waterdiepte_field = 'NoData'
# breedte_wa_field = 'NoData'
# bodemhoogte_field = 'bodemh'
# bodembreedte_field = 'bodembr'
# talud_l_field = 'talud_l'
# talud_r_field = 'talud_r'
# peiljaar_field = 'jr_gebagrd'
# 
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#    
#     
# output_file =  os.path.join(test_dir, 'test_leggerpunten.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Lijn identificatie veld = ' + line_id_field)
arcpy.AddMessage('Objectnaam veld = ' + name_field)
arcpy.AddMessage('Waterpeil veld  = ' + waterpeil_field)
arcpy.AddMessage('Waterdiepte veld = ' + waterdiepte_field)
arcpy.AddMessage('Waterbreedte veld = ' + breedte_wa_field)
arcpy.AddMessage('Bodemhoogte veld = ' + bodemhoogte_field)
arcpy.AddMessage('Bodembreedte veld = ' + bodembreedte_field)
arcpy.AddMessage('Talud links veld = ' + talud_l_field)
arcpy.AddMessage('Talud rechts veld = ' + talud_r_field)
arcpy.AddMessage('Peiljaar veld = ' + peiljaar_field)
arcpy.AddMessage('Doelbestand = ' + str(output_file))

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
    
    properties['line_id'] = row.getValue(line_id_field)
    properties['name'] = row.getValue(name_field)
    properties['waterpeil'] = row.getValue(waterpeil_field)
    properties['waterdiepte'] = row.getValue(waterdiepte_field)
    properties['breedte_wa'] = row.getValue(breedte_wa_field)
    properties['bodemhoogte'] = row.getValue(bodemhoogte_field)
    properties['bodembreedte'] = row.getValue(bodembreedte_field)
    properties['talud_l'] = row.getValue(talud_l_field)
    properties['talud_r'] = row.getValue(talud_r_field)
    properties['peiljaar'] = str(row.getValue(peiljaar_field)).split('.')[0]
            
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection.writerecords(records)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van de tool...')
legger_point_col = get_leggerprofiel(collection)
    
# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_fl).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)


# add additional fields with output of tool
arcpy.AddField_management(output_fl, 'line_id', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'name', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'puntcode', 'integer', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'z_waarde', 'float', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'volgnr', 'integer', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'afstand', 'float', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'peiljaar', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'L22', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'L22_peil', 'float', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'knik_l', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'knik_l_dpt', 'float', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'knik_r', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'knik_r_dpt', 'float', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'R22', 'string', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'R22_peil', 'float', field_is_nullable=True)


dataset = arcpy.InsertCursor(output_fl)

for p in legger_point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0][0]
    point.Y = p['geometry']['coordinates'][0][1]
    row.Shape = point
    
    for extra in ['name', 'puntcode', 'z_waarde', 'volgnr', 'afstand', 'L22_peil', 'knik_l_dpt',
                   'knik_r_dpt', 'R22_peil'
                  ]:
#         print  'waarde ' + extra + ' = ' + str(p['properties'].get(extra, 'faal'))
        row.setValue(extra, p['properties'].get(extra, None))   
    
    for extra in ['line_id', 'peiljaar', 'L22', 'knik_l', 'knik_r', 'R22'
                  ]:
#         print  'waarde ' + extra + ' = ' + str(p['properties'].get(extra, 'faal'))
        row.setValue(extra, str(p['properties'].get(extra, None)))        
    
    arcpy.AddMessage('Bezig met wegschrijven van profielpunt voor ' + str(p['properties'].get('name', None)))
    
    dataset.insertRow(row)

add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')
