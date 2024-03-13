#include <string.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <iomanip>
#include "TFile.h"
#include "TTree.h"
#include "TMath.h"
using namespace std;

void new_txt_tree(const char *infname="./wave0.txt",
                  const char* outfname="./event1.root")
//void wrong_txt_tree( const char *dir= "/junofs/users/yejiaxuan/C14junodata/202305/0606/1133_2228" )
{

    //const char* inputfile = Form("%s/ch0.txt", dir);
    //cout<<dir<<endl;
    //const char* inputfile = Form("%s/wave0.txt", dir);
    const char* inputfile = infname;
    cout <<inputfile<<endl;
    ifstream f0(inputfile);
    if(!f0.is_open()){
        cout << "file does not exists " << endl;
        exit(1);
    }

    cout << "=====================================" << endl;
    cout << "Processing file " << inputfile << endl;

    //TFile* f4 = new TFile(Form("%s/event1.root", dir),"recreate");
    TFile* f4 = new TFile(outfname,"recreate");
    const Int_t record_length =1029;

    Int_t RecordLength;
    Int_t BoardID;
    Int_t Channel;
    Int_t EventNumber;
    TString Pattern;
    Double_t TriggerTimeStamp;
    TString DCOffset;

    Double_t TriggerTime;
    TString tmp_holder; 

    Float_t ch0[record_length];

    TTree* tree = new TTree("data","data");
    tree->Branch("RecordLength",    &RecordLength,  "RecordLength/I");
    tree->Branch("BoardID",         &BoardID,       "BoardID/I");
    tree->Branch("EventNumber",     &EventNumber,   "EventNumber/I");
    tree->Branch("TriggerTimeStamp",&TriggerTimeStamp,"TriggerTimeStamp/D"); // timestamp from 5751
    tree->Branch("TriggerTime",     &TriggerTime,   "TriggerTime/D"); // in us
    tree->Branch("ch0",             ch0,            "ch0[RecordLength]/F");
  
    double oldTimeTag = 0.;
    int timeTagRollover = 0;
    int lastEventNumber = -1;

    while(f0.eof()!=1 or f0.good()==1)
    {
        f0 >> tmp_holder >> tmp_holder >> RecordLength; 
        f0 >> tmp_holder >> BoardID; 
        f0 >> tmp_holder >> Channel; 
        f0 >> tmp_holder >> tmp_holder >> EventNumber; 
        f0 >> tmp_holder >> Pattern; 
        f0 >> tmp_holder >> tmp_holder >> tmp_holder >> TriggerTimeStamp; 
        f0 >> tmp_holder >> tmp_holder >> tmp_holder >> DCOffset; 

	cout << fixed;
	cout << setprecision(0);        
        cout << RecordLength << endl;
        cout << BoardID << endl;
        cout << Channel << endl;
        cout << EventNumber << endl;
        cout << Pattern << endl;
        cout << TriggerTimeStamp << endl;
        cout << DCOffset << endl;

        if (TriggerTimeStamp < oldTimeTag){
            timeTagRollover += 1;
            oldTimeTag = TriggerTimeStamp;
        }
        else oldTimeTag = TriggerTimeStamp;

        // correcting triggerTimeTag for rollover
        TriggerTimeStamp += timeTagRollover*(TMath::Power(2, 31));

        // convert from ticks to us since the beginning of the file
        TriggerTime = TriggerTimeStamp * 8e-3;

        cout << "Entry #" << EventNumber << endl;

        // break loop
	if(EventNumber==lastEventNumber) break;


        for(int i=0; i<RecordLength;i++)
        {
            f0>>ch0[i];
        }
        
        tree->Fill();
	lastEventNumber = EventNumber;

        //break;
        //if(EventNumber>1000) break;

    }

    tree->Write();
    f4->Close();
    f0.close();
    
    cout << "Finished" << endl;

}

int main(int argc, char** argv){

    //if(argc!=2 && argc!=3){
    if(argc!=3){
        cout << "syntax: " << argv[0] << " <input filename> <output filename>" << endl;
        exit(1);
    }
    else{
        const char* infname = argv[1];
        const char* outfname = argv[2];
        new_txt_tree(infname, outfname);
    }

    return 0;

}
     
