import arcpy
import pandas as pd
from utils.addresulttodisplay import add_result_to_display

# get parameters
input_dwarsprofiel = arcpy.GetParameterAsText(0)
distance_field_dwp = arcpy.GetParameterAsText(1)
hydrovak_dwp = str(arcpy.GetParameterAsText(2))
input_meetpunten = arcpy.GetParameterAsText(3)
distance_field_meet = arcpy.GetParameterAsText(4)
hydrovak_meet = str(arcpy.GetParameterAsText(5))
column_to_interpolate = arcpy.GetParameterAsText(6)
output = arcpy.GetParameterAsText(7)

# Test script without GUI
# input_dwarsprofiel = 'C:/Users/tom/Documents/_Python_projects/punten_interpoleren/output/TI20237_Week40_Uitpeiling_DWP_middenpunten_snap_mv_afstand_onderdiep.shp' # lijnen of punten
# distance_field_dwp = 'distance'
# hydrovak_dwp = 'monstervak'
# input_meetpunten = 'C:/Users/tom/Documents/_Python_projects/punten_interpoleren/data/TI20237_Week40_Uitpeiling_Lengteprofiel_Punten.shp' # Lijnen of punten
# distance_field_meet = 'distance'
# hydrovak_meet = 'monstervak'
# column_to_interpolate = 'Onder_Diep'
# output = 'C:/Users/tom/Documents/_Python_projects/punten_interpoleren/output/meet_met_afstand_week_40.shp' # Lijnen of punten van input meetpunten

arcpy.env.overwriteOutput = True

mem_points = arcpy.CopyFeatures_management(input_meetpunten, "in_memory/inMemoryFeatureClass")
arcpy.AddField_management(mem_points, column_to_interpolate, "FLOAT")

with arcpy.da.SearchCursor(input_dwarsprofiel, hydrovak_dwp) as hydro_rows:
    hydrovakken = list(r[0].encode("ascii") for r in hydro_rows)
    hydrovakken = list(dict.fromkeys(hydrovakken))

for hydrovak in hydrovakken:
    expr = hydrovak

    with arcpy.da.SearchCursor(input_dwarsprofiel, [distance_field_dwp, 'SHAPE@', column_to_interpolate, hydrovak_dwp],
                               where_clause="{} = '{}'".format(hydrovak_dwp, expr)) as dwp_rows:
        # dwp_profiles = list(r for r in dwp_rows if r[3] == expr)
        arcpy.AddMessage("{} = '{}'".format(hydrovak_dwp, expr))
        dwp_profiles = list(r for r in dwp_rows)
        dwp_profiles_sorted = sorted(dwp_profiles, key=lambda tup: tup[0])

        previous_dwp = None
        for i, dwp_row in enumerate(dwp_profiles_sorted):

            with arcpy.da.UpdateCursor(mem_points, [distance_field_meet, 'SHAPE@', column_to_interpolate, hydrovak_meet],
                                       where_clause="{} = '{}'".format(hydrovak_meet, expr)) as rows:
                arcpy.AddMessage("{} = '{}'".format(hydrovak_meet, expr))
                rowmeter = []
                for r in rows:
                    # first get associated line
                    if r[0] <= dwp_profiles_sorted[0][0] and r[2] is None:
                        r[2] = dwp_profiles_sorted[0][2]
                        rows.updateRow(r)
                    elif r[0] >= dwp_profiles_sorted[-1][0] and r[2] is None:
                        r[2] = dwp_profiles_sorted[-1][2]
                        rows.updateRow(r)
                    elif previous_dwp is not None and r[2] is None:
                        distance_between_dwp = dwp_row[0] - previous_dwp[0]
                        distance_to_dwp = abs(previous_dwp[0] - r[0])
                        percentage_to_dwp = distance_to_dwp / distance_between_dwp
                        if percentage_to_dwp <= 1:
                            range_zvalue = dwp_row[2] - previous_dwp[2]
                            new_z_value = previous_dwp[2] + (range_zvalue * percentage_to_dwp)
                            r[2] = new_z_value
                            rows.updateRow(r)
                    rowmeter.append(r[0])

            previous_dwp = dwp_row

        # if no value in dwp, give back 999
        with arcpy.da.UpdateCursor(mem_points, [distance_field_meet, 'SHAPE@', column_to_interpolate, hydrovak_meet],
                                   where_clause="{} = '{}'".format(hydrovak_meet, expr)) as rows:
            for r in rows:
                if r[2] == 0 or r[2] is None:
                    r[2] = 999
                    rows.updateRow(r)


output_fl = arcpy.CopyFeatures_management(mem_points, output)

add_result_to_display(output_fl, output)
