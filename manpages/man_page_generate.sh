#!/usr/bin/bash

PROGS=(da da-mod da-prep)
LONG_PROGS=(devassistant devassistant-modify devassistant-prepare)
BINS=()
MAN_PAGES=()
MAN_PAGES_FIRST=()
MAN_PAGES_SECOND=()
for i in ${!PROGS[@]}; do
    BINS[$i]="../${PROGS[$i]}.py"
    MAN_PAGES[$i]="${PROGS[$i]}.1"
    MAN_PAGES_FIRST[$i]="${PROGS[$i]}.1.head"
    MAN_PAGES_SECOND[$i]="${PROGS[$i]}.1.tail"
done

# TODO: we should have just one "parse" function for all assistant types
function parse () {
    local PROG=$1
    local CMD=$2
    local MP=$3
    RET=`$CMD --help | tail -n 1`
    ASSISTANTS=`echo ${RET:3:(-1)}`
    has_subass=`echo ${RET:2:1}`
    if [ x"$has_subass" != x"{" ]; then
        RET=`$CMD --help | head -n 2`
        RET=$(echo $RET | tr "\n" "\n")
        RES=`echo ${RET#*}`
	RES=`echo "$RES" | cut -f 3- -d " "`
        echo "Found command line possibilities: $RES"
        echo "\fB$PROG \fP $RES" >> $MP
        echo ".br" >> $MP
        return 
    fi
    arr=$(echo $ASSISTANTS | tr "," "\n")
    for ass in $arr
    do
        parse $PROG "$CMD $ass" $MP
    done
}

rm -f *.1.gz
echo "Find all assistants"

for i in ${!PROGS[@]}; do
    cat ${MAN_PAGES_FIRST[$i]} > ${MAN_PAGES[$i]}
    parse ${PROGS[$i]} ${BINS[$i]} ${MAN_PAGES[$i]}
    cat ${MAN_PAGES_SECOND[$i]} >> ${MAN_PAGES[$i]}
    cp ${MAN_PAGES[$i]} `echo ${MAN_PAGES[$i]} | sed "s|${PROGS[$i]}|${LONG_PROGS[$i]}|"`
done
