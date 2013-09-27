# bash completion for devassistant

function _get_subas () {
    # first, grep line with "blabla {as1,as2,as3} blabla"
    # second, remove blabla around
    # third, remove the curly braces
    local SUBAS=$(echo $2 | grep '{.*}' | sed -e 's|.*{\(.*\)}.*|\1|' -e 's|[{}]||g')
    # now split in places of commas
    SUBAS=(${SUBAS//,/ })
    echo ${SUBAS[@]}
}

function _get_opts () {
    # first, grep only lines with "--"
    # second, throw away lines with sth. like "[--venv] - these are from general synopsis, we don't want them
    # third, sed out the actual options without
    local OPTS=$(echo "$2" | grep '\--' | grep -v '\--[^ ]*\]' | sed 's|[^\(\-\)]*\(--[^ ]*\)[^-]*|\1 |g')
    echo ${OPTS[@]}
}

function _get_actions() {
    # only take lines under ACTIONS_HEADER
    local ACTION_LINES=$(echo "$1" | sed '/'"$2"'/,$!d' | sed '1d')
    local ACTIONS=()
    while read -r LINE; do
        # for each line select first word and then cut the initial ascii format code
        ACTIONS+=($(echo "$LINE" | cut -d " " -f1 | cut -c 5-))
    done <<< "$ACTION_LINES"
    echo ${ACTIONS[@]}
}

_da() {
    # current command
    CUR_COM="${COMP_WORDS[@]}"
    # strip "--" from the end (the bellow command needs to append "-h")
    CUR_COM="$(echo $CUR_COM | sed 's|--$||')"
    # read output and returncode of the command with "-h"
    DA_OUTPUT=$($CUR_COM -h 2>&1)
    RETCODE=$?

    # user had "--v" but there are two arguments like "--venv" and "--vim",
    # so Python thinks it's ambiguous definition and returns 1
    if [ $RETCODE -eq 1 ] ; then
        # assume that the "--v" (or so) is the last, remove it and rerun
        DA_OUTPUT=$($(echo $CUR_COM | sed 's|[^ ]*$||') -h 2>&1)
        RETCODE=$?
    fi

    # get list of subassistants, if any
    SUBAS=$(_get_subas $RETCODE "$DA_OUTPUT")
    if [ $RETCODE -eq 0 ] ; then # finished assistant/unfinished option - we can get subassistants/options from help
        OPTS=$(_get_opts $RETCODE "$DA_OUTPUT")
        RESULT="$SUBAS $OPTS"
    else # not finished assistant - just advise assistant names, not options
        RESULT="$SUBAS"
    fi

    # on top level, we have assistant types {crt,mod,prep} and actions as a list
    ACTIONS_HEADER='Available actions:'
    echo "$DA_OUTPUT" | grep "$ACTIONS_HEADER" > /dev/null
    if [ $? -eq 0 ] ; then
      ACTIONS=$(_get_actions "$DA_OUTPUT" "$ACTIONS_HEADER")
      RESULT="$RESULT $ACTIONS"
    fi

    COMPREPLY=( $(compgen -W "$RESULT" -- "$2") )
} &&
complete -F _da -o filenames da
# Local variables:
# mode: shell-script
# sh-basic-offset: 4
# sh-indent-comment: t
# indent-tabs-mode: nil
# End:
# ex: ts=4 sw=4 et filetype=sh
