import arcpy
arcpy.env.overwriteOutput = True
out_gdb = r"D:\Codex\building_01\data\processed\model_points.gdb"
if not arcpy.Exists(out_gdb):
    arcpy.management.CreateFileGDB(r"D:\Codex\building_01\data\processed", "model_points.gdb")
try:
    arcpy.management.XYTableToPoint(
        r"D:\Codex\building_01\data\processed\model_input_filled.csv",
        out_gdb + "\\points",
        "centroid_x",
        "centroid_y",
        arcpy.SpatialReference(3857)
    )
    print("ok")
except Exception as exc:
    print("ERR", exc)
    print(arcpy.GetMessages(2))
