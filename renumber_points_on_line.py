import os.path
import sys
import logging
from collections import OrderedDict
import arcpy
from utils.arcgis_logging import setup_logging
from utils.addresulttodisplay import add_result_to_display

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.collection import MemCollection
from gistools.tools.number_points import number_points_on_line

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: Lijnenbestand
# 1: Puntenbestand
# 2: Uitvoer in nieuw puntenbestand
# 3: Veld met volgorde nummer van lijn
# 4: Veld met lijn richting, negatief getal is tegengesteld aan geometrierichting
# 5: Veld waarin nieuwe volgorde wordt weggeschreven
# 6: Begin nummer voor nummering van punten
# 7: Doelbestand punten

input_line_fl = arcpy.GetParameter(0)
input_point_fl = arcpy.GetParameter(1)
create_new_file = arcpy.GetParameter(2)
line_nr_field = arcpy.GetParameterAsText(3)
line_direction_field = arcpy.GetParameterAsText(4)
point_nr_field = arcpy.GetParameterAsText(5)
start_nr = arcpy.GetParameter(6)
output_file = arcpy.GetParameterAsText(7)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#
# input_line_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'real_line_example.shp')
# input_point_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'points_on_real_line_example.shp')
# create_new_file = True
# line_nr_field = 'nr'
# line_direction_field = 'direction'
# point_nr_field = 'nr'
# start_nr = 1
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
# output_file = os.path.join(test_dir, 'renumbered shape.shp')

if create_new_file:
    if output_file == '':
        log.error('Uitvoerfile is verplicht als er een nieuw bestand moet worden gemaakt')
        raise arcpy.ExecuteError('Uitvoerfile is verplicht als er een nieuw bestand moet worden gemaakt')

# voorbereiden data typen en inlezen data
log.info('Bezig met lezen van lijndata...')
# clear selection of lines, we need all lines
line_selection_set = None

# maak selectie leeg, zodat alle lijnne worden meegenomen
if type(input_line_fl) == arcpy.mapping.Layer:
    log.debug('clear original selection of lines')
    line_selection_set = input_line_fl.getSelectionSet()
    arcpy.SelectLayerByAttribute_management(input_line_fl, "CLEAR_SELECTION")

line_col = MemCollection(geometry_type='MultiLinestring')
records = []
line_cursor = arcpy.SearchCursor(input_line_fl)
fields = arcpy.ListFields(input_line_fl)
point = arcpy.Point()

# vullen collection
for row in line_cursor:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                  point in line] for line in geom]},
                    'properties': properties})

line_col.writerecords(records)

# re-set original selection
if line_selection_set is not None and type(input_line_fl) == arcpy.mapping.Layer:
    log.debug('re-set original selection of lines')
    input_line_fl.setSelectionSet('NEW', line_selection_set)


log.info('Bezig met de puntdata...')

point_selection_set = None

if create_new_file:
    log.info('Kopieer puntdata naar doelbestand...')
    if type(input_point_fl) == arcpy.mapping.Layer:
        input_name = input_point_fl.dataSource
    else:
        input_name = input_point_fl

    arcpy.CopyFeatures_management(input_name, output_file)
    lyr = arcpy.mapping.Layer(output_file)

    if type(input_point_fl) == arcpy.mapping.Layer:
        point_selection_set = input_point_fl.getSelectionSet()
        lyr.setSelectionSet('NEW', point_selection_set)
else:
    lyr = input_point_fl

log.info('Bezig met de puntdata inlezen...')

# neem selectie over
if type(lyr) == arcpy.mapping.Layer:
    point_selection_set = lyr.getSelectionSet()
    arcpy.SelectLayerByAttribute_management(lyr, "CLEAR_SELECTION")

point_col = MemCollection(geometry_type='Point')
records = []
cursor = arcpy.SearchCursor(lyr)
fields = arcpy.ListFields(lyr)
point = arcpy.Point()

oid_fieldname = arcpy.ListFields(lyr, "", "OID")[0].name

# vullen collection
for row in cursor:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()

    selected = False
    if point_selection_set is None:
        selected = True
    else:
        oid = row.getValue(oid_fieldname)
        if oid in point_selection_set:
            selected = True

    for field in fields:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                    'properties': properties,
                    'selected': selected})

point_col.writerecords(records)

# aanroepen tool
log.info('Bezig met uitvoeren van tool...')

point_col = number_points_on_line(line_col, point_col, line_nr_field, line_direction_field, point_nr_field, start_nr)

# wegschrijven tool resultaat
log.info('Bezig met updaten van puntbestand...')

point_dict = dict(((point['properties'][oid_fieldname], point) for point in point_col))

cursor = arcpy.UpdateCursor(lyr)

for row in cursor:
    point = point_dict[row.getValue(oid_fieldname)]
    log.info(point['properties'])

    row.setValue(point_nr_field, point['properties'][point_nr_field])
    cursor.updateRow(row)

# re set selection
if type(lyr) == arcpy.mapping.Layer and point_selection_set is not None:
    input_point_fl.setSelectionSet('NEW', point_selection_set)

if create_new_file or type(lyr) != arcpy.mapping.Layer:
    output_name = os.path.basename(output_file).split('.')[0]
    add_result_to_display(lyr, output_name)

log.info('Gereed')
