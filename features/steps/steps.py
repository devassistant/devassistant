import getpass
import os

from behave import given, then

from dogtail import tree
from dogtail import utils

def startgui(context):
    context.dagui_pid = utils.run(context.dagui_scriptpath, appName=context.dagui_scriptname)
    context.dagui_root = tree.root.application(context.dagui_scriptname)

@given('da-gui has just started')
@given('da-gui is running')
def just_start_it(context):
    startgui(context)

@when('user clicks "{tab}" tab')
def click_tab(context, tab):
    context.dagui_root.child(tab).click()

@when('user clicks "{fullname}" assistant')
def click_assistant(context, fullname):
    # if I use just click(), it sometimes doesn't actually click. A bug?
    btn = context.dagui_root.child(fullname)
    btn.point()
    btn.click()

@when('user fills "{name}" in "Project name"')
def fill_project_name(context, name):
    # ok, so... I can't seem to find a way to assign a name to the text entry
    #  in glade file, so I guess I just have to do this... ugly, right?
    n = context.dagui_root.children[0].children[0].children[1].children[0].children[1].children[0]
    n.typeText(name)

@when('user fills "{path}" in "Create in"')
def fill_project_path(context, path):
    p = context.dagui_root.children[0].children[0].children[1].children[0].children[1]\
        .children[1].children[0]
    p.typeText(path)

@when('user clicks "Run" button')
def run_assistant(context):
    btn = context.dagui_root.child('Run')
    btn.point()
    btn.click()

@when('assistant run finishes with "{result}"')
def assistant_finished_with_result(context, result):
    context.dagui_root.child(result)

@then('"{tab}" is the current tab')
@given('"{tab}" is the current tab')
def tab_is_current(context, tab):
    assert context.dagui_root.child(tab).isSelected

@then('user should see "{what}"')
def is_to_be_seen(context, what):
    assert context.dagui_root.isChild(_substitute_feature_variables(what))

@then('"{fullname}" assistant should be listed')
def assistant_is_displayed(context, fullname):
    assert context.dagui_root.isChild(fullname)
    # TODO: how to text that the icon is there?

@then('log window should show')
def user_window_contains(context):
    for row in context.table:
        assert _log_window_contains(context, _substitute_feature_variables(row['output']))

def _log_window_contains(context, what):
    lw = context.dagui_root.children[0].children[0].children[0].children[0]
    return lw.isChild(what)

def _substitute_feature_variables(s):
    # if in quotes, remove just the outer ones
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    if '@whoami' in s:
        s = s.replace('@whoami@', getpass.getuser())
    if '@pwd@' in s:
        s = s.replace('@pwd@', os.getcwd())

    return s
