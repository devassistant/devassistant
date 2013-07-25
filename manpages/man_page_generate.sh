#!/bin/bash

PREFIX="da"
PROG="../$PREFIX.py"
MAN_PAGE="$PREFIX.1"
MAN_PAGE_FIRST="devassistant.1.head"
MAN_PAGE_SECOND="devassistant.1.tail"

PROG_MODIFY="../$PREFIX-mod.py"
MAN_PAGE_MODIFY="$PREFIX-mod.1"
MAN_PAGE_MODIFY_FIRST="devassistant-modify.1.head"
MAN_PAGE_MODIFY_SECOND="devassistant-modify.1.tail"

PROG_PREPARE="../$PREFIX-prep.py"
MAN_PAGE_PREPARE="$PREFIX-prep.1"
MAN_PAGE_PREPARE_FIRST="devassistant-prepare.1.head"
MAN_PAGE_PREPARE_SECOND="devassistant-prepare.1.tail"

# TODO: we should have just one "parse" function for all assistant types
function parse () {
    local CMD=$@
    RET=`$CMD --help | tail -n 1`
    ASSISTANTS=`echo ${RET:3:(-1)}`
    has_subass=`echo ${RET:2:1}`
    if [ x"$has_subass" != x"{" ]; then
        RET=`$CMD --help | head -n 2`
        RET=$(echo $RET | tr "\n" "\n")
        RES=`echo ${RET#*}`
        RES=`echo ${RES#usage: da.py}`
        echo "Found command line possibilities: $RES"
        echo "\fB$PREFIX \fP $RES" >> $MAN_PAGE
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
        RES=`echo ${RES#usage: da-mod.py}`
        echo "Found command line possibilities($PREFIX-mod): $RES"
        echo "\fB$PREFIX-mod \fP $RES" >> $MAN_PAGE_MODIFY
        echo ".br" >> $MAN_PAGE_MODIFY
        return 
    fi
    arr=$(echo $ASSISTANTS | tr "," "\n")
    for ass in $arr
    do
        parse_modify $CMD $ass
    done
}

function parse_prepare () {
    local CMD=$@
    RET=`$CMD --help | tail -n 1`
    ASSISTANTS=`echo ${RET:3:(-1)}`
    has_subass=`echo ${RET:2:1}`
    if [ x"$has_subass" != x"{" ]; then
        RET=`$CMD --help | head -n 2`
        RET=$(echo $RET | tr "\n" "\n")
        RES=`echo ${RET#*}`
        RES=`echo ${RES#usage: da-prep.py}`
        echo "Found command line possibilities($PREFIX-prep): $RES"
        echo "\fB$PREFIX-prep \fP $RES" >> $MAN_PAGE_PREPARE
        echo ".br" >> $MAN_PAGE_PREPARE
        return 
    fi
    arr=$(echo $ASSISTANTS | tr "," "\n")
    for ass in $arr
    do
        parse_prepare $CMD $ass
    done
}


echo "Find all assistants"
if [ -f $MAN_PAGE.gz ]; then
    rm $MAN_PAGE.gz
fi
if [ -f $MAN_PAGE_MODIFY.gz ]; then
    rm $MAN_PAGE_MODIFY.gz
fi
if [ -f $MAN_PAGE_PREPARE.gz ]; then
    rm $MAN_PAGE_PREPARE.gz
fi
cat $MAN_PAGE_FIRST > $MAN_PAGE
parse $PROG
cat $MAN_PAGE_SECOND >> $MAN_PAGE

cat $MAN_PAGE_MODIFY_FIRST > $MAN_PAGE_MODIFY
parse_modify $PROG_MODIFY
cat $MAN_PAGE_MODIFY_SECOND >> $MAN_PAGE_MODIFY

cat $MAN_PAGE_PREPARE_FIRST > $MAN_PAGE_PREPARE
parse_prepare $PROG_PREPARE
cat $MAN_PAGE_PREPARE_SECOND >> $MAN_PAGE_PREPARE
