from robocorp.tasks import task
from robocorp import browser
from RPA.Excel.Files import Files
import re
import time


@task
def thoughtful_rpa_challenge():
    """ Automate the process of extracting data from a news site."""
    browser.configure(slowmo=200)

    search_phrase = "Kamala"
    # Obtém o filtro selecionado
    category = select_filter()  
    months = 1
    output_file = "output/news_data.xlsx"

    open_website(search_phrase, category, months)
    #news_data = collect_and_save_data(search_phrase)  # Corrigido para passar o termo de busca

    news_data = []

    current_page = 1
    while current_page <= months:
        news_data = collect_and_save_data(search_phrase)  # Coleta dados da página atual
        news_data.extend(news_data)  # Adiciona à lista de dados

        if not go_to_next_page():
            break  # Se não houver próxima página, encerra o loop
        current_page += 1

    save_to_excel(news_data, output_file)

def open_website(search_phrase, news_category, months):
    browser.goto("https://apnews.com/")
    time.sleep(2)
    close_popup()
    perform_search(search_phrase, news_category)

def close_popup():
    page = browser.page()
    
    # Fechar pop-up principal
    close_button = page.query_selector('a.fancybox-item.fancybox-close')
    if close_button:
        close_button.click()
    
    # Clicar no botão "I Accept" se aparecer
    accept_button = page.query_selector('button#onetrust-accept-btn-handler')  # Usando ID comum para botão de aceitação de cookies
    if accept_button:
        accept_button.click()


def perform_search(search_phrase, news_category):
    page = browser.page()
    
    # Clique no botão de pesquisa
    search_button = page.query_selector('button.SearchOverlay-search-button')
    if search_button:
        search_button.click()
        time.sleep(2)  # Aguarde o campo de busca aparecer
    
    # Insira o texto da pesquisa
    search_input = page.query_selector('input.SearchOverlay-search-input')
    if search_input:
        search_input.fill(search_phrase)
        search_input.press('Enter')
        time.sleep(2)
        
        if news_category:
            select_category(news_category)

def select_category(news_category):
    page = browser.page()
    category_link = page.query_selector(f"a[href*='{news_category}']")
    if category_link:
        category_link.click()
        time.sleep(2)

def go_to_next_page():
    """Verifica e vai para a próxima página, se disponível."""
    page = browser.page()
    next_page_button = page.query_selector('div.Pagination-nextPage a')
    
    if next_page_button:
        next_page_url = next_page_button.get_attribute('href')
        browser.goto(next_page_url)
        time.sleep(2)  # Aguarda o carregamento da próxima página
        return True
    return False

def contains_money(text):
    """Detects if there is a money amount in the text."""
    money_patterns = [
        r"\$\d+(?:,\d{3})*(?:\.\d{1,2})?",  # Example: $11.1, $111,111.11
        r"\b\d+(?:,\d{3})*(?:\.\d{1,2})?\s*(dollars|USD)\b",  
    ]

    for pattern in money_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def select_filter():
    page = browser.page()
    
    # Encontre o item de filtro com o valor específico
    filter_checkbox = page.query_selector('input[value="00000188-f942-d221-a78c-f9570e360000"]')
    if filter_checkbox:
        filter_checkbox.click()
        time.sleep(2)  # Aguarde o filtro ser aplicado
        
        # Retorna o valor do filtro selecionado
        return filter_checkbox.get_attribute('value')
    return None

def ad_block(news_page_soup): 
    """Check if the text contains keywords that usually indicate an ad."""
    if not news_page_soup.find('time'):
        return True
    
    if news_page_soup.find_all('span', class_='video-label-box trc-main-label'):
        return True
    
    description_tags = news_page_soup.find_all('p')
    total_length = sum(len(p.text.strip()) for p in description_tags)
    if total_length < 100:
        return True

    ad_keywords = ["buy now", "offer", "discount", "deal", "shop", "subscribe", "sale", "sponsored"]
    for p_tag in description_tags:
        if any(keyword in p_tag.text.lower() for keyword in ad_keywords):
            return True
    return False

def collect_and_save_data(search_phrase):
    page = browser.page()
    articles = page.query_selector_all('div.PagePromo-title')
    descriptions = page.query_selector_all('div.PagePromo-description')
    dates = page.query_selector_all('span.Timestamp-template')
    images = page.query_selector_all('img.Image')  # Adicionando busca para a imagem
    data = []

    for i, article in enumerate(articles):
        # Coleta do título
        title_element = article.query_selector('a.Link > span.PagePromoContentIcons-text')
        title = title_element.inner_text() if title_element else ""
        
        # Coleta do link da notícia
        link_element = article.query_selector('a.Link')
        news_link = link_element.get_attribute('href') if link_element else ""

        # Coleta da descrição
        description_element = descriptions[i].query_selector('a.Link > span.PagePromoContentIcons-text') if i < len(descriptions) else None
        description = description_element.inner_text() if description_element else ""

        # Coleta da data
        date_element = dates[i] if i < len(dates) else None
        date = date_element.inner_text() if date_element else ""

        # Coleta da imagem (nome do arquivo)
        image_element = images[i] if i < len(images) else None
        image_src = image_element.get_attribute('src') if image_element else ""
        image_filename = image_src.split('/')[-1].split('?')[0] if image_src else ""

        # Contagem das palavras-chave
        count_search_phrase = title.lower().count(search_phrase.lower()) + description.lower().count(search_phrase.lower())
        
        money_detected = contains_money(title) or contains_money(description)
        
        # Adiciona os dados coletados à lista
        data.append({
            'Title': title,
            'Description': description,
            'Date': date,
            'Link': news_link,
            'Image Filename': image_filename,  # Adicionando o nome da imagem
            'Count of Search Phrase': count_search_phrase,
            'Money Detected': money_detected,
        })
    
    return data

def save_to_excel(news_data, output_file):
    # Cria um workbook do Excel e adiciona os dados
    excel = Files()
    excel.create_workbook(output_file)
    excel.create_worksheet("news_data")

    header = ["Title", "Description", "Date", "Link", "Image Filename", "Count of Search Phrase", "Money Detected (T/F)"]
    excel.append_rows_to_worksheet([header], "news_data")
    
    for data in news_data:
        excel.append_rows_to_worksheet([
            [data['Title'], data['Description'], data['Date'], data['Link'], data['Image Filename'], data['Count of Search Phrase'], data['Money Detected']]
        ], "news_data")
    
    excel.save_workbook()