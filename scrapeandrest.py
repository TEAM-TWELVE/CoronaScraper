from datetime import datetime, timedelta
from threading import Timer
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import json
import time
from flask import Flask, request
from flask_restful import Api, Resource

json_file = "data.json"
x = datetime.today()
y = x.replace(day=x.day, hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
delta_t = y - x

secs = delta_t.total_seconds()


def get_covid_color(imgURL):
    number = imgURL[-5]  # colors: 1:green, 2: yellow, 3:red
    if number == "1":
        return "green"
    elif number == "2":
        return "yellow"
    elif number == "3":
        return "red"
    return "blue"


def clean_country_name(country):
    if country[-1] == "*":
        country = country[:-2]
        return country
    return country


def save_to_json(covid_dict):
    # prepare json file ready for updates
    current_json = open(json_file)
    json_object = json.load(current_json)
    current_json.close()
    # check for color updates
    for dict_country, dict_color in covid_dict.items():
        json_color = json_object.get(dict_country)
        if json_color != dict_color:
            json_object[dict_country] = dict_color
            # log change
            print(dict_country, " .. has changed from ", json_color, " to ", dict_color)
            # close and save json file
            current_json = open(json_file, "w")
            json.dump(json_object, current_json)
    current_json.close()


def web_scrape():
    url = "https://who.maps.arcgis.com/apps/opsdashboard/index.html#/ead3c6475654481ca51c248d52ab9c61"
    # make chrome headless
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.set_headless()
    # fetch html using selenium
    driver = webdriver.Firefox(firefox_options=firefox_options)
    driver.get(url)
    time.sleep(10)
    html = driver.execute_script("return document.documentElement.outerHTML")
    # Use BeautifulSoup for working with html
    soup = BeautifulSoup(html, "html.parser")
    covid_soup = soup.find("div", id="ember44").div.nav.find_all("span", class_="flex-horizontal")
    # covid_dict = {}
    country, color = [], []
    for i in covid_soup:
        _country = i.find("strong").get_text(strip=True)
        _country = clean_country_name(_country)
        country.append(_country)
        imgURL = i.p.find_next("p").find_next("p").find("img").get('src')
        _color = get_covid_color(imgURL)
        color.append(_color)
    # save as json array
    countries = [{"country": _country, "color": _color} for _country, _color in zip(country, color)]
    with open(json_file, 'w') as f:
        json.dump(countries, f)
    # Printing in JSON format
    # print(json.dumps(countries))



t = Timer(secs, web_scrape)
t.start()
web_scrape()

time.sleep(20)

app = Flask(__name__)
api = Api(app)

# data for end point
f = open(json_file, )
thisdict = json.load(f)
f.close()


# Rest endpoint
class coronaStatus(Resource):
    def get(self):
        st = request.args.get('land')
        return {"status": thisdict.get(st)}


api.add_resource(coronaStatus, "/coronastatus")

if __name__ == "__main__":
    # app.run(debug=True)
    app.run()
