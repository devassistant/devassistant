" File: JavaBrowser.vim
" Author: Pradeep Unde (pradeep_unde AT yahoo DOT com)
" Version: 2.03
" Last Modified: September 15, 2006
"
" ChangeLog:
" Version 2.03:
" 2 small bug fixes
" 1. When UML visibility indicators are enabled, they were also included in
"    syntax highlighting
" 2. Sort by order not supported. But the window showed Sort by order at top
" Version 2.02:
" 1. Automatic tag highlighting supported now. Depending where the cursor is in
"    the java file, corresponding tag is automatically hightlighed in the
"    JavaBrowser window
" Version 2.01:
" Following bug fixes and one improvement
" 1. Fixed error showing tooltip when mouse was over "field" or "method"
" 2. The cache was not getting set for the tooltip correctly
" 3. The tooltip was staring with the <TAB> character picked up from the ctags
"    output. It has been removed now
" Version 2.0:
" 1. Overhauled the code for version 7.0
" 2. Does not give errors for version 7.0 now when browsing the class tree
" 3. Added caching for ctags output, so, buffer switching is very fast for
" previously viewed buffers
" Version 1.22:
" 1. Added function JavaBrowser_Set_Syntax_Highlighting().
" 2. Now, the syntax highlighting for the Class tree would automatically be set
" when a new window is opened or at the time of tag refersh. So, the user would
" always see the syntax highlighting set for JavaBrowser syntax groups even if
" the color scheme is changed in middle of an editing session.
" Version 1.21:
" 1. Added option JavaBrowser_Show_UML_Visibility. If set, which is the
" default, JavaBrowser uses UML visibility indicators. + => public,
" - => private, # => protected in addition to the syntax highlighting.
" Version 1.20:
" 1. Bugfix to correct the typo for balloon_eval
" 2. Now also checking if the version > 700 before setting the bexpr option
" Version 1.19:
" 1. Added the balloon (or tool-tip) for the prototype
" Version 1.18:
" 1. Bug fix when sorted by name. Fixed the tag position. Now it shows the
" arrow at correct position.
" Version 1.17:
" 1. Optimized so that when the cursor moves within a method/function, the tag
" is not rehighlighted, reducing the flicker on the screen.
" 2. The sorting now works properly and correct tag is highlighted after the
" sorting.
" 3. Set JavaBrowser_Expand_Tree_At_Startup = 1 so that the tree opens
" completely at :JavaBrowser command
" 4. Now escaping the SPACES in $VIM so that sign will be read properly.
" Version 1.16:
" 1. Added tagindicator.bmp for windows. Vim on Windows does not understand
" the xpms. Arrgghhh!
" Version 1.15:
" 1. Added various configurable ways to highlight current tag which include
" A. an icon or B. an arrow(=>) with highlight of Constant and/or C. normal
" search highlight
" 2. Added options to control all these. Added 'JavaBrowser_Use_Icon',
" 'JavaBrowser_Use_Text_Icon' and 'JavaBrowser_Use_Highlight_Tag'
" 3. All have default values
" Version 1.14:
" 1. Now automatically highlights the current tag name.
" Version 1.13:
" 1. Added variable JavaBrowser_Expand_Tree_At_Startup to expand the
" package/class/interface tree at startup.
" Version 1.12:
" 1. Small bug fix to remove unwanted echo for visibility.
" Version 1.11:
" 1. Now interface methods are highlighted as public, abstract. I missed
" the abstract part in the previous version.
" 2. The visibility modifier (public/protected/private) can now be anywhere
" in the method/field declaration and it will be highlighted correctly.
" Version 1.10:
" 1. Now interface methods are highlighted as public and fields as public,
" static
" Version 1.9:
" 1. Added syntax highlighting (italic, underline) for xterm users
" Version 1.8:
" 1. Bug fix for comment syntax matching.
" Version 1.7:
" 1. Now the syntax highlighting can be configured in the gvimrc for
" various types of members as per individual taste. Defaults provided with the
" script can be OK for the most. Variuos syntax highlight groups that can be
" configured can be found out from the file. They generally look like
" JavaBrowser_public_static etc. Think of all possible combinations for
" public/protected/private with static and abstarct.
" Version 1.6:
" 1. Added colors for color term. It seems to be working for me for color
" Xterm. I use Mandrake 9.0 and KDE (konsole as xterm).
" Version 1.5:
" 1. If JavaBrowser is requested (:JavaBrowser) for any file other than
" a 'java' file, an error message is shown.
" Version 1.4:
" 1. Fixed bug for overriden methods. Now JavaBrowser understands overriden
" methods and jumps to the proper ones.
" Version 1.3:
" 1. Fixed bugs for inner classes and other minor bug fixes.
" Version 1.2:
" 1. Added syntax matching for abstract and final with combination of
" visibility. abstract members are shown in italics, statics are underlined as
" per UML specs.
" 2. Various syntax groups are defined in the file that can be changed to user
" taste for colors.
"
" Version 1.1:
" 1. Added syntax matching for visibility i.e. public,protected and private
" Limitations: Last name of field/method wins the syntax highlight. So, if the
" file has 2 or more classes with same field/method name with different
" visibilites, both of them are highlighted with the syntax colour of the last
" one encountered.
"
" Version 1.01:
" 1. Added syntax matching for types
" 2. Added opening for one fold level so it looks like
"           package
"              java.util
"           class
"              TreeMap
"              TreeMap.SubMap
"              ....
" when you open JavaBrowser
"
" Overview
" --------
" The "Java Browser" plugin provides the following features:
"
" 1. Opens a vertically/horizontally split Vim window with a list of packages,
"    classes in the current Java file in a tree form. They can be expanded to
"    look at details. e.g:
"        package
"           java.util
"        class
"           HashSet
"              field
"                map
"                PRESENT
"                ...
"              method
"                iterator
"                size
"                ...
" 2. Groups the tags by their type and displays them in a foldable tree.
" 3. Automatically updates the browser window as you switch between
"    files/buffers.
" 4. When a tag name is selected from the taglist window, positions the cursor
"    at the definition of the tag in the source file
" 5. Automatically highlights the current tag name.
" 6. Can display the prototype of a tag from the taglist window.
" 7. The tag list can be sorted either by name or by line number.
" 8. Runs in all the platforms where the exuberant ctags utility and Vim are
"     supported (this includes MS-Windows and Unix based systems).
" 9. Runs in both console/terminal and GUI versions of Vim.
" 
" This plugin relies on the exuberant ctags utility to generate the tag
" listing. You can download the exuberant ctags utility from
" http://ctags.sourceforge.net. The exuberant ctags utility must be installed
" in your system to use this plugin. You should use exuberant ctags version
" 5.3 and above.  There is no need for you to create a tags file to use this
" plugin.
"
" This script relies on the Vim "filetype" detection mechanism to determine
" the type of the current file. To turn on filetype detection use
"
"               :filetype on
"
" This plugin will not work in 'compatible' mode.  Make sure the 'compatible'
" option is not set. This plugin will not work if you run Vim in the
" restricted mode (using the -Z command-line argument). This plugin also
" assumes that the system() Vim function is supported.
"
" Installation
" ------------
" 1. Copy the javabrowser.vim script to the $HOME/.vim/plugin directory. Refer to
"    ':help add-plugin', ':help add-global-plugin' and ':help runtimepath' for
"    more details about Vim plugins.
" 2. Set the JavaBrowser_Ctags_Cmd variable to point to the exuberant ctags utility
"    path.
" 3. If you are running a terminal/console version of Vim and the terminal
"    doesn't support changing the window width then set the JavaBrowser_Inc_Winwidth
"    variable to 0.
" 4. Restart Vim.
" 5. You can use the ":JavaBrowser" command to open/close the taglist window. 
"
" Usage
" -----
" You can open the taglist window from a source window by using the ":JavaBrowser"
" command. Invoking this command will toggle (open or close) the taglist
" window. You can map a key to invoke this command:
"
"               nnoremap <silent> <F8> :JavaBrowser<CR>
"
" Add the above mapping to your ~/.vimrc file.
"
" You can close the browser window from the browser window by pressing 'q' or
" using the Vim ":q" command. As you switch between source files, the taglist
" window will be automatically updated with the tag listing for the current
" source file.
"
" The tag names will grouped by their type (variable, function, class, etc)
" and displayed as a foldable tree using the Vim folding support. You can
" collapse the tree using the '-' key or using the Vim zc fold command. You
" can open the tree using the '+' key or using hte Vim zo fold command. You
" can open all the fold using the '*' key or using the Vim zR fold command
" You can also use the mouse to open/close the folds.
"
" You can select a tag either by pressing the <Enter> key or by double
" clicking the tag name using the mouse.
"
" The script will automatically highlight the name of the current tag.  The
" tag name will be highlighted after 'updatetime' milliseconds. The default
" value for this Vim option is 4 seconds.
"
" If you place the cursor on a tag name in the browser window, then the tag
" prototype will be displayed at the Vim status line after 'updatetime'
" milliseconds. The default value for the 'updatetime' Vim option is 4
" seconds. You can also press the space bar to display the prototype of the
" tag under the cursor.
"
" By default, the tag list will be sorted by the order in which the tags
" appear in the file. You can sort the tags either by name or by order by
" pressing the "s" key in the taglist window.
"
" You can press the 'x' key in the taglist window to maximize the taglist
" window width/height. The window will be maximized to the maximum possible
" width/height without closing the other existing windows. You can again press
" 'x' to restore the taglist window to the default width/height.
"
" You can open the taglist window on startup using the following command line:
"
"               $ vim +JavaBrowser
"
" If the line number is not supplied, this command will display the prototype
" of the current function.
"
" Configuration
" -------------
" By changing the following variables you can configure the behavior of this
" script. Set the following variables in your .vimrc file using the 'let'
" command.
"
" The script uses the JavaBrowser_Ctags_Cmd variable to locate the ctags utility.
" By default, this is set to ctags. Set this variable to point to the location
" of the ctags utility in your system:
"
"               let JavaBrowser_Ctags_Cmd = 'd:\tools\ctags.exe'
"
" By default, the tag names will be listed in the order in which they are
" defined in the file. You can alphabetically sort the tag names by pressing
" the "s" key in the taglist window. You can also change the default order by
" setting the variable JavaBrowser_Sort_Type to "name" or "order":
"
"               let JavaBrowser_Sort_Type = "name"
"
" Be default, the tag names will be listed in a vertically split window.  If
" you prefer a horizontally split window, then set the
" 'JavaBrowser_Use_Horiz_Window' variable to 1. If you are running MS-Windows
" version of Vim in a MS-DOS command window, then you should use a
" horizontally split window instead of a vertically split window.  Also, if
" you are using an older version of xterm in a Unix system that doesn't
" support changing the xterm window width, you should use a horizontally split
" window.
"
"               let JavaBrowser_Use_Horiz_Window = 1
"
" By default, the vertically split taglist window will appear on the left hand
" side. If you prefer to open the window on the right hand side, you can set
" the JavaBrowser_Use_Right_Window variable to one:
"
"               let JavaBrowser_Use_Right_Window = 1
"
" To automatically open the taglist window, when you start Vim, you can set
" the JavaBrowser_Auto_Open variable to 1. By default, this variable is set to 0 and
" the taglist window will not be opened automatically on Vim startup.
"
"               let JavaBrowser_Auto_Open = 1
"
" By default, only the tag name will be displayed in the taglist window. If
" you like to see tag prototypes instead of names, set the
" JavaBrowser_Display_Prototype variable to 1. By default, this variable is set to 0
" and only tag names will be displayed.
"
"               let JavaBrowser_Display_Prototype = 1
"
" The default width of the vertically split taglist window will be 30.  This
" can be changed by modifying the JavaBrowser_WinWidth variable:
"
"               let JavaBrowser_WinWidth = 20
"
" Note that the value of the 'winwidth' option setting determines the minimum
" width of the current window. If you set the 'JavaBrowser_WinWidth' variable to a
" value less than that of the 'winwidth' option setting, then Vim will use the
" value of the 'winwidth' option.
"
" By default, when the width of the window is less than 100 and a new taglist
" window is opened vertically, then the window width will be increased by the
" value set in the JavaBrowser_WinWidth variable to accomodate the new window.  The
" value of this variable is used only if you are using a vertically split
" taglist window.  If your terminal doesn't support changing the window width
" from Vim (older version of xterm running in a Unix system) or if you see any
" weird problems in the screen due to the change in the window width or if you
" prefer not to adjust the window width then set the 'JavaBrowser_Inc_Winwidth'
" variable to 0.  CAUTION: If you are using the MS-Windows version of Vim in a
" MS-DOS command window then you must set this variable to 0, otherwise the
" system may hang due to a Vim limitation (explained in :help win32-problems)
"
"               let JavaBrowser_Inc_Winwidth = 0
"
" By default, when you double click on the tag name using the left mouse 
" button, the cursor will be positioned at the definition of the tag. You 
" can set the JavaBrowser_Use_SingleClick variable to one to jump to a tag when
" you single click on the tag name using the mouse. By default this variable
" is set to zero.
"
"               let JavaBrowser_Use_SingleClick = 1
"
" By default, the taglist window will contain text that display the name of
" the file, sort order information and the key to press to get help. Also,
" empty lines will be used to separate different groups of tags. If you
" don't need these information, you can set the JavaBrowser_Compact_Format variable
" to one to get a compact display.
"
"               let JavaBrowser_Compact_Format = 1
"
" By default, the tree for package/class/interface members is folded. If you
" want the tree to be expanded at the startup, put the following statement in
" the vimrc file
"               let JavaBrowser_Expand_Tree_At_Startup = 1
"
" Extending
" ---------
" You can add support for new languages or modify the support for an already
" supported language by setting the following variables in the .vimrc file.
"
" To modify the support for an already supported language, you have to set the
" jbrowser_xxx_ctags_args and jbrowser_xxx_tag_types variables (replace xxx with the
" name of the language).  For example, to list only the classes and functions
" defined in a C++ language file, add the following lines to your .vimrc file
"
"       let jbrowser_cpp_ctags_args = '--language-force=c++ --c++-types=fc'
"       let jbrowser_cpp_tag_types = 'class function'
"
" The jbrowser_xxx_ctags_args setting will be passed as command-line argument to
" the exuberant ctags tool. The names set in the jbrowser_xxx_tag_types variable
" must exactly match the tag type names used by the exuberant ctags tool.
" Otherwise, you will get error messages when using the taglist plugin. You
" can get the tag type names used by exuberant ctags using the command line
"
"       ctags -f - --fields=K <filename>
"
" To add support for a new language, you have to set the name of the language
" in the jbrowser_file_types variable. For example,
"
"       let jbrowser_file_types = 'xxx'
"
" In addition to the above setting, you have to set the jbrowser_xxx_ctags_args
" and the jbrowser_xxx_tag_types variable as described above.
"
if exists('loaded_javabroswer') || &cp
    finish
