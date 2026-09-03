#!/bin/bash
# gadget_sweep.sh N_START N_END — serial sweep for Bensmail gadget cores K.
# For each even n: generate connected cubic triangle-free C4-free graphs
# (girth >= 5) and run gadget_check (conditions: no C8/C16/C32 + a pair (a,b)
# with all simple a-b path lengths avoiding {2,6,14,30}).
# Output: gadget_nNN.out / gadget_nNN.err per n.
set -u
NS=${1:-34}
NE=${2:-40}
for n in $(seq $NS 2 $NE); do
  e=$((3*n/2))
  echo "=== n=$n start $(date) ===" >> gadget_sweep.log
  ./nauty2_8_9/geng $n $e:$e -d3 -D3 -c -t -f -q | ./gadget_check > gadget_n${n}.out 2> gadget_n${n}.err
  echo "=== n=$n end   $(date) | $(tail -1 gadget_n${n}.err) ===" >> gadget_sweep.log
done
echo "ALL-DONE $(date)" >> gadget_sweep.log
