#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re
import sublime
import sublime_plugin


# System path separation characters
PATH_SEPS = r'[\\¥/]'

# Valid characters found in a filename
VALID_PATH_CHAR = r'[^<>:"/|?*\\¥/]'


def open_file(path, row=1, col=1):
    '''
    Opens a file at the given row & column
    '''
    path += ':{row}:{col}'.format(row=row, col=col)

    sublime.active_window().open_file(path, sublime.ENCODED_POSITION)


class OpenFindFileAtPosCommand(sublime_plugin.TextCommand):
    # Finds a valid line found in a file
    LINE_RE = re.compile((
        r'^'
        # The line has chars that don't come from the file
        # You need to use these to find out the actual cursor position
        r'(?P<prefix>'

            r' *'
            r'(?P<line_num>[0-9]+)'

            # Lines which have text that was found have a colon
            # otherwise there is a space for formatting
            r'([: ])'
            # Extra space for alignment
            r' '

        r')'

        # Actual file line
        r'.*$'
    ), re.DOTALL)

    # Finds a valid path-line shown in a sublime search
    FILE_RE = re.compile((
        r'^'

        # The path starts here
        r'(?P<path>'

            # Start with the drive letter
            r'(?P<drive>[a-zA-Z]:)?'

            # Each directory
            r'('
                r'{PATH_SEPS}'
                r'{VALID_PATH_CHAR}+'
            r')+'

            # Trailing Slash
            r'{PATH_SEPS}?'

        r')'

        # File search puts a colon at the end
        r':$'
    ).format(**{
        'PATH_SEPS': PATH_SEPS,
        'VALID_PATH_CHAR': VALID_PATH_CHAR,
    }), re.DOTALL)

    def is_enabled(self):
        if self.view.settings().get('syntax') != 'Packages/Default/Find Results.hidden-tmLanguage':
            return False

        cursor = self.get_cursor()
        path = self.find_cur_file(cursor)
        return path is not None

    def get_cursor(self):
        '''
        Returns the first selected region
        '''
        selected = self.view.sel()

        # No idea what to open if nothing is selected
        if len(selected) == 0:
            return
        cursor = selected[0]

        return cursor


    def run(self, edit=None):
        cursor = self.get_cursor()

        # Otherwise we load the topmost selection
        line = self.view.substr(self.view.line(cursor))

        # Classify the line: Text line
        # This is a valid line of text, open the file its in at the correct position
        match = OpenFindFileAtPosCommand.LINE_RE.match(line)
        if match is not None:
            return self.open_line(match, cursor)

        # Classify the line: Filepath
        # This is the file identifier line, just open the file normally
        match = OpenFindFileAtPosCommand.FILE_RE.match(line)
        if match is not None:
            path = match.group('path')
            return open_file(path)

        # No classification? just open the nearest file
        path = self.find_cur_file(cursor)
        if path is not None:
            return open_file(path)

    def open_line(self, match, cursor):
        '''
        Opens the search at the exact line the cursor is on
        '''

        # First we need to find the cursor
        cur_row = match.group('line_num')
        _, cur_col = self.view.rowcol(cursor.begin())

        # The line that is show has a prefix added by sublime
        # Thus the actual file will need to be opened at an earlier point
        # Also: off by one as sublime likes 1 based positions
        cur_col -= len(match.group('prefix')) - 1

        # Now find what file this is
        path = self.find_cur_file(cursor)
        if path is None:
            raise RuntimeError('Could not find path above a line with a linenumber')

        open_file(path, row=cur_row, col=cur_col)

    def find_cur_file(self, cursor):
        '''
        Locate the file this search line was found in
        '''
        cur_row, cur_col = self.view.rowcol(cursor.begin())

        for row in range(cur_row, 0, -1):
            # convert the row to a valid sublime view point
            point = self.view.text_point(row, 0)

            # Now use the point to find the line data
            line = self.view.substr(self.view.line(point))

            # Now see if we have a valid filepath
            match = OpenFindFileAtPosCommand.FILE_RE.match(line)
            if match is not None:
                path = match.group('path')
                return path
