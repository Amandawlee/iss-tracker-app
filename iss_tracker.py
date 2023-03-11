from flask import Flask, request
from geopy.geocoders import Nominatim
import json
import xmltodict
import requests
import math
import time

app = Flask(__name__)
geocoder = Nominatim(user_agent='iss_tracker')
MEAN_EARTH_RADIUS = 6371 #km

response = requests.get(url = 'https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')
data = xmltodict.parse(response.text)

@app.route('/', methods = ['GET'])
def entire_data_set() -> dict:
    """
    Accesses data set from the URL
    
    Args:
        No arguments
    
    Returns:
        data: A dictionary of data set
    """
    return(data)

@app.route('/epochs', methods = ['GET'])
def epochs() -> list:
    """
    Generates all epochs as a list from the dictionary of the data set
    
    Args:
        No arguments
    
    Returns:
        allEpochs: A list of all epoch time stamps (with corresponding information from the data set)
    """

    if (data == []):
        return([])
        exit()

    offset = request.args.get('offset',0)
    limit = request.args.get('limit',len(data['ndm']['oem']['body']['segment']['data']['stateVector']))

    if offset:
        try:
            offset = int(offset)
        except ValueError:
            return("Error: Offset parameter must be greater than 0.")

    if limit:
        try:
            limit = int(limit)
        except ValueError:
            return("Error: Limit parameter must be greater than 0.")

    epochsList = []
    count = 0
    offset_count = 0

    for d in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        if (count == limit):
            break

        if offset_count >= offset:
            epochsList.append(d['EPOCH'])
            count += 1

        offset_count += 1

    return(epochsList)

@app.route('/epochs/<epoch>', methods = ['GET'])
def state_vector(epoch) -> list:
    """
    Displays the state vector for a specific epoch from query parameter
    
    Args:
        epoch: Specific epoch time stamp from data set (referenced in query line

    Returns:
        stateVector: The state vector of the specific epoch time stamp referenced by user
    """

    if (data == []):
        return([])
        exit()

    allEpochs = []
    for d in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        allEpochs.append(d['EPOCH'])

    if epoch in allEpochs:
        specific = allEpochs.index(epoch)
        stateVector = data['ndm']['oem']['body']['segment']['data']['stateVector'][specific]
        return(stateVector)
    else:
        return('Please enter a valid Epoch time stamp.\n')

@app.route('/epochs/<epoch>/speed', methods = ['GET'])
def speed(epoch) -> dict:
    """
    Reads the list of epochs and calculates the instantaneous speed from a specific epoch time stamp from the state vector
    
    Args:
        epoch: Specific epoch time stamp from data set (referenced in query line)
    
    Returns: 
        speedDict: The instantaneous speed calculated from the state vector in a dictionary
    """

    if (data == []):
        return([])
        exit()

    speedDict = {}
    allEpochs = epochs()
    if epoch in allEpochs:
        epochData = state_vector(epoch)
        x_dot = float(epochData['X_DOT']['#text'])
        y_dot = float(epochData['Y_DOT']['#text'])
        z_dot = float(epochData['Z_DOT']['#text'])
     
        speedDict['value'] = math.sqrt(x_dot**2 + y_dot**2 + z_dot**2)
        speedDict['units'] = "km/s"
        return(speedDict)
    else:
        return('Please enter a valid Epoch time stamp.')

@app.route('/help', methods = ['GET'])
def help() -> str:
    """
    Produces a help text that briefly describes each route
    
    Args:
        No arguments
    
    Returns:
        helpText: Returns help text as a guide for all routes
    """

    helpText = "Access elements from the NASA ISS Trajectory data set with the following routes:\n\
$ curl http://127.0.0.1:5000... \n\
\t/                                  Returns entire data set\n\
\t/epochs                            Returns list of all Epochs in the data set\n\
\t/epochs?limit=int&offset=int       Returns modified list of Epochs given query parameters\n\
\t/epochs/<epoch>                    Returns state vectors for a specific Epoch from the data set\n\
\t/epochs/<epoch>/speed              Returns instantaneous speed for a specific Epoch in the data set\n\
\t/help                              Returns help text that briefly describes each route\n\
\t/delete-data                       Deletes all data from the dictionary object\n\
\t/post-data                         Reloads the dictionary object with data from the web\n"

    return(helpText)

@app.route('/delete-data', methods = ['DELETE'])
def delete_data() -> str:
    """
    Deletes the data set from the .json file that was being used
    
    Args:
        No arguments
    
    Returns:
        deleted_data_statement: A statement (str) indicating that the  data set has been deleted
    """

    global data
    data = []
    deleted_data_statement = "NASA ISS trajectory data set has been deleted.\n"
    return(deleted_data_statement)

