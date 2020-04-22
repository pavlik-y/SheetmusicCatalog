import re
import collections
import csv
import io

Entry = collections.namedtuple('Entry',
    'original_line, l, id, composer, title, publisher, comment, oclc, classification')
def NewEntry(l):
  return Entry(original_line=l, l=l, id=None, composer=None,
      title=None, publisher=None, comment=None,
      oclc=None, classification=None)

def extract_id(r):
  m = re.match(r'^\s*(\d+)\.\s*(.*)$', r.l)
  return r._replace(id=int(m.group(1)), l=m.group(2))

def fix_OCLC(r):
  if r.l.find('OCLC ') == -1:
    i = r.l.rfind('.') + 1
    r = r._replace(l=r.l[:i] + ' OCLC .' + r.l[i:])
  return r

def extract_OCLC_and_classification(r):
  try:
    m = re.match(r'(.*)OCLC (\d*)\s*\.?\s*(.*)$', r.l)
    return r._replace(l=m.group(1), oclc=m.group(2), classification=m.group(3))
  except:
    print(r.l)
    raise

def get_composer_index(composers, l):
  best_match = ''
  index = -1
  for (i, c) in enumerate(composers):
    if l.startswith(c) and len(c) > len(best_match):
      best_match = c
      index = i
  return index

def extract_composer(composers, r):
  i = get_composer_index(composers, r.l)
  assert i >= 0
  composer = composers[i]
  l = r.l[len(composer):].strip()
  return r._replace(l=l, composer=composer)

def get_publisher(publishers, l):
  best_match = ''
  for (i, p) in enumerate(publishers):
    if l.find(p) != -1 and len(p) > len(best_match):
      best_match = p
  return best_match

def fix_publisher(publisher):
  m = re.match(r'^\S*\s*(.*)$', publisher)
  return m.group(1)

def extract_title_publisher_comment(publishers, r):
  p = get_publisher(publishers, r.l)
  i = r.l.index(p)
  title = r.l[:i]
  comment = r.l[i+len(p):]
  p = fix_publisher(p)
  return r._replace(title=title, publisher=p, comment=comment, l=None)

def copy_into_title(r):
  return r._replace(title=r.l, publisher='', comment='', l=None)

def main():
  with open("original_list.txt") as f:
    lines = f.read().decode('utf-8-sig').splitlines(False)
  lines = filter(lambda l: re.match(r'\s*\d+\.\s', l), lines)
  with open("composers.txt") as f:
    composers = f.read().decode('utf-8').splitlines(False)
  composers = filter(lambda l: len(l) > 0, composers)

  with open("publishers.txt") as f:
    publishers = f.read().decode('utf-8').splitlines(False)
  publishers = filter(lambda l: len(l) > 0, publishers)

  records = map(lambda x: NewEntry(x), lines)
  records = map(extract_id, records)
  records = map(fix_OCLC, records)
  records = map(extract_OCLC_and_classification, records)

  without_composer = filter(lambda r: get_composer_index(composers, r.l) == -1, records)
  assert len(without_composer) == 0
  records = map(lambda r: extract_composer(composers, r), records)

  with_publisher = filter(
      lambda r: get_publisher(publishers, r.l) != '',
      records)
  without_publisher = filter(
      lambda r: get_publisher(publishers, r.l) == '',
      records)

  records = map(
      lambda r: extract_title_publisher_comment(publishers, r),
      with_publisher)
  processed = map(copy_into_title, without_publisher)
  records.extend(processed)

  with io.open('unknown_publishers.txt', mode='w', encoding='utf-8') as f:
    f.write(u'\n'.join(map(lambda r:r.l, without_publisher)))
  print(len(without_publisher))

  with open('data.csv', mode='w') as f:
    wr = csv.writer(f)
    wr.writerow([u'id', u'Composer', u'Title', u'Publisher', u'Comment', u'OCLC', u'Classification'])
    for r in records:
      wr.writerow([
        r.id,
        r.composer.encode('utf-8'),
        r.title.encode('utf-8'),
        r.publisher.encode('utf-8'),
        r.comment.encode('utf-8'),
        r.oclc.encode('utf-8'),
        r.classification.encode('utf-8')
      ])

if __name__ == "__main__":
  main()