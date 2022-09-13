import asyncio
import aiohttp

from app.utils import parse_number_of_pages, get_ads


async def get_number_of_pages(session):
    last_page_html = await get_page_html(session, page_n=999999)
    number_of_pages = parse_number_of_pages(last_page_html)
    return number_of_pages, last_page_html


async def get_page_html(session, page_n):
    async with session.get(f'/b-apartments-condos/city-of-toronto/page-{page_n}/c37l1700273') as response:
        return await response.text()


async def get_all_pages():
    async with aiohttp.ClientSession(base_url='https://www.kijiji.ca') as session:
        print('Getting number of pages...')
        number_of_pages, last_page_html = await get_number_of_pages(session)
        print('Number of pages:', number_of_pages)
        pages_html = []
        if number_of_pages > 1:
            pages_html = await asyncio.gather(*[get_page_html(session, page_n=n) for n in range(number_of_pages)])
            pages_html.append(last_page_html)
        else:
            pages_html = [last_page_html]
        return pages_html

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    pages = loop.run_until_complete(get_all_pages())
    print(type(pages), len(pages))
    print(pages[1])
