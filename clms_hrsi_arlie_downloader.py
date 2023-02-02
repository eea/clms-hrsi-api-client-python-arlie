import os
import re
import sys
import json
import time
import logging
import datetime
import argparse
import subprocess
from functools import partial
import requests
import numpy as np
import copy
import xml.etree.ElementTree as ET

METADATA_URL = ET.Element("MT_Metadata", url="https://sdi.eea.europa.eu/catalogue/srv/eng/catalog.search#/metadata/219a6cd4-edfe-4982-8470-39b60421ed74")

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected for requestGeometries parameter.')

def validate_Rfc3339(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return date_text
    except:
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

def format_arlie_product(arlie, index):
    arlie_formatted = []
    arlie_formatted.append(index + 1)
    arlie_formatted.append(arlie[0])
    arlie_formatted.append(datetime.datetime.strptime(str(arlie[1]) + 'T' + str(arlie[2]), '%Y%m%dT%H%M%S').strftime('%Y-%m-%dT%H:%M:%S'))
    arlie_formatted.append(arlie[3])
    arlie_formatted.append(arlie[4])
    arlie_formatted.append(arlie[5])
    arlie_formatted.append(arlie[6])
    arlie_formatted.append(arlie[7])
    arlie_formatted.append(arlie[8])
    
    mission = ""
    if arlie[-1] == 1:
        mission = 'Sentinel-1'
    elif arlie[-1] == 2:
        mission = 'Sentinel-2'
    elif arlie[-1] == 0:
        mission = 'Sentinel-1 Sentinel-2'
    else:
        mission = ""
    arlie_formatted.append(mission)
    return arlie_formatted

class ArlieRequest(object):
    '''
    Request arlie products in the catalogue.
     * https://cryo.land.copernicus.eu/arlie/
    '''

    # Request URL root
    URL_ROOT = 'https://cryo.land.copernicus.eu/arlie/'

    # ARLIE procedure
    ARLIE_PROC = 'get_arlie'

    # Geometry procedure
    GEOMETRY_PROC = 'get_geometries'

    # URL parameter: geometry - region of interest, defined as WKT string (POINT, POLYGON, etc.)
    # in WGS84 projection.
    URL_PARAM_GEOMETRY = 'geometrywkt'

    # URL parameters: startDate, completionDate - the date limits when the sensing was performed
    URL_PARAM_OBSERVATIONDATE_AFTER = 'startdate'
    URL_PARAM_OBSERVATIONDATE_BEFORE = 'completiondate'

    #URL parameter : cloud
    URL_PARAM_CLOUD_PERCENTAGE = 'cloudcoveragemax'

    def __init__(self, outputDir):
        if outputDir is not None:
            self.outputDir = os.path.abspath(outputDir)
            if not os.path.exists(self.outputDir):
                print("Creating directory " + self.outputDir)
                os.makedirs(self.outputDir)
            else:
                logging.warning("Existing directory " + self.outputDir)
        else:
            self.outputDir = None
        self.arlie_http_request = None
        self.geometry_http_request = None
        self.arlie_result_file = None

    def set_arlie_http_request(self, arlie_http_request):
        self.arlie_http_request = arlie_http_request

    def set_geometry_http_request(self, geometry_http_request):
        self.geometry_http_request = geometry_http_request

    def set_arlie_result_file(self, arlie_result_file):
        self.arlie_result_file = arlie_result_file

    def build_request(self,
                        startDate=None,
                        completionDate=None,
                        geometry=None,
                        cloudCoverageMax=None):
        '''
        Build the request to access HR-S&I catalogue.
        :param startDate: Min request date, as a datetime object.
        :param completionDate: Max request date, as a datetime object.
        :param geometry: Area Of Interest (AOI) to query, in WGS84 projection, in the WKT format.
        :return: formatted arlie_http_request.
        '''
        # URL parameters.
        url_params = {}
        if geometry:
            geometry = geometry.replace(',', '%2C')
            geometry = geometry.replace(' ', '+')
            url_params[ArlieRequest.URL_PARAM_GEOMETRY] = geometry

        if geometry is None:
            logging.error("You must specify polygon")
            sys.exit(-2)
        if cloudCoverageMax:
            url_params[ArlieRequest.URL_PARAM_CLOUD_PERCENTAGE] = cloudCoverageMax
        if startDate:
            url_params[ArlieRequest.URL_PARAM_OBSERVATIONDATE_AFTER] = \
                validate_Rfc3339(startDate)
        if completionDate:
            url_params[ArlieRequest.URL_PARAM_OBSERVATIONDATE_BEFORE] = \
                validate_Rfc3339(completionDate)


        if(url_params):
            self.set_arlie_http_request(ArlieRequest.URL_ROOT + ArlieRequest.ARLIE_PROC + \
                      '?' + \
                      '&'.join(['%s=%s'%(key, value) for key, value in url_params.items()]))

            self.set_geometry_http_request(ArlieRequest.URL_ROOT + ArlieRequest.GEOMETRY_PROC + \
                      '?' + '&'.join(['%s=%s'%(ArlieRequest.URL_PARAM_GEOMETRY, url_params.get(ArlieRequest.URL_PARAM_GEOMETRY))]))

        else:
            logging.error("No query parameters were provided, no query was generated")
            sys.exit(-2)
        return


    def execute_request(self, returnMode, request_geometries=False):
        # Check that the request was set before the call
        if self.arlie_http_request is None:
            logging.error("No arlie_http_request was provided or configured")
            sys.exit(-2)
        if self.geometry_http_request is None:
            logging.error("No geometry_http_request was provided or configured")
            sys.exit(-2)     

        # Send page requests, until no results are returned.
        # The results have a 'totalResults' value that we could use, but
        # it gives wrong and inconsistent values.

        # Resulting arlie_products
        geometries = self.request_geometry(self.geometry_http_request, returnMode, request_geometries=request_geometries, geometriesPath=self.outputDir)


        arlie_products = []
        arlie_products = self.request_page(self.arlie_http_request)


        # Save result file in the output folder
        if returnMode == 'csv' or returnMode == 'csv_and_variable':
            self.set_arlie_result_file(os.path.join(self.outputDir, "arlie.csv"))
            print("Writing ARLIE in " + self.arlie_result_file)
            with open(self.arlie_result_file, 'w') as f:
                f.write('id;river_km_id;datetime;water_perc;ice_perc;other_perc;cloud_perc;nd_perc;qc;source\n')
                for ii, p in enumerate(arlie_products):
                    f.write('%d;%d;%s;%d;%d;%d;%d;%d;%d;%s\n'%(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8],p[9]))
                f.close()

        print("Found " + str(len(arlie_products)) + " ARLIE products.")

        if returnMode == 'csv' or returnMode == 'csv_and_variable':
            print("Writing metadata link into %s"%(os.path.join(self.outputDir, "ARLIE_MTD.xml")))
            with open(os.path.join(self.outputDir, "ARLIE_MTD.xml"), 'w') as f:
                f.write(ET.tostring(METADATA_URL, encoding='utf8', method='xml').decode())
                f.close()

        if returnMode == 'csv':
            geometries = None
            arlie_products = None
            
        return geometries, arlie_products




    def request_geometry(self, http_request, returnMode, request_geometries=False, geometriesPath = None):
        # Send Get request
        
        req = http_request + "&getonlyids=True"
        response = requests.get(req)
        print('Executing request for geometries: %s'%req)
        geometries = []
        if response:
            json_root = response.json()
            if len(json_root) > 70000:
                print('Big number of polygons requested (%d), please make a request on a smaller area. Maximum size allowed: 70000 polygons'%(len(json_root)))
                sys.exit(-2)  
            else:
                # Read JSON response
                json_root = {}
                if request_geometries:
                    print('Executing request for geometries: %s'%http_request)
                    response = requests.get(http_request)
                    if response:
                        json_root = response.json()
                        for ii in range(len(json_root)):
                            geometries.append(json_root[ii].get('j'))
                        if returnMode == 'csv' or returnMode == 'csv_and_variable':
                            print("Writing geometries in " + os.path.join(geometriesPath, "geometries.csv"))
                            with open(os.path.join(geometriesPath, "geometries.csv"), 'w') as f:
                                f.write('id;geometry;basin_name;eu_hydro_id;object_nam;area;river_km\n')
                                for ii, p in enumerate(geometries):
                                    f.write('%s;%s;%s;%s;%s;%s;%s\n'%(p[0],p[1],p[2],p[3],p[4],p[5],p[6]))
                                f.close()

        # Return the geometries list
        return geometries        



    def request_page(self, http_request):
        '''Request one page of arlie products (each page contains URL_PAGE_SIZE products).'''

        # Send Get request
        print('Executing request for ARLIE: %s'%http_request)
        response = requests.get(http_request)
        print('Done')
        # Read JSON response
        json_root = {}
        if response:
            json_root = response.json()

        # Resulting arlie products
        arlie_products = []
        for ii in range(len(json_root)):
            arlie_products.append(json_root[ii].get('j'))

        for ii in range(len(arlie_products)):
            arlie_products[ii] = format_arlie_product(arlie_products[ii], ii)

        # Return the arlie_products list
        return arlie_products


