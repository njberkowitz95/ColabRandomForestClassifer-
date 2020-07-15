# -*- coding: utf-8 -*-
"""2020SummerCL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FKYDCs0UuTJo48DUZSEdf7PT9lu6TKqS

# Import GEE API
"""

from google.colab import auth
auth.authenticate_user()

import ee
ee.Authenticate()
ee.Initialize()

# use the Folium library for visualization
import folium

"""# Define variables"""

# import data from earth engine asset
# missing mask
missing_18 = ee.Image('users/zhmeng0119/missing_18')
# print(missing_18)
# vectorized training sites 
training_vct = ee.FeatureCollection('users/zhmeng0119/vct_training4k_Chanthaburi')

# create the point of interest
POI = ee.Geometry.Point(101.995989,13.012611);

# use landsat 8 T1 level data
landsat8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")

"""# Load up data"""

# filter the date of data by POI
landsat8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
l8filtered = landsat8.filterBounds(POI).filterDate('2018-01-01', '2018-12-31').first()
# print(l8filtered)

# visualize the data
# use folium to visualize the imagery.
mapid = l8filtered.getMapId({'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3})
map = folium.Map(location=[13.012611,101.995989])

folium.TileLayer(
    tiles=mapid['tile_fetcher'].url_format,
    attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
    overlay=True,
    name='median composite',
  ).add_to(map)

map.add_child(folium.LayerControl())
map

# # filter the date of data by POI
# landsat8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
# l8filtered = landsat8.filterBounds(POI).filterDate('2018-01-01', '2018-12-31').first()
# # pansharpending
# hsv = l8filtered.select(['B4', 'B3', 'B2']).rgbToHsv();
# l8filtered = ee.Image.cat([
#   hsv.select('hue'), hsv.select('saturation'), l8filtered.select('B8')
# ]).hsvToRgb();
# # print(sharpened)

# # print(l8filtered)

# # visualize the data
# # use folium to visualize the imagery.
# mapid = l8filtered.getMapId({'bands': ['red', 'green', 'blue'], 'min': 0, 'max': 0.3})
# map = folium.Map(location=[13.012611,101.995989])

# folium.TileLayer(
#     tiles=mapid['tile_fetcher'].url_format,
#     attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
#     overlay=True,
#     name='median composite',
#   ).add_to(map)

# map.add_child(folium.LayerControl())
# map

"""#Preprocess data"""

# apply missing mask
masked_l8 = l8filtered.updateMask(missing_18);

#Exoprt panchromatic band 
# B8Panchromatic = masked_l8.select(['B8'])
# assexport = ee.batch.Export.image.toDrive(B8Panchromatic,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='B8Panchromatic',
#                 scale=15,
#                 maxPixels=9000000000)
# assexportid = str(assexport.id)
# print('****Exporting to Assets, task id: %s '%assexportid)
# assexport.start() 

# Export masked_l8 to drive for pansharpen process
# assexport = ee.batch.Export.image.toDrive(masked_l8.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']),
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='Landsat8Image_training_input',
#                 scale=30,
#                 maxPixels=9000000000)
# assexportid = str(assexport.id)
# print('****Exporting to Assets, task id: %s '%assexportid)
# assexport.start() 

# select the training data for each class
mangrove = training_vct.filter(ee.Filter.eq("grid_code",1))
wetland = training_vct.filter(ee.Filter.eq("grid_code",2))
pond = training_vct.filter(ee.Filter.eq("grid_code",3))
water = training_vct.filter(ee.Filter.eq("grid_code",4))
other = training_vct.filter(ee.Filter.eq("grid_code",5))
# print(other)

# Set the class "mangrove" to 1 and all others to 0
def setClass(feat):
  return feat.set("class",1)

def setOther(feat):
  return feat.set("class",0)

man = mangrove.map(setClass)
oth = wetland.map(setOther).merge(pond.map(setOther)).merge(water.map(setOther)).merge(other.map(setOther))

referenceData = man.merge(oth)

"""#Random Forest Classification with GEE Python Library

##Part A: regular RF for all class
"""

# Sample data
trainingA = masked_l8.sampleRegions(training_vct,['grid_code'],30);
# Define a classifier and train it
classifierA = ee.Classifier.smileRandomForest(100).train(trainingA,'grid_code',['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']);
# classifierA = ee.Classifier.smileRandomForest(10).train(trainingA,'grid_code',['red', 'green', 'blue']);
# Classify masked_l8.
classifiedA = masked_l8.classify(classifierA);
# print(classifiedA)

# visualize the result
# use folium to visualize the imagery.
resultidA = classifiedA.getMapId({'bands': ['classification'], 'min': 1, 'max': 5, 'palette': ["e07a5f","3d405b","81b29a","f2cc8f","ff0e19"]})
map = folium.Map(location=[13.012611,101.995989])

folium.TileLayer(
    tiles=resultidA['tile_fetcher'].url_format,
    attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
    overlay=True,
    name='median composite',
  ).add_to(map)
map.add_child(folium.LayerControl())
map

"""##Part B: soft RF for one class (Mangrove)"""

# sample data
trainingB = masked_l8.sampleRegions(referenceData,['class'],masked_l8.get('GRID_CELL_SIZE_REFLECTIVE'));
# print(trainingB)
# define a classifier and train it
classifierB = ee.Classifier.smileRandomForest(10).setOutputMode('PROBABILITY').train(trainingB,'class',['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']);
# Classify masked_l8.
classifiedB = masked_l8.classify(classifierB);

# # visualize the result
# # use folium to visualize the imagery.
palette = ['black','blue','green','yellow','orange','red','purple']
resultidB = classifiedB.getMapId({'bands': ['classification'], 'min': 0, 'max': 1,'palette':palette})
map = folium.Map(location=[13.012611,101.995989])

folium.TileLayer(
    tiles=resultidB['tile_fetcher'].url_format,
    attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
    overlay=True,
    name='median composite',
  ).add_to(map)
map.add_child(folium.LayerControl())
map

# assexport = ee.batch.Export.image.toDrive(classifiedB,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='softRF_Mangrove',
#                 scale=30)
# assexportid = str(assexport.id)
# print('****Exporting to Assets, task id: %s '%assexportid)
# assexport.start()

"""##Part C: soft RF for all classes - Batch

#### Classes we have are mangrove(1),wetland(2),pond(3),water(4),other(5)
"""

#### Classes we have are mangrove(1),wetland(2),pond(3),water(4),other(5)
Classes = {
    'mangrove':mangrove,
    'wetland':wetland,
    'pond':pond,
    'water':water,
    'other':other
}

def batchSoftRF(image, name):
  # create name list to index 'Classes'
  classname = ['mangrove','wetland','pond','water','other']
  del classname[classname.index(name)]

  # Set the class "name" to 1 and all others to 0
  target = Classes[name].map(setClass)
  other = Classes[classname[0]].map(setOther)
  del classname[0]
  for i in classname:
    other = other.merge(Classes[i].map(setOther))
  
  # create ref points dataset
  referenceData = target.merge(other)

  # properties of image
  spResolution = image.get('GRID_CELL_SIZE_REFLECTIVE')
  bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']

  # sample data based on ref points dataset
  training = image.sampleRegions(referenceData,['class'],30);
  # define a classifier and train it
  classifier = ee.Classifier.smileRandomForest(100).setOutputMode('PROBABILITY').train(training,'class',bands);
  # Classify masked_l8.
  classified = image.classify(classifier);

  return classified


def visualizeResult(result):
  # # visualize the result
  # # use folium to visualize the imagery.
  # palette
  palette = ['black','blue','green','yellow','orange','red','purple']
  resultid = result.getMapId({'bands': ['classification'], 'min': 0, 'max': 1,'palette':palette})
  map = folium.Map(location=[13.012611,101.995989])
  folium.TileLayer(
      tiles=resultid['tile_fetcher'].url_format,
      attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
      overlay=True,
      name='median composite',
    ).add_to(map)
  map.add_child(folium.LayerControl())
  map
  return map

result_mangrove = batchSoftRF(masked_l8,'mangrove')
visualizeResult(result_mangrove)

# assexport = ee.batch.Export.image.toDrive(result_mangrove,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='softRF_mangrove_15',
#                 scale=15,
#                 maxPixels=9000000000)
# assexportid = str(assexport.name)
# print('****Exporting to Assets, task name: %s '%assexportid)
# assexport.start()

result_wetland = batchSoftRF(masked_l8,'wetland')
visualizeResult(result_wetland)

# assexport = ee.batch.Export.image.toDrive(result_wetland,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='softRF_Wetland_15',
#                 scale=15,
#                 maxPixels=9000000000)
# assexportid = str(assexport.name)
# print('****Exporting to Assets, task name: %s '%assexportid)
# assexport.start()

result_pond = batchSoftRF(masked_l8,'pond')
visualizeResult(result_pond)

# assexport = ee.batch.Export.image.toDrive(result_pond,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='softRF_Pond_15',
#                 scale=15,
#                 maxPixels=9000000000)
# assexportid = str(assexport.name)
# print('****Exporting to Assets, task name: %s '%assexportid)
# assexport.start()

result_water = batchSoftRF(masked_l8,'water')
visualizeResult(result_water)

# assexport = ee.batch.Export.image.toDrive(result_water,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='softRF_Water_15',
#                 scale=15,
#                 maxPixels=9000000000)
# assexportid = str(assexport.name)
# print('****Exporting to Assets, task name: %s '%assexportid)
# assexport.start()

result_other = batchSoftRF(masked_l8,'other')
visualizeResult(result_other)

# assexport = ee.batch.Export.image.toDrive(result_other,
#                 description='assetExportTask', 
#                 folder='DATA_2020SummerCL',
#                 fileNamePrefix='softRF_Other_15',
#                 scale=15,
#                 maxPixels=9000000000)
# assexportid = str(assexport.name)
# print('****Exporting to Assets, task name: %s '%assexportid)
# assexport.start()

"""#Testing with GDAL"""

from google.colab import drive
drive.mount('/content/drive')

# GDAL
# import osgeo
from osgeo import gdal

"""##Opening the File"""

dataset = gdal.Open('/content/drive/My Drive/DATA_2020SummerCL/Landsat8Image_training_input.tif')
panband = gdal.Open('/content/drive/My Drive/DATA_2020SummerCL/B8Panchromatic.tif')
if not panband:
  print("GG")
else:
  print("Data read in successed!")

"""### Getting Dataset Information"""

print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
                            dataset.GetDriver().LongName))
