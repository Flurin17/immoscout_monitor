from dataclasses import dataclass, asdict

import requests
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
import logging
import pymongo
from datetime import datetime


from config import *
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
db = pymongo.MongoClient(mongoDBUrl).monitors.flats

@dataclass
class propertieClass:
    id: int
    location: str
    price: str
    rooms: str
    squaremeter: str
    url: str
    image: str
    latitude: float
    longtitude: float


class Monitor:
    def __init__(self) -> None:
        self.propertiesList = []
        pass
    
    def send_webhook(self, propertie):
        
        webhook = DiscordWebhook(url=discordWebhook, rate_limit_retry=True)
        embed = DiscordEmbed(title=f'Found new appartment in {propertie["location"]}', color='03b2f8')
        embed.set_author(name=f'Immoscout24 monitor')

        # set thumbnail

        # set timestamp (default is now)
        i = propertie
        # add fields to embed
        embed.add_embed_field(name='Price', value=i["price"])
        embed.add_embed_field(name='Rooms', value=i["rooms"])
        embed.add_embed_field(name='City', value=i["location"])
        embed.add_embed_field(name='Surface', value=i["squaremeter"])
        embed.add_embed_field(name='Url', value=f'[{i["url"]}]({i["url"]})')

        embed.set_image(url=propertie["image"])

        embed.set_footer(text=f"Found appartment at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Monitor created by sorry#8866")
        embed.set_timestamp()
        # add embed object to webhook

        webhook.add_embed(embed)

        response = webhook.execute()
    
    def get_page(self):
        while True:
            try:
                r = requests.get(
                    url=immoscoutLink,
                    headers={
                        "Accept": "text/plain, application/json, text/json",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Connection": "keep-alive",
                        "Host": "rest-api.immoscout24.ch",
                        "is24-meta-pagenumber": "1",
                        "Origin": "https://www.immoscout24.ch",
                        "Referer": "https://www.immoscout24.ch/",
                        "sec-ch-ua": '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
                        "X-OriginalUrl": "http%3A%2F%2Fwww.immoscout24.ch%2Fde"
                    }
                )

                if r.status_code == 200:
                    responseJson = r.json()
                    properties = responseJson["properties"]
                    try:
                        for i in properties:
                            id = i["id"]
                            cityName = i["cityName"]
                            normalizedPriceFormatted = i["normalizedPriceFormatted"]
                            numberOfRoomsFormatted = i["numberOfRoomsFormatted"]
                            try:
                                surfaceLivingFormatted = i["surfaceLivingFormatted"]
                            except:
                                surfaceLivingFormatted = "Unknown"
                            propertyUrl = "https://www.immoscout24.ch" + i["propertyUrl"]

                            try:
                                imageData = i["images"][0]
                                imageUrl = imageData["url"].replace('{width}', str(imageData["originalWidth"])).replace('{height}', str(imageData["originalHeight"])).replace('{resizemode}', "1").replace('{quality}', "100000")
                            except Exception as e:

                                imageUrl = "https://jfv-asp.de/wp-content/themes/ryse/assets/images/no-image/No-Image-Found-400x264.png"
                            latitude = i["latitude"]
                            longitude = i["longitude"]

                            propertie = propertieClass(
                                id,
                                cityName,
                                normalizedPriceFormatted,
                                numberOfRoomsFormatted,
                                surfaceLivingFormatted,
                                propertyUrl,
                                imageUrl,
                                latitude,
                                longitude,

                            )
                            self.propertiesList.append(asdict(propertie))
                        break

                    except Exception as e:
                        logging.error(f"Failed to capture propertie. Error : {e}")
                        time.sleep(20)
            except Exception as e:
                logging.error(f"Failed to capture propertie. Error : {e}")
                time.sleep(20)

    def send_message(self, id):
        r = requests.post(
            url=f'https://rest-api.immoscout24.ch/v4/de/properties/{str(id)}/contacts',
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0',
                'Accept': 'text/plain, application/json, text/json',
                'Accept-Language': 'en-GB,en;q=0.5',
                # 'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.immoscout24.ch/',
                # Already added when you pass json=
                # 'Content-Type': 'application/json',
                'X-OriginalClientIp': '212.243.177.218',
                'X-OriginalUrl': 'http%3A%2F%2Fwww.immoscout24.ch%2Fde',
                'Origin': 'https://www.immoscout24.ch',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
            },
            json = {
                'message': 'Guten Tag\nIch möchte einen Besichtigungstermin vereinbaren.\n Bitte kontaktieren Sie mich.',
                'fullName': fullname,
                'email': email,
                'phone': phoneNr,
                'propertyId': int(id),
                'contactFormTypeId': 2,
                'searchGroupId': 1,
                'searchOfferTypeId': 1,
                'searchLocationIds': '4147',
                'searchRadius': '40',
            }
        )

        try:
            if r.status_code == 200:
               logging.info("Sent contact request")
        except:
            logging.error(f"Status code: {r.status_code}")
            

    def check_new_properties(self):
        foundNew = False
        for propertie in self.propertiesList:
            result = db.find_one({'id': propertie["id"]})
            if result != None:
                pass
            else:
                logging.info(f"Found new propertie in {propertie['location']}")
                self.send_webhook(propertie)
                db.insert_one(propertie)
                if sendContactRequest:
                    self.send_message(propertie['id'])
                foundNew = True
        
        if foundNew == False:
            logging.info(f"Found nothing new. Checked {len(self.propertiesList)} properties")

    def start(self):
        while True:
            self.get_page()
            self.check_new_properties()

            self.propertiesList = []
            time.sleep(delay)
Monitor().start()