def download_arlie_products(returnMode, outputDir=None, startDate=None, completionDate=None, geometryWkt=None, cloudCoverageMax=None, requestGeometries=False):
    # Init Request
    if returnMode == 'variable':
        outputDir = None

    if returnMode not in ['csv', 'csv_and_variable', 'variable']:
        logging.error('Return mode must be csv | csv_and_variable | variable')
        sys.exit(-2)

    if (returnMode == 'csv' or returnMode == 'csv_and_variable'):
        if outputDir is None:
            logging.error("outputDir must be specified")
            sys.exit(-2)
            
    if startDate == None:
        logging.error('Error: you must specify startDate argument')
        sys.exit(-2)
        
    if completionDate == None:
        logging.error('Error: you must specify completionDate argument')
        sys.exit(-2)
        
    if geometryWkt == None:
        logging.error('Error: you must specify geometryWkt argument')
        sys.exit(-2)

    arlie = ArlieRequest(outputDir)

    arlie_http_request = arlie.build_request(startDate=startDate, completionDate=completionDate, geometry=geometryWkt, cloudCoverageMax=cloudCoverageMax)

    # Query HTTP API to list results
    geometries, arlie_products = arlie.execute_request(returnMode, request_geometries=requestGeometries)

    print("End.")

    return geometries, arlie_products


