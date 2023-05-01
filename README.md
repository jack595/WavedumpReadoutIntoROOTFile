# The file "wavedumpReader.py is copy from thomas Langford's work. 
## But the previous reader is only able to access 751 trigger time tag which is stored in 31-bits. For 742 series, the trigger time tag is stored in 30 bits. Therefore, there are some special operaction neeeded which can be found in wavedumpReader.py and the option `self.is742` is to turn on the those options.
## If you are looking for the binary reader for CAEN 742 series, I really hope this can help you!! 

# WavedumpReadoutIntoROOTFile
Turn readout from wavedump into ROOT file


This scipt can be use like:


python TurnWaveDumpDataIntoROOT.py --input full_path_for_wave1.dat --output path_output 


OR 


python TurnWaveDumpDataIntoROOT.py --input path_for_wave*.dat/ --output path_output 
