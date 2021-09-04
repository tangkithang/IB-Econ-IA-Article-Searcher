from __future__ import print_function, unicode_literals
from pattern.en import sentiment
from GoogleNews import GoogleNews
import pandas as pd
from summa import summarizer
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm 
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def getTextFromURL(url):
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    text = ' '.join(map(lambda p: p.text, soup.find_all('p')))
    return text.replace(u"Â", u"").replace(u"â", u"")

def wordCount(url_text):
    noOfWords = len(url_text.split())
    return noOfWords

def getTitles(searchString, timePeriod, countryAcronym, pageNo):
    print("Searching for Articles...")
    gn = GoogleNews(lang='en', region= countryAcronym, period = timePeriod)
    stories = []
    gn.search(searchString)
    gn.clear()
    gn.getpage(pageNo)
    search = gn.result()
    for i in tqdm (range(len(search))):
        for item in search:
            story = {
                'title': item['title'],
                'link': item['link']
            }
            stories.append(story)
    return stories

def checkKeyword (searchString, keyword_extracted):
    for word in searchString.split():
        if any (str(word) in keyword for keyword in keyword_extracted):
            return True 
    else: 
        return False 

def deleteArticle(indvItem):
    print("Deleting unwanted articles...")
    for i in tqdm (range(len(indvItem))):
        for article in indvItem: 
            url = article['link']
            url_text = getTextFromURL(article['link'])
            sentimentanalysis = sentiment(url_text)
            if (-0.2 <= sentimentanalysis[0] <= 0.2 and 0.3 <= sentimentanalysis[1] <= 0.7) \
            and (700 <= wordCount(url_text) <= 1000): 
                pass
            else: 
                indvItem[:] = [item for item in indvItem if item.get('link')!= url]
    print("remaining articles: " + str(len(indvItem)))
    return indvItem
    
def articleSummary(indvItem):
    allSummary = []
    print("summarizing articles...")
    for i in tqdm (range(len(indvItem))):
        for article in indvItem: 
            url_text = getTextFromURL(article['link'])
            allSummary.append(summarizer.summarize(url_text, words=200))
    return allSummary


presetSearch = {
    '1 country': 'HK',
    '2 time period (months)': '12m',
    '3 polarity range': [-0.1, 0.1],
    '4 subjectivity range': [0.45,0.55],
    '5 upper word limit' : 900,
    '6 lower word limit' : 700
}

print("preset search parameters:\n")
for attribute, value in presetSearch.items():
    print('{}: {}'.format(attribute, value))

searchString = input('\ntype your search string here:  ')
noOfArticles = int(input('\nno.of output articles (each article takes 15s, on average):  '))

nextNoOfArticles = 5
lastNoOfArticles = 0 
allSummary = []
indvItem = [] 
pageNo = 1 

stories = getTitles(searchString, \
        presetSearch['2 time period (months)'], presetSearch['1 country'], pageNo)

while len(indvItem) <= noOfArticles :  
    if lastNoOfArticles <= len(stories): 
        newIndvItem = deleteArticle(stories[lastNoOfArticles:nextNoOfArticles])

        indvItem = indvItem + newIndvItem
        df=pd.DataFrame(indvItem)

        newSummaries = articleSummary(newIndvItem)
        allSummary = allSummary + newSummaries
        df['summary'] = pd.Series(allSummary, dtype='string')
        df.to_excel("C:/Users//Desktop/master_econ.xlsx")
        print("one saving cycle complete, " + str(noOfArticles-len(indvItem)) + " articles remaining.")
        lastNoOfArticles = nextNoOfArticles
        nextNoOfArticles+=5 
    else: 
        pageNo +=1 
        lastNoOfArticles = 0
        nextNoOfArticles = 5
        stories = getTitles(searchString, \
        presetSearch['2 time period (months)'], presetSearch['1 country'], pageNo)
        print("page number: " + str(pageNo))

print("process complete and saved")
