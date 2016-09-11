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
            metadata_rows = listing.find('tbody').find_all(
                has_two_tds, recursive=False
            )
            for row in metadata_rows:
                for td in row.find_all('td', recursive=False):
                    print(repr(clean_data(td)))
