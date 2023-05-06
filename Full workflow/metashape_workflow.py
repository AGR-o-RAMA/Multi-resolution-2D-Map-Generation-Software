

import sys

manual_config_file = "/home/mulham/agrorama/python/example.yaml"
# "/home/mulham/agrorama/automate-metashape/config/example.yml"




try: 
    from python import metashape_workflow_functions as meta
    from python import read_yaml
except:
    import metashape_workflow_functions as meta
    import read_yaml

config_file = manual_config_file
cfg = read_yaml.read_yaml(config_file)

doc, log, run_id = meta.project_setup(cfg, config_file)

meta.enable_and_log_gpu(log, cfg)

if cfg["photo_path"] != "":
    meta.add_photos(doc, cfg)

if cfg["alignPhotos"]["enabled"]:
    meta.align_photos(doc, log, cfg)
    meta.reset_region(doc)

if cfg["filterPointsUSGS"]["enabled"]:
    meta.filter_points_usgs_part1(doc, cfg)
    meta.reset_region(doc)

if cfg["filterPointsUSGS"]["enabled"]:
    meta.filter_points_usgs_part2(doc, cfg)
    meta.reset_region(doc)

if cfg["buildPointCloud"]["enabled"]:
    meta.build_point_cloud(doc, log, run_id, cfg)

if cfg["buildDem"]["enabled"]:
    meta.build_dem(doc, log, run_id, cfg)

if cfg["buildOrthomosaic"]["enabled"]:
    meta.build_orthomosaics(doc, log, run_id, cfg)

meta.export_report(doc, run_id, cfg)

meta.finish_run(log, config_file)






