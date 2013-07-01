#!/bin/bash

PROG="./devassistant.py"
MAN_PAGE="devassistant.1"
MAN_PAGE_FIRST="devassistant.1.head"
MAN_PAGE_SECOND="devassistant.1.tail"

PROG_MODIFY="./devassistant-modify.py"
MAN_PAGE_MODIFY="devassistant-modify.1"
MAN_PAGE_MODIFY_FIRST="devassistant-modify.1.head"
MAN_PAGE_MODIFY_SECOND="devassistant-modify.1.tail"

function parse () {
    local CMD=$@
    RET=`$CMD --help | tail -n 1`
    ASSISTANTS=`echo ${RET:3:(-1)}`
    has_subass=`echo ${RET:2:1}`
    if [ x"$has_subass" != x"{" ]; then
        RET=`$CMD --help | head -n 2`
        RET=$(echo $RET | tr "\n" "\n")
        RES=`echo ${RET#*}`
        RES=`echo ${RES#usage: devassistant.py}`
        echo "Found command line possibilities: $RES"
        echo "\fBdevassistant \fP $RES" >> $MAN_PAGE
        echo ".br" >> $MAN_PAGE
        return 
    fi
    arr=$(echo $ASSISTANTS | tr "," "\n")
    for ass in $arr
    do
        parse $CMD $ass
    done
}

function parse_modify () {
    local CMD=$@
    RET=`$CMD --help | tail -n 1`
    ASSISTANTS=`echo ${RET:3:(-1)}`
    has_subass=`echo ${RET:2:1}`
    if [ x"$has_subass" != x"{" ]; then
        RET=`$CMD --help | head -n 2`
        RET=$(echo $RET | tr "\n" "\n")
        RES=`echo ${RET#*}`
        RES=`echo ${RES#usage: devassistant-modify.py}`
        echo "Found command line possibilities(devassistant-modify): $RES"
        echo "\fBdevassistant-modify \fP $RES" >> $MAN_PAGE_MODIFY
        echo ".br" >> $MAN_PAGE_MODIFY
        return 
    fi
    arr=$(echo $ASSISTANTS | tr "," "\n")
    for ass in $arr
    do
        parse_modify $CMD $ass
    done
}
echo "Find all assistants"
if [ -f $MAN_PAGE.gz ]; then
    rm $MAN_PAGE.gz
fi
if [ -f $MAN_PAGE_MODIFY.gz ]; then
    rm $MAN_PAGE_MODIFY.gz
fi
cat $MAN_PAGE_FIRST > $MAN_PAGE
parse $PROG
cat $MAN_PAGE_SECOND >> $MAN_PAGE

cat $MAN_PAGE_MODIFY_FIRST > $MAN_PAGE_MODIFY
parse_modify $PROG_MODIFY
cat $MAN_PAGE_MODIFY_SECOND >> $MAN_PAGE_MODIFY
