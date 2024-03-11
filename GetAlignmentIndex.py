# -*- coding:utf-8 -*-
# @Time: 2023/5/16 9:31
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: GetAlignmentIndex.py
import matplotlib.pylab as plt
import numpy as np
from IPython.display import display

plt.style.use("/afs/ihep.ac.cn/users/l/luoxj/Style/Paper.mplstyle")
import sys

sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/root_tool/python_script/")
from DigitizerSychronization import GetAlignedEventsPair_Simplified
from WavedumpDataAnalysisTools import SetAlignmentCriteriaTo0
from LoadMultiFiles import LoadMultiFilesDataframe, LoadOneFileUproot
from WavedumpDataAnalysisTools import FindTimeCriteria, CheckIndexStart

from DataReader import WaveDumpReader

if __name__ == "__main__":
    # Usage example:
    #python GetAlignmentIndex.py --list-path \
    # /afs/ihep.ac.cn/users/l/luoxj/Data_PMT_test_dEdxExp_junofs/Sr90R7600ProvideTrigger/DT5742/wave_0.dat\
    # /afs/ihep.ac.cn/users/l/luoxj/Data_PMT_test_dEdxExp_junofs/Sr90R7600ProvideTrigger/V1751/wave0.dat
    import argparse
    parser = argparse.ArgumentParser("Synchronization of Digitizers")
    parser.add_argument("--list-path",type=str, action="append", nargs="+",
                        help="data path for each digitizers")
    parser.add_argument("--save-path",type=str, help="path to save aligned index",
                        default="")
    args = parser.parse_args()

    from ArgsparseTools import PrintArgsParameters
    PrintArgsParameters(args)

    if args.save_path=="":
        path_save_output = "/".join(args.list_path[0][0].split("/")[:-2])+"/dict_index.npz"
    else:
        path_save_output = args.save_path

    filelist = args.list_path[0]
    dict_digitizer2path = {}
    for file in filelist:
        if ".dat" in file:
            dict_digitizer2path[file.split("/")[-2]] = file
        elif (".root" in file) or (".pkl" in file):
            dict_digitizer2path[file.split("/")[-1].split(".")[0].split("_")[0]] = file
        else:
            print("*.pkl, *.root OR *.dat are expected to input! Please Check Input!!!Now input is "+file)
            exit(0)
    print("dict_digitizer2path:\t",dict_digitizer2path)

    dict_df_wave = {}
    for key, path in dict_digitizer2path.items():
        is_742 = True if "742" in path else False
        print(key, path)
        if ".pkl" in path:
            dict_df_wave[key] =  LoadMultiFilesDataframe(path)
        elif ".dat" in path:
            dict_df_wave[key] = WaveDumpReader(path, is5742=is_742, nEvts=-1, save_wave=False)
        elif ".root" in path:
            dict_df_wave[key] = LoadOneFileUproot(path, name_branch="WaveDump")
        else:
            print("*.pkl, *.root OR *.dat are expected to input! Please Check Input!!!")
            exit(0)

    dict_delta_triggerTime = {}
    dict_triggerTime = {}
    for key, df_wave in dict_df_wave.items():
        dict_delta_triggerTime[key] = np.diff(df_wave["triggerTime"])
        dict_triggerTime[key] = df_wave["triggerTime"]
        # display(df_wave)

    n_events_to_align, dict_index_start = FindTimeCriteria(dict_delta_triggerTime)
    dict_triggerTimeWithCriteria = SetAlignmentCriteriaTo0(dict_triggerTime, dict_index_start)
    print("Available Keys:\t", dict_triggerTimeWithCriteria.keys())
    dict_index_aligned = GetAlignedEventsPair_Simplified(dict_triggerTimeWithCriteria, key_base="DT5742" if "DT5742" in dict_triggerTimeWithCriteria.keys() else "DT5751")
    for key in dict_triggerTimeWithCriteria.keys():
        # print(dict_index_aligned[key][-10:])
        v_time = dict_triggerTimeWithCriteria[key][dict_index_aligned[key][-10:]]-dict_triggerTimeWithCriteria[key][dict_index_aligned[key][-10:][0]]
        # print(v_time)
        # plt.scatter(v_time, [key]*len(v_time), s=3)

    for key in dict_triggerTimeWithCriteria.keys():
        v_time = dict_triggerTimeWithCriteria[key][dict_index_aligned[key][-1]:dict_index_aligned[key][-1]+10]
        # plt.scatter(v_time-dict_triggerTimeWithCriteria[key][dict_index_aligned[key][-10:][0]], [key]*len(v_time), s=3, marker="*")
    dict_index_aligned_forRawData = {}
    for key in dict_index_aligned.keys():
         dict_index_aligned_forRawData[key] = np.array(dict_index_aligned[key])+dict_index_start[key]


    print("Saving Output.......")
    np.savez( path_save_output, dict_index_aligned=dict_index_aligned_forRawData )





