import sublime
import sublime_plugin


class JumpToFindResults(sublime_plugin.TextCommand):
    '''
    Surrounds the selections with quotes or brackets (basesd on the character passed in)

    if expand==True then it also expands the selection to a word
    '''

    def run(self, edit, expand=False):
        window = self.view.window()

        # print(self.view.window().find_open_file('Find Results'))
        for view in window.views():
            if view.name() == 'Find Results' and view.file_name() is None:
                break
        else:
            print("Find Results is not open right now")
            return

        window.focus_view(view)
