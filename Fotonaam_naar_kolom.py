import logging
import os.path
import sys

import arcpy

from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

"""Deze tool kan gebruikt worden voor het verwerken van de foto's uit de collectorapp.
De verschillende namen van de foto's worden elk in een eigen kolom geplaatst. Dit resulteert in een lijst van 
 verschillende kolommen per object. Het resultaat wordt weggeschreven in een .csv bestand.
Het idee is dat dit bestand daarna handmatig gekoppeld wordt aan de InvulGDB, zodat er per object overzichtelijk
is welke foto's er zijn genomen.

input: csv_bestand -> ATTACH tabel met daarin de fotonamen (export uit de GDB van de download van Arcgidonline)
ouitput: cvs_bestand -> hierin het objectid en de verschillende kolommen met elk 1 fotonaam
"""


# Read the parameter values
# 0: Tabel waar de foto's instaan
# 1: Doelmap waar de output-csv wordt weggeschreven

# Obtaining parameters from the user
input_tabel = arcpy.GetParameterAsText(0)
output_file = arcpy.GetParameterAsText(1)

# Send received input to the console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Tabel waar de fotos instaan = ' + input_tabel)
arcpy.AddMessage('Doelbestand waar de csv wordt weggeschreven = ' + output_file)

# Prepare data types and read data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

## Create dict to store the fotonames, shapeids and foto numbers
output_dict = {}
output_dict['names'] = []
output_dict['ids'] = []
output_dict['nrs'] = []
filename = os.path.split(input_tabel)

# Read out the data and store the id and the fotonames in dictionary
with open(input_tabel) as f:
    lines = f.read().splitlines()

for ind, each in enumerate(lines):
    # Assumuption there is a header, so skip the first line
    if ind == 0:
        print 'Header is skipped'
    # For the rest of the lines, take the fotoname and extract the ID and number of the foto
    else:
        info = each.split(';')
        if len(info) < 4:
            print 'Empty row'
            break
        else:
            fotoname = info[4]  # Total name of the foto
            id_shape = fotoname[0:fotoname.find('_')]  # The ID of the shape the foto belongs to
            nr_foto = fotoname[-6:-4]  # The number of the foto
            # Test if the nr is indeed a number, or that part of it is text. example: attachment2.jpg -> 't2'
            try:
                nr_foto = int(nr_foto)  # Yes it is a number
            except:
                nr_foto = int(nr_foto[-1])  # No only the last character is a number
            # Store the values in the output_dict
            output_dict['names'].append(fotoname)
            output_dict['ids'].append(id_shape)
            output_dict['nrs'].append(nr_foto)

# print 'Er is een output gemaakt waarin alles is weggeschreven'
# print 'Nu verder met het maken van de iutput csv'

# Find out how many foto's there maximal at one location are
max_foto = max(output_dict['nrs'])

# Create empty template list for the output, with length max_foto
template_list = [''] * (max_foto + 1)

# Create headerline: id_shape, foto_1, foto_2 etc.
headerline = template_list[:]
headerline[0] = 'id_shape'
for i in range(1, max_foto + 1):
    headerline[i] = 'foto_' + str(i)

## Write output to csv file
pathname_output = output_file
f = open(pathname_output, 'w')
f.write(",".join(headerline) + '\n')

# Get the output sorted per shape-id
unieke_ids = set(output_dict['ids'])

for uni in unieke_ids:
    # store the template for this shape
    shape_output = template_list[:]
    # Get the indices of the shapes with same ind
    index_list = [i for i, x in enumerate(output_dict['ids']) if x == uni]
    # Use this index_list to get all the fotos from this shape
    foto_list = list(output_dict['names'][i] for i in index_list)
    # Fill in the template list
    shape_output[0] = str(uni)
    for t, foto in enumerate(foto_list):
        shape_output[t + 1] = foto

    # Convert outputlist to string and write to csv
    f.write(",".join(shape_output))
    f.write('\n')
f.close()

arcpy.AddMessage('Het output-bestand is gemaakt: ' + output_file)
arcpy.AddMessage('Gereed')
