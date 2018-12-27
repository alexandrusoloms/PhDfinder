import sys
import os
import re
import json
from bs4 import BeautifulSoup

from crawly.scrapers import ConcurrentRequester
from ams_pymail.send_mail import send_mail


def check_if_entry_exists(potential_entry):
    for f in os.listdir(output_path):
        if 'saved_entries' in f:
            with open(output_path + 'saved_entries.json', 'r') as handle:
                saved_entries = json.load(handle)
                if potential_entry in saved_entries:
                    return True
                else:
                    saved_entries.append(potential_entry)
                    # save it
                    with open(output_path + 'saved_entries.json', 'w') as handle:
                        json.dump(saved_entries, handle)
                    return False

    # save the file for the first time (making sure it is a list)
    with open(output_path + 'saved_entries.json', 'w') as handle:
        potential_entry = [potential_entry]
        json.dump(potential_entry, handle)


def send_info(html_code):
    """
    parse find a phd and email the results

    :param html_code: <str> html of the page scraped
    :return:
    """
    soup = BeautifulSoup(html_code, 'html.parser')
    results_list = [x for x in
                    soup.find('div', attrs={'id': 'SearchResults'}).findAll('div', attrs={'class': 'resultsRow'})
                    if x.find('a', attrs={'class': 'courseLink'}, href=True)]

    for result in results_list:
        course_title = result.find('a', attrs={'class': 'courseLink'}).text.strip()

        course_link = 'https://www.findaphd.com' + result.find('a', attrs={'class': 'courseLink'})['href']
        institution = result.find('a', attrs={'class': 'instLink'}).text.replace('Application Deadline:', '').strip()

        application_time = result.find('div', attrs={'class': 'apply'}).text.strip()
        application_time = ' '.join(re.findall(r'\w+', application_time))

        supervisor = result.find('div', attrs={'class': 'super'}).text.strip()
        supervisor = ' '.join(re.findall(r'\w+', supervisor))

        funding_type = (
            result.find('div', attrs={'class': 'FundingLink'}).find('img')['src'].split('.')[0].split('/')[-1])

        description = result.find('div', attrs={'class': 'descFrag'}).text.strip()

        body = """Application Deadline: {}\n\nFunding Type: {}\n\nSupervisor(s): {}\n\nDescription:{}\n\n\n\nThe
        course link is: {}. The institution is {}.""".format(
            application_time,
            funding_type,
            supervisor,
            description,
            course_link,
            institution)
        body = body.encode('ascii', 'ignore').decode('utf8')
        institution = institution.encode('ascii', 'ignore').decode('utf8')
        course_title = course_title.encode('ascii', 'ignore').decode('utf8')

        potential_entry = '{}-{}'.format(course_title, application_time)
        if not check_if_entry_exists(potential_entry=potential_entry):
            send_mail(subject='[{}-{}]: {}'.format(word_searched, institution, course_title), body=body, to_address=my_email)


output_path = os.path.join(os.path.dirname('__file__'), '..', ) + '/output/'
my_email = os.environ['MyEmail']
word_searched = sys.argv[1:]


if len(word_searched) > 1:
    word_searched = '+'.join(word_searched)
else:
    word_searched = word_searched[0]

find_phd_url = [
    'https://www.findaphd.com/phds/queen-mary-university-of-london/?40wM00&PP=30&Keywords={}'.format(word_searched),
    'https://www.findaphd.com/phds/university-college-london/?40w410&PP=30&Keywords={}'.format(word_searched),
    'https://www.findaphd.com/phds/university-of-bath/?400610&PP=30&Keywords={}'.format(word_searched),
    'https://www.findaphd.com/phds/university-of-nottingham/?40wk10&PP=30&Keywords={}'.format(word_searched),
    'https://www.findaphd.com/phds/king-s-college-london/?400x00&PP=30&Keywords={}'.format(word_searched)
]

response = ConcurrentRequester(list_of_urls=find_phd_url).run()

for (url, html) in response.items():
    try:
        send_info(html_code=html)
    except AttributeError:
        # sometimes universities do not have an entry for the `words_searched`
        # this will be successfully ignored.
        continue
