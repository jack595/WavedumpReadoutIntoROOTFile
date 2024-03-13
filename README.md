# The file `wavedumpReader.py` is inherited from Thomas Langford's work. 
But the previous reader is only able to access 751 trigger time tag which is stored in 31-bits. For 742 series, the trigger time tag is stored in 30 bits. Therefore, there are some special operaction neeeded which can be found in wavedumpReader.py and the option `self.is742` is to turn on the those options.
## If you are looking for the binary reader for CAEN 742 series, I really hope this can help you!! 

# WavedumpReadoutIntoROOTFile
Turn readout from wavedump into ROOT file


This scipt can be use like:


python TurnWaveDumpDataIntoROOT.py --input full_path_for_wave1.dat --output path_output 


OR 


python TurnWaveDumpDataIntoROOT.py --input directory_for_wave*.dat/ --output path_output 


Now Cpp version has been acheived which can speed up a lot. 
Use executable file to run the transportation process:
1. For IHEP users: 
Login afs
then setup JUNO enviroment in cvmfs
`source /cvmfs/juno.ihep.ac.cn/centos7_amd64_gcc1120/Pre-Release/J23.1.0-rc5.dc1/setup.sh`
then directly use executed command
`<your_path>/BinaryFileToROOT <directory of wave_*.dat> ./test.root -1 `
* Second parameter means output path
* Third parameter is the entries of events to executed, -1 means loop over the whole dataset

2. For non-IHEP users: 
* you need ROOT enviroment to complie the project
`cd DataReaderPublic/TurnRawToROOTCppVersion/
make BinaryFileToROOT`
then you can get the executable file
* then run the command
`<your_path>/BinaryFileToROOT <directory of wave_*.dat> ./test.root -1 `
* Second parameter means output path
* Third parameter is the entries of events to executed, -1 means loop over the whole dataset
  

