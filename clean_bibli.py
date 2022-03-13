from pybtex.database.input import bibtex
from termcolor import colored
from dblp.dblp_api import search_publication, get_bibtex
from difflib import SequenceMatcher
import requests
import re


FILENAME = 'bibliography.bib'


parser = bibtex.Parser()
new_entries = bibtex.Parser()
bib_data = parser.parse_file(FILENAME)


USELESS_FIELDS = ['howpublished', 'month', 'pages', 'volume', 'publisher',
                  'organization', 'number', 'url', 'timestamp', 'eprinttype',
                  'eprint', 'biburl', 'bibsource', 'isbn', 'abstract', 'address',
                  'editor', 'archivePrefix', 'series', 'doi']


def similarity(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()


def handrepair_booktitle(fields):
    booktitle = fields["booktitle"]
    parts = booktitle.split(", ")
    if len(parts) > 2:
        string1 = parts[1]
        try:
            date = int(re.search(r'\d+', string1).group())
        except AttributeError:
            date = 1
        if len(str(date)) == 4 and date > 1900 and date < 2030:
            conf = string1
            for to_rm in [str(date), "{", "}", " "]:
                conf = conf.replace(to_rm, "")
            new_booktitle = parts[0] + f" ({conf})"
            txt = f'Updating booktitle for {title}:\n\t{booktitle}\n' + \
                  f' -> {new_booktitle} (hand-made)'
            print(colored(txt, 'green'))
            fields.update({"booktitle": new_booktitle})
            return True
        else:
            print(colored(f"Couldn't update {booktitle}.", "red"))
            return False


def repair_booktitle(fields):
    doi = None
    title = fields['title']
    if "doi" in fields.keys():
        doi = fields['doi'].replace("\\", '')
    else:
        # extract id
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        response = requests.get(url=url, params={"query": title})
        if response.ok:
            json_parsed = response.json()
            if json_parsed['total'] > 0:
                for paper in json_parsed["data"]:
                    if similarity(title, paper["title"]) > 0.8:
                        doi = paper["paperId"]
                        break
    if doi:
        url = f"https://api.semanticscholar.org/v1/paper/{doi}"
        response = requests.get(url=url)
        data = response.json()
        new_booktitle = data["venue"]
        booktitle = fields["booktitle"]
        if similarity(booktitle, new_booktitle) > 0.3:
            txt = f'Updating booktitle for {title}:\n\t{booktitle}\n' + \
                  f' -> {new_booktitle} (from SemanticScholar database)'
            print(colored(txt, 'green'))
            fields.update({"booktitle": new_booktitle})
            return True
        else:
            return handrepair_booktitle(fields)


def change_key(bibtex_string, key):
    to_replace = "DBLP:" + bibtex_string.split(',\n')[0].split("DBLP:")[-1]
    return bibtex_string.replace(to_replace, key)


def process_title(title):
    for lat_char in ['$', '\\']:
        if lat_char in title:
            title = (" ").join([wd for wd in title.split() if lat_char not in wd])
    return title


def process_first_author(author_str):
    last_name, first_name = author_str.split(', ')
    if len(first_name) == 3 and first_name[1] == "-":
        first_name = ''
    if "{" in first_name:
        first_name = first_name[:first_name.find("{")]
    if "{" in last_name:
        last_name = last_name[:last_name.find("{")]
    return ' '.join([first_name, last_name])


total = 0
success = 0

for key in bib_data.entries:
    entry = bib_data.entries[key]
    title = process_title(entry.fields['title'])
    first_author = process_first_author(str(entry.persons['author'][0]))
    results = search_publication(f"{title} {first_author}").results
    publi = None
    for result in results:
        new_title = result.publication.title
        if similarity(title.lower(), new_title.lower()) > 0.8:
            if "corr" not in result.publication.venue.lower():
                print(colored(f"Found {new_title}", "green"))
                publi = result
                break # Breaking if no arxiv
            else:  # no break if arxiv
                publi = result
    if publi:
        bibtex_result = get_bibtex(publi.publication.key)
        bibtex_result = change_key(bibtex_result, key)
        new_entries.parse_string(bibtex_result)
        success += 1
    else:
        print(colored(f"Could not find {title} from {first_author} on dblp", "yellow"))
        for res in results:
            print(colored(f"Found {res.publication.title}", "yellow"))
        new_entries.data.add_entry(key, entry)
    total += 1

print("\n" + "-" * 50 + "\n")
print("NOW REPAIRING BOOKTITLES:\n")

nb_booktitles = 0
repaired_booktitles = 0
for key in new_entries.data.entries:
    entry = new_entries.data.entries[key]
    if "booktitle" in entry.fields:
        repaired_booktitles += int(repair_booktitle(entry.fields))
        nb_booktitles += 1
    for rem in USELESS_FIELDS:
        if rem in entry.fields:
            value = entry.fields.pop(rem)

print(colored(f"\n\nSuccessfully updated {success}/{total} entries", "green"))
print(colored(f"\n\nSuccessfully updated {success}/{total} entries", "green"))


new_entries.data.to_file(f"clean_{FILENAME}", "bibtex")
print(colored(f"\nSuccessfully saved the bibliography to clean_{FILENAME}", "green"))
