from __future__ import print_function

import pprint
import sys

class DAPrettyPrinter(pprint.PrettyPrinter):
    def pformat(self, object, indent=1, width=80, depth=None, special=False):
        lines = pprint.pformat(object, indent, width, depth).splitlines()
        for i, line in enumerate(lines):
            if special:
                lines[i] = '>>> ' + line
            else:
                lines[i] = '    ' + line
        return '\n'.join(lines)

def excepthook(type, value, traceback):
    curr_tb = traceback
    run_section_frames = []
    while curr_tb:
        if 'yaml_assistant.py' in curr_tb.tb_frame.f_code.co_filename and \
           curr_tb.tb_frame.f_code.co_name == '_run_one_section':
               run_section_frames.append(curr_tb.tb_frame)
            
        curr_tb = curr_tb.tb_next

    if run_section_frames:
        pp = DAPrettyPrinter()
        # keep last file to reference it if we are still in the file, but in
        # different run section/condition
        last_file = run_section_frames[0].f_locals['self'].path
        print('File {0}'.format(last_file))
        print('  In {0} assistant'.format(run_section_frames[0].f_locals['self'].fullname))

        for frame in run_section_frames:
            current_command_dict = frame.f_locals['command_dict']
            print_up_to = frame.f_locals['section'].index(current_command_dict) + 1
            section_upto_command = frame.f_locals['section'][:print_up_to]

            for i, command in enumerate(section_upto_command):
                print(pp.pformat(command, special=(i==len(section_upto_command) - 1)))
            print('\n')
            ccd_short = str(current_command_dict)
            ccd_short = ccd_short[:46] + ' ...' if len(ccd_short) > 50 else ccd_short

            if 'snippet' in frame.f_locals:
                last_file = frame.f_locals['snippet'].path
            print('File {0}:'.format(last_file))
            print('  In {0}:'.format(ccd_short))

    old_excepthook(type, value, traceback)

old_excepthook = sys.excepthook
sys.excepthook = excepthook
