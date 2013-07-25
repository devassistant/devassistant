# bash completion for devassistant

_devassistant_baseopts_c()
{
	echo ""
    local opts='--deps-only --github --help --vim --build --eclipse --name'
    printf %s "$opts"
}

_devassistant_baseopts_python()
{
	echo ""
    local opts='--deps-only --github --help --eclipse --name --vim'
    printf %s "$opts"
}

_devassistant_baseopts_java()
{
	echo ""
    local opts='--deps-only --github --help --eclipse --name'
    printf %s "$opts"
}

_devassistant_baseopts_perl()
{
	echo ""
    local opts='--deps-only --github --help --eclipse --name'
    printf %s "$opts"
}

_devassistant_baseopts_perl_dancer()
{
	echo ""
    local opts='--deps-only --github --cgi --help --eclipse --name --fastcgi'
    printf %s "$opts"
}

_devassistant_baseopts_php()
{
	echo ""
    local opts='--deps-only --github --help --eclipse --name --rootdb --vim'
    printf %s "$opts"
}

_devassistant()
{
    COMPREPLY=()
    local devassistant=$1 cur=$2 prev=$3 words=("${COMP_WORDS[@]}")
    declare -F _get_comp_words_by_ref &>/dev/null && \
        _get_comp_words_by_ref -n = cur prev words

    # Commands offered as completions
    local cmds=( c cpp java python perl php)

    local i c cmd subcmd
    for (( i=1; i < ${#words[@]}-1; i++ )) ; do
        [[ -n $cmd ]] && subcmd=${words[i]} && break
        # Recognize additional commands and aliases
        for c in ${cmds[@]} ; do
            [[ ${words[i]} == $c ]] && cmd=$c && break
        done
    done

	#echo "devassistant: $devassistant, cur: $cur, prev: $prev, word: $words, subcmd: $subcmd, cmd:$cmd"
    case $cmd in

        c)
			if [[ $prev == $cmd ]] ; then
				COMPREPLY=( $( compgen -W '--deps-only --github --help --vim --build --eclipse --name' -- "$cur" ) )
				return 0
			fi
			if [[ $subcmd == -* ]] ; then
				COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_c )' -- "$cur" ) )
				return 0
			fi
            ;;

        cpp)
			if [[ $prev == $cmd ]] ; then
				COMPREPLY=( $( compgen -W '--deps-only --github --help --vim --build --eclipse --name' -- "$cur" ) )
				return 0
			fi
			if [[ $subcmd == -* ]] ; then
				COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_c )' -- "$cur" ) )
				return 0
			fi
            ;;

        java)
            if [[ $prev == $cmd ]] ; then
                COMPREPLY=( $( compgen -W 'jsf maven' -- "$cur" ) )
                return 0
            fi
            case $subcmd in
                jsf)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_java )' -- "$cur" ) )
					return 0
					;;
                maven)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_java )' -- "$cur" ) )
					return 0
					;;
            esac
            return 0
            ;;

        perl)
            if [[ $prev == $cmd ]] ; then
                COMPREPLY=( $( compgen -W 'class dancer' -- "$cur" ) )
                return 0
            fi
            case $subcmd in
                class)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_perl )' -- "$cur" ) )
					return 0
					;;
                dancer)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_perl_dancer )' -- "$cur" ) )
					return 0
					;;
            esac
            return 0
            ;;


        python)
            if [[ $prev == $cmd ]] ; then
				COMPREPLY=( $( compgen -W 'lib django flask pygtk' -- "$cur" ) )
				return 0
			fi
            case $subcmd in
                lib)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_python )' -- "$cur" ) )
					return 0
					;;
                django)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_python )' -- "$cur" ) )
					return 0
					;;
                flask)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_python )' -- "$cur" ) )
					return 0
					;;
                pygtk)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_python )' -- "$cur" ) )
					return 0
					;;
            esac
            return 0
            ;;

        php)
            if [[ $prev == $cmd ]] ; then
				COMPREPLY=( $( compgen -W 'lamp' -- "$cur" ) )
				return 0
			fi
            case $subcmd in
                lamp)
					COMPREPLY=( $( compgen -W '$( _devassistant_baseopts_php )' -- "$cur" ) )
					return 0
					;;
            esac
            return 0
            ;;
    esac

    local split=false
    declare -F _split_longopt &>/dev/null && _split_longopt && split=true

    #_devassistant_complete_baseopts "$cur" "$prev" && return 0

    $split && return 0

    #if [[ $cur == -* ]] ; then
    #    COMPREPLY=( $( compgen -W '$( _devassistant_baseopts )' -- "$cur" ) )
    #    return 0
    #fi
    COMPREPLY=( $( compgen -W '${cmds[@]}' -- "$cur" ) )
} &&
complete -F _devassistant da

# Local variables:
# mode: shell-script
# sh-basic-offset: 4
# sh-indent-comment: t
# indent-tabs-mode: nil
# End:
# ex: ts=4 sw=4 et filetype=sh
