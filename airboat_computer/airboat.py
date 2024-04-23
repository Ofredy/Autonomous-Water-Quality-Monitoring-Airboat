# System imports
import time
import math

# Library imports
from dronekit import connect, LocationGlobalRelative

# Our imports
from wqm import WQM, SERVER_IP, SERVER_PORT, OUTPUT_FILE


# System defaults
AUTO_MODE          = 'AUTO'

WAYPOINT_RADIUS    = 1.5
NORMAL_WAYPOINT    = 16
LOITER_UNLIMITED   = 17
LOITER_TIMER       = 19


def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the 
    earth's poles. It comes from the ArduPilot test code: 
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

def distance_to_current_waypoint(vehicle):
    """
    Gets distance in metres to the current waypoint. 
    It returns None for the first waypoint (Home location).
    """
    nextwaypoint = vehicle.commands.next
    if nextwaypoint==0:
        return None
    missionitem=vehicle.commands[nextwaypoint-1] #commands are zero indexed
    lat = missionitem.x
    lon = missionitem.y
    alt = missionitem.z
    targetWaypointLocation = LocationGlobalRelative(lat,lon,alt)
    distancetopoint = get_distance_metres(vehicle.location.global_frame, targetWaypointLocation)
    return distancetopoint


############################## CONNECTING & INITIALIZING VEHICLE ##############################
airboat = connect('/dev/ttyAMA0', buad=115200, wait_ready=True)
airboat_wqm = WQM(SERVER_IP, SERVER_PORT, OUTPUT_FILE)

############################## WAITING TILL AUTOPILOT BEGINS ##############################
while not airboat.mode.name == 'AUTO': 
    time.sleep(1)

############################## ONCE IN AUTOPILOT DOWNLOADING MISSION ##############################
cmds = airboat.commands
cmds.download()
cmds.wait_ready() 

############################## MISSION OPERATION ##############################
while airboat.commands.next <= len(cmds):

    ################# ONCE A LOITER_UNLIMITED WAYPOINT IS REACHED BEGIN WATER COLLECTION #################
    if cmds[airboat.commands.next].command == LOITER_UNLIMITED and WAYPOINT_RADIUS > distance_to_current_waypoint(airboat):

        # water collection
        airboat_wqm.deploy()

        # move on to next waypoint
        airboat.commands.next += 1
    
    time.sleep(0.1)
