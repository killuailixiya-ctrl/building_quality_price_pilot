import arcpy
from arcpy.sa import KernelDensity, ZonalStatisticsAsTable
arcpy.env.overwriteOutput=True
arcpy.CheckOutExtension("Spatial")
gdb=r"D:\Codex\building_01\data\processed\paper_features.gdb"
blocks=r"D:\Codex\building_01\data\processed\wuhan_blocks.gdb\blocks"
sr=arcpy.Describe(blocks).spatialReference
cats=["kindergarten","basic_health","dining","shopping","leisure","company","bus"]
for cat in cats:
    src=f"{gdb}\\poi_{cat}"
    prj=f"{gdb}\\poi_{cat}_proj"
    if arcpy.Exists(prj): arcpy.management.Delete(prj)
    arcpy.management.Project(src, prj, sr)
    kde=KernelDensity(prj,"NONE",cell_size=500,search_radius=2000,area_unit_scale_factor="SQUARE_KILOMETERS")
    kde.save(f"{gdb}\\kde_{cat}_proj")
    table=f"{gdb}\\zonal_{cat}_kde_proj"
    ZonalStatisticsAsTable(blocks,"block_id",f"{gdb}\\kde_{cat}_proj",table,"DATA","MEAN")
    print(cat, arcpy.GetCount_management(table)[0])
