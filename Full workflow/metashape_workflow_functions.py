
import time
import datetime
import platform
import os
import glob
import re
import yaml


import Metashape

sep = "; "

def stamp_time():

    stamp = datetime.datetime.now().strftime('%Y%m%dT%H%M')
    return stamp

def diff_time(t2, t1):
    '''
    Give a end and start time, subtract, and round
    '''
    total = str(round(t2-t1, 1))
    return total

#### Functions for each major step in Metashape

def project_setup(cfg, config_file):
    if not os.path.exists(cfg["output_path"]):
        os.makedirs(cfg["output_path"])
    if not os.path.exists(cfg["project_path"]):
        os.makedirs(cfg["project_path"])

    run_name = cfg["run_name"]

    if(run_name == "from_config_filename"):
        file_basename = os.path.basename(config_file) 
        run_name, _ = os.path.splitext(file_basename) 

    timestamp = stamp_time()
    run_id = "_".join([run_name,timestamp])

    project_file = os.path.join(cfg["project_path"], '.'.join([run_id, 'psx']) )
    log_file = os.path.join(cfg["output_path"], '.'.join([run_id+"_log",'txt']) )
    doc = Metashape.Document() 
    if cfg["load_project"] != "":
        doc.open(cfg["load_project"])
    else:
        chunk = doc.addChunk()
        chunk.crs = Metashape.CoordinateSystem(cfg["project_crs"])
        #chunk.marker_crs = Metashape.CoordinateSystem(cfg["addGCPs"]["gcp_crs"])
    doc.save(project_file)

    with open(log_file, 'a') as file:

        file.write(sep.join(['Project', run_id])+'\n')
        file.write(sep.join(['Agisoft Metashape Professional Version', Metashape.app.version])+'\n')
        file.write(sep.join(['Processing started', stamp_time()]) +'\n')
        file.write(sep.join(['Node', platform.node()])+'\n')
        file.write(sep.join(['CPU', platform.processor()]) +'\n')
    return doc, log_file, run_id



def enable_and_log_gpu(log_file, cfg):

    gpustringraw = str(Metashape.app.enumGPUDevices())
    gpucount = gpustringraw.count("name': '")
    gpustring = ''
    currentgpu = 1
    while gpucount >= currentgpu:
        if gpustring != '': gpustring = gpustring+', '
        gpustring = gpustring+gpustringraw.split("name': '")[currentgpu].split("',")[0]
        currentgpu = currentgpu+1
    #gpustring = gpustringraw.split("name': '")[1].split("',")[0]
    gpu_mask = Metashape.app.gpu_mask

    with open(log_file, 'a') as file:
        file.write(sep.join(['Number of GPUs Found', str(gpucount)]) +'\n')
        file.write(sep.join(['GPU Model', gpustring])+'\n')
        file.write(sep.join(['GPU Mask', str(gpu_mask)])+'\n')

        if (gpucount > 0) and (gpu_mask == 0):
            Metashape.app.gpu_mask = 1
            gpu_mask = Metashape.app.gpu_mask
            file.write(sep.join(['GPU Mask Enabled', str(gpu_mask)])+'\n')
    Metashape.app.cpu_enable = False

    if not cfg["use_cuda"]:
        Metashape.app.settings.setValue("main/gpu_enable_cuda", "0")
    #Metashape.app.settings.setValue("main/depth_max_gpu_multiplier", cfg["gpu_multiplier"])

    return True


def add_photos(doc, cfg):

    a = glob.iglob(os.path.join(cfg["photo_path"],"**","*.*"), recursive=True) 
    b = [path for path in a]
    photo_files = [x for x in b if (re.search("(.tif$)|(.jpg$)|(.TIF$)|(.JPG$)",x) and (not re.search("dem_usgs.tif",x)))]


    doc.chunk.addPhotos(photo_files)

    for camera in doc.chunk.cameras:
        path = camera.photo.path
        rel_path = path.replace(cfg["photo_path"],"")
        newlabel = re.sub("^/","",rel_path)
        camera.label = newlabel

    doc.save()

    return True

