#include <fstream>
#include <iostream>
#include <vector>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include "TFile.h"
#include "TTree.h"
#include "TMath.h"
#include <dirent.h>
using namespace std;
const float epsilon = 1e-10;
const int length_742 = 1024;
const int n_channels_742 = 18;


class RawTrigger {
public:
    uint32_t pattern;
    uint32_t channel;
    unsigned long eventCounter;
    double triggerTimeTag;
    double triggerTime;
    int WaveLength;
    uint32_t boardId;
    std::vector<unsigned short> trace; // or std::vector<float> for is742 case
    float trace_742[1024];

    // Additional fields for is742
    uint32_t DC_offset;
    uint32_t Start_Index_Cell;
};

class DataFile {
public:
    DataFile(const std::string& fileName, bool is742 = false);
    ~DataFile(){};
    RawTrigger* getNextTrigger();
    RawTrigger* trigger= nullptr;

    unsigned long counter;
    void close();

private:
    std::ifstream file;
    bool is742;
    double oldTimeTag;
    unsigned long timeTagRollover;
    unsigned long eventCounter_previous;

    uint32_t readUInt32();
};

DataFile::DataFile(const std::string& fileName, bool is742)
        : file(fileName, std::ios::binary), is742(is742), oldTimeTag(0), timeTagRollover(0),
        eventCounter_previous(0),counter(0){
}

uint32_t DataFile::readUInt32() {
    uint32_t value;
    file.read(reinterpret_cast<char*>(&value), sizeof(value));
    return value;
}

RawTrigger* DataFile::getNextTrigger() {
    if (!file.good()) return nullptr;

    if (trigger== nullptr)
    {
        cout << "Start to Initialize trigger object!!!" <<endl;
        trigger = new RawTrigger();
    }


    try {
        if (is742) {
            // Read the 8 long-words of the event header
            uint32_t i0 = readUInt32();
            trigger->boardId = readUInt32();
            trigger->pattern = readUInt32();
            trigger->channel = readUInt32();
            trigger->eventCounter = readUInt32();
            trigger->triggerTimeTag = readUInt32();
            trigger->DC_offset = readUInt32();
            trigger->Start_Index_Cell = readUInt32();

            int eventSize = (i0 - 32) / 4;
            trigger->WaveLength = eventSize;
            if(eventSize!=length_742)
                cout<<"Cautious!!! The length of waveform stored in 742 files is less than 1024! We keep the rest of waveform as zeros!" << endl;
//            trigger->trace_742.resize(eventSize);
//            cout<< "Waveform Length:\t"<<eventSize<<endl;
            file.read(reinterpret_cast<char*>(trigger->trace_742), eventSize * sizeof(float));
//            for(int i=0; i<eventSize;i++)
//                file>>trigger->trace_742[i];

        } else {
            // Read the 6 long-words of the event header
            uint32_t i0 = readUInt32();
            trigger->boardId = readUInt32();
            trigger->pattern = readUInt32();
            trigger->channel = readUInt32();
            trigger->eventCounter = readUInt32();
            trigger->triggerTimeTag = readUInt32();

            int eventSize = (i0 - 24) / 2;
            trigger->WaveLength = eventSize;
            trigger->trace.resize(eventSize);
            file.read(reinterpret_cast<char*>(trigger->trace.data()), eventSize * sizeof(unsigned short));
        }

        // Time tag and time calculations
//        cout<< "timeTagRollover:\t" << timeTagRollover << endl;
//        cout<< "Old Time Tag:\t" << oldTimeTag << endl;
        trigger->triggerTimeTag = trigger->triggerTimeTag+ timeTagRollover * (is742 ? pow(2, 30) : (pow(2,31)));


        if (trigger->triggerTimeTag < oldTimeTag) {
            timeTagRollover++;
            trigger->triggerTimeTag = trigger->triggerTimeTag+ (is742 ? pow(2, 30) : (pow(2,31)));
        }

        // Convert from ticks to microseconds
        trigger->triggerTime = trigger->triggerTimeTag * (is742 ? 8.533333333e-3 : 8e-3);

//        cout << "Trigger Time:\t"<<trigger->triggerTime << "\t"<< trigger->triggerTimeTag  << endl;
        oldTimeTag = trigger->triggerTimeTag;
//        cout << "eventCounter_previous:\t"<< eventCounter_previous<<"\t"<< trigger->eventCounter<<endl;
//        cout << "Counter:\t"<< counter<<endl;


//        if (timeTagRollover>3)
//            exit(1);

        if ( (eventCounter_previous!=0)&(trigger->eventCounter-eventCounter_previous!=1) )
        {
            cout<< "End of File Reading!!!"<<endl;
//            delete trigger;
            return nullptr;
        }
        else
            eventCounter_previous = trigger->eventCounter;
        counter ++;


        return trigger;
    } catch (...) {
//        delete trigger;
        return nullptr;
    }
}

void DataFile::close() {
    if (file.is_open()) {
        file.close();
    }
}

