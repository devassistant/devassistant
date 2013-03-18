#!/bin/bash

if [ $# -ne 1 ]; then
    echo "vimrc file delivered by devassistant feature was not found and a parameter"
    echo "syntax is: $0 <path_to_vim_rc_dev_assistant_file>"
    exit 1
fi

echo "This procedure is used for update your current vim and improve them"
PWD=`pwd`
HOME_DIR=`echo $HOME`
CUR_VIM="$HOME/.vimrc"
NEW_VIM="$PWD/$1"
if [ -f $CUR_VIM ]; then
	grep "BEGIN_DEVASSISTANT_1" $CUR_VIM 1>/dev/null 2>&1
	if [ $? -eq 0 ]; then
	    echo "$CUR_VIM file was already modified by devassistant"
	    exit 0
	fi
fi
echo "" >> $CUR_VIM
echo "\"BEGIN_DEVASSISTANT_1" >> $CUR_VIM
echo "\"Turning value devassistant to 0 you will used your already defined .vimrc file" >> $CUR_VIM
echo "\"Turning value devassistant to 1 you will use vimrc defined by devassistant feature" >> $CUR_VIM
echo "" >> $CUR_VIM
echo "let devassistant=0" >> $CUR_VIM
echo "if devassistant==1" >> $CUR_VIM
echo " :source $NEW_VIM" >> $CUR_VIM
echo "endif" >> $CUR_VIM
echo "\"END_DEVASSISTANT_1" >> $CUR_VIM
echo ""
echo ""
echo "Updating of ~/.vimrc file was successfull"
echo "For turning on devassistant vimrc file"
echo "open ~/.vimrc file and change value \"let devassistant=0\" to \"let devassistant=1\""
echo "After pressing F1 you see help about commands etc."
