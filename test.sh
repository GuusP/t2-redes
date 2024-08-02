#!/bin/bash

# Define the inputs
inputs=("3" "2" "1" "0")

# Loop to open terminals and run the script with different inputs
for i in "${!inputs[@]}"
do
    gnome-terminal --title="Terminal ${inputs[$i]}" -- bash -c "python3 player.py ${inputs[$i]}; exec bash"
done