void SetTriggersListVariables(const vector<RawTrigger*> v_triggers, int& RecordLength,
                              int& BoardID, int& Channel, int& EventNumber,
                            Int_t & Pattern, double& TriggerTimeStamp, double& TriggerTime,
                            int& DCOffset, vector<vector<unsigned short>>&  v2d_waveform) {
    auto trigger = v_triggers[0];
    // Set saving variables
    RecordLength = trigger->WaveLength;
    BoardID = trigger->boardId;
    Channel = trigger->channel;
    EventNumber = trigger->eventCounter;
    Pattern = trigger->pattern;
    TriggerTimeStamp = trigger->triggerTimeTag;
    TriggerTime = trigger->triggerTime;
    DCOffset = trigger->DC_offset;

    for (int i=0;i<v2d_waveform.size();i++)
        for(int j=0;j<v2d_waveform[i].size();j++)
            v2d_waveform[i][j] = v_triggers[i]->trace[j];
}

void SetTriggersListVariables(const vector<RawTrigger*> v_triggers, int& RecordLength,
                              int& BoardID, int& Channel, int& EventNumber,
                              Int_t & Pattern, double& TriggerTimeStamp, double& TriggerTime,
                              int& DCOffset, float v2d_waveform[n_channels_742][length_742],
                              int& n_channels) {
    auto trigger = v_triggers[0];
    // Set saving variables
    RecordLength = trigger->WaveLength;
    BoardID = trigger->boardId;
    Channel = trigger->channel;
    EventNumber = trigger->eventCounter;
    Pattern = trigger->pattern;
    TriggerTimeStamp = trigger->triggerTimeTag;
    TriggerTime = trigger->triggerTime;
    DCOffset = trigger->DC_offset;
    for (int i=0;i<n_channels;i++)
        for(int j=0;j<length_742;j++)
            v2d_waveform[i][j] = v_triggers[i]->trace_742[j];

}

vector<RawTrigger*> GetTriggerEventFromDataFile(vector<DataFile*> v_DataFile)
{
    vector<RawTrigger*> v_triggers;
    for (auto dataFile:v_DataFile)
        v_triggers.push_back(dataFile->getNextTrigger());
    return v_triggers;
}

bool UpdateTrigger(vector<DataFile*> v_DataFile)
{
    for (auto dataFile:v_DataFile)
    {
        RawTrigger* trigger_tmp = dataFile->getNextTrigger();
        if (trigger_tmp== nullptr)
            return false;
    }
    return true;
}

bool CheckWhetherAlignTriggers(vector<RawTrigger*> v_triggers)
{
    bool same_triggerTime = true;
    double triggerTime_base = v_triggers[0]->triggerTime;
    for (auto trigger:v_triggers)
        same_triggerTime = same_triggerTime& (abs(trigger->triggerTime-triggerTime_base)<epsilon);

    return same_triggerTime;
}


bool containsNullptr(const std::vector<RawTrigger*>& vec) {
    for (const auto& elem : vec) {
        if (elem == nullptr)
            return true;
    }
    return false;
}

