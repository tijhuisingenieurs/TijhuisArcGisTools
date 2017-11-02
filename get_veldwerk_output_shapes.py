import os.path
import sys
import arcpy
from utils.addresulttodisplay import add_result_to_display

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.collection import MemCollection
from gistools.tools.create_veldwerk_output_shapes import create_fieldwork_output_shapes
from gistools.utils.csv_handler import import_csv_to_memcollection
from gistools.utils.conversion_tools import get_float

# Read the parameter values
# 0: Bronbestand lijnen
# 1: Bronbestand puntdata (csv)
# 2: Bronbestand puntdata (shape)
# 3: Doelbestand voor lijnen
# 4: Doelbestand voor punten

input_fl_lines = arcpy.GetParameterAsText(0)
input_fl_points_csv = arcpy.GetParameterAsText(1)
input_fl_points_shape = arcpy.GetParameterAsText(2)
output_file_lines = arcpy.GetParameterAsText(3)
output_file_points = arcpy.GetParameterAsText(4)

# input_fl_lines = "C:\\werk\\P2017\\2017.01 - Ondersteuning Tijhuis\\aangeleverd\\invoer bugfix #96\\TI17141_20170831_lines.shp"
# input_fl_points_csv = "C:\\werk\\P2017\\2017.01 - Ondersteuning Tijhuis\\aangeleverd\\invoer bugfix #96\\TI17141_20170831_metingen_BEWERKT.csv"
# input_fl_points_shape = ""
# output_file_lines = "c:\\tmp\\t10.shp"
# output_file_points = "c:\\tmp\\t11.shp"
#
# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#      
# input_fl_lines = os.path.join(os.path.dirname(__file__), 'test', 'data', 'test_toolc_profielen.shp')
#      
# input_fl_points_csv = os.path.join(os.path.dirname(__file__), 'test', 'data', 'test_toolc_metingen.csv')
#  
# input_fl_points_shape = ''
#       
# # input_fl_points_csv = ''
# # input_fl_points_shape = os.path.join(os.path.dirname(__file__), 'test', 'data', 'test_toolc_metingen.shp')
#       
#       
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#                
# output_file_lines = os.path.join(test_dir, 'corrected_lines_toolc.shp')
# output_file_points = os.path.join(test_dir, 'corrected_points_toolc.shp')
# 
# test_dir_sp = os.path.dirname(input_fl_lines)
# test_name_sp = os.path.basename(input_fl_lines).split('.')[0]
# singepartfile = os.path.join(test_dir_sp, test_name_sp + '_sp.shp' )
# singepartfile_xml = os.path.join(test_dir_sp, test_name_sp + '_sp.shp.xml' )
# 
# if os.path.isfile(singepartfile):
#     os.remove(singepartfile)
#     os.remove(singepartfile_xml)

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand profiel lijnen = ' + input_fl_lines)
arcpy.AddMessage('Bronbestand metingen in csv = ' + input_fl_points_csv)
arcpy.AddMessage('Bronbestand metingen in shape = ' + input_fl_points_shape)
arcpy.AddMessage('Doelbestand gecorrigeerde profiel lijnen = ' + output_file_lines)
arcpy.AddMessage('Doelbestand gecorrigeerde metingen shape = ' + output_file_points)

# validatie ontvangen parameters
if input_fl_points_csv is None and input_fl_points_shape is None:
    raise ValueError('Geen brondata met meetpunten opgegeven')

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

arcpy.AddMessage('Omzetten bronbestand profiel lijnen naar singel part shape...')
output_dir_sp = os.path.dirname(output_file_lines)

output_name_sp = os.path.basename(output_file_lines).split('.')[0]
output_fl_lines_sp = arcpy.MultipartToSinglepart_management(
    input_fl_lines,
    os.path.join(output_dir_sp, output_name_sp + '_sp'))

input_line_col = MemCollection(geometry_type='MultiLineString')
records1 = []
rows1 = arcpy.SearchCursor(output_fl_lines_sp)
fields1 = arcpy.ListFields(output_fl_lines_sp)
point = arcpy.Point()

# vullen collection lijnen
arcpy.AddMessage('Bezig met vullen lijnen collection...')
for row in rows1:
    geom = row.getValue('SHAPE')
    properties = {}
    for field in fields1:
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

    records1.append({'geometry': {'type': 'MultiLineString',
                                  'coordinates': [[(point.X, point.Y) for
                                                   point in line] for line in geom]},
                     'properties': properties})

input_line_col.writerecords(records1)

