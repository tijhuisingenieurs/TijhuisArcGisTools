import os.path
import sys
import arcpy
from utils.addresulttodisplay import add_result_to_display

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.collection import MemCollection
from gistools.tools.profile_point_type import update_profile_point_type
from gistools.utils.conversion_tools import get_float

# Read the parameter values
# 0: Bronbestand puntdata (shape)
# 1: Doelbestand voor punten

input_fl_points_shape = arcpy.GetParameterAsText(0)
output_file_points = arcpy.GetParameterAsText(1)
method = arcpy.GetParameterAsText(2)

# input_fl_points_shape = "C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_3c_correctcodes\Eline\TI17127_Deel1_Aangepast_GIS_points.shp"
# output_file_points = "C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_3c_correctcodes\correctCodes_Testfiles.shp"
# method = "Waternet"
#input_fl_points_shape = "C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_3c_correctcodes\TI17061_06_Amstelveen\TI17061_06_Amstelveen.shp"
#output_file_points = "C:\Users\eline\Documents\Algemeen\GIS\Tooltesting\TestData\Tool_3c_correctcodes\correctCodes_Testfiles_Amstelveen.shp"
# input_fl_points_shape = "c:\\tmp\\t11.shp"
# output_file_points = "c:\\tmp\\t15.shp"

# if os.path.isfile(singepartfile):
#     os.remove(singepartfile)
#     os.remove(singepartfile_xml)


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bronbestand metingen in shape = ' + input_fl_points_shape)
arcpy.AddMessage('Doelbestand gecorrigeerde metingen shape = ' + output_file_points)
arcpy.AddMessage('Methode = ' + method)


arcpy.AddMessage('Bezig met voorbereiden van de data...')

# vullen collection punten
arcpy.AddMessage('Bezig met vullen punten collection...')

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

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_veldwerk_output_shapes..')


output_point_col = update_profile_point_type(input_point_col, method)

# wegschrijven tool resultaat
output_name_p = os.path.basename(output_file_points).split('.')[0]
output_dir_p = os.path.dirname(output_file_points)

arcpy.AddMessage('Bezig met het genereren van het doelbestand met gecorrigeerde meetpunten...')
# spatial_reference = arcpy.spatialReference(28992)

#  specific file name and data
output_fl_points = arcpy.CreateFeatureclass_management(output_dir_p, output_name_p, 'POINT',
                                                       spatial_reference=28992)

# fields_points = next(output_point_col.filter())['properties'].keys()

arcpy.AddField_management(output_fl_points, 'prof_ids', "TEXT")
arcpy.AddField_management(output_fl_points, 'datum', "TEXT")
arcpy.AddField_management(output_fl_points, 'code', "TEXT")
arcpy.AddField_management(output_fl_points, 'sub_code', "TEXT")
arcpy.AddField_management(output_fl_points, 'code_oud', "TEXT")
arcpy.AddField_management(output_fl_points, 'tekencode', "TEXT") 
arcpy.AddField_management(output_fl_points, 'afstand', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'x_coord', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'y_coord', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_bk_wp', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_bk_nap', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_ok_wp', "DOUBLE")
arcpy.AddField_management(output_fl_points, '_ok_nap', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'opm', "TEXT")

dataset = arcpy.InsertCursor(output_fl_points)
                   
for p in output_point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    for field in ['prof_ids', 'datum', 'code', 'sub_code', 'code_oud', 'tekencode', 'opm']:
        row.setValue(field, p['properties'].get(field, '')) 
    
    for field in ['afstand', 'x_coord', 'y_coord', '_bk_wp', '_bk_nap', '_ok_wp', '_ok_nap']:
        value = get_float(p['properties'].get(field, -9999))
        row.setValue(field, value)

    dataset.insertRow(row)

add_result_to_display(output_fl_points, output_name_p)

print 'Gereed'
