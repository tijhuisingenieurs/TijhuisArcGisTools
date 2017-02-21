import arcpy


def add_result_to_display(result, display_name):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = mxd.activeDataFrame
    arcpy.env.overwriteOutput = True
    temp_layer = display_name
    arcpy.MakeFeatureLayer_management(result, temp_layer)
    add_layer = arcpy.mapping.Layer(temp_layer)
    arcpy.mapping.AddLayer(df, add_layer, "AUTO_ARRANGE")
    arcpy.RefreshTOC()
