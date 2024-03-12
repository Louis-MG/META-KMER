#!/bin/python3

import argparse
import numpy as np
import os
import sys
import re
from typing import List, Dict, Union
from math import tan, pi
from scipy.stats import cauchy


def getArgs() :
	parser = argparse.ArgumentParser(description='Aggregates pvalues from kmdiff to a single p-value per unitig.')
	parser.add_argument('-k', '--kmdiff', type=str, dest = 'kmdiff_input_path', action = 'store', required=True,
                    help = 'Path to the kmdiff fasta file.')
	parser.add_argument('-u', '--unitigs', type=str, dest= 'unitigs_input_path', action= 'store', required=True,
		    help = 'Path to the unitigs fasta file.' )
	parser.add_argument('-o', '--output', type=str, dest = 'output_path', action = 'store', required=True,
		    help = 'Path to the output directory.')
	args = parser.parse_args()
	return(args)


def verif_input(path: Union[str, bytes, os.PathLike]) :
	"""
	Checks that the input file exists.
	path : string or path-like object.
	"""
	path = str(path)
	if os.path.isfile(path):
		pass
	else :
		print(f"ERROR: file {path} does not exist or is not a file.")
		sys.exit()


def verif_output(path: Union[str, bytes, os.PathLike]) :
	"""
	Checks that the output directorory exists and that no file with output name exists already.
	path : string or path-like object.
	"""
	path = str(path)
	if os.path.isdir(path) :
		pass
	else :
		print(f"ERROR: folder {path} not found.")
		sys.exit()
	if os.path.isfile(path+"/unitigs.aggregated_pvalues.fa") :
		print(f"ERROR: folder {path} contains a 'unitigs.aggregated_pvalues.fa' file already.")
		sys.exit()


def write_output(path: Union[str, bytes, os.PathLike], list_unitigs: list[object]):
	"""
	Writes output.
	path : string or path-like object.
	"""
	with open(path+"unitigs.aggregated_pvalues.fa", 'w') as f:
		for i in range(0, len(list_unitigs)):
			f.write( ">unitig_"+str(i)+"_pval="+str(list_unitigs[i].pvalue))
			f.write("\n"+list_unitigs[i].sequence)


def load_pvalue_dict(path: Union[str, bytes, os.PathLike]) -> dict[str, float]:
	"""
	Loads the fasta file from kmdiff output as a dictionnary :  {'sequence':'p-value'} and returns the dictionnary.
	path: string or path-like object.
	"""
	kmer_2_pvalue = dict()
	with open(path) as f :
		for line in f :
			if line.startswith(">") :
				temp_str = re.sub('.*pval=', '', line)
				temp_str = re.sub('_control=.*', '', temp_str)
				pvalue = float(temp_str)
			else :
				sequence = line.rstrip('\n')
				try :
					kmer_2_pvalue[str(sequence)] = pvalue
				except MemoryError :
					size = sys.getsizeof(kmer_2_pvalue)
					size += sum(map(sys.getsizeof, kmer_2_pvalue.values())) + sum(map(sys.getsizeof, kmer_2_pvalue.keys()))
					print(size)
					exit()
	return kmer_2_pvalue


def reverse_complement(kmer: str):
        """
        Reverse complement a kmer.
        kmer: string
        """
        rev_compl_kmer = ""
        rev_kmer = kmer[::-1]
        dict_reverse_nucleotides = {"A":"T", "T":"A", "C":"G", "G":"C"}
        for i in range(0, len(kmer)) :
                rev_compl_kmer += dict_reverse_nucleotides[rev_kmer[i]]
        return rev_compl_kmer


class Unitig(object) :
	"""
	Object representing a unitig, with its sequence and aggregated pvalue.
	"""
	sequence : ""
	pvalue : 0
	kmer_pvalues : []
	def __init__(self, sequence, pvalue, kmer_pvalues) :
		self.sequence = sequence
		self.pvalue = pvalue
		self.kmer_pvalues = kmer_pvalues


def make_unitig(sequence: str, kmer_dict: dict[str, float]) -> object :
	"""
	Takes a sequence and/or a pvalue to build and return an object of class unitig.
	sequence : string
	pvalue : float
	kmer_pvalues : list of floats
	"""
	list_kmer_pvalues = []
	for i in range(0, len(sequence)-31):
		kmer = str(sequence[i:i+31])
		try :
			list_kmer_pvalues.append(kmer_dict[kmer])
		except KeyError :
			rev_compl_kmer = reverse_complement(kmer)
			list_kmer_pvalues.append(kmer_dict[rev_compl_kmer])
	unitig = Unitig(sequence, 0, list_kmer_pvalues)
	return unitig


def load_unitigs(path: Union[str, bytes, os.PathLike], kmer_dict: dict[str, float]) -> list[object]:
	"""
	Loads unitigs as objects from the unitigs fasta file.
	path : string or path-like object.
	"""
	list_unitigs = []
	with open(path) as f :
		for line in f :
			if line.startswith(">") :
				pass
			else :
				sequence = line
				unitig = make_unitig(sequence, kmer_dict)
				unitig_CCT = CCT(unitig)
				list_unitigs.append(unitig_CCT)
	return list_unitigs


def CCT(unitig: object) -> object :
	"""
	Cauchy Combination Test application.
	pvalues: list of floats
	"""
	cauchy_values = [tan((0.5-x)*pi) for x in unitig.kmer_pvalues]
	cauchy_stat = sum(cauchy_values)/len(cauchy_values)
	unitig.pvalue = 1-cauchy.cdf(cauchy_stat, loc=0, scale=1)
	return unitig


#def aggregate_pvalues(list_unitigs: list[object]) -> list[object]:
#	"""
#	Tranforms the pvalues of kmers of each unitigs into the unitigs' pvalues.
#	list_unitigs: list of objects Unitigs
#	"""
#	list_modified_unitigs = [CCT(unitig) for unitig in list_unitigs]
#	list_modified_unitigs.sort(key = lambda x: (x.pvalue, len(x.sequence)))
#	return list_modified_unitigs


def main(kmdiff_input_path: Union[str, bytes, os.PathLike], unitigs_input_path: Union[str, bytes, os.PathLike], output_path: Union[str, bytes, os.PathLike]):
	verif_input(kmdiff_input_path)
	verif_input(unitigs_input_path)
	verif_output(output_path)
	kmer_dict = load_pvalue_dict(kmdiff_input_path)
	list_unitigs_with_pvalues = load_unitigs(unitigs_input_path, kmer_dict)
	#list_unitigs_with_pvalues = aggregate_pvalues(list_unitigs) si marche pas remettre et la ligne au dessus est juste list_unitigs, et enlever la ligne en dessous
	list_unitigs_with_pvalues.sort(key = lambda x: (x.pvalue, len(x.sequence)))
	write_output(output_path, list_unitigs_with_pvalues)
	print("Aggregation done !")


if __name__ == "__main__" :
	args = getArgs()
	main(args.kmdiff_input_path, args.unitigs_input_path, args.output_path)