endif
let loaded_javabroswer=1

" Location of the exuberant ctags tool
if !exists('JavaBrowser_Ctags_Cmd')
    let JavaBrowser_Ctags_Cmd = 'ctags'
endif

" Option to show UML like visibility notations
if !exists('JavaBrowser_Show_UML_Visibility')
    let JavaBrowser_Show_UML_Visibility = 1
endif

" Tag listing sort type - 'name' or 'order'
if !exists('JavaBrowser_Sort_Type')
    let JavaBrowser_Sort_Type = 'order'
endif

" Tag listing window split (horizontal/vertical) control
if !exists('JavaBrowser_Use_Horiz_Window')
    let JavaBrowser_Use_Horiz_Window = 0
endif

" Open the vertically split taglist window on the left or on the right side.
" This setting is relevant only if JavaBrowser_Use_Horiz_Window is set to zero (i.e.
" only for vertically split windows)
if !exists('JavaBrowser_Use_Right_Window')
    let JavaBrowser_Use_Right_Window = 0
endif

" Flag to indicate if the tree for package/class/interface members needs to be
" expanded at startup
if !exists('JavaBrowser_Expand_Tree_At_Startup')
    let JavaBrowser_Expand_Tree_At_Startup = 1
endif

" Increase Vim window width to display vertically split taglist window.  For
" MS-Windows version of Vim running in a MS-DOS window, this must be set to 0
" otherwise the system may hang due to a Vim limitation.
if !exists('JavaBrowser_Inc_Winwidth')
    if (has('win16') || has('win95')) && !has('gui_running')
        let JavaBrowser_Inc_Winwidth = 0
    else
        let JavaBrowser_Inc_Winwidth = 1
    endif
endif

" Vertically split taglist window width setting
if !exists('JavaBrowser_WinWidth')
    let JavaBrowser_WinWidth = 30
endif

