import streamlit as st
from collections import deque
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def setup_driver():
    from selenium.webdriver.chrome.service import Service
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
    )
    
    # Spécifier explicitement le chemin vers Chromium
    chrome_options.binary_location = "/usr/bin/chromium"
    
    # Utiliser directement le chromedriver système
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def crawl_website(start_url, max_pages=50):
    """
    Génére (visited_count, visited) à chaque page visitée
    en excluant les URLs pointant vers des images.
    """
    visited = set()
    queue = deque([start_url])

    driver = setup_driver()
    visited_count = 0

    # Extensions à exclure (images, etc.)
    excluded_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue

        visited.add(current_url)

        try:
            driver.get(current_url)
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    full_link = urljoin(current_url, href)

                    # Vérifier qu'on reste sur le même domaine
                    if urlparse(full_link).netloc == urlparse(start_url).netloc:
                        # Vérifier que l'extension n'est pas dans la liste exclue
                        if not full_link.lower().endswith(excluded_extensions):
                            if full_link not in visited:
                                queue.append(full_link)

        except Exception:
            pass  # On ignore l'erreur et on continue

        visited_count += 1
        yield visited_count, visited

    driver.quit()

def main():
    st.set_page_config(page_title="Sitemap Generator", layout="centered")
    st.title("Générateur de Sitemap (URLs uniquement, sans JPEG)")

    st.markdown("""
    **Comment ça marche ?**  
    1. Entrez l'URL de départ (ex : `https://example.com`).  
    2. Indiquez le nombre max de pages à explorer.  
    3. Cliquez sur **Lancer le crawl**.  
    4. Les URLs (hors images) s'afficheront en temps réel.
    """)

    start_url = st.text_input("URL à crawler", "https://example.com")
    max_pages = st.number_input("Nombre maximum de pages à explorer", min_value=1, value=10)

    if st.button("Lancer le crawl"):
        st.info("Démarrage du crawler...")

        progress_bar = st.progress(0)
        status_text = st.empty()
        urls_placeholder = st.empty()
        final_text_placeholder = st.empty()

        with st.spinner("Crawl en cours..."):
            visited_urls = set()
            total_visited = 0

            for visited_count, visited_set in crawl_website(start_url, max_pages):
                total_visited = visited_count
                visited_urls = visited_set

                # Mise à jour de la barre de progression
                progress_value = int((visited_count / max_pages) * 100)
                progress_bar.progress(progress_value)

                # Indiquer combien de pages visitées
                status_text.markdown(f"**Pages visitées** : {visited_count} / {max_pages}")

                # Affichage des URLs déjà trouvées
                sorted_urls = sorted(list(visited_urls))
                urls_text = "\n".join(sorted_urls)
                urls_placeholder.text_area("URLs explorées", urls_text, height=200)

            st.success("Crawl terminé !")

        st.write("Nombre total de liens visités :", total_visited)

        # Affichage final (copier-coller)
        all_urls_text = "\n".join(sorted(list(visited_urls)))
        final_text_placeholder.text_area("Toutes les URLs (sans images) :", all_urls_text, height=200)

        # Bouton "Copier dans le presse-papier" via un hack JS
        copy_button_code = f"""
            <script>
            function copyToClipboard() {{
                const textToCopy = `{all_urls_text.replace("`", "\\`")}`;
                navigator.clipboard.writeText(textToCopy)
                    .then(() => {{
                        alert("URLs copiées dans le presse-papier !");
                    }})
                    .catch(err => {{
                        alert("Impossible de copier : " + err);
                    }});
            }}
            </script>
            <button onclick="copyToClipboard()">Copier toutes les URLs</button>
        """
        st.markdown(copy_button_code, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