# vullen collection punten
arcpy.AddMessage('Bezig met vullen punten collection...')
if input_fl_points_csv != '':
    input_point_col = import_csv_to_memcollection(input_fl_points_csv)
elif input_fl_points_shape != '':
    input_point_col = MemCollection(geometry_type='MultiPoint')
    records2 = []
    rows2 = arcpy.SearchCursor(input_fl_points_shape)
    fields2 = arcpy.ListFields(input_fl_points_shape)
    
    point = arcpy.Point()
    
    # vullen collection 
    for row in rows2:
        geom = row.getValue('SHAPE')
        properties = {}
        for field in fields2:
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

        records2.append({'geometry': {'type': 'Point',
                                      'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                         'properties': properties})
    
    input_point_col.writerecords(records2)
else:
    # todo: raise warning
    exit(-1)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_veldwerk_output_shapes..')

output_line_col, output_point_col = create_fieldwork_output_shapes(input_line_col, input_point_col)

# wegschrijven tool resultaat
output_name_l = os.path.basename(output_file_lines).split('.')[0]
output_dir_l = os.path.dirname(output_file_lines)

output_name_p = os.path.basename(output_file_points).split('.')[0]
output_dir_p = os.path.dirname(output_file_points)

arcpy.AddMessage('Bezig met het genereren van het doelbestand met gecorrigeerde profiellijnen...')
# spatial_reference = arcpy.spatialReference(28992)

point = arcpy.Point()
output_fl_lines = arcpy.CreateFeatureclass_management(output_dir_l, output_name_l, 'POLYLINE',
                                                      spatial_reference=28992)
       
arcpy.AddField_management(output_fl_lines, 'pk', "TEXT")
arcpy.AddField_management(output_fl_lines, 'ids', "TEXT")
arcpy.AddField_management(output_fl_lines, 'project_id', "TEXT")
arcpy.AddField_management(output_fl_lines, 'proj_name', "TEXT")
arcpy.AddField_management(output_fl_lines, 'opm', "TEXT")
arcpy.AddField_management(output_fl_lines, 'wpeil', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'datum', "TEXT")
arcpy.AddField_management(output_fl_lines, 'breedte', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'xb_prof', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'yb_prof', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'xe_prof', "DOUBLE")
arcpy.AddField_management(output_fl_lines, 'ye_prof', "DOUBLE")

dataset = arcpy.InsertCursor(output_fl_lines)
fields_lines = next(output_line_col.filter())['properties'].keys()

for l in output_line_col.filter():
    row = dataset.newRow()
    mline = arcpy.Array()
    array = arcpy.Array()
    for p in l['geometry']['coordinates']:
        point.X = p[0]
        point.Y = p[1]
        array.add(point)

    mline.add(array)

    row.Shape = mline
    
    for field in fields_lines:
        value = l['properties'].get(field, None)
        if value is None:
            value = -9999
        row.setValue(field, value) 
    
    dataset.insertRow(row)

arcpy.AddMessage('Bezig met het genereren van het doelbestand met gecorrigeerde meetpunten...')
# spatial_reference = arcpy.spatialReference(28992)

#  specific file name and data
output_fl_points = arcpy.CreateFeatureclass_management(output_dir_p, output_name_p, 'POINT',
                                                       spatial_reference=28992)

# fields_points = next(output_point_col.filter())['properties'].keys()

arcpy.AddField_management(output_fl_points, 'prof_ids', "TEXT")
arcpy.AddField_management(output_fl_points, 'datum', "TEXT")
arcpy.AddField_management(output_fl_points, 'code', "TEXT")              
arcpy.AddField_management(output_fl_points, 'tekencode', "TEXT") 
arcpy.AddField_management(output_fl_points, 'afstand', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'x_coord', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'y_coord', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_bk_wp', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_bk_nap', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_ok_wp', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_ok_nap', "DOUBLE")

dataset = arcpy.InsertCursor(output_fl_points)
                   
for p in output_point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for field in ['prof_ids', 'datum', 'code', 'tekencode']:
        row.setValue(field, p['properties'].get(field, '')) 
    
    for field in ['afstand', 'x_coord', 'y_coord', '_bk_wp', '_bk_nap', '_ok_wp', '_ok_nap']:
        value = get_float(p['properties'].get(field, None))
        if value is None:
            value = -9999
        row.setValue(field, value)

    dataset.insertRow(row)

add_result_to_display(output_fl_lines, output_name_l)
add_result_to_display(output_fl_points, output_name_p)
add_result_to_display(output_fl_lines_sp, output_name_sp)

print 'Gereed'
