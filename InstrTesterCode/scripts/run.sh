# Script to Run Instr-Tester
if [ $# -eq 0 ]
	then
	echo "Run with the name of the .instr file located within the instr/ directory." 
	echo "e.g. "
	echo "./scripts/run.sh a_granularlooper"
	echo "-----------------------------------------------------------"
    read -r -p "Would you like to run the default instrument? [Y/n] " response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]
        then
        python instr_tester/nebulae.py 
    fi
else
    python instr_tester/nebulae.py $1
fi
echo "Done."
