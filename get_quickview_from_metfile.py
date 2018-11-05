'''This tool creates a quickview of the location of the profieles in the metfile by reading from a metfile only
the first coordinate. This coordinate is written to a point shapefile'''

import os.path
import sys
import arcpy
import glob

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from utils.addresulttodisplay import add_result_to_display
from gistools.tools.quickview_metfile_locaties import quickview_metfile_locaties
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.xml_handler import import_xml_to_memcollection
from gistools.utils.conversion_tools import get_float

# Read the parameter values
# 0: boolean file of folder input
# 1: path input folder
# 2: path input file
# 3: path output folder

folder_or_file = arcpy.GetParameterAsText(0)
input_file = arcpy.GetParameterAsText(1)
input_folder = arcpy.GetParameterAsText(2)
output_folder = arcpy.GetParameterAsText(3)

arcpy.AddMessage('Input file voor metfile: ' + input_file)
arcpy.AddMessage('Input folder voor meerdere metfiles: ' + input_folder)
arcpy.AddMessage('Output folder: ' + output_folder)

#folder_or_file = False
#input_file = "C:\Users\elma\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\quick_view_metfile\quick_view_metfile.met"
#input_folder = " "
#output_folder = "C:\Users\elma\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\quick_view_metfile"

# folder_or_file = True
# input_file = " "
# input_folder = "C:\Users\elma\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\quick_view_metfile"
# output_folder = "C:\Users\elma\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\quick_view_metfile"

# Check if folder of only 1 metfile is given and make a list of the files
if folder_or_file: # folder with metfiles
    list_metfile_names = glob.glob(input_folder+'\*.met')
    output_name = 'quickview_metfiles'
else: # Just 1 metfile
    list_metfile_names = [input_file]
    output_name = os.path.basename(input_file).split('.')[0] + '_quickview'

# Get memcolection points from metfile met de gegevens uit de metfile erin
point_col = quickview_metfile_locaties(list_metfile_names)

# wegschrijven tool resultaat naar shapefile
# specific file name and data
output_dir = output_folder
output_file = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT', spatial_reference=28992)

# op volgorde fields toevoegen en typeren
arcpy.AddField_management(output_file, 'Metfile', 'TEXT')
arcpy.AddField_management(output_file, 'P_naam', 'TEXT')
arcpy.AddField_management(output_file, 'P_naam_2', 'TEXT')
arcpy.AddField_management(output_file, 'Datum', 'TEXT')
arcpy.AddField_management(output_file, 'x_coord', 'DOUBLE')
arcpy.AddField_management(output_file, 'y_coord', 'DOUBLE')

dataset = arcpy.InsertCursor(output_file)

# Geef de velden weer die aan de keys van de properties zijn
fields = next(point_col.filter())['properties'].keys()

# Vul de shapefile in met de waardes
for p in point_col.ordered_dict:
    row = dataset.newRow()
    # Voeg de coordinaten toe aan het punt
    point = arcpy.Point()
    point.X = point_col.ordered_dict[p]['geometry']['coordinates'][0]
    point.Y = point_col.ordered_dict[p]['geometry']['coordinates'][1]

    # Voeg de properties toe aan de attribuuttable
    row.Shape = point
    for field in fields:
        row.setValue(field, point_col.ordered_dict[p]['properties'].get(field, ''))

    row.setValue('x_coord', point_col.ordered_dict[p]['geometry']['coordinates'][0])
    row.setValue('y_coord', point_col.ordered_dict[p]['geometry']['coordinates'][1])

    dataset.insertRow(row)

add_result_to_display(output_file, output_name)
