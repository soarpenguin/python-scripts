def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    quot, rem = divmod(col-1, 26)
    return((chr(quot-1 + ord('A')) if quot else '') +
           (chr(rem + ord('A')) + str(row)))

if __name__ == '__main__':
    addresses = [(1,   1), (1,  26),
                 (1,  27), (1,  52),
                 (1,  53), (1,  78),
                 (1,  79), (1, 104)]

    print '(row, col) --> Excel'
    print '---------------------'
    for row, col in addresses:
        print '({:3d}, {:3d}) --> {!r}'.format(row, col, excel_style(row, col))
