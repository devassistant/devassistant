from __future__ import print_function

import pprint
import sys


class DAPrettyPrinter(pprint.PrettyPrinter):
    def pformat(self, object, indent=1, width=80, depth=None, special=False):
        # we explicitly pass indent=1 because we don't want the dict indented
        lines = pprint.pformat(object, indent=0, width=width, depth=depth).splitlines()
        return '\n'.join(map(lambda l: ' ' * indent + l, lines))

    def pformat_kwargs(self, object, indent=1, width=80, depth=None, special=False):
        res = []
        varname_maxlen = max(map(lambda k: len(k), object.keys()))
        for k, v in sorted(object.items()):
            varname = '{indent}{var}: {space}'.format(indent=' ' * indent,
                                                      var=k,
                                                      space=' ' * (varname_maxlen - len(k)))
            res.append(varname + v.__repr__())
        return '\n'.join(res)


def is_local_subsection(command_dict):
    """Returns True if command dict is "local subsection", meaning
    that it is "if", "else" or "for" (not a real call, but calls
    run_section recursively."""
    for local_com in ['if ', 'for ', 'else ']:
        if list(command_dict.keys())[0].startswith(local_com):
            return True
    return False


def excepthook(type, value, traceback):
    print('DevAssistant traceback (most recent call last):')
    curr_tb = traceback
    run_section_frames = []
    record_frames_in = ['eval_exec_section', 'eval_literal_section']
    while curr_tb:
        if 'lang.py' in curr_tb.tb_frame.f_code.co_filename and \
                curr_tb.tb_frame.f_code.co_name in record_frames_in:
                run_section_frames.append(curr_tb.tb_frame)

        curr_tb = curr_tb.tb_next

    if run_section_frames:
        pp = DAPrettyPrinter()
        for frame in run_section_frames:
            current_command_dict = frame.f_locals['command_dict']
            # skip 'if', 'else' and 'for' commands
            # they call run_section recursively, but are still in the same 'run*' section
            if not is_local_subsection(current_command_dict):
                print('File {0}:'.format(frame.f_locals['kwargs']['__sourcefiles__'][-1]))
                print(pp.pformat(current_command_dict, indent=2))

        print('Variables in last frame:')
        print(pp.pformat_kwargs(frame.f_locals['kwargs'], indent=2))
    else:
        print('Error: No DevAssistant frames to print.')
    print()

    old_excepthook(type, value, traceback)

old_excepthook = sys.excepthook
sys.excepthook = excepthook