" Horizontally split taglist window height setting
if !exists('JavaBrowser_WinHeight')
    let JavaBrowser_WinHeight = 10
endif

" Automatically open the taglist window on Vim startup
if !exists('JavaBrowser_Auto_Open')
    let JavaBrowser_Auto_Open = 0
endif

" Display tag prototypes or tag names in the taglist window
if !exists('JavaBrowser_Display_Prototype')
    let JavaBrowser_Display_Prototype = 0
endif

" Use single left mouse click to jump to a tag. By default this is disabled.
" Only double click using the mouse will be processed.
if !exists('JavaBrowser_Use_SingleClick')
    let JavaBrowser_Use_SingleClick = 0
endif

" Control whether additional help is displayed as part of the taglist or not.
" Also, controls whether empty lines are used to separate the tag tree.
if !exists('JavaBrowser_Compact_Format')
    let JavaBrowser_Compact_Format = 0
endif

" Use tagindicator (an arrow) icon to show the current tag
if !exists('JavaBrowser_Use_Icon')
    let JavaBrowser_Use_Icon = 0
endif

" Use a text simulated arrow (=>) to show the current tag
if JavaBrowser_Use_Icon == 0 && !exists('JavaBrowser_Use_Text_Icon')
    let JavaBrowser_Use_Text_Icon = 1
endif

" Use a highlight to show the current tag
if !exists('JavaBrowser_Use_Highlight_Tag')
    let JavaBrowser_Use_Highlight_Tag = 0
endif

" Check if vim has been compiled with the signs feature or not
" if not, we enable the highlight tag at least to show current tag
if !has('signs')
    let JavaBrowser_Use_Icon = 0
    let JavaBrowser_Use_Text_Icon = 0
    let JavaBrowser_Use_Highlight_Tag = 1
endif

" Check and define signs, if required
if g:JavaBrowser_Use_Icon == 1
    let imgName = 'tagindicator.xpm'
    if has('win32')
        let imgName = 'tagindicator.bmp'
    endif
    exe 'sign define currTag icon=' . substitute(expand('$VIM'), ' ', '\\ ', 'g') . '/pixmaps/' . imgName . ' text==> texthl=Constant'
else
    if g:JavaBrowser_Use_Text_Icon == 1
        exe 'sign define currTag text==> texthl=Constant'
    endif
endif

" Display the prototype of the tag where mouse is pointing to
if version >= 700 && has('balloon_eval')
    set bexpr=JavaBrowser_Show_Prototype()
    set ballooneval
endif


" File types supported by taglist
let s:jbrowser_file_types = 'java'
if exists('g:jbrowser_file_types')
    " Add user specified file types
    let s:jbrowser_file_types = s:jbrowser_file_types . ' ' . g:jbrowser_file_types
endif

" c++ language
"let s:jbrowser_def_cpp_ctags_args = '--language-force=c++ --c++-types=vdtcgsuf'
"let s:jbrowser_def_cpp_tag_types = 'macro typedef class enum struct union ' .
"                            \ 'variable function'
" java language
let s:jbrowser_def_java_ctags_args = '--language-force=java --java-types=pcifm'
let s:jbrowser_def_java_tag_types = 'package class interface field method'
let s:jbrowser_def_java_super_tag_types = 'package class interface'
let s:jbrowser_def_java_visibilities = 'public protected private'

" JavaBrowser_Init()
" Initialize the taglist script local variables for the supported file types
" and tag types
function! s:JavaBrowser_Init()
    let s:jbrowser_winsize_chgd = 0
    let s:jbrowser_win_maximized = 0
endfunction

" Initialize the script
call s:JavaBrowser_Init()

function! s:JavaBrowser_Show_Help()
    echo 'Keyboard shortcuts for the browser window'
    echo '-----------------------------------------'
    echo '<Enter> : Jump to the definition'
    echo 'o       : Jump to the definition in a new window'
    echo '<Space> : Display the prototype'
    echo 'u       : Update the browser window'
    echo 's       : Sort the list by ' . 
                            \ (b:jbrowser_sort_type == 'name' ? 'order' : 'name')
    echo 'x       : Zoom-out/Zoom-in the window'
    echo '+       : Open a fold'
    echo '-       : Close a fold'
    echo '*       : Open all folds'
    echo 'q       : Close the browser window'
endfunction

" An autocommand is used to refresh the taglist window when entering any
" buffer. We don't want to refresh the taglist window if we are entering the
" file window from one of the taglist functions. The 'JavaBrowser_Skip_Refresh'
" variable is used to skip the refresh of the taglist window
let s:JavaBrowser_Skip_Refresh = 0

function! s:JavaBrowser_Warning_Msg(msg)
    echohl WarningMsg
    echomsg a:msg
    echohl None
endfunction

" JavaBrowser_Skip_Buffer()
" Check whether tag listing is supported for the specified buffer.
function! s:JavaBrowser_Skip_Buffer(bufnum)
    " Skip buffers with 'buftype' set to nofile, nowrite, quickfix or help
    if getbufvar(a:bufnum, '&buftype') != ''
        return 1
    endif

    " Skip buffers with filetype not set
    if getbufvar(a:bufnum, '&filetype') == ''
        return 1
    endif

    let filename = fnamemodify(bufname(a:bufnum), '%:p')

    " Skip buffers with no names
    if filename == ''
        return 1
    endif

    " Skip files which are not readable or files which are not yet stored
    " to the disk
    if !filereadable(filename)
        return 1
    endif

    return 0
endfunction

" JavaBrowser_TagType_Init
function! s:JavaBrowser_TagType_Init(ftype)
    " If the user didn't specify any settings, then use the default
    " ctags args. Otherwise, use the settings specified by the user
    let var = 'g:jbrowser_' . a:ftype . '_ctags_args'
    if exists(var)
        " User specified ctags arguments
        let s:jbrowser_{a:ftype}_ctags_args = {var}
    else
        " Default ctags arguments
        let s:jbrowser_{a:ftype}_ctags_args = s:jbrowser_def_{a:ftype}_ctags_args
    endif

    " Same applies for tag types
    let var = 'g:jbrowser_' . a:ftype . '_tag_types'
    if exists(var)
        " User specified exuberant ctags tag names
        let s:jbrowser_{a:ftype}_tag_types = {var}
    else
        " Default exuberant ctags tag names
        let s:jbrowser_{a:ftype}_tag_types = s:jbrowser_def_{a:ftype}_tag_types
    endif

    let s:jbrowser_{a:ftype}_count = 0

    " Get the supported tag types for this file type
    let txt = 's:jbrowser_' . a:ftype . '_tag_types'
    if exists(txt)
        " Process each of the supported tag types
        let tts = s:jbrowser_{a:ftype}_tag_types . ' '
        let cnt = 0
        while tts != ''
            " Create the script variable with the tag type name
            let ttype = strpart(tts, 0, stridx(tts, ' '))
            if ttype != ''
                let cnt = cnt + 1
                let s:jbrowser_{a:ftype}_{cnt}_name = ttype
            endif
            let tts = strpart(tts, stridx(tts, ' ') + 1)
        endwhile
        " Create the tag type count script local variable
        let s:jbrowser_{a:ftype}_count = cnt
    endif
endfunction

" JavaBrowser_Cleanup()
" Cleanup all the taglist window variables.
function! s:JavaBrowser_Cleanup()
    match none

    if exists('b:jbrowser_ftype') && b:jbrowser_ftype != ''
        let count_var_name = 's:jbrowser_' . b:jbrowser_ftype . '_count'
        if exists(count_var_name)
            let old_ftype = b:jbrowser_ftype
            let i = 1
            while i <= s:jbrowser_{old_ftype}_count
                let ttype = s:jbrowser_{old_ftype}_{i}_name
                let j = 1
                let var_name = 'b:jbrowser_' . old_ftype . '_' . ttype . '_count'
                if exists(var_name)
                    let cnt = b:jbrowser_{old_ftype}_{ttype}_count
                else
                    let cnt = 0
                endif
                while j <= cnt
                    unlet! b:jbrowser_{old_ftype}_{ttype}_{j}
                    let j = j + 1
                endwhile
                unlet! b:jbrowser_{old_ftype}_{ttype}_count
                "unlet! b:jbrowser_{old_ftype}_{ttype}_start
                let i = i + 1
            endwhile
        endif
    endif

    " Clean up all the variables containing the tags output
    if exists('b:jbrowser_tag_count')
        while b:jbrowser_tag_count > 0
            unlet! b:jbrowser_tag_{b:jbrowser_tag_count}
            let b:jbrowser_tag_count = b:jbrowser_tag_count - 1
        endwhile
    endif

    unlet! b:jbrowser_bufnum
    unlet! b:jbrowser_bufname
    unlet! b:jbrowser_ftype
