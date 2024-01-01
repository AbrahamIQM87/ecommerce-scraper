from datetime import date
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
        soup = BeautifulSoup(response.content, "html.parser")

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


def get_product_data(product_url: str,
                     headers: dict = {},
                     timeout: int = 10,
                     max_retries: int = 1) -> dict:
    """Get the data of the product from the product URL.
    
    :param product_url: The URL of the product.
    :type product_url: str
    :param headers: The headers to use in the request.
    :type headers: dict
    :param timeout: The timeout in seconds.
    :type timeout: int
    :param max_retries: The maximum number of retries.
    :type max_retries: int
    :return: The data of the product.
    :rtype: dict"""
    retries = 1
    while True:
        try:
            response = requests.get(product_url, headers=headers, timeout=timeout)
            break
        except:
            if retries < max_retries:
                retries += 1
                continue
            else:
                print(f"\nRequest failed after {max_retries} retries. Aborting.")
                return {}
        
    soup = BeautifulSoup(response.content, "html.parser")

    publication_number = re.search(r"((?<=MLM-)|(?<=MLM))\d+", product_url).group(0)

    image_url = soup.find("img", attrs={"class": "ui-pdp-image ui-pdp-gallery__figure__image", "data-index": "0"})
    image_url = image_url.get("src") if image_url else None
    
    title = soup.find("h1", attrs={"class": "ui-pdp-title"})
    title = title.text if title else None

    subtitle = soup.find("span", attrs={"class": "ui-pdp-subtitle"})
    if subtitle:
        condition = re.search(r"(\w+)", subtitle.text).group(0)
        sales = re.search(r"\+*\d+[a-zA-Z]*", subtitle.text)
        if sales:
            sales =  sales.group(0)
            sales = sales.replace("mil", "000")
        else:
            sales = "0"
    else:
        condition = None
        sales = None
    
    rating_info = soup.find("div", attrs={"class": "ui-pdp-header__info"})
    if rating_info:
        review_rating = rating_info.find("span", attrs={"class": "ui-pdp-review__rating"}).text
        review_rating = float(review_rating)
        review_amount = rating_info.find("span", attrs={"class": "ui-pdp-review__amount"}).text
        review_amount = int(re.search(r"\d+", review_amount).group(0))
    else:
        review_rating = None
        review_amount = None
    
    price_container = soup.find("div", attrs={"class": "ui-pdp-price__main-container"})
    if price_container:
        regular_price = price_container.find("s")
        if regular_price:
            regular_price = regular_price.find("span", attrs={"class": "andes-money-amount__fraction"})
            regular_price = int(regular_price.text.replace(",", "")) if regular_price else None

        final_price = price_container.find("div", attrs={"class": "ui-pdp-price__second-line"})
        final_price = final_price.find("meta", attrs={"itemprop": "price"}).get("content")
        final_price = float(final_price)
    else:
        regular_price = None
        final_price = None
    
    shipping_summary = soup.find("div", attrs={"id": "shipping_summary"})
    if shipping_summary:
        shipping_summary = shipping_summary.find("span")
        shipping_summary = shipping_summary.text if shipping_summary else "Más gastos de envío"
    else:
        shipping_summary = None
    
    available_quantity = soup.find("span", attrs={"class": "ui-pdp-buybox__quantity__available"})
    if available_quantity:
        available_quantity = re.search(r"\d+", available_quantity.text)
        available_quantity = int(available_quantity.group(0)) if available_quantity else 1
    else:
        available_quantity = None

    return {
        "publication_number": publication_number,
        "url": product_url,
        "image_url": image_url,
        "title": title,
        "condition": condition,
        "sales": sales,
        "review_rating": review_rating,
        "review_amount": review_amount,
        "regular_price": regular_price,
        "final_price": final_price,
        "shipping_summary": shipping_summary,
        "available_quantity": available_quantity,
        "scraping_date": date.today().strftime("%d/%m/%Y")
    }

def scrape_search_results(search_url: str,
                          headers: dict = {},
                          timeout: int = 10,
                          max_retries: int = 1) -> list:
    """Scrape the search results from the search URL.

    :param search_url: The URL of the search page.
    :type search_url: str
    :param headers: The headers to use in the request.
    :type headers: dict
    :param timeout: The timeout in seconds.
    :type timeout: int
    :param max_retries: The maximum number of retries.
    :type max_retries: int
    :return: A list of the data of the products.
    :rtype: list
    """
    product_urls = get_product_urls(search_url,
                                    headers=headers,
                                    timeout=timeout,
                                    max_retries=max_retries)

    print("Getting the data of the products...")
    product_data = []
    for count, product_url in enumerate(product_urls):
        print(f"\rScraping product {(count + 1):4}/{len(product_urls)}", end="")
        product_data.append(
            get_product_data(
                product_url,
                headers=headers,
                timeout=timeout,
                max_retries=max_retries
            )
        )
    print(f"\nDone! Obtained data of {len(product_data)} products.")

    return product_data