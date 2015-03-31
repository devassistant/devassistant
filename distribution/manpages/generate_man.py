#!/usr/bin/python

def generate_man(template, args):
    if 'binary' not in args:
        raise Exception('Binary name must be specified, it is used as file name.')
    with open(template, 'r') as temp:
        text = temp.read()
    with open('{binary}.1'.format(binary=args['binary']), 'w') as output:
        output.write(text.format(**args))

if __name__ == '__main__':

    values = [('da.txt',       {'binary':  'da',
                                'desc':    '',
                                'seealso': ''}),
              ('da.txt',       {'binary':  'devassistant',
                                'desc':    'Please note that the \\fBda\\fP command is the recommended way of running DevAssistant (even though it works exactly the same).\n\n',
                                'seealso': '.BR da (1)\n'}),
              ('da-gui.txt',   {'binary':  'da-gui',
                                'cli-bin': 'da'}),
              ('da-gui.txt',   {'binary':  'devassistant-gui',
                                'cli-bin': 'devassistant'})]

    for (template, args) in values:
        generate_man(template, args)
