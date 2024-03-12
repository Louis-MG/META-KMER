#!/bin/bash

set -e

Help() {
	echo "
This script summerises the blast results of unitigs. Its arguments are :
	-i --input <PATH> path to the input file which should be named something like blast_results.txt.
			  should be from '--format-output query,target,fident,alnlen,mismatch,gapopen,qstart,qend,tstart,tend,evalue,bits,qset'
	-o --output <PATH> path to the output directory.
	-r --reference <PATH> path to the file of sequenceID_to_species.tsv correspondance.
	-d --detailed <PATH> path to the file of sequenceID_to_genomes.tsv correspondance.
	-h --help displays this help message and exits.

Output :
	- alignment_summary.txt
	- alignment_summary_detailed.txt

"
}

if [ $# -eq 0 ]
then
	Help
	exit 0
fi

output="./"
detailed=false

while [[ $# -gt 0 ]]
do
	case $1 in
	-i | --input) input="$2"
	shift 2;;
	-o | --output) output="$2"
	shift 2;;
	-r | --reference) ref="$2"
	shift 2;;
	-d | --detailed) detailed="$2"
	shift 2;;
	-h | --help) Help; exit 0;;
	-* | --*) unknown="$1"; echo "Unknown option: ${unknown}"; Help; exit 1;;
	*) shift;;
	esac
done

if [ ! -f $input ]
then
	echo "$input file does not exist. Exiting."
	exit 1
fi

if [ ! -f $ref ]
then
        echo "$ref file does not exist. Exiting."
        exit 1
fi

if [ ! -f $detailed ]
then
        echo "$detailed file does not exist. Exiting."
        exit 1
fi


if [ ! -d $output ]
then
	mkdir $output
fi

#####################################
#
#	RESUMER FIN
#
#####################################

#champ 2 du fichier d'entree : sequences
#champ 4 du fichier d'entree : longueur d alignement

# fait un array associatif des noms de sequences a leur espece a partir du fichier de ref; parcours ensuite le fichier d'input pour prendre les noms de sp associes aux seq et imprime longueur d alignement \t sp

awk -F'\t' 'FNR==NR {seq_to_sp[$1]=$2;next} {print $4, seq_to_sp[">"$2]}' "$detailed" "$input" > "$output"/tmp.txt
#premier fichier: FNR==NR, puis quand FNR!=NR
awk -F'\t' 'FNR==NR {seq_to_sp[$1]=$2;next} {print $4, seq_to_sp[">"$2]}' "$ref" "$input" > "$output"/tmp_simple.txt

sed -i 's/ /\t/1' "$output"/tmp.txt
sed -i 's/ /\t/1' "$output"/tmp_simple.txt

#sort les lignes par especes
sort -T /mnt/ssd/LM/tmp/ -k2 -t $'\t'  "$output"/tmp.txt > "$output"/tmp_sorted.txt
sort -T /mnt/ssd/LM/tmp/ -k2 -t $'\t'  "$output"/tmp_simple.txt > "$output"/tmp_sorted_simple.txt

#addition des longueurs d'alignement si $2 = prev
awk -F'\t' 'BEGIN {sum = 0; prev=""; OFS="\t"} ($2 == prev){sum+=$1}  ($2 != prev){print sum, prev; sum = $1; prev = $2} END {print sum, prev}' "$output"/tmp_sorted.txt > "$output"/tmp1.txt
awk -F'\t' 'BEGIN {sum = 0; prev=""; OFS="\t"} ($2 == prev){sum+=$1}  ($2 != prev){print sum, prev; sum = $1; prev = $2} END {print sum, prev}' "$output"/tmp_sorted_simple.txt > "$output"/tmp1_simple.txt

#ordonne par score
sort -T /mnt/ssd/LM/tmp/ -k1 -r -g -t $'\t' "$output"/tmp1.txt > "$output"/alignment_summary_detailed.txt
sort -T /mnt/ssd/LM/tmp/ -k1 -r -g -t $'\t' "$output"/tmp1_simple.txt > "$output"/alignment_summary.txt

rm "$output"/tmp*