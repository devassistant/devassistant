#!/usr/bin/python

TEMPLATE = 'template.txt'

def generate_man(template, binary, args):
    with open(template, 'r') as temp:
        text = temp.read()
    with open('{binary}.1'.format(binary=binary), 'w') as output:
        output.write(text.format(binary=binary, **args))

if __name__ == '__main__':

    values = [('da',           {'desc':    '',
                                'seealso': ''}),
              ('devassistant', {'desc':    'Please note that the \\fBda\\fP command is the recommended way of running DevAssistant (even though it works exactly the same).\n\n',
                                'seealso': '.BR da (1)\n'})]
    for (binary, args) in values:
        generate_man(TEMPLATE, binary, args)
