#!/bin/bash

PROG="./devassistant.py"
MAN_PAGE="devassistant.1"
MAN_PAGE_FIRST="devassistant.1.head"
MAN_PAGE_SECOND="devassistant.1.tail"

function parse () {
    local CMD=$@
    RET=`$CMD --help | tail -n 1`
    ASSISTANTS=`echo ${RET:3:(-1)}`
    has_subass=`echo ${RET:2:1}`
    if [ x"$has_subass" != x"{" ]; then
        RET=`$CMD --help | head -n 2`
        RET=$(echo $RET | tr "\n" "\n")
        RES=`echo ${RET#* }`
        echo "$CMD"
        echo "Found command line possibilities: $RES"
        echo "$RES" >> $MAN_PAGE
        echo ".br" >> $MAN_PAGE
        return 
    fi
    arr=$(echo $ASSISTANTS | tr "," "\n")
    for ass in $arr
    do
        parse $CMD $ass
    done
}
echo "Find all assistants"
if [ -f $MAN_PAGE.gz ]; then
    rm $MAN_PAGE.gz
fi
cat $MAN_PAGE_FIRST > $MAN_PAGE
parse $PROG
cat $MAN_PAGE_SECOND >> $MAN_PAGE
gzip $MAN_PAGE
