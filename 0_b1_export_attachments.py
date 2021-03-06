###########################################################################
#################### 0_b1 Exporteer bijlagen naar map #####################
###########################################################################

import os
import arcpy

from arcpy import da

# Read the parameter values
# inTable = './testdata/input/Testdata_watergangen.shp'
# fileLocation = './testdata/output/0_a7_output/

inTable = arcpy.GetParameterAsText(0)
fileLocation = arcpy.GetParameterAsText(1)

with da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'ATTACHMENTID']) as cursor:

    for item in cursor:

        attachment = item[0]

        filenum = "ATT" + str(item[2]) + "_"

        filename = str(item[1])

        open(fileLocation + os.sep + filename, 'wb').write(attachment.tobytes())

        del item

        del filenum

        del filename

        del attachment