endfunction

" JavaBrowser_Open_Window
" Create a new taglist window. If it is already open, clear it
function! s:JavaBrowser_Open_Window()
    " Tag list window name
    let bname = '__JBrowser_List__'

    " Cleanup the taglist window listing, if the window is open
    let winnum = bufwinnr(bname)
    if winnum != -1
        " Jump to the existing window
        if winnr() != winnum
            exe winnum . 'wincmd w'
        endif
    else
        " Create a new window. If user prefers a horizontal window, then open
        " a horizontally split window. Otherwise open a vertically split
        " window
        if g:JavaBrowser_Use_Horiz_Window == 1
            " If a single window is used for all files, then open the tag
            " listing window at the very bottom
            let win_dir = 'botright'
            " Horizontal window height
            let win_size = g:JavaBrowser_WinHeight
        else
            " Increase the window size, if needed, to accomodate the new
            " window
            if g:JavaBrowser_Inc_Winwidth == 1 &&
                        \ &columns < (80 + g:JavaBrowser_WinWidth)
                " one extra column is needed to include the vertical split
                let &columns= &columns + (g:JavaBrowser_WinWidth + 1)
                let s:jbrowser_winsize_chgd = 1
            else
                let s:jbrowser_winsize_chgd = 0
            endif

            " Open the window at the leftmost place
            if g:JavaBrowser_Use_Right_Window == 1
                let win_dir = 'botright vertical'
            else
                let win_dir = 'topleft vertical'
            endif
            let win_size = g:JavaBrowser_WinWidth
        endif

        " If the tag listing temporary buffer already exists, then reuse it.
        " Otherwise create a new buffer
        let bufnum = bufnr(bname)
        if bufnum == -1
            " Create a new buffer
            let wcmd = bname
        else
            " Edit the existing buffer
            let wcmd = '+buffer' . bufnum
        endif

        " Create the taglist window
        exe 'silent! ' . win_dir . ' ' . win_size . 'split ' . wcmd
    endif
endfunction

" JavaBrowser_Zoom_Window
" Zoom (maximize/minimize) the taglist window
function! s:JavaBrowser_Zoom_Window()
    if s:jbrowser_win_maximized == 1
        if g:JavaBrowser_Use_Horiz_Window == 1
            exe 'resize ' . g:JavaBrowser_WinHeight
        else
            exe 'vert resize ' . g:JavaBrowser_WinWidth
        endif
        let s:jbrowser_win_maximized = 0
    else
        " Set the window size to the maximum possible without closing other
        " windows
        if g:JavaBrowser_Use_Horiz_Window == 1
            resize
        else
            vert resize
        endif
        let s:jbrowser_win_maximized = 1
    endif
endfunction

" JavaBrowser_Init_Window
" Set the default options for the taglist window
function! s:JavaBrowser_Init_Window(bufnum)
    " Set report option to a huge value to prevent informations messages
    " while deleting the lines
    let old_report = &report
    set report=99999

    " Mark the buffer as modifiable
    setlocal modifiable

    " Delete the contents of the buffer to the black-hole register
    silent! %delete _

    " Mark the buffer as not modifiable
    setlocal nomodifiable

    " Restore the report option
    let &report = old_report

    " Clean up all the old variables used for the last filetype
    call <SID>JavaBrowser_Cleanup()

    let filename = fnamemodify(bufname(a:bufnum), ':p')

    " Set the sort type. First time, use the global setting. After that use
    " the previous setting
    let b:jbrowser_sort_type = getbufvar(a:bufnum, 'jbrowser_sort_type')
    if b:jbrowser_sort_type == ''
        let b:jbrowser_sort_type = g:JavaBrowser_Sort_Type
    endif

    let b:jbrowser_tag_count = 0
    let b:jbrowser_bufnum = a:bufnum
    let b:jbrowser_bufname = fnamemodify(bufname(a:bufnum), ':p')
    let b:jbrowser_ftype = getbufvar(a:bufnum, '&filetype')
    let b:buf_tag_line_no = -2

    " Mark the buffer as modifiable
    setlocal modifiable

    if g:JavaBrowser_Compact_Format == 0
        call append(0, '" Press ? for help')
        "call append(1, '" Sorted by ' . b:jbrowser_sort_type)
        call append(1, '" Sorted by name')
        call append(2, '" =' . fnamemodify(filename, ':t') . ' (' . 
                                   \ fnamemodify(filename, ':p:h') . ')')
    endif
    if has('syntax')
        syntax match JavaBrowserComment '^" .*'
    endif

    " Mark the buffer as not modifiable
    setlocal nomodifiable
    
    " Folding related settings
    if has('folding')
        setlocal foldenable
        setlocal foldmethod=manual
        setlocal foldcolumn=2
        setlocal foldtext=v:folddashes.getline(v:foldstart)
    endif

    " Mark buffer as scratch
    silent! setlocal buftype=nofile
    silent! setlocal bufhidden=delete
    silent! setlocal noswapfile
    silent! setlocal nowrap
    silent! setlocal nobuflisted

    " If the 'number' option is set in the source window, it will affect the
    " taglist window. So forcefully disable 'number' option for the taglist
    " window
    silent! setlocal nonumber

    " Create buffer local mappings for jumping to the tags and sorting the list
    nnoremap <buffer> <silent> <CR> :call <SID>JavaBrowser_Jump_To_Tag(0)<CR>
    nnoremap <buffer> <silent> o :call <SID>JavaBrowser_Jump_To_Tag(1)<CR>
    nnoremap <buffer> <silent> <2-LeftMouse> :call <SID>JavaBrowser_Jump_To_Tag(0)<CR>
    nnoremap <buffer> <silent> s :call <SID>JavaBrowser_Change_Sort()<CR>
    nnoremap <buffer> <silent> + :silent! foldopen<CR>
    nnoremap <buffer> <silent> - :silent! foldclose<CR>
    nnoremap <buffer> <silent> * :silent! %foldopen!<CR>
    nnoremap <buffer> <silent> <kPlus> :silent! foldopen<CR>
    nnoremap <buffer> <silent> <kMinus> :silent! foldclose<CR>
    nnoremap <buffer> <silent> <kMultiply> :silent! %foldopen!<CR>
    nnoremap <buffer> <silent> <Space> :call <SID>JavaBrowser_Show_Tag_Prototype()<CR>
    nnoremap <buffer> <silent> u :call <SID>JavaBrowser_Update_Window()<CR>
    nnoremap <buffer> <silent> x :call <SID>JavaBrowser_Zoom_Window()<CR>
    nnoremap <buffer> <silent> ? :call <SID>JavaBrowser_Show_Help()<CR>
    nnoremap <buffer> <silent> q :close<CR>

    " Map single left mouse click if the user wants this functionality
    if g:JavaBrowser_Use_SingleClick == 1
    nnoremap <silent> <LeftMouse> <LeftMouse>:if bufname("%") =~ "__JBrowser_List__"
                        \ <bar> call <SID>JavaBrowser_Jump_To_Tag(0) <bar> endif <CR>
    else
        if hasmapto('<LeftMouse>')
            nunmap <LeftMouse>
        endif
    endif

    " Define the autocommand to highlight the current tag
    augroup JavaBrowserAutoCmds
        autocmd!
        " Display the tag prototype for the tag under the cursor.
        autocmd CursorHold __JBrowser_List__ call s:JavaBrowser_Show_Tag_Prototype()
        " Highlight the current tag 
        autocmd CursorHold *.java silent call s:JavaBrowser_Highlight_Tag(bufnr('%'), 
                                       \ line('.'))
        " Unlighlight the previous search
        autocmd CursorHold *.java call s:JavaBrowser_Unhighlight_Prvline()
        " Adjust the Vim window width when taglist window is closed
        autocmd BufUnload __JBrowser_List__ call <SID>JavaBrowser_Close_Window()
        " Auto refresh the taglisting window
        autocmd BufEnter * call <SID>JavaBrowser_Refresh_Window()
    augroup end
endfunction

