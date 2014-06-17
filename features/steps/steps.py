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

@then('"{tab}" is the current tab')
@given('"{tab}" is the current tab')
def tab_is_current(context, tab):
    assert context.dagui_root.child(tab).isSelected

@then('"{fullname}" assistant should be listed')
def assistant_is_displayed(context, fullname):
    assert context.dagui_root.child(fullname)
    # TODO: how to text that the icon is there?
