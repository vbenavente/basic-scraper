import requests
import io
from bs4 import BeautifulSoup
import sys
import re

DOMAIN = 'http://info.kingcounty.gov'
SEARCH_RESULTS = '/health/ehs/foodsafety/inspections/Results.aspx'
QUERY_PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '',
    'Inspection_Type': 'All',
    'Inspection_Start': '',
    'Inspection_End': '',
    'Inspection_Closed_Business': 'A',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'H'
}


def get_inspection_page(**kwargs):
    """Get request to King County server for health inspection info."""
    payload = QUERY_PARAMS.copy()
    if kwargs is not None:
        for k, v in kwargs.items():
            if k in QUERY_PARAMS:
                payload[k] = v

    url = DOMAIN + SEARCH_RESULTS
    inspection_info = requests.get(url, params=payload)
    inspection_info.raise_for_status()
    return inspection_info.content, inspection_info.encoding


def load_inspection_page(file_path):
    """Read static html file from disk and return content and encoding."""
    files = io.open(file_path, 'rb')
    response = files.read()
    files.close()
    encoding = 'utf-8'
    return response, encoding


def parse_source(html, encoding='utf-8'):
    """Parse response body using BeautifulSoup and return parsed object."""
    parsed = BeautifulSoup(html, 'html5lib', from_encoding=encoding)
    return parsed


def extract_data_listings(html):
    """Finds container nodes for restaurant listings."""
    id_finder = re.compile(r'PR[\d]+~')
    return html.find_all('div', id=id_finder)


def has_two_tds(elem):
    """Returns True if element passes filter and False if not."""
    is_tr = elem.name == 'tr'
    td_children = elem.find_all('td', recursive=False)
    has_two = len(td_children) == 2
    return is_tr and has_two


def clean_data(td):
    """Returns tag.string with extra characters stripped."""
    data = td.string
    try:
        return data.strip("\n:-")
    except AttributeError:
        return u""


def extract_restraunt_metadata(listing):
    """Return dictionary containing extracted metadata from single listing."""
    metadata_rows = listing.find('tbody').find_all(
        has_two_tds, recursive=False
    )
    restaurant_metadata = {}
    current_label = ''
    for row in metadata_rows:
        key_cell, val_cell = row.find_all('td', recursive=False)
        new_label = clean_data(key_cell)
        current_label = new_label if new_label else current_label
        restaurant_metadata.setdefault(current_label, []).append(clean_data(val_cell))
    return restaurant_metadata


def is_inspection_row(elem):
    """Returns True if the element is a <tr>,
    Each row conatians exactly four table cells or <td> elements,
    Each row has text in first cell with the word 'inspection',
    'inspection' is not the first word."""
    is_tr = elem.name == 'tr'
    if not is_tr:
        return False
    td_children = elem.find_all('td', recursive=False)
    has_four = len(td_children) == 4
    this_text = clean_data(td_children[0]).lower()
    contains_word = 'inspection' in this_text
    does_not_start = not this_text.startswith('inspection')
    return is_tr and has_four and contains_word and does_not_start


def extract_score_data(elem):
    """Return average inspection score, high score and total inspections."""
    inspection_rows = elem.find_all(is_inspection_row)
    samples = len(inspection_rows)
    total = high_score = average = 0
    for row in inspection_rows:
        strval = clean_data(row.find_all('td')[2])
        try:
            intval = int(strval)
        except (ValueError, TypeError):
            samples -= 1
        else:
            total += intval
            high_score = intval if intval > high_score else high_score
        if samples:
            average = total/float(samples)
        data = {
            u'Average Score': average,
            u'High Score': high_score,
            u'Total Inspections': samples
        }
        return data


if __name__ == '__main__':
    kwargs = {
        'Inspection_Start': '4/11/2015',
        'Inspection_End': '4/18/2015',
        'Zip_Code': '98121',
    }
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        html, encoding = load_inspection_page('inspection_page.html')
    else:
        html, encoding = get_inspection_page(**kwargs)
        doc = parse_source(html, encoding)
        listings = extract_data_listings(doc)
        for listing in listings[:5]:
            metadata = extract_restraunt_metadata(listing)
            score_data = extract_score_data(listing)
            print(score_data)
