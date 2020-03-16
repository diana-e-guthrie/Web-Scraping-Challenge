
import os
from bs4 import BeautifulSoup as bs
import requests
from splinter import Browser
import pandas as pd
from flask import Flask, render_template, redirect
import pymongo

conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)

db = client.Mars
collection = db.scrape_mars

app = Flask(__name__)

def init_browser():
    executable_path = {'executable_path': '../chromedriver.exe'}
    browser = Browser('chrome', **executable_path, headless=False)

    return browser

def get_news(browser):
    news_url = 'https://mars.nasa.gov/news/?page=0&per_page=40&order=publish_date+desc%2Ccreated_at+desc&search=&category=19%2C165%2C184%2C204&blank_scope=Latest'
    browser.visit(news_url)
    html = browser.html
    soup = bs(html, 'html.parser')
    ul = soup.find('ul', class_='item_list')
    li = ul.find('li', class_='slide')
    news_title = li.find('div', class_='content_title').text
    news_p = li.find('div', class_='article_teaser_body').text
    return {'news_title': news_title, 'news_p': news_p}

def get_image(browser):

    image_url = 'https://www.jpl.nasa.gov/spaceimages/details.php?id=PIA18322'
    browser.visit(image_url)
    html = browser.html
    soup = bs(html, 'html.parser')
    image_url = soup.select_one('figure.lede a img').get('src')
    featured_image_url = (f'https://www.jpl.nasa.gov{image_url}')

    return featured_image_url

def get_weather(browser):

    weather_url = 'https://twitter.com/marswxreport?lang=en'
    browser.visit(weather_url)
    html = browser.html
    soup = bs(html, 'html.parser')
    results = soup.find('div', class_='css-1dbjc4n')
    tweet = results.find('span').get_text()

    return tweet

def get_facts(browser):
    facts_url = 'https://space-facts.com/mars/'
    browser.visit(facts_url)
    html = browser.html
    soup = bs(html, 'html.parser')
    results = soup.find('table', class_='tablepress tablepress-id-p-mars')
    mars_facts = str(results)
    return mars_facts

def get_hemispheres(browser):
    hemis = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'
    browser.visit(hemis)
    hemisphere_urls = []
    links = browser.find_by_css('a.product-item h3')
    for i in range(len(links)):
        hemisphere = {}
        browser.find_by_css('a.product-item h3')[i].click()
        sample_elem = browser.find_link_by_text('Sample').first
        hemisphere['img_url'] = sample_elem['href']
        hemisphere['title'] = browser.find_by_css('h2.title').text
        hemisphere_urls.append(hemisphere)
        browser.back()

    return hemisphere_urls
    
@app.route("/")
def index():
    mars = collection.find_one()
    return render_template("index.html", mars=mars)
    
@app.route("/scrape")
def scrape():
    browser = init_browser()
    mars_dict = {
        'news': get_news(browser),
        'image': get_image(browser),
        'weather': get_weather(browser),
        'facts': get_facts(browser),
        'hemispheres': get_hemispheres(browser)
    }
    collection.update({}, mars_dict, upsert=True)
    
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
