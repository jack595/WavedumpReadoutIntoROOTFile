# -*- coding:utf-8 -*-
# @Time: 2024/1/11 12:40
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: GatherDataTogether.py
import matplotlib.pylab as plt
import numpy as np

plt.style.use("/afs/ihep.ac.cn/users/l/luoxj/Style/Paper.mplstyle")
import sys
sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/root_tool/python_script/")
from glob import glob
from copy import copy
import pandas as pd
import os
from LoadMultiFiles import LoadMultiFilesDataframe, LoadOneFile

v_Digitizer = ["DT5751", "V1751", "DT5742"]
def LoadDigitizerData(path:str, v_Digitizers):
    dict_df_TQ_raw = {}
    for Digitizer in v_Digitizers:
        print(f"Loading Data of {Digitizer}.....")
        if os.path.isfile(f"{path}{Digitizer}_1.pkl"):
            df_TQ_BeforeCut = LoadMultiFilesDataframe(f"{path}{Digitizer}_*.pkl", 
                                                      file_key_excluded="AfterCutAndT0Correction")
        elif os.path.isfile(f"{path}{Digitizer}.pkl"):
            df_TQ_BeforeCut = LoadMultiFilesDataframe(f"{path}{Digitizer}.pkl",
                                                      file_key_excluded="AfterCutAndT0Correction")
        else:
            print(f"Cannot Load TQ Dataset of {Digitizer}!!! Please Check!")
            exit(1)
            
        df_TQ_AfterCut = LoadMultiFilesDataframe(f"{path}{Digitizer}_AfterCutAndT0Correction.pkl")
        df_TQ_AfterCut.drop(["triggerTime", "triggerTimeTag"],axis=1, inplace=True)
        df_TQ_concat = pd.concat((df_TQ_BeforeCut, df_TQ_AfterCut), axis=1)

        # Tag Dataset Columns with Digitizers
        v_columns = [column for column in df_TQ_concat.columns if "_ch" in column]
        dict_rename_column = {}
        for column in v_columns:
            dict_rename_column[column] = f"{Digitizer}_{column}"
        df_TQ_concat.rename(columns=dict_rename_column,
                            inplace=True)

        dict_df_TQ_raw[Digitizer] = copy( df_TQ_concat )

    return copy(dict_df_TQ_raw)

def LoadIndexAlignmentBetweenDigitizers(path_index_file:str):
    if not os.path.isfile(path_index_file):
        print("Cannot Load Alignment Index file `Dict_Index.npz`, Please Check Workflow!!")
        exit(1)
    dict_align_index_Digitizers = LoadOneFile(path_index_file, key_in_file="dict_index_aligned")
    return dict_align_index_Digitizers


def MergeDatasetBetweenDigitizers(dict_df_TQ_raw:dict,
                                  dict_align_index_Digitizers:dict):
    from collections import Counter
    df_TQ_MergeDigitizers = pd.DataFrame()
    
    # Align Dataset Between Digitizers with Previous Index
    for Digitizer, index_align_digitizer in dict_align_index_Digitizers.items():
        df_TQ_tmp = dict_df_TQ_raw[Digitizer].loc[list(index_align_digitizer)]

        df_TQ_tmp[f"EvtID_{Digitizer}"] = df_TQ_tmp.index
        df_TQ_tmp.reset_index(drop=True,inplace=True)
        if len(df_TQ_MergeDigitizers):
            # Check TriggerTime Alignment
            print("Check Trigger Time Alignment:\t",
                  Counter( (np.diff(np.array(df_TQ_MergeDigitizers["triggerTime"]))-np.diff(np.array(df_TQ_tmp["triggerTime"])))<10 ))
            df_TQ_tmp.drop(["triggerTime", "triggerTimeTag"], axis=1, inplace=True)
            df_TQ_MergeDigitizers = pd.concat((df_TQ_MergeDigitizers,
                                               copy(df_TQ_tmp)), axis=1)
        else:
            df_TQ_MergeDigitizers = copy(df_TQ_tmp)
    return df_TQ_MergeDigitizers



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Apply Signal Pulse Discrimination and T0 Correction T/Q pairs")
    parser.add_argument("--input-path",type=str, help="path of intput pkl files(The pkl file output from ReconstructTQPairs.py)")
    parser.add_argument("--output",type=str, default="", help="path of output file(*.pkl)")
    args = parser.parse_args()
    from ArgsparseTools import PrintArgsParameters
    PrintArgsParameters(args)

    dict_alignment_index = LoadIndexAlignmentBetweenDigitizers(args.input_path+"/Dict_Index.npz")

    v_Digitizers = sorted(list( dict_alignment_index.keys()) )
    dict_df_TQ_raw = LoadDigitizerData(args.input_path, v_Digitizers)

    df_TQ_MergeDigitizers = MergeDatasetBetweenDigitizers(dict_df_TQ_raw, dict_alignment_index)

    if args.output=="":
        path_save_output = f"{args.input_path}/df_TQ_concatDigitizers.pkl"
    else:
        path_save_output = args.output

    print("Saving Concatenated Dataframe.............")
    df_TQ_MergeDigitizers.to_pickle(path_save_output)

