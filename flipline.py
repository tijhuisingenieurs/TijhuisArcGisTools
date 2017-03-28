import os.path
import sys
import logging
import arcpy
from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.geometry import TMultiLineString

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)
    
# Read the parameter values
# 0: Lijnenbestand
# 1: Nieuw bestand maken (boolean)
# 2: Doelbestand
input_fl = arcpy.GetParameter(0)
create_new_file = arcpy.GetParameter(1)
output_file = arcpy.GetParameterAsText(2)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
# 
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit.shp')
# create_new_file = True
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#  
# output_file = os.path.join(test_dir, 'test_flip.shp')

# Print ontvangen input naar console
log.info('Ontvangen parameters:')
log.info('Lijnenbestand = %s', str(input_fl))
log.info('Nieuw bestand maken = %s', str(create_new_file))
log.info('Doelbestand = %s', str(output_file))

if create_new_file:
    if output_file == '':
        log.error('Uitvoerfile is verplicht als er een nieuw bestand moet worden gemaakt')
        raise arcpy.ExecuteError('Uitvoerfile is verplicht als er een nieuw bestand moet worden gemaakt')

# voorbereiden data typen en inlezen data
log.info('Bezig met voorbereiden van de data...')

if create_new_file:
    log.info('Bezig met het kopieren naar het doelbestand...')
    if type(input_fl) == arcpy.mapping.Layer:
        input_name = input_fl.dataSource
    else:
        input_name = input_fl

    arcpy.CopyFeatures_management(input_name, output_file)
    lyr = arcpy.mapping.Layer(output_file)

    selection_set = input_fl.getSelectionSet()
    lyr.setSelectionSet('NEW', selection_set)
else:
    lyr = input_fl

log.info('Bezig met uitvoeren van line_flip en update bestand...')
# only takes selection
cursor = arcpy.UpdateCursor(lyr, ['SHAPE'])

for row in cursor:
    geom = row.getValue('SHAPE')
    line = TMultiLineString([[(point.X, point.Y) for
                              point in line] for line in geom])
    line.get_flipped_line()

    mline = arcpy.Array()
    for line_part in line.get_flipped_line():
        array = arcpy.Array()
        for p in line_part:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)

        mline.add(array)
    row.setValue('SHAPE', mline)
    cursor.updateRow(row)

# nieuwe file of geupdate laag die niet uit layers is geselecteerd toevoegen aan arcgis lagen
if create_new_file or type(lyr) != arcpy.mapping.Layer:
    output_name = os.path.basename(output_file).split('.')[0]
    add_result_to_display(lyr, output_name)

log.info('Gereed')