def align_photos(doc, log_file, cfg):
    timer1a = time.time()

    doc.chunk.matchPhotos(downscale=cfg["alignPhotos"]["downscale"],
                          subdivide_task = cfg["subdivide_task"],
                          keep_keypoints = cfg["alignPhotos"]["keep_keypoints"],
                          generic_preselection = cfg["alignPhotos"]["generic_preselection"],
                          reference_preselection = cfg["alignPhotos"]["reference_preselection"],
                          reference_preselection_mode = cfg["alignPhotos"]["reference_preselection_mode"])
    doc.chunk.alignCameras(adaptive_fitting=cfg["alignPhotos"]["adaptive_fitting"],
                           subdivide_task = cfg["subdivide_task"],
                           reset_alignment = cfg["alignPhotos"]["reset_alignment"])
    doc.save()

    timer1b = time.time()

    time1 = diff_time(timer1b, timer1a)

    with open(log_file, 'a') as file:
        file.write(sep.join(['Align Photos', time1])+'\n')

    return True


def reset_region(doc):
    doc.chunk.resetRegion()
    region_dims = doc.chunk.region.size
    region_dims[2] *= 3
    doc.chunk.region.size = region_dims

    return True



def filter_points_usgs_part1(doc, cfg):

    doc.chunk.optimizeCameras(adaptive_fitting=cfg["optimizeCameras"]["adaptive_fitting"])

    rec_thresh_percent = cfg["filterPointsUSGS"]["rec_thresh_percent"]
    rec_thresh_absolute = cfg["filterPointsUSGS"]["rec_thresh_absolute"]
    proj_thresh_percent = cfg["filterPointsUSGS"]["proj_thresh_percent"]
    proj_thresh_absolute = cfg["filterPointsUSGS"]["proj_thresh_absolute"]
    reproj_thresh_percent = cfg["filterPointsUSGS"]["reproj_thresh_percent"]
    reproj_thresh_absolute = cfg["filterPointsUSGS"]["reproj_thresh_absolute"]

    fltr = Metashape.TiePoints.Filter()
    fltr.init(doc.chunk, Metashape.TiePoints.Filter.ReconstructionUncertainty)
    values = fltr.values.copy()
    values.sort()
    thresh = values[int(len(values) * (1 - rec_thresh_percent / 100))]
    if thresh < rec_thresh_absolute:
        thresh = rec_thresh_absolute 
    fltr.removePoints(thresh)

    doc.chunk.optimizeCameras(adaptive_fitting=cfg["optimizeCameras"]["adaptive_fitting"])

    fltr = Metashape.TiePoints.Filter()
    fltr.init(doc.chunk, Metashape.TiePoints.Filter.ProjectionAccuracy)
    values = fltr.values.copy()
    values.sort()
    thresh = values[int(len(values) * (1- proj_thresh_percent / 100))]
    if thresh < proj_thresh_absolute:
        thresh = proj_thresh_absolute   
    fltr.removePoints(thresh)

    doc.chunk.optimizeCameras(adaptive_fitting=cfg["optimizeCameras"]["adaptive_fitting"])

    fltr = Metashape.TiePoints.Filter()
    fltr.init(doc.chunk, Metashape.TiePoints.Filter.ReprojectionError)
    values = fltr.values.copy()
    values.sort()
    thresh = values[int(len(values) * (1 - reproj_thresh_percent / 100))]
    if thresh < reproj_thresh_absolute:
        thresh = reproj_thresh_absolute 
    fltr.removePoints(thresh)

    doc.chunk.optimizeCameras(adaptive_fitting=cfg["optimizeCameras"]["adaptive_fitting"])

    doc.save()


def filter_points_usgs_part2(doc, cfg):

    doc.chunk.optimizeCameras(adaptive_fitting=cfg["optimizeCameras"]["adaptive_fitting"])

    reproj_thresh_percent = cfg["filterPointsUSGS"]["reproj_thresh_percent"]
    reproj_thresh_absolute = cfg["filterPointsUSGS"]["reproj_thresh_absolute"]

    fltr = Metashape.TiePoints.Filter()
    fltr.init(doc.chunk, Metashape.TiePoints.Filter.ReprojectionError)
    values = fltr.values.copy()
    values.sort()
    thresh = values[int(len(values) * (1 - reproj_thresh_percent / 100))]
    if thresh < reproj_thresh_absolute:
        thresh = reproj_thresh_absolute  # don't throw away too many points if they're all good
    fltr.removePoints(thresh)

    doc.chunk.optimizeCameras(adaptive_fitting=cfg["optimizeCameras"]["adaptive_fitting"])

    doc.save()


