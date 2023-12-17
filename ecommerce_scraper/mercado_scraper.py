import re

from bs4 import BeautifulSoup
import requests

def get_product_urls(search_url: str,
                     headers: dict = {},
                     timeout: int = 10,
                     max_retries: int = 1) -> list:
    """Get the URLs of the products from the search URL.
    
    :param search_url: The URL of the search page.
    :type search_url: str
    :param headers: The headers to use in the request.
    :type headers: dict
    :param timeout: The timeout in seconds.
    :type timeout: int
    :param max_retries: The maximum number of retries.
    :type max_retries: int
    :return: A list of the URLs of the products.
    :rtype: list
    """
    product_urls = []
    current_url = search_url
    retries = 1
    pagination_count = 1

    print("Getting the URLs of the products...")
    while True:
        try:
            response = requests.get(current_url, headers=headers, timeout=timeout)
        except:
            if retries < max_retries:
                retries += 1
                continue
            else:
                print(f"\nRequest failed after {max_retries} retries. Aborting.")
                print(f"Pages scraped: {pagination_count - 1}")
                print(f"URL failed to be scraped: {current_url}")
                print(f"URLs obtained: {len(product_urls)}")
                return product_urls
        
        print(f"\rScraping page: {pagination_count:2}", end="")
        soup = BeautifulSoup(response.text, "html.parser")

        products = soup.find_all("li", attrs={"class": "ui-search-layout__item"})
        for product in products:
            url = product.find("a", attrs={"class": "ui-search-link"}).get("href")
            url = re.search(r".+JM(?=#)|.+(?=\?)", url).group(0)
            product_urls.append(url)
        
        current_url = soup.find("li", attrs={"class": "andes-pagination__button andes-pagination__button--next"})
        if current_url:
            current_url = current_url.find("a").get("href")
            pagination_count += 1
            retries = 1
        else:
            break
    
    print(f"\nDone! Found {len(product_urls)} URLs in {pagination_count} pages.")
    return product_urls