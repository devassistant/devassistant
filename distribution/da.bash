# Copyright 2015 Devassistant contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

_da () {

    local cur prev_path tokens

    COMPREPLY=()
    cur=$(_get_cword)
    # The sed workaround is there so that underscores don't get interpreted by
    # argparse.
    prev_path=$( echo ${COMP_WORDS[@]:1:COMP_CWORD-1} | sed -e 's/^-/_/' -e 's/^\(.\)-/\1_/' )

    tokens="$(da autocomplete "$prev_path")"

    if echo $tokens | grep -q _FILENAMES; then
        _filedir
        tokens=$( echo $tokens | sed -e 's/_FILENAMES//' )
        COMPREPLY=( ${COMPREPLY[@]} $( compgen -W "$tokens" -- "$cur" ) )
    else
        COMPREPLY=( $( compgen -W "$tokens" -- "$cur" ) )
    fi
}

complete -o filenames -F _da da