" JavaBrowser_Close_Window()
" Close the taglist window and adjust the Vim window width
function! s:JavaBrowser_Close_Window()
    " Remove the autocommands for the taglist window
    silent! autocmd! JavaBrowserAutoCmds

    if g:JavaBrowser_Use_Horiz_Window || g:JavaBrowser_Inc_Winwidth == 0 ||
                \ s:jbrowser_winsize_chgd == 0 ||
                \ &columns < (80 + g:JavaBrowser_WinWidth)
        " No need to adjust window width if horizontally split tag listing
        " window or if columns is less than 101 or if the user chose not to
        " adjust the window width
    else
        " Adjust the Vim window width
        let &columns= &columns - (g:JavaBrowser_WinWidth + 1)
    endif
endfunction

" JavaBrowser_Get_Visib_From_Proto
" Get the visibility of a class member from its prototype
function! s:JavaBrowser_Get_Visib_From_Proto(bufnum, proto)
    let l:visib = 'default'
    let ftype = getbufvar(a:bufnum, '&filetype')
    let l:visibstartidx = match(a:proto, '\a')
    let l:visibendidx = match(a:proto, '(', visibstartidx)
    if l:visibendidx == -1
        let l:visibendidx = match(a:proto, '$', visibstartidx)
    endif
    let l:tmp_proto = strpart(a:proto, l:visibstartidx, l:visibendidx-l:visibstartidx)
    while l:visibstartidx != -1
        let l:cur_proto_part = strpart(l:tmp_proto, 0, stridx(l:tmp_proto, " "))
        "call s:JavaBrowser_Warning_Msg('current proto part: '.l:cur_proto_part)
        if stridx(s:jbrowser_def_{ftype}_visibilities, l:cur_proto_part) != -1
            let l:visib = l:cur_proto_part
            break
        endif
        " Remove the word
        let l:tmp_proto = strpart(l:tmp_proto, stridx(l:tmp_proto, " ") + 1)
        let l:visibstartidx = match(l:tmp_proto, " ")
    endwhile
    return l:visib
endfunction

" JavaBrowser_Explore_File()
" List the tags defined in the specified file in a Vim window
function! s:JavaBrowser_Explore_File(bufnum)
    " Get the filename and file type
    let filename = fnamemodify(bufname(a:bufnum), ':p')
    let ftype = getbufvar(a:bufnum, '&filetype')

    " Check for valid filename and valid filetype
    if filename == '' || !filereadable(filename) || ftype == ''
        return
    endif

    " Make sure the current filetype is supported by exuberant ctags
    if stridx(s:jbrowser_file_types, ftype) == -1
        call s:JavaBrowser_Warning_Msg('File type ' . ftype . ' not supported')
        return
    endif

    " If the tag types for this filetype are not yet created, then create
    " them now
    let var = 's:jbrowser_' . ftype . '_count'
    if !exists(var)
        call s:JavaBrowser_TagType_Init(ftype)
    endif

    " If the cached ctags output exists for the specified buffer, then use it.
    " Otherwise run ctags to get the output
    let valid_cache = getbufvar(a:bufnum, 'jbrowser_valid_cache')
    if valid_cache != ''
        " Load the cached processed tags output from the buffer local
        " variables
        let b:classes_dict = getbufvar(a:bufnum, 'jbrowser_classes_dict')
        let b:jbrowser_to_buffer_lno_dict = getbufvar(a:bufnum, 'jbrowser_to_buffer_lno_dict')
        let b:buffer_to_jbrowser_lno_dict = getbufvar(a:bufnum, 'buffer_to_jbrowser_lno_dict')
        let b:protos_dict = getbufvar(a:bufnum, 'jbrowser_protos_dict')
    else
        " Exuberant ctags arguments to generate a tag list
        let ctags_args = ' -f - --format=2 --excmd=pattern --fields=nKs '

        " Form the ctags argument depending on the sort type 
        if b:jbrowser_sort_type == 'name'
            let ctags_args = ctags_args . ' --sort=yes '
        else
            let ctags_args = ctags_args . ' --sort=no '
        endif

        " Override count
        let l:override_cnt = 1

        " Add the filetype specific arguments
        let ctags_args = ctags_args . ' ' . s:jbrowser_{ftype}_ctags_args

        " Ctags command to produce output with regexp for locating the tags
        let ctags_cmd = g:JavaBrowser_Ctags_Cmd . ctags_args
        let ctags_cmd = ctags_cmd . ' "' . filename . '"'

        " Run ctags and get the tag list
        let cmd_output = system(ctags_cmd)

        " Handle errors
        if v:shell_error && cmd_output != ''
            call s:JavaBrowser_Warning_Msg(cmd_output)
            return
        endif

        " No tags for current file
        if cmd_output == ''
            call s:JavaBrowser_Warning_Msg('No tags found for ' . filename)
            return
        endif
        
        " Initialize the variables
        let b:classes_dict = {}
        let b:jbrowser_to_buffer_lno_dict = {}
        let b:buffer_to_jbrowser_lno_dict = {}
        let b:protos_dict = {}

        " Process the ctags output one line at a time. Separate the tag output
        " based on the tag type and store it in the tag type variable
        let l:alltypes = ""
        let l:prefix = 'jbrowser_' . ftype
        while cmd_output != ''
            " Extract one line at a time
            let one_line = strpart(cmd_output, 0, stridx(cmd_output, "\n"))
            " Remove the line from the tags output
            let cmd_output = strpart(cmd_output, stridx(cmd_output, "\n") + 1)

            if one_line == ''
                " Line is not in proper tags format
                continue
            endif

            " Extract the tag type
            let ttype = s:JavaBrowser_Extract_Tagtype(one_line)
            if ttype == 'package'
                continue
            endif

            let protostart = stridx(one_line, '^')
            let protoend = stridx(one_line, '$')
            let proto = strpart(one_line, protostart+1, protoend-protostart-1)
            let visib = s:JavaBrowser_Get_Visib_From_Proto(a:bufnum, proto)

            if ttype == ''
                " Line is not in proper tags format
                continue
            endif

            " Extract the tag name
            let ttxt = strpart(one_line, 0, stridx(one_line, "\t"))
            
            " Add the tag scope, if it is available. Tag scope is the last
            " field after the 'line:<num>\t' field
            let start = strridx(one_line, 'line:')
            let end = strridx(one_line, "\t")
            let lnnostart = strridx(one_line, 'line:')
            let lnnoend = strridx(one_line, "\t")
            let tscope = ''
            if end > start
                let lnno = strpart(one_line, lnnostart+5, lnnoend-lnnostart-5)
                let tscope = strpart(one_line, end + 1)
                let tscope = strpart(tscope, stridx(tscope, ':') + 1)
            else
                let lnno = strpart(one_line, lnnostart+5)
            endif

            " DEBUG messages
            "call s:JavaBrowser_Warning_Msg('scope for '.ttxt.' is '.tscope)
            "call s:JavaBrowser_Warning_Msg('lineno for '.ttxt.' is '.lnno)
            if tscope == ''
                continue
            endif
            
            " Check if the class entry exists already
            if ! has_key(b:classes_dict, tscope)
                " Add an empty entry for this class
                let b:classes_dict[tscope] = {}
            endif

            " Get the members dictionary for this class
            let l:members = b:classes_dict[tscope]
            if ! has_key(l:members, ttype)
                " Add an empty entry for this class member type
                let l:members[ttype] = {}
            endif

            " Get the members of type ttype for this class
            let l:members_list = l:members[ttype]
            
            " Check for overriden methods
            if has_key(l:members_list, ttxt)
                " We got an overriden method
                let ttxt = ttxt . '__OVERRIDE__' . l:override_cnt
                let l:override_cnt = l:override_cnt + 1
            endif
            " Add an empty entry for this class member type
            let l:members_list[ttxt] = []
            let l:member_details = l:members_list[ttxt]

            " DEBUG messages
            "let l:str = string(l:member_details)
            "call s:JavaBrowser_Warning_Msg('member_details: '.l:str)

            " Add the line number, prototype and visibility for this member
            call add(l:member_details, lnno)

            " Check if the prototype starts with a tab and remove it
            if stridx(proto, "\t") == 0
                let proto = strpart(proto, 1)
            endif
            call add(l:member_details, proto)

            " DEBUG messages
            "let l:str = string(l:member_details)
            "call s:JavaBrowser_Warning_Msg('member_details: '.l:str)

            " Form the visibility
            let l:visibility = ''
            if stridx(s:jbrowser_def_{ftype}_visibilities, visib) != -1
                let l:visibility = visib
            endif

            " Check if we are working on an interface
            if  ttype == 'interface'
                if stridx(l:visibility, 'public') == -1
                    let l:visibility = l:visibility . 'public'
                endif
                if ttype == 'field'
                    let l:visibility = l:visibility . '_static'
                endif
                if ttype == 'method' && stridx(proto, 'abstract ') == -1
                    let l:visibility = l:visibility . '_abstract'
                endif
            endif

            " Deal with other types here
            if stridx(proto, ' abstract ') != -1
                let l:visibility = l:visibility . '_abstract'
            endif
            if stridx(proto, ' static ') != -1
                let l:visibility = l:visibility . '_static'
            endif
            call add(l:member_details, l:visibility)
        endwhile
    endif
    
    " Cache the processed tags output using buffer local variables
    call setbufvar(a:bufnum, 'jbrowser_valid_cache', 'Yes')
    call setbufvar(a:bufnum, 'jbrowser_classes_dict', b:classes_dict)
    call setbufvar(a:bufnum, 'jbrowser_to_buffer_lno_dict', b:jbrowser_to_buffer_lno_dict)
    call setbufvar(a:bufnum, 'buffer_to_jbrowser_lno_dict', b:buffer_to_jbrowser_lno_dict)
    call setbufvar(a:bufnum, 'jbrowser_protos_dict', b:protos_dict)
    call setbufvar(a:bufnum, 'jbrowser_sort_type', b:jbrowser_sort_type)

    " Cache the protos in JavaBrowser buffer
    let l:jbrow_bname = '__JBrowser_List__'
    let l:jbrow_bufnum = bufnr(l:jbrow_bname)
    call setbufvar(l:jbrow_bufnum, 'jbrowser_protos_dict', b:protos_dict)

    " Set report option to a huge value to prevent informational messages
    " while adding lines to the taglist window
    let old_report = &report
    set report=99999

    " Mark the buffer as modifiable
    setlocal modifiable

    " Clear the previous buffer to JBrowser line mapping
    call s:JavaBrowser_Clear_Buf_To_JBrowser_Map()
    let b:buf_to_jbrowser_line_nos = ''

    let i = 1
    let l:ttype_put = ''
	
    " Iterate through all the classes
    for l:class_name in sort(keys(b:classes_dict))
        let l:class_start_line = line('.')
        " Add the class/interface name
        silent! put ='  '.l:class_name
        " Syntax highlight the tag type names
        if has('syntax')
            exe 'syntax match JavaBrowserType /^' . '  '.l:class_name . '$/'
        endif
        
        " DEBUG messages
        "let l:str = string(b:classes_dict)
        "call s:JavaBrowser_Warning_Msg('class details dictionary: '.str)
        let l:members = b:classes_dict[l:class_name]
        " s:jbrowser_def_java_tag_types = 'package class interface field method'
        let l:types = 'field method '
        while l:types != ''
            let l:type = strpart(l:types, 0, stridx(l:types, " "))
            if l:type == ''
                break
            endif
            let l:types = strpart(l:types, stridx(l:types, " ") + 1)
            let l:type_start_line = line('.')

            " Get the list of fields/methods for this class/interface
            if ! has_key(l:members, l:type)
                continue
            endif
            
            " Put the type (field/method)
            silent! put ='    '.l:type
            " Syntax highlight the tag type names
            if has('syntax')
                exe 'syntax match JavaBrowserId /^' . '  '.l:type . '$/'
            endif
            
            let l:members_list = l:members[l:type]
            for l:member_name in sort(keys(l:members_list))
                let l:curr_line = line('.')
                let l:members_details = l:members_list[l:member_name]
                let l:line_no = get(l:members_details, 0, "NONE")
                let l:proto = get(l:members_details, 1, "NONE")
                let l:visib = get(l:members_details, 2, "NONE")
               
                " Store the line numbers mapping
                let b:jbrowser_to_buffer_lno_dict[l:curr_line] = l:line_no
                let b:buffer_to_jbrowser_lno_dict[l:line_no] = l:curr_line
                let b:protos_dict[l:curr_line] = l:proto

                " Check for overriden methods and get the actual method name
                let l:override_idx = stridx(l:member_name, '__OVERRIDE__')
                if l:override_idx != -1
                    let l:member_name = strpart(l:member_name, 0, l:override_idx)
                endif
                
                let l:orig_member_name = l:member_name
                " Show UML visibility notations
                if g:JavaBrowser_Show_UML_Visibility == 1
                    if stridx(l:proto, 'public') != -1
                        let l:member_name = '+ ' . l:member_name
                    endif
                    if stridx(l:proto, 'protected') != -1
                        let l:member_name = '# ' . l:member_name
                    endif
                    if stridx(l:proto, 'private') != -1
                        let l:member_name = '- ' . l:member_name
                    endif
                endif

                " Put the field/method and syntax highlight it
                silent! put ='      ' . l:member_name
                let l:syntaxGrp = 'JavaBrowser'
                if stridx(l:visib, '_') == 0
                    let l:syntaxGrp = l:syntaxGrp . l:visib
                else
                    let l:syntaxGrp = l:syntaxGrp . '_' . l:visib
                endif
                if has('syntax')
                    exe 'syntax match ' . l:syntaxGrp . ' /' . l:orig_member_name . '$/'
                endif
            endfor
            " create a fold for this tag type
            if has('folding')
                let fold_start = l:type_start_line+1
                let fold_end = line('.')
                exe fold_start . ',' . fold_end  . 'fold'
            endif
        endwhile
        " create a fold for this field/method type
        if has('folding')
            let fold_start = l:class_start_line+1
            let fold_end = line('.')
            exe fold_start . ',' . fold_end  . 'fold'
            exe 'normal ' . fold_start . 'G'
            exe 'normal zo'
            exe 'normal ' . fold_end . 'G'
        endif
        " Separate the tag types with a empty line
        normal! G
        if g:JavaBrowser_Compact_Format == 0
            silent! put =''
        endif
	endfor

    " Mark the buffer as not modifiable
    setlocal nomodifiable

    " Restore the report option
    let &report = old_report

    " Goto the first line in the buffer
    go

    " Expand the tree if expand flag is set
    if g:JavaBrowser_Expand_Tree_At_Startup == 1
        silent! %foldopen!
    endif
