# Nikolaus Howe (May 2016)
# Kaustuv Datta and Jayesh Mahaptra (July 2016)
# Maurizio Pierni (April 2017)
# Matt Zhang (May 2017)

from __future__ import division
import numpy as np
import scipy.stats
import sys
import ast
import h5py
import nsub
import os
from featuresList import FeaturesList
import addFeatures

##################################
# Functions for finding centroid #
##################################

# Given a list of distances and corresponding weights, calculate the weighted average
def findMidpoint(distance, energy):
    return np.average(distance, weights = energy)
    
# Given an array of interactions (ix,iy,iz,E,X,Y,Z), returns the weighted average (aveY, aveZ)
def findEventMidpoint(event):
    Yave = findMidpoint(event[:,5], event[:,3]) 
    Zave = findMidpoint(event[:,6], event[:,3]) 
    return (Yave, Zave)

##################################################
# Check if between bounds for calorimeter window #
##################################################

#Checking range for ECAL (including min and max as the total number of cells is odd)
def withinEcal(value, mymin, mymax):
    return (value >= mymin and value <= mymax)

#Checking range for HCAL (including min and max as the total number of cells is odd)     
def withinHcal(value, mymin, mymax):
    return (value >= mymin and value <= mymax)

########################################
# Implementation of calorimeter window #
########################################

# Given an event, get the 25x25x25 array of energies around its barycentre
def getECALArray(event):
    
    # Get the event midpoint (returns absolute Y,Z weighted average at index 0,1 respectively)
    midpoint = findEventMidpoint(event)
    
    #Map absolute Y  and Z weighted average to ix and iy respectively
    #Rounding the mapping to get barycenter ix,iy values as integer (in order to select a particular cell as barycenter)
    # CHECKPOINT - this function may need updating - why is pixel [x, y] obtained by just dividing position [x, y] by 5?
    barycenter_ix = round(midpoint[0]/5)
    barycenter_iy = round(midpoint[1]/5)
    
    # Get the limit points for our grid
    # CHECKPOINT - what about wraparound?
    xmin = barycenter_ix - 12
    xmax = barycenter_ix + 12
    ymin = barycenter_iy - 12
    ymax = barycenter_iy + 12
    
    # Create the empty array to put the energies in
    # CHECKPOINT - cells are non-uniform in z after 16 layers (last layers are twice as thick, according to https://www.dropbox.com/s/ktu1ly0ge9n4jyd/CaloImagingDataset.pdf?dl=0)
    final_array = np.zeros((25, 25, 25))
    
    # Fill the array with energy values, if they exist
    for ix, iy, iz, E, x, y, z in event:
        if withinEcal(ix, xmin, xmax) and withinEcal(iy, ymin, ymax):
            final_array[ix-xmin,iy-ymin,iz] = E
    return final_array,midpoint[0],midpoint[1]

# Given an event and Absolute Y and Z coordinates of the ECAL centroid
# get the 4x4x60 array of energies around the same coordinates of HCAL
def getHCALArray(event,midpointY,midpointZ):
    
    # Use the Y and Z of ECAL centroid
   
    #Map absolute Y and Z weighted average to ix and iy respectively
    #Rounding the mapping to get barycenter ix,iy values as integer (in order to select a particular cell as barycenter)
    # CHECKPOINT - same issue as above
    barycenter_ix = round(midpointY/30)
    barycenter_iy = round(midpointZ/30)
    
    # Get the limit points for our grid
    # CHECKPOINT - same issue as above
    xmin = barycenter_ix - 2
    xmax = barycenter_ix + 2
    ymin = barycenter_iy - 2
    ymax = barycenter_iy + 2
    
    # Create the empty array to put the energies in
    final_array = np.zeros((5, 5, 60))
    
    # Fill the array with energy values, if they exist
    #for element in event:
    #    if within(element[0], xmin, xmax) and within(element[1], ymin, ymax) and within(element[2], zmin, zmax):
    #        final_array[element[0], element[1], element[2]] = element[3]
  
    # Fill the array with energy values, if they exist
    for ix, iy, iz, E, x, y, z in event:
        if withinHcal(ix, xmin, xmax) and withinHcal(iy, ymin, ymax):
            final_array[ix-xmin,iy-ymin,iz] = E
    return final_array

############################
# File reading and writing #
############################

def convertFile(inFile, outFile):

    # Open file and extract events
    with open(inFile) as myfile:
        my_events_string = myfile.read().replace('\n', '')
    my_events_string = my_events_string.replace(' ', '')
    my_events_string = my_events_string.replace('}{','} {')
    my_events_string = my_events_string.split()

    ########################
    # Calculating features #
    ########################

    myFeatures = FeaturesList()

    # Loop through all the events
    for index, string in enumerate(my_events_string):

        my_event = ast.literal_eval(string)

        if index%200 == 0:
            print "Event", index, "out of", len(my_events_string)

        # Make a list containing all the cell readouts of ECAL for the event and store it in a single ECAL array
        ECAL_list = []
        for cell_readout in my_event['ECAL']:
            ECAL_list.append(np.array(cell_readout))
        if len(ECAL_list)<= 0: continue

        # Get the barycenter details (The ECAL array around barycenter, Absolute Y and Z coordinates of ECAL centroid at index 0,1,2 respectively)
        ECAL_barycenter_details = getECALArray(np.array(ECAL_list))

        # Append the ECAL array of 25x25x25 cells around the barycenter to the ECAL array list
        ECALarray = ECAL_barycenter_details[0]/1000.*50 # Geant is in units of 1/50 GeV for some reason
        myFeatures.add("ECAL", ECALarray)

        # Make a list containing all the cell readouts of HCAL for the event and store it in a single ECAL array
        HCAL_list = []
        for cell_reading in my_event['HCAL']:
            HCAL_list.append(np.array(cell_reading))

        # Pass the absolute Y and Z cooridnates as input for determining HCAL array around barrycenter and append it to the HCAl array list
        HCALarray = getHCALArray(np.array(HCAL_list),ECAL_barycenter_details[1],ECAL_barycenter_details[2])/1000.*50 # Geant is in units of 1/50 GeV for some reason
        myFeatures.add("HCAL", HCALarray)

        # Truth info from txt file
        myFeatures.add("energy", my_event['E'])
        myFeatures.add("pdgID", my_event['pdgID'])

    # Save features to an h5 file
    f = h5py.File(outFile, "w")
    for key in myFeatures.keys():
        f.create_dataset(key, data=np.array(myFeatures.get(key)).squeeze(),compression='gzip')
    f.close()
    
#################
# Main function #
#################

if __name__ == "__main__":
    import sys
    inFile = sys.argv[1]
    outFile = sys.argv[2]
    print "Converting file"
    convertFile(inFile, outFile+"_temp")
    print "Calculating features"
    addFeatures.convertFile(outFile+"_temp", outFile)
    os.remove(outFile+"_temp")
