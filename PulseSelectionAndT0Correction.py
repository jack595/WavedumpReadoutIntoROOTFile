# -*- coding:utf-8 -*-
# @Time: 2024/1/7 22:35
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: PulseSelectionAndT0Correction.py
import matplotlib.pylab as plt
import numpy as np
import pandas as pd

plt.style.use("/afs/ihep.ac.cn/users/l/luoxj/Style/Paper.mplstyle")
import sys

sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/root_tool/python_script/")

from DataReader import GetPeakToValleyRatio
from LoadMultiFiles import LoadMultiFilesDataframe
from TimeProfileTools import GetT0FromTR
from TimeProfileTools import CorrectT0ForEachChannel, ChannelsNameForAnalysis
import swifter
from glob import glob

def PulseSelectionIndex(row,  channel, PeakToValleyRatio_threshold=0.5,
                        amp_threshold=4, ):
    if len(row[f"amplitude_{channel}"])>0:
        return (np.array(row[f"PeakToValleyRatio_{channel}"])>PeakToValleyRatio_threshold)&(np.array(row[f"amplitude_{channel}"])>amp_threshold)
    else:
        return None

def GetDataframeAfterCut(df_TQ:pd.DataFrame, chanel_T0:str, WithExtraT0=False):
    df_TQ["t0"] = GetT0FromTR(df_TQ, name_channel_trigger=chanel_T0)
    if WithExtraT0 and ("T_constant_frac_ch1" in df_TQ.columns):
        print("Getting Extra t0.........")
        df_TQ["t0_dE"] = GetT0FromTR(df_TQ, name_channel_trigger="ch1")

    v_channels = ChannelsNameForAnalysis(df_TQ)
    for channel in v_channels:
        if channel==chanel_T0:
            continue
        df_TQ[f"PeakToValleyRatio_{channel}"] = df_TQ.swifter.apply(lambda row:
                                                                    GetPeakToValleyRatio(np.array(row[f"amplitude_{channel}"]),
                                                                     np.array(row[f"valley_{channel}"])) if len(row[f"amplitude_{channel}"]) else [], axis=1 )
        df_TQ[f"TagVetoCrossTalk_{channel}"] = df_TQ.swifter.apply(lambda row:PulseSelectionIndex(row, channel), axis=1)
        df_TQ[f"T_CorrectedT0_AfterCut_{channel}"] = df_TQ.apply(lambda row:
                                                                         (np.array(row[f"T_constant_frac_{channel}"])[row[f"TagVetoCrossTalk_{channel}"]]-row["t0"]) if
                                                                         # print(row[f"TagVetoCrossTalk_{channel}"]) if
                                                                         (not np.isnan(row["t0"])) and (not row[f"TagVetoCrossTalk_{channel}"] is None) and (len(row[f"TagVetoCrossTalk_{channel}"])>0)
                                                                         else [], axis=1 )
        if WithExtraT0 and ("T_constant_frac_ch1" in df_TQ.columns):
            df_TQ[f"T_CorrectedT0Extra_AfterCut_{channel}"] = df_TQ.apply(lambda row:
                                                                         (np.array(row[f"T_constant_frac_{channel}"])[row[f"TagVetoCrossTalk_{channel}"]]-row["t0_dE"]) if
                                                                         (not np.isnan(row["t0"])) and (not row[f"TagVetoCrossTalk_{channel}"] is None) and (len(row[f"TagVetoCrossTalk_{channel}"])>0)
                                                                         else [], axis=1 )

        df_TQ[f"Q_CorrectedT0_AfterCut_{channel}"]  = df_TQ.apply(lambda row:
                                                                          np.array(row[f"Q_{channel}"])[row[f"TagVetoCrossTalk_{channel}"]] if
                                                                            len(row[f"T_CorrectedT0_AfterCut_{channel}"]) > 0 else [],
                                                                           axis=1)

        df_TQ[f"T_WithMaxQ_CorrectedT0_AfterCut_{channel}"]  = df_TQ.apply(lambda row:
                                                                  row[f"T_CorrectedT0_AfterCut_{channel}"][np.argmax(row[f"Q_CorrectedT0_AfterCut_{channel}"])] if
                                                                  len(row[
                                                                          f"T_CorrectedT0_AfterCut_{channel}"]) > 0 else None,
                                                                           axis=1)

        df_TQ[f"Q_Max_CorrectedT0_AfterCut_{channel}"]  = df_TQ.apply(lambda row:
                                                                           np.max(row[f"Q_CorrectedT0_AfterCut_{channel}"]) if
                                                                           len(row[
                                                                                   f"T_CorrectedT0_AfterCut_{channel}"]) > 0 else None,
                                                                           axis=1)

        df_TQ[f"Amp_CorrectedT0_AfterCut_{channel}"]  = df_TQ.apply(lambda row:
                                                                            np.array(row[f"amplitude_{channel}"])[row[f"TagVetoCrossTalk_{channel}"]] if
                                                                            len(row[
                                                                                    f"T_CorrectedT0_AfterCut_{channel}"]) > 0 else [],
                                                                    axis=1)
        df_TQ[f"Valley_CorrectedT0_AfterCut_{channel}"]  = df_TQ.apply(lambda row:
                                                                               np.array(row[f"valley_{channel}"])[row[f"TagVetoCrossTalk_{channel}"]] if
                                                                               len(row[
                                                                                       f"T_CorrectedT0_AfterCut_{channel}"]) > 0 else [],
                                                                       axis=1)

        df_TQ[f"Width_CorrectedT0_AfterCut_{channel}"]  = df_TQ.apply(lambda row:
                                                                              np.array(row[f"width_{channel}"])[row[f"TagVetoCrossTalk_{channel}"]] if
                                                                              len(row[
                                                                                      f"T_CorrectedT0_AfterCut_{channel}"]) > 0 else [],
                                                                      axis=1)
    return df_TQ

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Apply Signal Pulse Discrimination and T0 Correction T/Q pairs")
    parser.add_argument("--input-path",type=str, help="path of intput pkl files(The pkl file output from ReconstructTQPairs.py)")
    parser.add_argument("--Digitizer",type=str, help="Digitizer type to Process")
    parser.add_argument("--output",type=str, default="", help="path of output file(*.pkl)")
    parser.add_argument("--channelT0",type=str, default="", help="the name of channel to get the t0(--channelT0 ch3)")
    parser.add_argument("--dEPMTTrigger", action="store_true", default=False,
                        help="dE PMT Trigger Mode have different t0 trigger")
    args = parser.parse_args()
    from ArgsparseTools import PrintArgsParameters
    PrintArgsParameters(args)


    # Extract Name of Digitizer from path
    import os
    directory = args.input_path
    Digitizer = args.Digitizer
    print(f"~~~~~~~~~~~~~~~~Processing {Digitizer} Digitizer~~~~~~~~~~~")

    # Set Default Output Path
    if args.output!="":
        output_path = args.output
    else:
        print("=======> Save Output to Default Path")
        output_path = directory+"/"+Digitizer+"_AfterCutAndT0Correction.pkl"
    print(f"Output Path:\t{output_path}")

    channel_t0 = None
    if args.channelT0=="":
        sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/Data_PMT_test_dEdxExp/code/KrBeamTest/")
        from GlobalVariables import GetDictT0Channel
        if args.dEPMTTrigger:
            print("->>>>>>>>>>Running with dE PMT Trigger Configure")
        else:
            print("->>>>>>>>>>Running with t_stop Trigger Configure")

        dict_channel_t0 = GetDictT0Channel(args.dEPMTTrigger)
        channel_t0 = dict_channel_t0[Digitizer]
    else:
        channel_t0 = args.channelT0

    print(f"------>>  Subtract t0 from {channel_t0}  <<------- ")

    template_files_prefix = f"{directory}/{Digitizer}"

    # Check Splitting file list
    file_list_splitMode = []
    for file in glob(template_files_prefix+"_*.pkl"):
        if "_AfterCutAndT0Correction" not in file:
            file_list_splitMode.append(file)

    # Loading Data
    if len(file_list_splitMode)>0:
        print(f"Running Splitting Mode, Loading {Digitizer}_*.pkl files")
        print("Loading Files:\t", glob(template_files_prefix+"_*.pkl"))
        df_TQ = LoadMultiFilesDataframe(template_files_prefix+"_*.pkl", file_key_excluded="_AfterCutAndT0Correction")
    else:
        print(f"Running Not Splitting Mode, Loading {template_files_prefix}.pkl")
        df_TQ = LoadMultiFilesDataframe(template_files_prefix + ".pkl")
    GetDataframeAfterCut(df_TQ, channel_t0, WithExtraT0=(True if args.Digitizer=="DT5751" else False))
    list_columns_save = ["triggerTime", "triggerTimeTag"]
    for column in df_TQ.columns:
        if "CorrectedT0" in column:
            list_columns_save.append(column)

    # Saving TQ pairs After Cut and T0 Correction
    df_TQ_save = df_TQ[list_columns_save]
    df_TQ_save.to_pickle(output_path)
