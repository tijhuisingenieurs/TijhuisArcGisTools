import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy


def add_result_to_display(result, display_name):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = mxd.activeDataFrame
    arcpy.env.overwriteOutput = True
    tempLayer = display_name
    arcpy.MakeFeatureLayer_management(result,tempLayer)   
    addLayer = arcpy.mapping.Layer(tempLayer)
    arcpy.mapping.AddLayer(df, addLayer, "AUTO_ARRANGE")
    arcpy.RefreshTOC()
