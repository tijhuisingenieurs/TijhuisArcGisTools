import os.path
import sys
import arcpy
import copy
#from ..utils.addresulttodisplay import add_result_to_display

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, 'external'))

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

# Testwaarden voor test zonder GUI:
# input_fl_lines = os.path.join(os.path.dirname(__file__), os.path.pardir, 'test', 'data', 'hdsr_output', 'lines_veldwerkapp.shp')
# input_fl_points_csv = os.path.join(os.path.dirname(__file__), os.path.pardir, 'test', 'data', 'hdsr_output', 'Meetpunten.csv')
# input_fl_points_shape = ""
# output_file_lines = "c:\\tmp\\hdsr21.shp"
# output_file_points = "c:\\tmp\\hdsr22.shp"

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
#spatial_reference = arcpy.spatialReference(28992)

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


# prof_ids afstand

hdsr_points = []
nr = 1
org_points = [p for p in output_point_col.filter()]

last_code = ''

for i, p in enumerate(org_points):
    point = {}
    point['x'] = p['geometry']['coordinates'][0]
    point['y'] = p['geometry']['coordinates'][1]

    point['code'] = 'dp'
    point['profiel'] = format(int(p['properties']['prof_ids']), '04d')
    point['distance'] = p['properties'].get('afstand', -999.0)

    if p['properties']['code'] in ('22L', '22R'):
        point['type'] = 'waterlijn'
        point['z'] = p['properties']['wpeil']
        point['pnt_nr'] = nr
        hdsr_points.append(point)
        nr += 1
    elif p['properties']['code'] == '99' and last_code == '22L':
        point['type'] = 'bagger_en_vastebodem'
        point['z'] = p['properties']['_bk_nap']
        point['pnt_nr'] = nr
        hdsr_points.append(point)
        nxt_bagger_en_vastebodem = False
        nr += 1
    elif p['properties']['code'] == '99' and org_points[i+1]['properties']['code'] == '22R':
        point['type'] = 'bagger_en_vastebodem'
        point['z'] = p['properties']['_bk_nap']
        point['pnt_nr'] = nr
        hdsr_points.append(point)
        nr += 1
    elif p['properties']['code'] == '99':
        point['type'] = 'bagger'
        point['z'] = p['properties']['_bk_nap']
        point['pnt_nr'] = nr
        hdsr_points.append(copy.copy(point))
        nr += 1

        point['type'] = 'vaste_bodem'
        point['z'] = p['properties']['_ok_nap']
        point['pnt_nr'] = nr
        hdsr_points.append(point)
        nr += 1
    elif p['properties']['code'] not in ['1', '2', '3']:
        print("skip punt met code %s" % p['properties']['code'])
        # skip
        pass
    else:
        if p['properties']['code'] == '1':
            point['type'] = 'Maaiveld'
        elif p['properties']['code'] == '2':
            point['type'] = 'Insteek'
        elif p['properties']['code'] == '3':
            point['type'] = 'Beschoeiing'

        point['z'] = p['properties']['_ok_nap']
        point['pnt_nr'] = nr
        hdsr_points.append(point)
        nr += 1

    last_code = p['properties']['code']

arcpy.AddField_management(output_fl_points, 'TYPE', "TEXT")
arcpy.AddField_management(output_fl_points, 'OPMERKING', "TEXT")
arcpy.AddField_management(output_fl_points, 'PNT_NR', "INTEGER")
arcpy.AddField_management(output_fl_points, 'X', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'Y', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'Z', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'CODE', "TEXT")
arcpy.AddField_management(output_fl_points, 'Profiel', "TEXT")
arcpy.AddField_management(output_fl_points, 'wcode', "TEXT")
arcpy.AddField_management(output_fl_points, 'peil', "DOUBLE")
arcpy.AddField_management(output_fl_points, 'distance', "DOUBLE")

dataset = arcpy.InsertCursor(output_fl_points)

for p in hdsr_points:
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['x']
    point.Y = p['y']

    row.Shape = point

    row.setValue("TYPE", p['type'])
    row.setValue("PNT_NR", p['pnt_nr'])
    row.setValue("X", round(p['x'], 4))
    row.setValue("Y", round(p['y'], 4))
    row.setValue("Z", round(p['z'], 2))
    row.setValue("CODE", p['code'])
    row.setValue("Profiel", p['profiel'])
    row.setValue("peil", 0.0)
    row.setValue("distance", round(p['distance'], 2))

    dataset.insertRow(row)

# add_result_to_display(output_fl_lines, output_name_l)
# add_result_to_display(output_fl_points, output_name_p)
# add_result_to_display(output_fl_lines_sp, output_name_sp)

print 'Gereed'