void TurnBinaryFileToROOT(vector<DataFile*> v_DataFile,
                          const bool is742,
                          const char* outfname,
                          int nEvts=-1)
{


    //TFile* f4 = new TFile(Form("%s/event1.root", dir),"recreate");
    TFile* f4 = TFile::Open(outfname, "recreate");

    Int_t RecordLength;
    Int_t BoardID;
    Int_t Channel;
    Int_t EventNumber;
    Int_t Pattern;
    Double_t TriggerTimeStamp;
    Double_t TriggerTime;
    Int_t filePath;
    TString tmp_holder;

    // For 742 Series
    Int_t DCOffset;
    Int_t Start_Index_Cell;

    // Get First Event to Determine Waveform Length
    vector<RawTrigger*> v_triggers = GetTriggerEventFromDataFile(v_DataFile);
    int n_channels_total_loaded = v_triggers.size();
    cout.precision(12);
    if (!CheckWhetherAlignTriggers(v_triggers))
    {
        cout << "Trigger Time:"<<endl;
        for (auto trigger:v_triggers)
            cout<< trigger->triggerTime<< endl;
        cout << "Loading Events Files are not Aligned Well(TriggerTime doesn't equal to each other!!!!)"<<endl;
        exit(1);
    }
//    RawTrigger* trigger = dataFile->getNextTrigger();

    vector<vector<unsigned short>> v2d_waveform;
    float v2d_waveform_742[n_channels_742][length_742];

    if (is742)
    {
//        for (int i=0;i<v_triggers.size();i++) {
//            vector<float> waveform(v_triggers[0]->WaveLength);
//            v2d_waveform_742.push_back(waveform);
//        }
        SetTriggersListVariables(v_triggers, RecordLength, BoardID, Channel, EventNumber, Pattern,
                                 TriggerTimeStamp, TriggerTime, DCOffset,
                                 v2d_waveform_742, n_channels_total_loaded);

    }else
    {
        for (int i=0;i<v_triggers.size();i++){
            vector<unsigned short> waveform(v_triggers[0]->WaveLength);
            v2d_waveform.push_back(waveform);
        }
        SetTriggersListVariables(v_triggers, RecordLength, BoardID, Channel, EventNumber, Pattern,
                                 TriggerTimeStamp, TriggerTime, DCOffset, v2d_waveform);
    }


    TTree* tree = new TTree("WaveDump","WaveDump");
    tree->Branch("length_waveform",    &RecordLength,  "length_waveform/I");
    tree->Branch("boardID",         &BoardID,       "boardID/I");
    tree->Branch("pattern", &Pattern, "pattern/I");
    tree->Branch("eventCounter",     &EventNumber,   "eventCounter/I");
    tree->Branch("triggerTime",     &TriggerTime,   "triggerTime/D"); // in us
    tree->Branch("triggerTimeTag",     &TriggerTimeStamp,   "triggerTimeTag/D"); // in us

    TString prefix_channel = "waveform_ch";
    for (int i=0; i<v_triggers.size();i++)
    {
        if (is742)
        {
//            tree->Branch(prefix_channel+v_triggers[i]->channel, &v2d_waveform_742[i] );
            tree->Branch(prefix_channel+v_triggers[i]->channel, &v2d_waveform_742[i],
                         prefix_channel+v_triggers[i]->channel+"[length_waveform]/F");

        }
        else
            tree->Branch(prefix_channel+v_triggers[i]->channel, &v2d_waveform[i] );

    }

    int lastEventNumber = -1;
    // Save the first event
    tree->Fill();
//    v_triggers.clear();

    while (true) {
        // Process each trigger as needed
        if (!UpdateTrigger(v_DataFile))
            break;

        if (!CheckWhetherAlignTriggers(v_triggers))
        {
            cout << "Trigger Time:"<<endl;
            for (auto trigger:v_triggers)
                cout<< trigger->triggerTime<< endl;

            cout << "Loading Events Files are not Aligned Well(TriggerTime doesn't equal to each other!!!!)"<<endl;
            break;
        }

        // Set saving variables
        if (is742)
            SetTriggersListVariables(v_triggers, RecordLength, BoardID, Channel,
                                     EventNumber, Pattern, TriggerTimeStamp, TriggerTime,
                                     DCOffset, v2d_waveform_742, n_channels_total_loaded);
        else
            SetTriggersListVariables(v_triggers, RecordLength, BoardID, Channel,
                                EventNumber, Pattern, TriggerTimeStamp, TriggerTime,
                                DCOffset, v2d_waveform);


        if (v_DataFile[0]->counter%1000==0)
            cout << "Entry #" << v_DataFile[0]->counter << endl;
        if ((nEvts!=-1)&(v_DataFile[0]->counter>nEvts))
            break;

        // break loop
        if(EventNumber==lastEventNumber) break;


        tree->Fill();
        lastEventNumber = EventNumber;

//        v_triggers.clear();

    }

    tree->Write();
    f4->Close();

    cout << "Finished" << endl;
}

vector<string> GetFileList(const std::string& directoryPath) {
    DIR* dirp = opendir(directoryPath.c_str());
    struct dirent* dp;
    vector<string> file_list;

    if (dirp != nullptr) {
        while ((dp = readdir(dirp)) != nullptr) {
            std::string filename(dp->d_name);
            // Check for ".dat" extension
            if (filename.size() >= 4 && filename.substr(filename.size() - 4) == ".dat") {
                std::cout << "Processing:\t"<< directoryPath+filename << std::endl;
                file_list.push_back(filename);
            }
        }
        closedir(dirp);
    } else {
        std::cerr << "Cannot open directory: " << directoryPath << std::endl;
    }
    return file_list;
}

bool endsWith(const std::string &str, const std::string &suffix) {
    if (str.length() >= suffix.length()) {
        return (0 == str.compare(str.length() - suffix.length(), suffix.length(), suffix));
    } else {
        return false;
    }
}

int main(int argc, char** argv) {

    if(argc!=4){
        cout << "syntax: " << argv[0] << " <input directory> <output filename (*.root)> <nEvts>\nnEvts=-1 means to "
                                         "loop over all the events" << endl;
        exit(1);
    }
    else {
        string path = argv[1];
        if (!endsWith(path, "/"))
        {
            cout << path << " doesn't end with /, add / at the end of the path"<< endl;
            path += "/";
        }

        auto v_file_list =
                GetFileList(path);
        vector<DataFile *> v_DataFile;

        // Check which type of digitizer
        bool is742;
        TString path_s = path;
        if (path_s.Contains("742")) {
            cout << "########## Reading 742 Series Digitizer Data ###########" << endl;
            is742 = true;
        }
        else {
            cout << "########## Reading 751 Series Digitizer Data ###########" << endl;
            is742 = false;
        }

        for (auto file: v_file_list) {
            DataFile *dataFile = new DataFile(path + file, is742); // Set to true for is742
            v_DataFile.push_back(dataFile);
        }

        TString nEvts = argv[3];
        cout<< "Output Path in BinaryFileToROOT.C:\t"<<argv[2]<<endl;

        TurnBinaryFileToROOT(v_DataFile, is742,argv[2], nEvts.Atoi());

        for (auto dataFile: v_DataFile)
            dataFile->close();
    }
    return 0;
}
