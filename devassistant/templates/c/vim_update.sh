#!/bin/bash

if [ $# -ne 1 ]; then
    echo "vimrc file delivered by devassistant feature was not found and a parameter"
    echo "syntax is: $0 <path_to_vim_rc_dev_assistant_file>"
    exit 1
fi

echo "This procedure is used for update your current vim and improve them"
HOME_DIR=`echo $HOME`
DEVASSISTANT="$HOME_DIR/.vimrc.devassistant"
CUR_VIM="$HOME/.vimrc"
OLD_VIM=`cat $CUR_VIM`
NEW_VIM=$1
DEVASS_VIM=`cat $NEW_VIM`
if [ ! -f $DEVASSISTANT ]; then
    grep "BEGIN_DEVASSISTANT" $CUR_VIM 1>/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "$CUR_VIM file was already modified by devassistant"
        exit 0
    fi
    echo "Used for new creatinon of vimrc based on older one"
    echo "Firstly backup $CUR_VIM to $DEVASSISTANT"
    mv $CUR_VIM $DEVASSISTANT
    echo "\"BEGIN_DEVASSISTANT_1" > $CUR_VIM
    echo "\"Turning value devassistant to 0 you will used your already defined .vimrc file" >> $CUR_VIM
    echo "\"Turning value devassistant to 1 you will use vimrc defined by devassistant feature" >> $CUR_VIM
    echo "let devassistant=0" >> $CUR_VIM
    echo "if devassistant==0" >> $CUR_VIM
    echo "\"END_DEVASSISTANT_1" >> $CUR_VIM
    echo "$OLD_VIM" >> $CUR_VIM
    echo "\"BEGIN_DEVASSISTANT_2" >> $CUR_VIM
    echo "endif" >> $CUR_VIM
    echo "if devassistant==1" >> $CUR_VIM
    echo "$DEVASS_VIM" >> $CUR_VIM
    echo "endif" >> $CUR_VIM
    echo "\"END_DEVASSISTANT_2" >> $CUR_VIM
    echo ""
    echo ""
    echo "Updating of ~/.vimrc file was successfull"
    echo "For turning on devassistant vimrc file"
    echo "open ~/.vimrc file and change value \"let devassistant=0\" to \"let devassistant=1\""
else
    echo "This section is used for updating already created vimrc"
fi