def classify_ground_points(doc, log_file, run_id, cfg):

        timer_a = time.time()

        doc.chunk.point_cloud.classifyGroundPoints(max_angle=cfg["classifyGroundPoints"]["max_angle"],
                                                   max_distance=cfg["classifyGroundPoints"]["max_distance"],
                                                   cell_size=cfg["classifyGroundPoints"]["cell_size"])
        doc.save()


        timer_b = time.time()


        time_tot = diff_time(timer_b, timer_a)


        with open(log_file, 'a') as file:
            file.write(sep.join(['Classify Ground Points', time_tot]) + '\n')





def build_point_cloud(doc, log_file, run_id, cfg):

    timer2a = time.time()


    doc.chunk.buildDepthMaps(downscale=cfg["buildPointCloud"]["downscale"],
                             filter_mode=cfg["buildPointCloud"]["filter_mode"],
                             reuse_depth=cfg["buildPointCloud"]["reuse_depth"],
                             max_neighbors=cfg["buildPointCloud"]["max_neighbors"],
                             subdivide_task=cfg["subdivide_task"])
    doc.save()
    timer2b = time.time()

    time2 = diff_time(timer2b, timer2a)

    with open(log_file, 'a') as file:
        file.write(sep.join(['Build Depth Maps', time2]) + '\n')

    timer3a = time.time()

    doc.chunk.buildPointCloud(max_neighbors=cfg["buildPointCloud"]["max_neighbors"],
                              keep_depth = cfg["buildPointCloud"]["keep_depth"],
                              subdivide_task = cfg["subdivide_task"],
                              point_colors = True)
    doc.save()


    if cfg["buildPointCloud"]["classify_ground_points"]:
    	classify_ground_points(doc, log_file, run_id, cfg)


    ### Export points

    if cfg["buildPointCloud"]["export"]:

        output_file = os.path.join(cfg["output_path"], run_id + '_points.las')

        if cfg["buildPointCloud"]["classes"] == "ALL":
            doc.chunk.exportPointCloud(path=output_file,
                                   source_data=Metashape.PointCloudData,
                                   format=Metashape.PointCloudFormatLAS,
                                   crs=Metashape.CoordinateSystem(cfg["project_crs"]),
                                   subdivide_task=cfg["subdivide_task"])
        else:
            doc.chunk.exportPointCloud(path=output_file,
                                   source_data=Metashape.PointCloudData,
                                   format=Metashape.PointCloudFormatLAS,
                                   crs=Metashape.CoordinateSystem(cfg["project_crs"]),
                                   clases=cfg["buildPointCloud"]["classes"],
                                   subdivide_task=cfg["subdivide_task"])

    timer3b = time.time()

    time3 = diff_time(timer3b, timer3a)

    with open(log_file, 'a') as file:
        file.write(sep.join(['Build Point Cloud', time3])+'\n')

    return True




def build_dem(doc, log_file, run_id, cfg):

    if cfg["buildDem"]["classify_ground_points"]:
    	classify_ground_points(doc, log_file, run_id, cfg)


    timer5a = time.time()


    projection = Metashape.OrthoProjection()
    projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])
    compression = Metashape.ImageCompression()
    compression.tiff_big = cfg["buildDem"]["tiff_big"]
    compression.tiff_tiled = cfg["buildDem"]["tiff_tiled"]
    compression.tiff_overviews = cfg["buildDem"]["tiff_overviews"]

    if (cfg["buildDem"]["type"] == "DSM") | (cfg["buildDem"]["type"] == "both"):
        doc.chunk.buildDem(source_data = Metashape.PointCloudData,
                           subdivide_task = cfg["subdivide_task"],
                           projection = projection)
        output_file = os.path.join(cfg["output_path"], run_id + '_dsm.tif')
        if cfg["buildDem"]["export"]:
            doc.chunk.exportRaster(path=output_file,
                                   projection=projection,
                                   nodata_value=cfg["buildDem"]["nodata"],
                                   source_data=Metashape.ElevationData,
                                   image_compression=compression)
    if (cfg["buildDem"]["type"] == "DTM") | (cfg["buildDem"]["type"] == "both"):
        doc.chunk.buildDem(source_data = Metashape.PointCloudData,
                           classes = Metashape.PointClass.Ground,
                           subdivide_task = cfg["subdivide_task"],
                           projection = projection)
        output_file = os.path.join(cfg["output_path"], run_id + '_dtm.tif')
        if cfg["buildDem"]["export"]:
            doc.chunk.exportRaster(path=output_file,
                                   projection=projection,
                                   nodata_value=cfg["buildDem"]["nodata"],
                                   source_data=Metashape.ElevationData,
                                   image_compression=compression)
    if (cfg["buildDem"]["type"] != "DTM") & (cfg["buildDem"]["type"] == "both") & (cfg["buildDem"]["type"] == "DSM"):
        raise ValueError("DEM type must be either 'DSM' or 'DTM' or 'both'")

    doc.save()

    timer5b = time.time()

    time5 = diff_time(timer5b, timer5a)

    with open(log_file, 'a') as file:
        file.write(sep.join(['Build DEM', time5])+'\n')

    return True


