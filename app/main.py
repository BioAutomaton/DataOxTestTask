import asyncio

import aiohttp

from app.database import Session, Base, engine
from app.utils import parse_number_of_pages, parse_ads, validate_html, Ad

user_agent = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
}


async def get_number_of_pages(session):
    """Function to get number of pages with results"""
    response = {'html': None, 'page_number': None}
    while not response or not validate_html(response['html']):
        response = await get_page(session, page_number=999999)

    number_of_pages = parse_number_of_pages(response['html'])
    return number_of_pages, response['html']


async def get_page(session, page_number):
    """Request a page from kijiji"""
    async with session.get(f'/b-apartments-condos/city-of-toronto/page-{page_number}/c37l1700273',
                           headers=user_agent) as response:
        html = await response.text()
        is_valid_html = validate_html(html)

        if is_valid_html:
            return {'html': html, 'page_number': page_number}
        else:
            return None



async def get_all_ads():
    async with aiohttp.ClientSession(base_url='https://www.kijiji.ca') as session:
        print('Getting number of pages...')
        number_of_pages, last_page_html = await get_number_of_pages(session)
        print('Number of pages:', number_of_pages)

        page_numbers = set(range(1, number_of_pages))
        pages_html = []
        ads = []
        ads.extend(parse_ads(last_page_html))

        while page_numbers:
            responses = await asyncio.gather(*[get_page(session, page_number=n) for n in page_numbers])

            for response in responses:
                if response:
                    page_numbers.remove(response['page_number'])
                    pages_html.append(response['html'])

            pages_remaining = len(page_numbers)
            valid_results = sum(bool(r) for r in responses)

            if pages_html:
                print(f"Server returned {valid_results} valid HTML pages. Parsing received ads...")
                while pages_html:
                    ads.extend(parse_ads(pages_html.pop()))
            if valid_results <= pages_remaining:
                print(f"Server returned invalid HTML for {pages_remaining} pages. Retrying...")
                # print(f'{pages_remaining} pages remaining...')
                await asyncio.sleep(5)

        return ads


if __name__ == '__main__':
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    loop = asyncio.get_event_loop()

    with Session() as db_session:
        ads = loop.run_until_complete(get_all_ads())
        print("Number of ads collected:", len(ads))
        for ad in ads:
            db_session.add(ad)
        db_session.commit()

        print("Printing sample of 5 parsed ads:")
        for ad in ads[:5]:
            print(repr(ad))
