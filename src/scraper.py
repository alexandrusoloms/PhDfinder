import sys
import os
import re
from bs4 import BeautifulSoup

from crawly.scrapers import ConcurrentRequester
from ams_pymail.send_mail import send_mail


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

        send_mail(subject='[{}-{}]: {}'.format(word_searched, institution, course_title), body=body, to_address=my_email)


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
