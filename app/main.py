import asyncio

import aiohttp

from app.utils import parse_number_of_pages, get_ads, validate_html

user_agent = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
}


async def get_number_of_pages(session):
    response = {'html': None, 'page_number': None}
    while not validate_html(response['html']):
        response = await get_page(session, page_number=999999)

    number_of_pages = parse_number_of_pages(response['html'])
    return number_of_pages, response['html']


async def get_page(session, page_number):
    async with session.get(f'/b-apartments-condos/city-of-toronto/page-{page_number}/c37l1700273', headers=user_agent) as response:
        html = await response.text()
        is_valid_html = validate_html(html)

        if is_valid_html:
            return {'html': html, 'page_number': page_number}
        else:
            return None


async def get_all_pages():
    async with aiohttp.ClientSession(base_url='https://www.kijiji.ca') as session:
        print('Getting number of pages...')
        number_of_pages, last_page_html = await get_number_of_pages(session)
        print('Number of pages:', number_of_pages)

        page_numbers = set(range(1, number_of_pages))
        pages_html = []

        while page_numbers:
            responses = await asyncio.gather(*[get_page(session, page_number=n) for n in page_numbers])
            for response in responses:
                if response:
                    # print(f"Page {response['page_number']}: {validate_html(response['html'])}")
                    page_numbers.remove(response['page_number'])
                    pages_html.append(response['html'])
            print(f'{len(page_numbers)} pages remaining...')
            print(page_numbers)
            await asyncio.sleep(5)

        pages_html.append(last_page_html)
        return pages_html


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    pages = loop.run_until_complete(get_all_pages())
    print(type(pages), len(pages))

    print("Parsing received ads...")
    ads = []
    for page in pages:
        ads.extend(get_ads(page))
    print("Number of ads collected:", len(ads))
