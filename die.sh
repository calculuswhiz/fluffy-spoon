# Usage: "sh die.sh <angle>"
# Wrapper for the following:
# - C file spits out "dx dy"
# - Python parses input given desired angle.
# - Python then uses notification.

./deathmeasure | python deathmeasure.py $1