endfunction

" JavaBrowser_Set_Syntax_Highlighting()
" Set the syntax highlighting groups
function! s:JavaBrowser_Set_Syntax_Highlighting()
  " Highlight the comments
  if has('syntax')
      syntax match JavaBrowserComment '^" .*'
  
      " Colors used to highlight the selected tag name
      highlight clear TagName
      if has('gui_running') || &t_Co > 2
          highlight link TagName Search
      else
          highlight TagName term=reverse cterm=reverse
      endif
  
      " Colors to highlight. These are the defaults. User can change them in
      " their gvimrc as per their wish
      highlight link JavaBrowserComment Comment
      highlight clear JavaBrowserTitle
      highlight link JavaBrowserTitle Title
      highlight link JavaBrowserType Type
      highlight link JavaBrowserId Identifier
      
      " Colors for public members
      highlight link JavaBrowser_public Special
      highlight JavaBrowser_public ctermfg=darkgreen guifg=darkgreen
  
      " Colors for protected members
      highlight link JavaBrowser_protected Statement
      highlight JavaBrowser_protected ctermfg=brown guifg=orange
  
      " Colors for private members
      highlight link JavaBrowser_private Keyword
      highlight JavaBrowser_private ctermfg=red guifg=red
  
      " Colors for public, abstract members
      highlight link JavaBrowser_public_abstract JavaBrowser_public
      highlight JavaBrowser_public_abstract ctermfg=darkgreen term=italic cterm=italic guifg=darkgreen gui=italic
      
      " Colors for protected, abstract members
      highlight link JavaBrowser_protected_abstract JavaBrowser_protected
      highlight JavaBrowser_protected_abstract ctermfg=brown term=italic cterm=italic guifg=orange gui=italic
      
      " Colors for private, abstarct members
      highlight link JavaBrowser_private_abstract JavaBrowser_private
      highlight JavaBrowser_private_abstract ctermfg=red term=italic cterm=italic guifg=red gui=italic
  
      " Colors for public, static members
      highlight link JavaBrowser_public_static JavaBrowser_public
      highlight JavaBrowser_public_static ctermfg=darkgreen term=underline cterm=underline guifg=darkgreen gui=underline
      
      " Colors for protected, static members
      highlight link JavaBrowser_protected_static JavaBrowser_protected
      highlight JavaBrowser_protected_static ctermfg=brown term=underline cterm=underline guifg=orange gui=underline
      
      " Colors for private, static members
      highlight link JavaBrowser_private_static JavaBrowser_private
      highlight JavaBrowser_private_static ctermfg=red term=underline cterm=underline guifg=red gui=underline
  
      " Colors for abstract, static members (with default visibility)
      highlight link JavaBrowser_abstract_static Normal
      highlight JavaBrowser_abstract_static term=italic,underline cterm=italic,underline gui=italic,underline
      
      " Colors for static members (with default visibility)
      highlight link JavaBrowser_static Normal
      highlight JavaBrowser_static term=underline cterm=underline gui=underline
      
      " Colors for abstract members (with default visibility)
      highlight link JavaBrowser_abstract Normal
      highlight JavaBrowser_abstract term=italic cterm=italic gui=italic
      
      " Colors for public, abstract, static members
      highlight link JavaBrowser_public_abstract_static JavaBrowser_public
      highlight JavaBrowser_public_abstract_static ctermfg=darkgreen term=italic,underline cterm=italic,underline guifg=darkgreen gui=italic,underline
      
      " Colors for protected, abstract, static members
      highlight link JavaBrowser_protected_abstract_static JavaBrowser_protected
      highlight JavaBrowser_protected_abstract_static ctermfg=brown term=italic,underline cterm=italic,underline guifg=orange gui=italic,underline
      
      " Colors for private, abstract, static members
      highlight link JavaBrowser_private_abstract_static JavaBrowser_private
      highlight JavaBrowser_private_abstract_static ctermfg=red term=italic,underline cterm=italic,underline guifg=red gui=italic,underline
  endif
