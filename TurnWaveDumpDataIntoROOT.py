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


def WaveDumpReader(path_file:str, nEvts:int=-1, return_Dataframe=True, is5742=False):
    """

    :param path_file: output from DT5751, binary file
    :param nEvts: N of events to be loaded
    :param return_Dataframe: return dataframe or dict
    :return:
    """
    reader = DataFile(path_file, is5742)
    dir_data = {"boardID":[],  "filePath":[],"channel":[], "pattern":[], "eventCounter":[],
                "triggerTimeTag":[], "triggerTime":[], "waveform":[]}
    i_event = 0
    while True:
        try:
        # if True:
            trigger = reader.getNextTrigger()
            dir_data["waveform"].append( trigger.trace)
            dir_data["boardID"].append( reader.boardId)
            dir_data["filePath"].append( trigger.filePos)
            dir_data["channel"].append( trigger.channel)
            dir_data["pattern"].append( trigger.pattern)
            dir_data["eventCounter"].append( trigger.eventCounter)
            dir_data["triggerTimeTag"].append( trigger.triggerTimeTag)
            dir_data["triggerTime"].append( trigger.triggerTime)
        except AttributeError:
            print("AttributeError!!!")
            break

        # if nEvts==-1, loops over the whole samples
        if (nEvts!=-1) & (i_event>nEvts):
            break
        i_event += 1

    if return_Dataframe:
        return pd.DataFrame.from_dict(dir_data)
    else:
        return dir_data

def SaveWaveDumpDictIntoROOT(dict_wave:dict, path_output:str):
    del dict_wave["triggerTimeTag"]
    file = ROOT.TFile.Open(path_output, "recreate")
    tree = ROOT.TTree("WaveDump", "WaveDump")

    # Initialize Branch of TTree
    length_wave = 0
    has_create_length_branch = False
    for key, item in dict_wave.items():
        if key == "waveform":
            length_wave = len(item[0])
            locals()[key] = array("I", length_wave*[0] )
            tree.Branch(key, locals()[key], f"{key}[{length_wave}]/I" )
            if has_create_length_branch:
                length_waveform =np.empty(1, "int")
                tree.Branch("length_waveform", length_waveform, "length_wave/I" )
                has_create_length_branch = True
        else:
            locals()[key] = np.empty(1, "float64" if key=="triggerTime" else "int")
            tree.Branch(key, locals()[key], f"{key}/"+("D" if key=="triggerTime" else "I"))
    # Fill TTree
    for i in range(len(dict_wave["waveform"])):
        for key, item in dict_wave.items():
            if key == "triggerTime":
                locals()[key][0] = item[i]
            elif key=="waveform":
                for k in range(length_wave):
                    locals()[key][k] = int(item[i][k])
                length_waveform[0] = length_wave
            else:
                locals()[key][0] = item[i]
        tree.Fill()
    tree.Write()
    file.Write()
    file.Close()

def SaveWaveDumpDictIntoROOTWithMerging(dict_wave:dict, path_output:str):
    del dict_wave["triggerTimeTag"]
    df_wave = pd.DataFrame.from_dict(dict_wave)
    v_name_channels = list(set(df_wave["channel"]))
    df_wave_subset = df_wave[df_wave["channel"]==v_name_channels[0]]
    df_wave_subset.rename(columns={"waveform": f"waveform_ch{v_name_channels[0]}"}, inplace=True)
    df_wave_subset.set_index("triggerTime", inplace=True)
    # Separate the rest of channels
    dict_df_diff_channels = {}
    for name_channel in v_name_channels[1:]:
        df_wave_tmp = df_wave[df_wave["channel"]==name_channel][["triggerTime", "waveform"]]
        df_wave_tmp.rename(columns={"waveform":f"waveform_ch{name_channel}"}, inplace=True)
        df_wave_tmp.set_index("triggerTime", inplace=True)
        dict_df_diff_channels[name_channel] = df_wave_tmp
    df_wave_concat = pd.concat((df_wave_subset, *dict_df_diff_channels.values()), axis=1).reset_index()

    file = ROOT.TFile.Open(path_output, "recreate")
    tree = ROOT.TTree("WaveDump", "WaveDump")

    # Initialize Branch of TTree
    length_wave = 0
    for key in df_wave_concat.columns:
        if  "waveform" in key:
            print("Running:\t",key, "\t", df_wave_concat[key].iloc[1])
            length_wave = len(df_wave_concat[key].iloc[0])
            locals()[key] = array("I", length_wave*[0] )
            tree.Branch(key, locals()[key], f"{key}[{length_wave}]/I" )
            length_waveform =np.empty(1, "int")
            tree.Branch("length_waveform", length_waveform, "length_wave/I" )
        else:
            locals()[key] = np.empty(1, "float64" if key=="triggerTime" else "int")
            tree.Branch(key, locals()[key], f"{key}/"+("D" if key=="triggerTime" else "I"))
    # Fill TTree
    for i in range(len(df_wave_concat)):
        for key in df_wave_concat.columns:
            item = df_wave_concat[key].iloc[i]
            if key == "triggerTime":
                locals()[key][0] = item
            elif "waveform" in key:
                for k in range(length_wave):
                    locals()[key][k] = int(item[k])
                length_waveform[0] = length_wave
            else:
                locals()[key][0] = item
        tree.Fill()
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
        print("Attention:\tReading the data in 742 Series Rules!!!!!!!")
        is742 = False

    dict_wave = {}
    # Case for inputting one file
    if ".dat" in args.input:
        dict_wave = WaveDumpReader(args.input, return_Dataframe=False, nEvts=args.nEvts,
                                   is5742=is742)
        dict_wave["fileID"] = [int(args.input.split(".dat")[0][-1])]*len(dict_wave["waveform"])
    else:
    # Case for inputting path of directory
        v_dict = []
        if "/" == args.input[-1]:
            input_path = args.input+"*.dat"
        else:
            input_path = args.input+"/*.dat"
        v_files = glob.glob(input_path)

        for file in tqdm(v_files):
            dict_wave_tmp = WaveDumpReader(file, return_Dataframe=False, nEvts=args.nEvts, is5742=is742)
            dict_wave_tmp["fileID"] = [int(file.split(".dat")[0][-1])]*len(dict_wave_tmp["waveform"]) if ("wave" in file)\
                else [100+int(file.split(".dat")[0][-1])]*len(dict_wave_tmp["waveform"])
            v_dict.append(copy(dict_wave_tmp))
        dict_wave = MergeEventsDictionary(v_dict, return_array=(not args.MergerChannels) )
    if args.MergerChannels:
        print("Attention:\tRunning in Merging mode!!!!!!!!!!!!!!!")
        SaveWaveDumpDictIntoROOTWithMerging(dict_wave, args.output)
    else:
        SaveWaveDumpDictIntoROOT(dict_wave, args.output)
