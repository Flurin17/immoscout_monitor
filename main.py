from dataclasses import dataclass, asdict
from email.mime import image

import requests
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
import logging
import pymongo


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
        embed = DiscordEmbed(title='Found new appartment', description=f'Found propertie in {propertie["location"]}', color='03b2f8')
        embed.set_author(name=f'Immoscout monitor')

        # set thumbnail
        embed.set_thumbnail(url=propertie["image"])

        # set timestamp (default is now)
        embed.set_timestamp()
        i = propertie
        # add fields to embed
        embed.add_embed_field(name='Price', value=i["price"])
        embed.add_embed_field(name='Rooms', value=i["rooms"])
        embed.add_embed_field(name='City', value=i["location"])
        embed.add_embed_field(name='Surface', value=i["squaremeter"])
        embed.add_embed_field(name='Url', value=f'[{i["url"]}]({i["url"]})')

        # add embed object to webhook
        webhook.add_embed(embed)

        response = webhook.execute()
    
    def get_page(self):
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

        try:
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

                except Exception as e:
                    logging.error(f"Failed to capture propertie. Error : {e}")
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
                logging.info("Send webhook")
                db.insert_one(propertie)
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