print("Size is {} x {} x {}".format(dataset.RasterXSize,
                                    dataset.RasterYSize,
                                    dataset.RasterCount))
print("Projection is {}".format(dataset.GetProjection()))
geotransform = dataset.GetGeoTransform()
if geotransform:
    print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
    print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))

"""### Fetching a Raster Band"""

band = dataset.GetRasterBand(7)
print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))

min = band.GetMinimum()
max = band.GetMaximum()
if not min or not max:
    (min,max) = band.ComputeRasterMinMax(True)
print("Min={:.3f}, Max={:.3f}".format(min,max))

if band.GetOverviewCount() > 0:
    print("Band has {} overviews".format(band.GetOverviewCount()))

if band.GetRasterColorTable():
    print("Band has a color table with {} entries".format(band.GetRasterColorTable().GetCount()))

opt = """
<VRTDataset subClass="VRTPansharpenedDataset">
    <PansharpeningOptions>
        <PanchroBand>
            <SourceFilename relativeToVRT="1">panchromatic.tif</SourceFilename>
            <SourceBand>1</SourceBand>
        </PanchroBand>
        <SpectralBand dstBand="1">
            <SourceFilename relativeToVRT="1">multispectral.tif</SourceFilename>
            <SourceBand>1</SourceBand>
        </SpectralBand>
        <SpectralBand dstBand="2">
            <SourceFilename relativeToVRT="1">multispectral.tif</SourceFilename>
            <SourceBand>2</SourceBand>
        </SpectralBand>
        <SpectralBand dstBand="3">
            <SourceFilename relativeToVRT="1">multispectral.tif</SourceFilename>
            <SourceBand>3</SourceBand>
        </SpectralBand>
    </PansharpeningOptions>
</VRTDataset>
"""