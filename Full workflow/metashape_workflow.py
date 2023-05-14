
import sys
import argparse
import metashape_workflow_functions as meta
import read_yaml

def main():
    parser = argparse.ArgumentParser(description='Metashape Workflow Script')
    parser.add_argument('config_file', type=str, help='Path to the YAML configuration file')
    args = parser.parse_args()

    config_file = args.config_file
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


if __name__ == '__main__':
    main()



