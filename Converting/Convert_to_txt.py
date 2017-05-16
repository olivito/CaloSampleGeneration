# Remember that we need to do this beforehand
# source /afs/cern.ch/eng/clic/work/ilcsoft/HEAD-2016-04-06/init_ilcsoft.sh

import ROOT
import sys

ROOT.gSystem.Load('libDDG4')
ROOT.gSystem.Load('libDDCore')
ROOT.gSystem.Load('libDDG4Plugins')

import argparse
from pyLCIO import UTIL

def getEnergies(path_to_file, outfile):
  idDecoder = UTIL.BitField64("system:5,side:2,module:8,stave:4,layer:9,submodule:4,x:32:-16,y:-16")
  idDecoderHCAL = UTIL.BitField64("system:5,side:2,module:8,stave:4,layer:9,submodule:4,x:32:-16,y:-16")
  
  fil = ROOT.TFile.Open(str(path_to_file), "read")
  iEvt = 0
    
  # We make an empty list of events
  event_list = []

  for event in fil.EVENT:

    # We make an empty list of hits (within this event)
    hit_list = []
    hit_listHCAL = []

    iEvt = iEvt + 1

    # Read HCAL
    for i in range(len(event.HCalBarrelCollection)):
      idDecoderHCAL.setValue(event.HCalBarrelCollection[i].cellID)
      
      z = idDecoderHCAL['layer'].value()
      x = idDecoderHCAL['x'].value()
      y = idDecoderHCAL['y'].value()
      E = event.HCalBarrelCollection[i].energyDeposit
      pos = event.HCalBarrelCollection[i].position
      hit_listHCAL.append((int(x), int(y), int(z), E, pos.X(), pos.Y(), pos.Z()))

    # Read ECAL
    for i in range(len(event.ECalBarrelCollection)):

      #print event.ECalBarrelCollection.getParameters()
      idDecoder.setValue(event.ECalBarrelCollection[i].cellID)

      z = idDecoder['layer'].value()
      x = idDecoder['x'].value()
      y = idDecoder['y'].value()
      E = event.ECalBarrelCollection[i].energyDeposit
      pos = event.ECalBarrelCollection[i].position
      if (z < 25):
          hit_list.append((int(x), int(y), int(z), E, pos.X(), pos.Y(), pos.Z()))

    # Read energy
    gunpx = event.MCParticles[0].psx
    gunpy = event.MCParticles[0].psy
    gunpz = event.MCParticles[0].psz
    m = event.MCParticles[0].mass
    gunE = ROOT.TMath.Sqrt(m*m + gunpx*gunpx + gunpy*gunpy + gunpz*gunpz)
    pdgID = event.MCParticles[0].pdgID

    event_list.append({'pdgID' : pdgID, 'E': gunE, 'px':gunpx, 'py':gunpy, 'pz':gunpz, 'ECAL': hit_list, 'HCAL': hit_listHCAL})

    print(len(hit_list), len(hit_listHCAL))

  # Append this event to the event list
  text_file = open(outfile, "w") 
  for evt in event_list:  
    text_file.write(str(evt)+"\n")
  text_file.close()

if __name__ == "__main__":
  
  inFile = sys.argv[1]
  outFile = sys.argv[2]
  getEnergies(inFile, outFile)

  # # convert the root file to txt file
  # out = sys.argv[1].replace(".root",".txt")
  # getEnergies(sys.argv[1], out)