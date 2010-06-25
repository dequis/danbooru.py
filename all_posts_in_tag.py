# Creates a link list of all posts in a tag,
# to be downloaded with aria2c -i file.txt

from __future__ import print_function # requires python 2.6
import sys
import danbooru

TAGLIST = '%(character)s - %(artist)s - %(general)s'
TEMPLATE = "%(url)s\n  out=%(rating)s/%(taglist)s - %(id)s.%(ext)s"
RATINGS = {
    'e': 'explicit',
    'q': 'questionable',
    's': 'safe',
}

def main():
    tag = file = None
    start = 0
    if len(sys.argv) >= 2:
        tag = sys.argv[1]
    if len(sys.argv) >= 3:
        start = int(sys.argv[2])
    if len(sys.argv) >= 4:
        file = open(sys.argv[3], "a")
    if tag is None:
        print("Usage:", sys.argv[0], "<tags> [<start page>] [<filename>]", file=sys.stderr)
        print("Example:", sys.argv[0], '"girl_in_a_box cat_ears"', file=sys.stderr)
        print("\t", sys.argv[0], "touhou 0 madness.txt", file=sys.stderr)
        return
    run(tag, file, start)

def run(tag, file, start):
    posts = danbooru.Danbooru().posts_paged(pages=-1, start=start, tags=tag)

    for post in posts:
        t = post.tags_parsed
        vars = {}
        vars['character'] = ' '.join(t.character)
        vars['artist'] = ' '.join(t.artist)
        vars['general'] = ' '.join(t.general)
        vars['taglist'] = TAGLIST % vars
        if len(vars['taglist']) > 195:
            vars['taglist'] = vars['taglist'][:190] + '(...)'
        vars['rating'] = RATINGS[post.rating]
        vars['id'] = post.id
        vars['url'] = post.sample_url
        vars['ext'] = post.sample_url[-3:]

        output = (TEMPLATE % vars).encode("utf-8")
        print(output)
        if file:
            print(output, file=file)

if __name__ == '__main__':
    main()