endfunction

" JavaBrowser_Toggle_Window()
" Open or close a taglist window
function! s:JavaBrowser_Toggle_Window(bufnum)
    " Set the syntx highlighting
    call s:JavaBrowser_Set_Syntax_Highlighting()

    let curline = line('.')

    " Tag list window name
    let bname = '__JBrowser_List__'

    " If taglist window is open then close it.
    let winnum = bufwinnr(bname)
    if winnum != -1
        if winnr() == winnum
            " Already in the taglist window. Close it and return
            close
        else
            " Goto the taglist window, close it and then come back to the
            " original window
            let curbufnr = bufnr('%')
            exe winnum . 'wincmd w'
            close
            " Need to jump back to the original window only if we are not
            " already in that window
            let winnum = bufwinnr(curbufnr)
            if winnr() != winnum
                exe winnum . 'wincmd w'
            endif
        endif
        return
    endif

    " Check if JavaBrowser is requested for a java file or not
    if &filetype !=# 'java'
        "call s:JavaBrowser_Warning_Msg('File type "' . &filetype . '" not supported. Only supported file types are: "java"')
        return
    endif

    " Open the taglist window
    call s:JavaBrowser_Open_Window()

    " Initialize the taglist window
    call s:JavaBrowser_Init_Window(a:bufnum)

    " List the tags defined in a file
    call s:JavaBrowser_Explore_File(a:bufnum)

    " Highlight the current tag
    call s:JavaBrowser_Highlight_Tag(a:bufnum, curline)

    " Go back to the original window
    "let s:JavaBrowser_Skip_Refresh = 1
    "wincmd p
    "let s:JavaBrowser_Skip_Refresh = 0
endfunction

" JavaBrowser_Extract_Tagtype
" Extract the tag type from the tag text
function! s:JavaBrowser_Extract_Tagtype(tag_txt)
    " The tag type is after the tag prototype field. The prototype field
    " ends with the /;"\t string. We add 4 at the end to skip the characters
    " in this special string..
    let start = strridx(a:tag_txt, '/;"' . "\t") + 4
    let end = strridx(a:tag_txt, 'line:') - 1
    let ttype = strpart(a:tag_txt, start, end - start)

    " Replace all space characters in the tag type with underscore (_)
    let ttype = substitute(ttype, ' ', '_', 'g')

    return ttype
endfunction

" JavaBrowser_Refresh_Window()
" Refresh the taglist window
function! s:JavaBrowser_Refresh_Window()
    " We are entering the buffer from one of the taglist functions. So no need
    " to refresh the taglist window again
    if s:JavaBrowser_Skip_Refresh == 1
        return
    endif

    " If the buffer doesn't support tag listing, skip it
    if s:JavaBrowser_Skip_Buffer(bufnr('%'))
        return
    endif

    let filename = expand('%:p')

    let curline = line('.')

    " Tag list window name
    let bname = '__JBrowser_List__'

    " Make sure the taglist window is open. Otherwise, no need to refresh
    let winnum = bufwinnr(bname)
    if winnum == -1
        return
    endif

    let bno = bufnr(bname)

    let cur_bufnr = bufnr('%')

    " If the tag listing for the current window is already present, no need to
    " refresh it
    if getbufvar(bno, 'jbrowser_bufnum') == cur_bufnr && 
                \ getbufvar(bno, 'jbrowser_bufname') == filename
        return
    endif

    " Save the current window number
    let cur_winnr = winnr()

    call s:JavaBrowser_Open_Window()

    call s:JavaBrowser_Init_Window(cur_bufnr)

    " Update the taglist window
    call s:JavaBrowser_Explore_File(cur_bufnr)

    " Highlight the current tag
    call s:JavaBrowser_Highlight_Tag(cur_bufnr, curline)

    " Refresh the taglist window
    "redraw

    " Jump back to the original window
    "exe cur_winnr . 'wincmd w'
endfunction

" JavaBrowser_Change_Sort()
" Change the sort order of the tag listing
function! s:JavaBrowser_Change_Sort()
    if !exists('b:jbrowser_bufnum') || !exists('b:jbrowser_ftype')
        return
    endif

    let sort_type = getbufvar(b:jbrowser_bufnum, 'jbrowser_sort_type')

    " Toggle the sort order from 'name' to 'order' and vice versa
    if sort_type == 'name'
        call setbufvar(b:jbrowser_bufnum, 'jbrowser_sort_type', 'order')
    else
        call setbufvar(b:jbrowser_bufnum, 'jbrowser_sort_type', 'name')
    endif

    " Save the current line for later restoration
    "let curline = '\V\^' . getline('.') . '\$'

    " Clear out the cached taglist information
    call setbufvar(b:jbrowser_bufnum, 'jbrowser_valid_cache', '')

    call s:JavaBrowser_Open_Window()

    call s:JavaBrowser_Init_Window(b:jbrowser_bufnum)

    call s:JavaBrowser_Explore_File(b:jbrowser_bufnum)

    " Go back to the tag line before the list is sorted
    "call search(curline, 'w')
    
    " Go to the java buffer
    wincmd p
    let l:curbufnr = bufnr('%')
    let l:curline = line('.')
    
    " Go back to the __JBrowser_List__ and highlight the current tag
    let l:bname = '__JBrowser_List__'
    let l:winnum = bufwinnr(l:bname)
    exe l:winnum . 'wincmd w'
    call s:JavaBrowser_Highlight_Tag(l:curbufnr, l:curline)
endfunction

" JavaBrowser_Update_Window()
" Update the window by regenerating the tag list
function! s:JavaBrowser_Update_Window()
    if !exists('b:jbrowser_bufnum') || !exists('b:jbrowser_ftype')
        return
    endif

    " Save the current line for later restoration
    let curline = '\V\^' . getline('.') . '\$'

    " Clear out the cached taglist information
    call setbufvar(b:jbrowser_bufnum, 'jbrowser_valid_cache', '')

    call s:JavaBrowser_Open_Window()

    call s:JavaBrowser_Init_Window(b:jbrowser_bufnum)

    " Update the taglist window
    call s:JavaBrowser_Explore_File(b:jbrowser_bufnum)

    " Go back to the tag line before the list is sorted
    "call search(curline, 'w')
    
    " Go to the java buffer
    wincmd p
    let l:curbufnr = bufnr('%')
    let l:curline = line('.')
    
    " Go back to the __JBrowser_List__ and highlight the current tag
    let l:bname = '__JBrowser_List__'
    let l:winnum = bufwinnr(l:bname)
    exe l:winnum . 'wincmd w'
    call s:JavaBrowser_Highlight_Tag(l:curbufnr, l:curline)
endfunction

