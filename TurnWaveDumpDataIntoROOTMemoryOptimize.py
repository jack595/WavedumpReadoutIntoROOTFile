# -*- coding:utf-8 -*-
# @Time: 2022/12/30 16:58
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: TurnWaveDumpDataIntoROOT.py
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import sys
from array import array

import ROOT
from wavedumpReader import DataFile
from tqdm import tqdm
import glob
from copy import copy
def MergeEventsDictionary(v_dir:list, return_array=True):
    keys_one_dir = v_dir[0].keys()
    for dir in v_dir:
        if keys_one_dir != dir.keys():
            print("ERROR: Input dictionaries should have the same keys!!!!!!!!!!!!")
            exit(1)

    # Initialization
    dir_return = copy(v_dir[0])

    # Merge into one dictionary
    for key in dir_return.keys():
        dir_return[key] = list(dir_return[key])
    for dir in v_dir[1:]:
        for key in dir.keys():
            dir_return[key].extend(list(dir[key]))
    if return_array:
        for key in dir_return.keys():
            dir_return[key] = np.array(dir_return[key])
    return dir_return

def WaveDumpReader(path_file:str, is5742=False):
    """
    Generator to read binary file row by row.
    """
    reader = DataFile(path_file, is5742)
    while True:
        try:
            trigger = reader.getNextTrigger()
            yield {"boardID": reader.boardId, "filePath": trigger.filePos,
                   "channel": trigger.channel, "pattern": trigger.pattern,
                   "eventCounter": trigger.eventCounter, "triggerTimeTag": trigger.triggerTimeTag,
                   "triggerTime": trigger.triggerTime, "waveform": trigger.trace}

        except AttributeError:
            print("AttributeError!!!")
            break


def SaveWaveDumpDictIntoROOTWithMerging(dict_generator:dict, path_output:str, nEvts:int=-1,):
    # Set related variables
    file = ROOT.TFile.Open(path_output, "recreate")
    tree = ROOT.TTree("WaveDump", "WaveDump")

    pbar = tqdm()

    hasCreatedOverlapBranch = False
    v_name_channels = []
    i_entry = 0
    break_loop = False
    while True:
        set_triggerTimeTag = set() # For Checking same triggerTime in the same row
        for i, (file_name, generator) in enumerate(dict_generator.items()):
            try:
                OneEvent = next(generator)
                set_triggerTimeTag.add(OneEvent["triggerTimeTag"])
            except Exception as e:
                break_loop = True
                print(f"An error occurred: {e}")
                break
            ################################################################################################
            # Initialize Branch
            if i_entry==0:
                print("Running:\t", file_name)
                v_name_channels.append(OneEvent["channel"])
                # initialize waveform branch
                length_wave = len(OneEvent["waveform"])
                name_branch = "waveform_ch" + str(OneEvent["channel"])
                locals()[name_branch] = array("I", length_wave * [0])
                tree.Branch(name_branch, locals()[name_branch], f"{name_branch}[{length_wave}]/I")

                if i==0:
                    length_waveform = np.empty(1, "int")
                    tree.Branch("length_waveform", length_waveform, "length_wave/I")
                # Initialize Branch of TTree
                for key in OneEvent.keys():
                    if  ("waveform" != key) and (i==0):
                        locals()[key] = np.empty(1, "float64" if (key=="triggerTime")or(key=="triggerTimeTag") else "int")
                        tree.Branch(key, locals()[key], f"{key}/"+("D" if key=="triggerTime" else "I"))
            ##################################################################################################

            # Fill TTree
            for key, item in OneEvent.items():
                if key == "triggerTime":
                    locals()[key][0] = item
                elif "waveform" in key:
                    name_branch = key+"_ch"+str(OneEvent["channel"])
                    for k in range(length_wave):
                        locals()[name_branch][k] = int(item[k])
                    length_waveform[0] = length_wave
                else:
                    locals()[key][0] = item
        if break_loop:
            break
        tree.Fill()


        if len(set_triggerTimeTag)!=1:
            print(f"ERROR:\tThere exist different triggerTime in the different *.dat!!! Set_TriggerTag:\t{set_triggerTimeTag}")
            exit(0)
        i_entry +=1
        if (nEvts!=-1) and(i_entry>nEvts):
            break
        if i_entry%1000:
            pbar.update(1)


    tree.Write()
    file.Write()
    file.Close()


if __name__ == "__main__":
    from tqdm import tqdm
    import argparse
    parser = argparse.ArgumentParser("Turn WaveDump Readout file(*.dat) into ROOT file")
    parser.add_argument("--input",type=str, help="path of intput files(directory for *.dat, for example /tmp/)")
    parser.add_argument("--output",type=str, default="./test.root", help="path of output file(*.root)")
    parser.add_argument("--nEvts",type=int, default=-1, help="How many events to process in each file")
    parser.add_argument("--MergerChannels", "-m", default=False,  action="store_true",
                        help="Merge different channels from the same event into one entry")
    args = parser.parse_args()


    # Check whether is 742 series
    if "742" in args.input:
        print("Attention:\tReading the data in 742 Series Rules!!!!!!!")
        is742 = True
    else:
        print("Attention:\tReading the data in 751 Series Rules!!!!!!!")
        is742 = False

    # Case for inputting one file
    if ".dat" in args.input:
        print("# No Merging Mode hasn't been implemented!!!!!!!!!")
        exit(0)
        # generator = WaveDumpReader(args.input, nEvts=args.nEvts, is5742=is742)
        # SaveWaveDumpDictIntoROOT(generator, args.output)
    # else:
    # if ".dat" in args.input:
    #     dict_wave = WaveDumpReader(args.input, return_Dataframe=False, nEvts=args.nEvts,
    #                                is5742=is742)
    #     dict_wave["fileID"] = [int(args.input.split(".dat")[0][-1])]*len(dict_wave["waveform"])
    else:
    # Case for inputting path of directory
        v_dict = []
        if "/" == args.input[-1]:
            input_path = args.input+"*.dat"
        else:
            input_path = args.input+"/*.dat"
        v_files = glob.glob(input_path)

        dict_generator = {}

        for file in tqdm(v_files):
            dict_generator[file] = WaveDumpReader(file,  is5742=is742)

        if args.MergerChannels:
            print("Attention:\tRunning in Merging mode!!!!!!!!!!!!!!!")
            SaveWaveDumpDictIntoROOTWithMerging(dict_generator, args.output,nEvts=args.nEvts)
        else:
            print("# No Merging Mode hasn't been implemented!!!!!!!!!")
            exit(0)