if __name__ == "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format= \
        '%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="""This script provides query to request ARLIE products, see example usages below:\n
    > python clms_hrsi_arlie_downloader.py -returnMode csv/variable/csv_and_variable -outputDir folder_to_store_csv_files -geometry "POLYGON((0 0,0 1, ...))" -startDate YYYY-MM-DD -completionDate YYYY-MM-DD\n""", formatter_class=argparse.RawTextHelpFormatter)


    # Parameters used to define a query, to use a query generated through the HR-S&I finder or to build a new one
    group_query = parser.add_argument_group("query_params", "mandatory parameters for query")
    group_query.add_argument("-returnMode",type=str, required=True, default='csv', help="specify if the return must be stored on a CSV file, on a variable or both (csv|variable|csv_and_variable)")
    group_query.add_argument("-startDate", type=str, required=True, help="2020-06-02")
    group_query.add_argument("-completionDate", type=str, required=True, help="2020-06-02")
    group_query.add_argument("-geometryWkt", type=str, help="WKT geometry as text to specify the desired location")


    group_query = parser.add_argument_group("query_params", "optional parameters for query")
    group_query.add_argument("-outputDir",type=str, required=False, default=None, help="output directory to store ARLIE products, required if returnMode is csv or csv_and_variable")
    group_query.add_argument("-cloudCoverageMax", type=str, required=False, default=100, help="0-100 (percent)")
    group_query.add_argument("-requestGeometries", type=str, required=False, default='False', help="Boolean to indicate if the geometries should be retrieved")


    args = parser.parse_args()
          
    download_arlie_products(args.returnMode,
            outputDir=args.outputDir,
            startDate=args.startDate,
            completionDate=args.completionDate,
            geometryWkt=args.geometryWkt,
            cloudCoverageMax=args.cloudCoverageMax,
            requestGeometries=str2bool(args.requestGeometries))