function! s:JavaBrowser_Highlight_Tagline()
    if g:JavaBrowser_Use_Highlight_Tag == 1
        " Clear previously selected name
        match none

        " Highlight the current selected name
        if g:JavaBrowser_Display_Prototype == 0
            exe 'match TagName /\%' . line('.') . 'l\s\+\zs.*/'
        else
            exe 'match TagName /\%' . line('.') . 'l.*/'
        endif
    endif

    " Place the current tag sign if required, clearing the previous
    if g:JavaBrowser_Use_Icon == 1 || g:JavaBrowser_Use_Text_Icon == 1
        exe 'sign unplace 2 buffer=' . bufnr('%')
        exe 'sign place 2 line=' . line('.') . ' name=currTag buffer=' . bufnr('%')
    endif
endfunction

function! s:JavaBrowser_Unhighlight_Prvline()
    " Clear previously selected name
    if g:JavaBrowser_Use_Highlight_Tag == 1
        match none
    endif

    " Clear the previous tag sign
    if g:JavaBrowser_Use_Icon == 1 || g:JavaBrowser_Use_Text_Icon == 1
        exe 'sign unplace 2 buffer=' . bufnr('%')
    endif
endfunction

" JavaBrowser_Jump_To_Tag()
" Jump to the location of the current tag
function! s:JavaBrowser_Jump_To_Tag(new_window)
    " Do not process comment lines and empty lines
    let curline = getline('.')
    if curline == '' || curline[0] == '"'
        return
    endif
    let l:lineno = line('.')
    let l:lineno = l:lineno - 1

    let s:JavaBrowser_Skip_Refresh = 1

    " Highlight the tagline
    call s:JavaBrowser_Highlight_Tagline()

    " If inside a fold, then don't try to jump to the tag
    if foldclosed('.') != -1
        return
    endif
    if has_key(b:jbrowser_to_buffer_lno_dict, l:lineno)
        let l:bufflineno = b:jbrowser_to_buffer_lno_dict[l:lineno]
        
        let winnum = bufwinnr(b:jbrowser_bufnum)
        exe winnum . 'wincmd w'
        exe 'normal ' . l:bufflineno . 'G'
        " Bring the line to the middle of the window
        normal! z.

        " If the line is inside a fold, open the fold
        if has('folding')
            if foldlevel('.') != 0
                normal zo
            endif
        endif
    endif

    " Highlight the tagline
    call s:JavaBrowser_Highlight_Tagline()

    let s:JavaBrowser_Skip_Refresh = 0
endfunction

" JavaBrowser_Show_Tag_Prototype()
" Display the prototype of the tag under the cursor
function! s:JavaBrowser_Show_Tag_Prototype()
    " If we have already display prototype in the tag window, no need to
    " display it in the status line
    if g:JavaBrowser_Display_Prototype == 1
        return
    endif

    " Clear the previously displayed line
    echo

    " Do not process comment lines and empty lines
    let curline = getline('.')
    if curline == '' || curline[0] == '"'
        return
    endif

    " If inside a fold, then don't display the prototype
    if foldclosed('.') != -1
        return
    endif

    let l:lineno = line('.')
    let l:lineno = l:lineno - 1
    if has_key(b:protos_dict, l:lineno)
        let l:proto = b:protos_dict[l:lineno]
        if l:proto != ''
            echo l:proto
        endif
    endif
endfunction

" JavaBrowser_Highlight_Tag
" Highlight tag from Javabrowser Buffer given the source line number and
" source buffer number
function! s:JavaBrowser_Highlight_Tag(buf_no, linenum)
    " Set the syntx highlighting
    call s:JavaBrowser_Set_Syntax_Highlighting()
    
    " Check if the line mapping between this buffer and Java Browser window
    " exists
    let l:buffer_to_jbrowser_lno_dict = getbufvar(a:buf_no, 'buffer_to_jbrowser_lno_dict')
    if empty(l:buffer_to_jbrowser_lno_dict)
        return
    endif

    " JavaBrowser window name
    let l:bname = '__JBrowser_List__'

    " Check if the JavaBrowser window is open
    let l:winnum = bufwinnr(l:bname)
    if l:winnum == -1
        return
    endif
    " Jump to the JavaBrowser window
    exe l:winnum . 'wincmd w'
   
    " Check if we have the current tag line no
    if !exists('b:buf_tag_line_no')
        let b:buf_tag_line_no = -2
    endif
    
    let l:buf_lineno = -1
    let l:prv_line_no = -1
    " Go through the line numbers in order
    for l:dict_line_no in sort(keys(l:buffer_to_jbrowser_lno_dict), 'JavaBrowser_IntCompare')
        if l:dict_line_no == a:linenum
            let l:buf_lineno = l:dict_line_no
            break
        endif
        if l:dict_line_no > a:linenum
            let l:buf_lineno = l:prv_line_no
            break
        endif
        let l:prv_line_no = l:dict_line_no
    endfor

    " Check if could find a matching line number or not
    if l:buf_lineno == -1
        if l:prv_line_no != -1
            let l:buf_lineno = l:prv_line_no
        endif
    endif
    if l:buf_lineno != -1 && l:buf_lineno != b:buf_tag_line_no
        if has_key(l:buffer_to_jbrowser_lno_dict, l:buf_lineno)
            let l:jbrowser_lineno = l:buffer_to_jbrowser_lno_dict[l:buf_lineno] + 1
            exe 'normal ' . l:jbrowser_lineno . 'G'
            " Highlight the tagline

            call s:JavaBrowser_Highlight_Tagline()

            " Store the line number of the current tag
            let b:buf_tag_line_no = l:buf_lineno
        endif
    endif
    let l:winnum = bufwinnr(a:buf_no)
    if l:winnum != -1
        " Jump to the Java source window
        exe l:winnum . 'wincmd w'
    endif
endfunction
    
" JavaBrowser_Clear_Buf_To_JBrowser_Map
" Clear previous java buffer to JBrowser line map
function! s:JavaBrowser_Clear_Buf_To_JBrowser_Map()
    " JavaBrowser window name
    let l:bname = '__JBrowser_List__'

    " Check if the JavaBrowser window is open
    let l:winnum = bufwinnr(l:bname)
    if l:winnum == -1
        return
    endif
    " Jump to the JavaBrowser window
    exe l:winnum . 'wincmd w'
   
    if !exists('b:buf_to_jbrowser_line_nos')
        return
    endif
    let l:all_line_nos = b:buf_to_jbrowser_line_nos
    while l:all_line_nos != ''
        " TODO: CHANGE ******
        "let l:line_no = strpart(l:all_line_nos, 0, stridx(l:all_line_nos, "\n"))
        let l:line_no = strpart(l:all_line_nos, 0, stridx(l:all_line_nos, "#"))
        " Remove the line
        " TODO: CHANGE ******
        "let l:all_line_nos = strpart(l:all_line_nos, stridx(l:all_line_nos, "\n") + 1)
        let l:all_line_nos = strpart(l:all_line_nos, stridx(l:all_line_nos, "#") + 1)
        let l:varname = 'b:buf_to_jbrowser_line_no_' . l:line_no
        if exists(l:varname)
            unlet! b:buf_to_jbrowser_line_no_{l:line_no}
        endif
    endwhile
endfunction

" Define tag listing autocommand to automatically open the taglist window on
" Vim startup
if g:JavaBrowser_Auto_Open
    autocmd VimEnter * nested JavaBrowser
endif

function! JavaBrowser_Show_Prototype()
    " Make sure that mouse in Javabrowser window name
    let l:bname = '__JBrowser_List__'
    let l:bufnum = bufnr(l:bname)
    if l:bufnum != v:beval_bufnr
        return ''
    endif
    
    " If we have already displayed prototype in the tag window, no need to
    " display it in the popup
    if g:JavaBrowser_Display_Prototype == 1
        return ''
    endif

    " Do not process comment lines and empty lines
    if v:beval_text == '' || v:beval_text[0] == '"'
        return ''
    endif

    " If inside a fold, then don't display the prototype
    if foldclosed(v:beval_lnum) != -1
        return ''
    endif

    let l:lineno = v:beval_lnum - 1
    let l:protos_dict = getbufvar(l:bufnum, 'jbrowser_protos_dict')
    let l:proto = ''
    if has_key(l:protos_dict, l:lineno)
        let l:proto = l:protos_dict[l:lineno]
    endif
    return l:proto
endfunction

func JavaBrowser_IntCompare(i1, i2)
    let l:i1 = str2nr(a:i1)
    let l:i2 = str2nr(a:i2)
    return l:i1 == l:i2 ? 0 : l:i1 > l:i2 ? 1 : -1
endfunc

" Define the 'JavaBrowser' and user commands to open/close taglist
" window
command! -nargs=0 JavaBrowser call s:JavaBrowser_Toggle_Window(bufnr('%'))
