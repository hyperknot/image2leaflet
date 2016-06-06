# image2leaflet

A command line tool for converting big images to Leaflet maps


# Installation

## Windows

1. Install **Python 2.7** for Windows from:
https://www.python.org/ftp/python/2.7.11/python-2.7.11.msi
Select "Add python.exe to Path" in the installer!

1. Install **GDAL core** from:
http://download.gisinternals.com/sdk/downloads/release-1500-gdal-1-11-4-mapserver-6-4-3/gdal-111-1500-core.msi

1. Install **GDAL Python** bindings from:
http://download.gisinternals.com/sdk/downloads/release-1500-gdal-1-11-4-mapserver-6-4-3/GDAL-1.11.4.win32-py2.7.msi

1. Set **GDAL environment variables** (from command line):
 
       setx PATH "%path%;C:\Program Files (x86)\GDAL"
       setx GDAL_DATA "C:\Program Files (x86)\GDAL\gdal-data"
       setx GDAL_DRIVER_PATH "C:\Program Files (x86)\GDAL\gdalplugins"
  
    
1. Install **image2leaflet**:

    1. Close and reopen the command line window
    2. run 
        
           pip install image2leaflet
            
            
# Usage

To use it:

    $ image2leaflet --help

