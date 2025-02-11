import streamlit as st
import datetime
import pandas as pd
import io
import time
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

st.title("🏡 Otodom Property Scraper")
st.write("Scraping property listings from Otodom with SeleniumBase...")

# User input for max pages
max_pages = st.number_input("Max pages to scrape", min_value=1, max_value=50, value=10, step=1)

# Button to start scraping
if st.button("Start Scraping"):
    
    progress_bar = st.progress(0)
    log_messages = []  # Store logs to display in a scrollable window
    
    driver = Driver(uc=True, headless2=True, browser="chrome")
    url_template = "https://www.otodom.pl/pl/wyniki/sprzedaz/inwestycja/mazowieckie/warszawa/warszawa/warszawa?ownerTypeSingleSelect=ALL&viewType=listing&limit=72&page={}"
    
    links = []
    scraped_data = []
    log_placeholder = st.empty()
    dataframe = st.empty()
    # Scrape listings page-by-page
    for page in range(1, max_pages + 1):
        driver.get(url_template.format(page))
        time.sleep(2)
        
        if driver.find_elements(By.XPATH, "//h3[contains(text(), 'Nie znaleźliśmy żadnych ogłoszeń')]"):
            log_messages.append(f"❌ No listings found on page {page}. Stopping.")
            break
        
        new_links = list(set(element.get_attribute("href") for element in driver.find_elements(By.CSS_SELECTOR, "a[data-cy='listing-item-link']")))
        links.extend(new_links)

        log_messages.append(f"✅ Scraped {len(new_links)} links from page {page}")
        progress_bar.progress(page / max_pages)

        # Update log in a scrollable window
        # **Update the same log window instead of creating a new one**
        log_placeholder.text_area("📜 Scraper Log", "\n".join(log_messages), height=300)

    links = list(set(links))
    log_messages.append(f"🔗 Total unique property links collected: {len(links)}")
    
    # Display final logs
    with st.container():
        log_placeholder.text_area("📜 Scraper Log", "\n".join(log_messages), height=300)

    # Scrape details from each listing
    for index, link in enumerate(links):
        driver.get(link)
        time.sleep(5)
        
        extraction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            element = driver.find_element(By.XPATH, "//p[contains(text(), 'Dostępne lokale')]/following-sibling::p")
            numbers = element.text.split(" z ")
            first_number, second_number = numbers if len(numbers) == 2 else (None, None)
        except NoSuchElementException:
            first_number, second_number = None, None
        
        scraped_data.append([extraction_date, link, first_number, second_number])
        log_messages.append(f"📌 Scraped {index+1}/{len(links)}: {link}")
        df = pd.DataFrame(scraped_data, columns=["Date of Extraction", "URL", "First Number", "Second Number"])
        
        progress_bar.progress((index + 1) / len(links))
        
        # Update log dynamically
        with st.container():
            log_placeholder.text_area("📜 Scraper Log", "\n".join(log_messages), height=300)
        # Display the DataFrame as it's being updated
            dataframe.table(df)
    driver.quit()

    # Save to Excel
    # df = pd.DataFrame(scraped_data, columns=["Date of Extraction", "URL", "First Number", "Second Number"])
    # df.to_excel("otodom_listings.xlsx", index=False)

    st.success(f"✅ Scraping complete! {len(scraped_data)} properties collected.")
    
    # Display DataFrame
    # st.dataframe(df,use_container_width=True)

    # Download button for Excel
    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)  # Move the cursor to the beginning of the file

    st.download_button(
        label="📥 Download Excel",
        data=excel_file,
        file_name="otodom_listings.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
