import re
from datetime import datetime, timedelta
from math import ceil

from bs4 import BeautifulSoup
from sqlalchemy import Column, String, Date, Numeric, Integer

from app.database import Base


class Ad(Base):
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True)
    listing_id = Column(String)
    title = Column(String)
    description = Column(String)
    image = Column(String)
    date = Column(Date)
    location = Column(String)
    bedrooms = Column(String)
    currency = Column(String)
    price = Column(Numeric(10, 2))

    def __str__(self):
        return f"Ad {self.listing_id}: {self.title} | {self.currency}{self.price}"

    def __repr__(self):
        return f"Title: {self.title}, Image: {self.image}, Date: {self.date}, Location: {self.location}, " \
               f"Bedrooms: {self.bedrooms}, Description: {self.description}, Currency: {self.currency}, Price: {self.price}"


def validate_html(html):
    return bool(html) and bool(BeautifulSoup(html, "html.parser").find('div', {'id': 'MainContainer'}))


def parse_number_of_pages(html):
    soup = BeautifulSoup(html, 'html.parser')
    resultsShowingCount = soup.find('span', {'class': re.compile('resultsShowingCount')})
    first_on_page, last_on_page, n_all = re.findall('\d+', resultsShowingCount.text)

    return ceil(int(n_all) / 40)


def parse_ads(page_html):
    soup = BeautifulSoup(page_html, 'html.parser')

    ads = []
    for ad_html in soup.find_all('div', {'class': re.compile('regular-ad')}):
        listing_id = ad_html['data-listing-id']
        try:
            title = ad_html.find('div', {'class': 'title'})
            if title:
                title = re.sub(r'\s+', ' ', title.text).strip()

            description = ad_html.find('div', {'class': 'description'})
            if description:
                description = re.sub(r'\s+', ' ', description.find(text=True, recursive=False)).strip()

            image = ad_html.find('div', {'class': 'image'}).find('picture')
            if image:
                image = image.img['data-src'].replace('200-jpg', '640-jpg')

            location_html = ad_html.find('div', {'class': 'location'})
            location = None
            date = None

            if location_html:
                location = location_html.span.text.strip()

                date = location_html.find('span', {'class': 'date-posted'}).text
                if 'ago' in date:
                    date = datetime.now().date()
                elif date == "Yesterday":
                    date = datetime.now().date() - timedelta(days=1)
                else:
                    date = datetime.strptime(date, '%d/%m/%Y').date()

            bedrooms = ad_html.find('span', {'class': 'bedrooms'})
            if bedrooms:
                bedrooms = re.sub(r'\s+', ' ', bedrooms.text).strip()

            price_html = ad_html.find('div', {'class': 'price'})
            currency = None
            price = None

            if price_html:
                parsed_price = re.match(r'(\D*)([\d,.]+)?', price_html.text.strip())

                if parsed_price.group(2):
                    #  if successfully parsed, there is a set price
                    currency = parsed_price.group(1)
                    price = parsed_price.group(2).replace(',', '')
                else:
                    #  otherwise, there was "Please contact" set as a price
                    price = None

            ads.append(Ad(listing_id=listing_id, title=title, description=description, image=image, date=date, location=location,
                          bedrooms=bedrooms, currency=currency, price=price))

        except TypeError:
            print(f"TypeError while processing ad with id {listing_id}. Skipping...")
        except AttributeError:
            print(f"TypeError while processing ad with id {listing_id}. Skipping...")
    return ads
