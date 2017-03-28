import arcpy


def add_result_to_display(result, display_name):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    df = mxd.activeDataFrame
    arcpy.env.overwriteOutput = True
    temp_layer = display_name
    if type(result) != arcpy.mapping.Layer:
        # arcpy.MakeFeatureLayer_management(result, temp_layer)
        add_layer = arcpy.mapping.Layer(str(result))
    else:
        add_layer = result
    arcpy.mapping.AddLayer(df, add_layer, "AUTO_ARRANGE")
    arcpy.RefreshTOC()