def build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending):
    '''
    Helper function called by build_orthomosaics. build_export_orthomosaic builds and exports an ortho based on the current elevation data.
    build_orthomosaics sets the current elevation data and calls build_export_orthomosaic (one or more times depending on how many orthomosaics requested)
    '''
    timer6a = time.time()

    #prepping params for buildDem
    projection = Metashape.OrthoProjection()
    projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])

    doc.chunk.buildOrthomosaic(surface_data=Metashape.ElevationData,
                               blending_mode=cfg["buildOrthomosaic"]["blending"],
                               fill_holes=cfg["buildOrthomosaic"]["fill_holes"],
                               refine_seamlines=cfg["buildOrthomosaic"]["refine_seamlines"],
                               subdivide_task=cfg["subdivide_task"],
                               projection=projection)

    doc.save()

    ## Export orthomosaic
    if cfg["buildOrthomosaic"]["export"]:
        output_file = os.path.join(cfg["output_path"], run_id + '_ortho_' + file_ending + '.tif')

        compression = Metashape.ImageCompression()
        compression.tiff_big = cfg["buildOrthomosaic"]["tiff_big"]
        compression.tiff_tiled = cfg["buildOrthomosaic"]["tiff_tiled"]
        compression.tiff_overviews = cfg["buildOrthomosaic"]["tiff_overviews"]

        projection = Metashape.OrthoProjection()
        projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])

        doc.chunk.exportRaster(path=output_file,
                               projection=projection,
                               nodata_value=cfg["buildOrthomosaic"]["nodata"],
                               source_data=Metashape.OrthomosaicData,
                               image_compression=compression)
    timer6b = time.time()
    time6 = diff_time(timer6b, timer6a)
    with open(log_file, 'a') as file:
        file.write(sep.join(['Build Orthomosaic', time6]) + '\n')

    return True


def build_orthomosaics(doc, log_file, run_id, cfg):
  
    projection = Metashape.OrthoProjection()
    projection.crs = Metashape.CoordinateSystem(cfg["project_crs"])
    timer6a = time.time()

    file_ending = cfg["buildOrthomosaic"]["surface"]

    if cfg["buildOrthomosaic"]["surface"] == "USGS":
        path = os.path.join(cfg["photo_path"],cfg["buildOrthomosaic"]["usgs_dem_path"])
        crs = Metashape.CoordinateSystem(cfg["buildOrthomosaic"]["usgs_dem_crs"])
        doc.chunk.importRaster(path=path,
                               crs=crs,
                               raster_type=Metashape.ElevationData)
        build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending = "USGS")
    if (cfg["buildOrthomosaic"]["surface"] == "DTM") | (cfg["buildOrthomosaic"]["surface"] == "DTMandDSM"): 
        doc.chunk.buildDem(source_data = Metashape.PointCloudData,
                           classes=Metashape.PointClass.Ground,
                           subdivide_task=cfg["subdivide_task"],
                           projection=projection)
        build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending = "dtm")
    if (cfg["buildOrthomosaic"]["surface"] == "DSM") | (cfg["buildOrthomosaic"]["surface"] == "DTMandDSM"):
        doc.chunk.buildDem(source_data = Metashape.PointCloudData,
                           subdivide_task=cfg["subdivide_task"],
                           projection=projection)
        build_export_orthomosaic(doc, log_file, run_id, cfg, file_ending = "dsm")

    return True


def export_report(doc, run_id, cfg):
    output_file = os.path.join(cfg["output_path"], run_id+'_report.pdf')

    doc.chunk.exportReport(path = output_file)

    return True


def finish_run(log_file,config_file):

    with open(log_file, 'a') as file:
        file.write(sep.join(['Run Completed', stamp_time()])+'\n')

    with open(config_file) as file:
        config_full = yaml.safe_load(file)

    with open(log_file, 'a') as file:
        file.write("\n\n### CONFIGURATION ###\n")
        documents = yaml.dump(config_full,file, default_flow_style=False)
        file.write("### END CONFIGURATION ###\n")


    return True
