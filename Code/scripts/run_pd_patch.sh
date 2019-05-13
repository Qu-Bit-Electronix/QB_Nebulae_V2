echo ""
INPUT=$1
if [ -f "${INPUT}" ]; then
    echo "Running $INPUT in pd"
    sudo pd -rt -r 48000 -nogui -verbose $1
    
else
    echo "No Input file detected"
    echo "Usage: "
    echo "./run_patch <filename.pd> - will run Puredata with audio enabled, at 48000Hz Samplerate."
fi
echo "Done"
    

