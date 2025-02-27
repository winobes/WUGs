
echo $(tput bold)$BASH_SOURCE$(tput sgr0)

graphdir=$dir/graphs
graphs=($graphdir/*)
outdir=$dir/plots
mkdir -p $outdir

outdirl=$outdir
#echo $outdirl
for graph in "${graphs[@]}"
do
    echo $graph
    for style in "${styles[@]}"
    do
	outdirls=$outdirl/$style	
	for mode in "${modes[@]}"
	do
	    outdirlm=$outdirls/$mode	
	    for color in "${colors[@]}"
	    do
		outdirlmc=$outdirlm/$color	
		for edgestyle in "${edgestyles[@]}"
		do
		    outdirlmcp=$outdirlmc/$edgestyle
		    mkdir -p $outdirlmcp
		    python3 $scriptsdir/graph2plot.py $graph $outdirlmcp $color $mode $style $edgestyle $annotators $thresholdplot $position $modus			
		done		   
	    done
	done
    done
done

#cd $dir/ && zip -r plots.zip plots/ && cd ..
