import re
import os
from subprocess import check_output

DEGREPPER = re.compile(r'^(.*?)[\/\\]?([^\\\/:]+):([\d]+):(.*)$')
LANGUAGES = {
    None: ['', 'txt', 'md'],
    'python': ['py', ],
    'html': ['html', ],
    'css': ['css', 'less', 'sass', ],
    'js': ['js', ],
}

COMMENTS_OPEN_CLOSE = [
    ('<!--', '-->'),  # HTML
    ('{#', '#}'),  # Jinja
    ('/*', '*/'),  # CSS
]


def get_language(ext):
    for lang, exts in LANGUAGES.iteritems():
        if ext and ext[1:] in exts:
            return lang
    return None


def degrep_line(line):
    match = DEGREPPER.match(line)
    if not match:
        return (None,)*4
    path = match.group(1)
    filename = match.group(2)
    line_number = int(match.group(3))
    contents = match.group(4)
    return path, filename, line_number, contents


def clean_description(item_desc):
    item_desc = item_desc.strip()
    for tag in COMMENTS_OPEN_CLOSE:
        if item_desc.endswith(tag[1]):
            item_desc = item_desc[:-len(tag[1])]
            break
    return item_desc.strip()


def get_list(target_folder):
    degrepped = []
    undegreppable = []
    cwd = os.path.abspath(target_folder)
    resp = check_output(['git',  '--no-pager', 'grep', '-EIn', 'TODO|FIXME'],
                        cwd=cwd)
    lines = resp.splitlines()
    for line in lines:
        p, fn, ln, cnt = degrep_line(line)
        fp = os.path.abspath(os.path.join(p, fn))
        if not ln:
            undegreppable.append('line')
            continue
        ext = os.path.splitext(fn)[1]
        language = get_language(ext)
        item_match = re.search('(TODO|FIXME)([\s\-:;\.]+)?(.*?)$', cnt)
        item_type = item_match.group(1) if item_match else ''
        item_desc = clean_description(
            item_match.group(3) if item_match else '')
        degrepped.append(
            (p, fn, fp, ln, cnt.strip(), language, item_type, item_desc))

    return degrepped, undegreppable

if __name__ == "__main__":
    degr, ungr = get_list('./')
    for item in degr:
        print item

