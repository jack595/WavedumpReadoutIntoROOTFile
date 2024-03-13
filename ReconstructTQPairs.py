# -*- coding:utf-8 -*-
# @Time: 2023/11/30 11:01
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: ReconstructTQPairs.py
import pandas as pd
# import matplotlib
# matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pylab as plt
import numpy as np
import array
import tqdm

plt.style.use("/afs/ihep.ac.cn/users/l/luoxj/Style/Paper.mplstyle")
import sys

sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/root_tool/python_script/")

from DataReader import GetMeanLocAroundPeak, GetBaselineByMean, WaveformRec
from ROOT import TChain,std,vector

class WaveRecFactory:
    def __init__(self, name_file,name_branch="WaveDump", Digitizer="751",
                 TurnADC2mV=True,negative=True):
        self.chain = TChain(name_branch)
        self.chain.Add(name_file)
        self.list_waveform_leaves_in_branch = [] # leaf to reconstruct
        self.list_need_to_save = []
        self.vector_type = None
        branches = self.chain.GetListOfBranches()
        for i in range(branches.GetEntries()):
            branch = branches.At(i)
            branchName = branch.GetName()
            className = branch.GetClassName()
            if ("waveform_ch" in branchName):
                self.vector_type = className
                break

        for object_leaf in self.chain.GetListOfLeaves():
            name_leaf = object_leaf.GetName()
            if "waveform_ch" in name_leaf:
                self.list_waveform_leaves_in_branch.append(name_leaf)
            elif ("length_wave" not in name_leaf ) and ("channel" not in name_leaf):
                self.list_need_to_save.append(name_leaf)

        print("To reconstruct leaves of waveform:\t", self.list_waveform_leaves_in_branch)
        self.Digitizer = Digitizer
        # Load One Waveform to Initialize
        self.chain.GetEntry(0)

        # from HistTools import GetPeakLocOfHist
        self.factor_amplitude = 1
        # self.length_store = len(self.chain.waveform_ch0)
        # print(self.list_waveform_leaves_in_branch[0])
        # print(self.list_waveform_leaves_in_branch[0])
        # print("length:\t", getattr(self.chain,self.list_waveform_leaves_in_branch[0]))
        self.length_store = len(getattr(self.chain,self.list_waveform_leaves_in_branch[0])) if Digitizer=="751" else 1024
        self.wave_length_cut = int( 0.96*self.length_store ) if Digitizer=="742" else None
        if Digitizer=="751":
            self.bins = np.arange(-10.5, 1025) # 10 bit
        elif Digitizer=="742":
            self.bins = np.arange(-10.5, 4100) # 12 bit

        if TurnADC2mV:
            if Digitizer=="742":
                self.factor_amplitude = 0.24414
            elif Digitizer=="751":
                self.factor_amplitude = 0.97656
            else:
                print("ERROR:\tInput name of Digitizer should be 751 or 742, but now input is ", Digitizer)

        self.polarity = (-1 if negative else 1)

    def SubtractBaseline(self, wave_raw, n_baseline=50,
                     hist_find_baseline=False, check_baseline_find=False, baseline_amp=5):
        wave_return = wave_raw
        if hist_find_baseline:
            h_baseline = np.histogram(wave_return, bins=self.bins)
            # baseline, baseline_sigma = FitWithGauss(h_baseline)
            baseline = GetMeanLocAroundPeak(h_baseline)
            if check_baseline_find:
                plt.hist(wave_return, bins=self.bins, histtype="step", label=f"Peak={baseline:.2f}")
                plt.legend()
        else:
            baseline = np.mean(wave_return[:n_baseline])

        wave_return = wave_return - baseline
        if hist_find_baseline:
        #     Align mean to zero
            wave_return -= GetBaselineByMean(wave_return, n_baseline=n_baseline, baseline_amp=baseline_amp)


        return np.array( self.polarity * wave_return[:self.wave_length_cut]*self.factor_amplitude, dtype=np.float32 )

    def GetDictOfTQPairs(self, wave_input, *args, **kargs):
        if self.Digitizer=="742":
            return WaveformRec(wave_input,  threshold_times_std=4.5,width_threshold=20,
                               linear_fit_time=True, SampleRate=5,*args, **kargs)
        elif self.Digitizer=="751":
            return WaveformRec(wave_input, threshold_amp=2, width_threshold=3,linear_fit_time=True,
                               *args, **kargs)

    def SaveResults(self, dir_TQ_pairs:dict, path_output="str"):
        # Update TQ in df_data
        df_data = pd.DataFrame.from_dict( dir_TQ_pairs )

        # Add Charge_max and Width_max which is more convenient to index waveforms
        for name_channel in self.list_waveform_leaves_in_branch:
            suffix = "_"+name_channel.split("_")[-1]
            df_data["charge_max"+suffix] = df_data.apply( lambda row: max(row["Q"+suffix]) if len(row["Q"+suffix])>0 else None,axis=1 )
            df_data["charge_sum"+suffix] = df_data["Q"+suffix].apply(lambda row:np.sum(row) )
            df_data["width_max"+suffix] =  df_data.apply( lambda row: max(row["width"+suffix]) if len(row["width"+suffix])>0 else None,axis=1 )
            df_data["amplitude_max"+suffix] = df_data.apply( lambda row: max(row["amplitude"+suffix]) if len(row["amplitude"+suffix])>0 else None,axis=1 )
            df_data["valley_min"+suffix] = df_data.apply( lambda row: min(row["valley"+suffix]) if len(row["valley"+suffix])>0 else None,axis=1 )
        print(df_data)
        df_data.to_pickle(path_output)


    def WaveformRecWorkflowOptimizeMemory(self,plot_into_pdf=True, path_pdf="./",
                                            path_output="data_rec_TQ.pkl",
                                          nEvts=-1, splitSaving=True, splitNEvts=50000):
        # Prepare a dictionary to hold the leaf vectors
        self.leaf_vectors = {}

        # Set branch addresses
        # Assuming that all leaves are vectors of a specific type, e.g., double

        print(f"Reading Waveform Data from {self.vector_type}")
        for leaf_name in self.list_waveform_leaves_in_branch:
            if self.vector_type=="vector<unsigned short>":
                self.leaf_vectors[leaf_name] = std.vector("unsigned short")() # Create a std::vector<int>
                self.chain.SetBranchAddress(leaf_name, self.leaf_vectors[leaf_name])  # Replace 'branchName' with your vector branch name
            elif (self.vector_type=="") and (self.Digitizer=="751"):
                self.leaf_vectors[leaf_name] = array.array('i', [0]*self.length_store)  # Create a std::vector<int>
                self.chain.SetBranchAddress(leaf_name, self.leaf_vectors[leaf_name])
            elif (self.vector_type == "") and (self.Digitizer == "742"):
                self.leaf_vectors[leaf_name] = array.array('f', [0] * self.length_store)  # Create a std::vector<int>
                self.chain.SetBranchAddress(leaf_name, self.leaf_vectors[leaf_name])
            else:
                print("The waveform vector stored in *.root is neither vector<int> nor float[], vector<unsigned short>")


        dir_TQ_pairs = {}
        if plot_into_pdf:
            from matplotlib.backends.backend_pdf import PdfPages
            plot_check = True
            dict_pdf = {}
            for name_channel in self.list_waveform_leaves_in_branch:
                dict_pdf[name_channel] = PdfPages(path_pdf+name_channel+".pdf")
        else:
            plot_check = False
            pdf = None
        for i in tqdm.trange(self.chain.GetEntries()):
            self.chain.GetEntry(i)
            for name_channel in self.list_waveform_leaves_in_branch:
                suffix = "_"+name_channel.split("_")[-1]
                # print(f"Let us check {name_channel} waveform")
                # print(self.leaf_vectors[name_channel][0])
                # print(self.SubtractBaseline(self.leaf_vectors[name_channel],hist_find_baseline=False)[0])
                #
                # print(name_channel)

                dir_TQ_pairs_aWaveform = self.GetDictOfTQPairs(
                    self.SubtractBaseline(
                                          np.array(self.leaf_vectors[name_channel], copy=False),
                                          hist_find_baseline=False),
                                            plot_check=True if (plot_check and i<8) else False,
                    pdf=None if not plot_check else dict_pdf[name_channel])

                ################################################################################
                # if dir_TQ_pairs is empty, initialize it keys with return dict by WaveformRec()
                if not dir_TQ_pairs:
                    for name_leaf in self.list_need_to_save:
                        dir_TQ_pairs[name_leaf] = []
                    for name_channel in self.list_waveform_leaves_in_branch:
                        for key in dir_TQ_pairs_aWaveform.keys():
                            dir_TQ_pairs[key+"_"+name_channel.split("_")[-1]] = []
                #################################################################################

                # Append reconstruct TQ into dir_TQ_pairs
                for key in dir_TQ_pairs_aWaveform.keys():
                    dir_TQ_pairs[key+suffix].append( dir_TQ_pairs_aWaveform[key] )
            for name_leaf in self.list_need_to_save:
                dir_TQ_pairs[name_leaf].append(getattr(self.chain, name_leaf))

            if splitSaving and (i%splitNEvts==0) and (i!=0):
                path_output_subset = path_output.split(".pkl")[0]+f"_{int(i/splitNEvts)}.pkl"
                self.SaveResults(dir_TQ_pairs, path_output_subset)
                dir_TQ_pairs = {}

            if (nEvts!=-1) and (i>nEvts):
                break

        suffix = f"_{int(i/splitNEvts)+1}" if splitSaving else ""
        self.SaveResults(dir_TQ_pairs, path_output.split(".pkl")[0]+suffix+".pkl")

        if plot_into_pdf:
            for name_channel in self.list_waveform_leaves_in_branch:
                dict_pdf[name_channel].close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Reconstruct T/Q pairs from WaveDump ROOT file")
    parser.add_argument("--input",type=str, help="path of intput ROOT file(The ROOT file output from TurnWaveDumpDataIntoROOT.root)")
    parser.add_argument("--output",type=str, default="./test.pkl", help="path of output file(*.pkl)")
    parser.add_argument("--output-pdf",type=str, default="./test.pdf", help="path of output pdf file(*.pdf)")
    parser.add_argument("--nEvts",type=int, default=-1, help="How many events to process in each file")
    parser.add_argument("--SplitSaving", "-s", default=True,  action="store_true",
                        help="Splitting Dataframe into several segment for memory optimization")

    args = parser.parse_args()

    from ArgsparseTools import PrintArgsParameters
    PrintArgsParameters(args)

    if ("751" in args.input) and ("742" in args.input):
        print("Both 751 and 742 appear in path, Please Check and Specific the Digitizer Type!!!")
        exit(0)
    # Check whether is 742 series
    elif "742" in args.input:
        print("Attention:\tReading the data in 742 Series Rules!!!!!!!")
        Digitizer = "742"
    elif "751" in args.input:
        print("Attention:\tReading the data in 751 Series Rules!!!!!!!")
        Digitizer = "751"
    else:
        print("Path should show which Digitizer is, 751 or 742")
        exit(0)



    waverec_tool = WaveRecFactory(args.input,Digitizer=Digitizer)
    waverec_tool.WaveformRecWorkflowOptimizeMemory(path_output=args.output, plot_into_pdf=True,
                                                   path_pdf=args.output_pdf,
                                                   nEvts=args.nEvts,
                                                   splitSaving=args.SplitSaving)