@app.route('/post-data', methods = ['POST'])
def post_data() -> str:
    """
    Reloads the data set from ISS Trajectory website and adds it to a .json file
    
    Args:
        No arguments
    
    Returns:
        reloaded_data_statement: A statement (str) indicating that the data set has been reloaded
    """

    global data
    response = requests.get(url = 'https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml')
    data = xmltodict.parse(response.text)
    reloaded_data_statement = "NASA ISS Trajectory data set has been reloaded.\n"
    return(reloaded_data_statement)

@app.route('/comment', methods = ['GET'])
def comment_list() -> list:
    """
    Returns the list of comments in the ISS trajectory data set

    Args:
        No arguments

    Returns:
        commentList: List object of comments from ISS trajectory data set
    """
    
    if (data == []):
        return([])
        exit()

    commentList = []
    for d in data['ndm']['oem']['body']['segment']['data']['COMMENT']:
        commentList.append(d)

    return(commentList)

@app.route('/header', methods = ['GET'])
def header_dict() -> dict:
    """
    Returns the dictionary for the header in the ISS trajectory data set

    Args:
        No arguments

    Returns:
        headerDict: Dictionary object of header from ISS trajectory data set
    """

    if (data == []):
        return([])
        exit()

    headerDict = data['ndm']['oem']['header']
    return(headerDict)

@app.route('/metadata', methods = ['GET'])
def metadata() -> dict:
    """
    Returns the dictionary of metadata in the ISS trajectory data set

    Args:
        No arguments

    Returns:
        metadata: Dictionary object of metadata from ISS trajectory dats set
    """

    if (data == []):
        return([])
        exit()

    metadata = data['ndm']['oem']['body']['segment']['metadata']
    return(metadata)

@app.route('/epochs/<epochs>/location', methods = ['GET'])
def location(epoch) -> dict:
    """
    Calculates the latitude, longitude, altitude, and geoposition using the state vectors function
    
    Args:
        epoch: Specific epoch time stamp from data set (referenced in query line)

    Returns:
        location: Location information at specific epoch time stamp in a dictionary
    """

    locationData = {}

    if (data == []):
        return([])
        exit()

    allEpochs = epochs()
    if epoch in allEpochs:
        epochData = state_vector(epoch)
        epoch = state_vector['EPOCH']
        hrs = int(epoch[9:11])
        mins = int(epoch[12:14])
        x = float(epochData['X']['#text'])
        y = float(epochData['Y']['#text'])
        z = float(epochData['Z']['#text'])
        
        locationData['LATITUDE']  = math.degrees(math.atan2(z,math.sqrt(x**2 + y**2)))
        
        longitude = math.degrees(math.atan2(y,x)) - ((hrs-12)+(mins/60))*(360/24) + 32
        if (longitude > 180):
            locationData['LONGITUDE'] = longitude - 360
        elif (longitude <-180):
            locationData['LONGITUDE'] = longitude + 360

        altitude = math.sqrt(x**2 + y**2 + z**2) - MEAN_EARTH_RADIUS
        locationData['ALTITUDE'] = { 'value' : altitude, 'units' : "km" }

        geolocation = geocode.reverse((locationData['LATITUDE'],locationData['LONGITUDE']), zoom = 10, language = 'en')
        if (geolocation == None):
            locationData['GEOPOSITION'] = "Error, the geolocation data is not available because the ISS is over the ocean."
        else:
            locationData['GEOPOSITION'] = geoposition.raw['address']

        return(locationData)

@app.route('/now', methods = ['GET'])
def now() -> dict:
    """
    Returns a dictionary of the latitude, longitude, altitude, and geopositon for the Epoch nearest in time

    Args:
        No arguments

    Returns:
        infoNow: Dictionary of location information, closest epoch, and instantaneous speed
    """

    stateVectors = data['ndm']['oem']['body']['segment']['data']['stateVector']
    infoNow = {}

    if (data == []):
        return([])
        exit()

    allEpochs = []
    minDifference = time.time() - time.mktime(time.strptime(data[0]['EPOCH'][:-5], '%Y-%jT%H:%M:%S'))
    minStateVector = data[0]

    for d in data['ndm']['oem']['body']['segment']['data']['stateVector']:
        allEpochs.append(d['EPOCH'])
        epoch = d['EPOCH']
        
        timeNow = time.time()
        timeEpoch = time.mktime(time.strptime(epoch[:-1], '%Y-%jT%H:%M:%S'))
        difference = timeNow - timeEpoch

        if abs(difference) < abs(minDifference):
            minDifference = difference
            minStateVector = epoch

    infoNow['closest_epoch'] = minStateVector['EPOCH']
    infoNow['time difference (sec)'] = minDifference
    infoNow['location'] = location(minStateVector['EPOCH']
    infoNow['speed'] = speed(minStateVector['EPOCH']

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
