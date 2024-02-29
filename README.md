# Python client for accessing the Copernicus Land Monitoring Service (CLMS) ARLIE products

Python client for accessing the CLMS Aggregated River and Lake Ice Extent products by means of REST calls.

The other Pan-European snow and ice products by the CLMS are reachable through the Python client https://github.com/eea/clms-hrsi-api-client-python

## Registration:
Data are accessible without any registration.

## API Url: 
Users are invited to consult the [ICE products user manual available on the Copernicus land portal for details on how to use the API](https://land.copernicus.eu/en/products/water-bodies/high-resolution-aggregated-river-and-lake-ice-extent).

To request ARLIE statistics, the url to use is the following "https<nolink>://cryo.land.copernicus.eu/arlie/get_arlie". It must be accompanied by several arguments. Eg: 
https://cryo.land.copernicus.eu/arlie/get_arlie?geometrywkt=POLYGON((6.591757812499995+47.438190548539666%2C12.172812499999997+47.734590790703436%2C12.172812499999997+45.347199858490285%2C6.240195312499996+45.28539584046706%2C6.591757812499995+47.438190548539666))&cloudcoveragemax=100&startdate=2016-10-01&completiondate=2017-03-31

To request the description of the geometries on which ARLIE statistics are computed, the url to use if the following "https<nolink>://cryo.land.copernicus.eu/arlie/get_geometries". It must be accompanied by several arguments.
Eg.: https://cryo.land.copernicus.eu/arlie/get_geometries?geometrywkt=POLYGON((6.591757812499995+47.438190548539666%2C12.172812499999997+47.734590790703436%2C12.172812499999997+45.347199858490285%2C6.240195312499996+45.28539584046706%2C6.591757812499995+47.438190548539666))&getonlyids=False

## Example:

For using the script in a terminal (only for storing results in CSV file):
```S
>python clms_hrsi_arlie_downloader.py --help

```

For using the script directly in a Python environment and get the results as Python variable and in a CSV file:
```
> python
>>> from clms_hrsi_arlie_downloader import download_arlie_products
>>> outputDir = '/path/to/store/results'
>>> startDate = '2022-12-01'
>>> completionDate = '2022-12-31'
>>> geometryWkt = 'POINT(27.633161183115938+56.56146774961596)'
>>> cloudCoverageMax = 100
>>> requestGeometries = True
>>> returnMode = 'csv_and_variable'

>>> geometries, arlie = download_arlie_products(returnMode, outputDir=outputDir, startDate=startDate, completionDate=completionDate, geometryWkt=geometryWkt, cloudCoverageMax=cloudCoverageMax, requestGeometries=requestGeometries)

```

## Legal notice about Copernicus Data:
Access to data is based on a principle of full, open and free access as established by the Copernicus data and information policy Regulation (EU) No 1159/2013 of 12 July 2013. This regulation establishes registration and licensing conditions for GMES/Copernicus users and can be found here: http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32013R1159.  

Free, full and open access to this data set is made on the conditions that:  
1. When distributing or communicating Copernicus dedicated data and Copernicus service information to the public, users shall inform the public of the source of that data and information.  
2. Users shall make sure not to convey the impression to the public that the user's activities are officially endorsed by the Union.  
3. Where that data or information has been adapted or modified, the user shall clearly state this.  
4. The data remain the sole property of the European Union. Any information and data produced in the framework of the action shall be the sole property of the European Union. Any communication and publication by the beneficiary shall acknowledge that the data were produced “with funding by the European Union”.  
