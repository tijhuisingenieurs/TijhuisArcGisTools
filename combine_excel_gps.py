import os.path
import sys
import arcpy
from utils.addresulttodisplay import add_result_to_display

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.tools.combine_manual_and_gps_points import CombineMeasurements

# Read the parameter values

wet_profile_xls = arcpy.GetParameterAsText(0)
gps_points_profile_xls = arcpy.GetParameterAsText(1)
output_shapefile = arcpy.GetParameterAsText(2)

# wet_profile_xls = 'C:\\Users\\basti\\Documents\\GitHub\\gistools\\test\\data\\combineer_tool\\Natte_Profielen.xlsx'
# gps_points_profile_xls = 'C:\\Users\\basti\\Documents\\GitHub\\gistools\\test\\data\\combineer_tool\\GPS_Punten.xlsx'
# output_shapefile = 'C:\\tmp\\combined.shp'
#
# if os.path.isfile(output_shapefile):
#     os.remove(output_shapefile)

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('natte profiel excel = ' + wet_profile_xls)
arcpy.AddMessage('GPS punten excel = ' + gps_points_profile_xls)
arcpy.AddMessage('Doelbestand  = ' + output_shapefile)


# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van combine_excel_gps')

cm = CombineMeasurements()
output_points, messages = cm.run(wet_profile_xls, gps_points_profile_xls)

if len(messages) >= 1:
    arcpy.AddWarning('Eén of meerdere waarschuwingen bij bewerken:')
    for msg in messages:
        arcpy.AddMessage(msg)

# wegschrijven tool resultaat
output_name_p = os.path.basename(output_shapefile).split('.')[0]
output_dir_p = os.path.dirname(output_shapefile)

arcpy.AddMessage('Bezig met het genereren van het doelbestand met punten...')
# spatial_reference = arcpy.spatialReference(28992)

#  specific file name and data
output_fl_points = arcpy.CreateFeatureclass_management(output_dir_p, output_name_p, 'POINT',
                                                       spatial_reference=28992)

# fields_points = next(output_point_col.filter())['properties'].keys()

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
                   
for p in output_points:
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
    row.setValue("CODE", p['code'])
    row.setValue("distance", round(p['distance'], 2))

    dataset.insertRow(row)

add_result_to_display(output_fl_points, output_name_p)

print 'Gereed'
