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
    context.dagui_root.child(fullname).point()
    context.dagui_root.child(fullname).click()

@when('user fills "{path}" in "Project name"')
def fill_project_name(context, path):
    # ok, so... I can't seem to find a way to assign a name to the text entry
    #  in glade file, so I guess I just have to do this... ugly, right?
    pn = context.dagui_root.children[0].children[0].children[1].children[0].children[1].children[0]
    pn.typeText(path)

@then('"{tab}" is the current tab')
@given('"{tab}" is the current tab')
def tab_is_current(context, tab):
    assert context.dagui_root.child(tab).isSelected

@then('"{fullname}" assistant should be listed')
def assistant_is_displayed(context, fullname):
    assert context.dagui_root.child(fullname)
    # TODO: how to text that the icon is there?
