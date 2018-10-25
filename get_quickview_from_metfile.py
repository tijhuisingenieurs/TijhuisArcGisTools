'''This tool creates a quickview of the location of the profieles in the metfile by reading from a metfile only
the first coordinate. This coordinate is written to a point shapefile'''

import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
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

# folder_or_file = arcpy.GetParameterAsText(0)
# input_file = arcpy.GetParameterAsText(1)
# input_folder = arcpy.GetParameterAsText(2)
# output_folder = arcpy.GetParameterAsText(3)

# arcpy.AddMessage(folder_or_file)
# arcpy.AddMessage(input_file)
# arcpy.AddMessage(input_folder)
# arcpy.AddMessage(output_folder)

folder_or_file = False
input_file = "C:\Users\elma\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\quick_view_metfile\quick_view_metfile.met"
input_folder = " "
output_folder = "C:\Users\elma\Documents\GitHub\TijhuisArcGisTools\external\gistools\\test\data\quick_view_metfile"


# Check if folder of only 1 metfile is given and make a list of the files
if folder_or_file: # folder with methfiles
    list_metfile_names = os.listdir(input_folder)
    output_name = 'quick_view_metfiles'
else: # Just 1 metfile
    list_metfile_names = [input_file]
    output_name = os.path.basename(input_file).split('.')[0] + 'nieuw1'

# Get memcolection points from metfile
point_col = quickview_metfile_locaties(list_metfile_names)

# wegschrijven tool resultaat naar shapefile
output_dir = output_folder

#  specific file name and data
output_file = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT', spatial_reference=28992)

arcpy.AddMessage(point_col)
arcpy.AddMessage(output_file)


# op volgorde fileds toevoegen en typeren
arcpy.AddField_management(output_file, 'Metfile', "TEXT")
arcpy.AddField_management(output_file, 'P_naam', "TEXT")
arcpy.AddField_management(output_file, 'P_naam_2', "TEXT")
arcpy.AddField_management(output_file, 'Datum', "TEXT")
arcpy.AddField_management(output_file, 'x_coord', "DOUBLE")
arcpy.AddField_management(output_file, 'y_coord', "DOUBLE")

dataset = arcpy.InsertCursor(output_file)

arcpy.AddMessage(output_file)
arcpy.AddMessage(dataset)

fields = next(point_col.filter())['properties'].keys()

for p in fields.filter():
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row = dataset.newRow()
    row.Shape = point

    for field in fields:
        row.setValue(field, p['properties'].get(field, ''))

    dataset.insertRow(row)

add_result_to_display(output_file, output_name)