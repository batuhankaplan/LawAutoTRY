from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
from selenium.webdriver.common.keys import Keys
import os
import subprocess
import logging
from datetime import datetime
import requests
from urllib.parse import urljoin
import re
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import zipfile
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UyapFile:
    """UYAP dosya bilgileri için veri sınıfı"""
    id: str
    esas_no: str
    mahkeme: str
    yargi_turu: str
    yargi_birimi: str
    durum: str
    acilis_tarihi: str
    taraflar: str
    davali: str = ""
    davaci: str = ""
    subject: str = ""
    last_action: str = ""
    next_hearing: str = ""

@dataclass
class UyapParty:
    """UYAP taraf bilgileri için veri sınıfı"""
    name: str
    capacity: str  # Davacı, Davalı, etc.
    identity_number: str = ""
    address: str = ""
    lawyer: str = ""
    lawyer_bar_number: str = ""

@dataclass
class UyapExpense:
    """UYAP masraf bilgileri için veri sınıfı"""
    expense_type: str
    amount: float
    date: str
    is_paid: bool = False
    description: str = ""

@dataclass
class UyapDocument:
    """UYAP evrak bilgileri için veri sınıfı"""
    name: str
    date: str
    size: str
    type: str
    url: str
    download_url: str = ""

class UYAPAdvancedIntegration:
    """
    UYAP Avukat Portalı ile gelişmiş entegrasyon sınıfı
    Dosya sorgulama, detay çekme, evrak indirme işlemleri
    """
    
    def __init__(self, downloads_path: str = None):
        """
        UYAP entegrasyon sınıfını başlatır
        
        Args:
            downloads_path: İndirilen dosyaların kaydedileceği dizin
        """
        self.driver = None
        self.wait = None
        self.downloads_path = downloads_path or os.path.join(os.getcwd(), "uploads", "uyap")
        self.session_active = False
        self.max_retries = 3
        self.retry_delay = 2
        
        # İndirme dizinini oluştur
        os.makedirs(self.downloads_path, exist_ok=True)
        
        # İşlenen dosyaları takip etmek için
        self.processed_files = set()
        self.session_cookies = {}
        
    def initialize_driver(self) -> bool:
        """
        Chrome sürücüsünü başlatır ve UYAP'a bağlanır
        
        Returns:
            bool: Başlatma başarılı ise True
        """
        try:
            # Chrome ayarları
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # İndirme klasörü ayarları
            prefs = {
                "download.default_directory": self.downloads_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Mevcut Chrome session'ı kullanmaya çalış
            try:
                chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Mevcut Chrome session'ına bağlandı")
            except Exception:
                # Yeni Chrome session başlat
                chrome_options = Options()  # Reset options
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_experimental_option("prefs", prefs)
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Yeni Chrome session başlatıldı")
            
            self.wait = WebDriverWait(self.driver, 30)
            
            # UYAP ana sayfasına git
            self.driver.get("https://avukatbeta.uyap.gov.tr")
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logger.error(f"Chrome sürücüsü başlatılamadı: {str(e)}")
            return False
    
    def check_login_status(self) -> bool:
        """
        UYAP'a giriş yapılıp yapılmadığını kontrol eder
        
        Returns:
            bool: Giriş yapılmış ise True
        """
        try:
            # Ana sayfa menüsünü kontrol et
            menu_items = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".dx-menu-item"))
            )
            
            if len(menu_items) > 3:  # Giriş yapılmışsa daha fazla menü öğesi olur
                self.session_active = True
                logger.info("UYAP'a giriş yapılmış")
                return True
            else:
                logger.info("UYAP'a giriş yapılmamış")
                return False
                
        except TimeoutException:
            logger.warning("Giriş durumu kontrol edilemedi")
            return False
    
    def wait_for_login(self, timeout: int = 300) -> bool:
        """
        Kullanıcının giriş yapmasını bekler
        
        Args:
            timeout: Maksimum bekleme süresi (saniye)
            
        Returns:
            bool: Giriş yapılırsa True
        """
        logger.info("UYAP'a e-imza ile giriş yapılması bekleniyor...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_login_status():
                return True
            time.sleep(2)
        
        logger.error("Giriş işlemi zaman aşımına uğradı")
        return False
    
    def navigate_to_file_search(self) -> bool:
        """
        Dosya sorgulama sayfasına gider
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            # Detaylı arama sayfasına git
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dx-box-item')]//div[contains(text(), 'Detaylı')]"))
            )
            self.driver.execute_script("arguments[0].click();", search_button)
            time.sleep(3)
            
            logger.info("Detaylı arama sayfasına geçildi")
            return True
            
        except Exception as e:
            logger.error(f"Dosya sorgulama sayfasına gidilemedi: {str(e)}")
            return False
    
    def search_files(self, filters: Dict) -> List[UyapFile]:
        """
        Verilen filtrelere göre dosyaları arar
        
        Args:
            filters: Arama filtreleri (yargi_turu, yargi_birimi, vb.)
            
        Returns:
            List[UyapFile]: Bulunan dosyalar listesi
        """
        try:
            # Filtreleri uygula
            if not self._apply_filters(filters):
                logger.error("Filtreler uygulanamadı")
                return []
            
            # Arama butonuna tıkla
            search_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dx-button-content')]//span[contains(text(), 'Sorgula')]"))
            )
            self.driver.execute_script("arguments[0].click();", search_btn)
            
            # Sonuçların yüklenmesini bekle
            time.sleep(5)
            
            # Sonuçları parse et
            files = self._parse_search_results()
            logger.info(f"{len(files)} dosya bulundu")
            
            return files
            
        except Exception as e:
            logger.error(f"Dosya arama hatası: {str(e)}")
            return []
    
    def _apply_filters(self, filters: Dict) -> bool:
        """
        Arama filtrelerini uygular
        
        Args:
            filters: Uygulanacak filtreler
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            # Yargı türü seç
            if filters.get('yargi_turu'):
                yargi_turu_dropdown = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dx-dropdowneditor-button')]"))
                )
                yargi_turu_dropdown.click()
                time.sleep(1)
                
                yargi_turu_option = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'dx-item-content') and contains(text(), '{filters['yargi_turu']}')]"))
                )
                yargi_turu_option.click()
                time.sleep(2)
            
            # Tarih aralığı
            if filters.get('start_date'):
                start_date_input = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Başlangıç')]")
                start_date_input.clear()
                start_date_input.send_keys(filters['start_date'])
            
            if filters.get('end_date'):
                end_date_input = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Bitiş')]")
                end_date_input.clear()
                end_date_input.send_keys(filters['end_date'])
            
            # Hızlı arama
            if filters.get('search'):
                search_input = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Arama')]")
                search_input.clear()
                search_input.send_keys(filters['search'])
            
            return True
            
        except Exception as e:
            logger.error(f"Filtre uygulama hatası: {str(e)}")
            return False
    
    def _parse_search_results(self) -> List[UyapFile]:
        """
        Arama sonuçlarını parse eder
        
        Returns:
            List[UyapFile]: Parse edilmiş dosyalar
        """
        files = []
        
        try:
            # Sonuç tablosunu bul
            table = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.dx-datagrid-table"))
            )
            
            # Tablo satırlarını al
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Header'ı atla
            
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:
                        file_data = UyapFile(
                            id=f"uyap_file_{i}_{int(time.time())}",
                            esas_no=cells[0].text.strip(),
                            mahkeme=cells[1].text.strip(),
                            yargi_turu=cells[2].text.strip() if len(cells) > 2 else "",
                            yargi_birimi=cells[1].text.strip(),  # Mahkemeden çıkar
                            durum=cells[3].text.strip() if len(cells) > 3 else "Aktif",
                            acilis_tarihi=cells[4].text.strip() if len(cells) > 4 else "",
                            taraflar=cells[5].text.strip() if len(cells) > 5 else ""
                        )
                        files.append(file_data)
                        
                except Exception as e:
                    logger.warning(f"Satır parse edilemedi: {str(e)}")
                    continue
            
            return files
            
        except Exception as e:
            logger.error(f"Sonuç parse hatası: {str(e)}")
            return []
    
    def get_file_details(self, file_id: str, esas_no: str) -> Optional[Dict]:
        """
        Belirli bir dosyanın detaylarını çeker
        
        Args:
            file_id: Dosya ID'si
            esas_no: Esas numarası
            
        Returns:
            Dict: Dosya detayları (taraflar, masraflar, evraklar)
        """
        try:
            # Dosyanın detay sayfasını aç
            detail_link = self.driver.find_element(
                By.XPATH, f"//td[contains(text(), '{esas_no}')]/following-sibling::td//a[contains(@title, 'Detay') or contains(@class, 'detail')]"
            )
            detail_link.click()
            time.sleep(3)
            
            # Detayları topla
            details = {
                'basic_info': self._extract_basic_info(),
                'parties': self._extract_parties(),
                'expenses': self._extract_expenses(),
                'documents': self._extract_documents()
            }
            
            # Geri dön
            self.driver.back()
            time.sleep(2)
            
            logger.info(f"Dosya detayları alındı: {esas_no}")
            return details
            
        except Exception as e:
            logger.error(f"Dosya detayları alınamadı {esas_no}: {str(e)}")
            return None
    
    def _extract_basic_info(self) -> Dict:
        """Dosya temel bilgilerini çıkarır"""
        basic_info = {}
        
        try:
            # Temel bilgi elementlerini bul
            info_elements = self.driver.find_elements(By.XPATH, "//td[contains(@class, 'info-label')]/following-sibling::td")
            
            for element in info_elements:
                # Bilgi türünü ve değerini al
                # Bu kısım UYAP'ın gerçek DOM yapısına göre ayarlanmalı
                pass
            
        except Exception as e:
            logger.warning(f"Temel bilgi çıkarılamadı: {str(e)}")
        
        return basic_info
    
    def _extract_parties(self) -> List[UyapParty]:
        """Taraf bilgilerini çıkarır"""
        parties = []
        
        try:
            # Taraflar sekmesine git
            parties_tab = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Taraflar') or contains(text(), 'Parties')]")
            parties_tab.click()
            time.sleep(2)
            
            # Taraf bilgilerini parse et
            party_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'party-info')]")
            
            for party_element in party_elements:
                try:
                    name = party_element.find_element(By.XPATH, ".//span[contains(@class, 'party-name')]").text
                    capacity = party_element.find_element(By.XPATH, ".//span[contains(@class, 'party-capacity')]").text
                    
                    party = UyapParty(
                        name=name.strip(),
                        capacity=capacity.strip()
                    )
                    parties.append(party)
                    
                except Exception as e:
                    logger.warning(f"Taraf bilgisi parse edilemedi: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"Taraf bilgileri çıkarılamadı: {str(e)}")
        
        return parties
    
    def _extract_expenses(self) -> List[UyapExpense]:
        """Masraf bilgilerini çıkarır"""
        expenses = []
        
        try:
            # Masraflar sekmesine git
            expenses_tab = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Masraflar') or contains(text(), 'Expenses')]")
            expenses_tab.click()
            time.sleep(2)
            
            # Masraf tablosunu bul
            expense_table = self.driver.find_element(By.XPATH, "//table[contains(@class, 'expense-table')]")
            rows = expense_table.find_elements(By.TAG_NAME, "tr")[1:]  # Header'ı atla
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        expense = UyapExpense(
                            expense_type=cells[0].text.strip(),
                            amount=float(cells[1].text.strip().replace(',', '.').replace('₺', '')),
                            date=cells[2].text.strip()
                        )
                        expenses.append(expense)
                        
                except Exception as e:
                    logger.warning(f"Masraf satırı parse edilemedi: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"Masraf bilgileri çıkarılamadı: {str(e)}")
        
        return expenses
    
    def _extract_documents(self) -> List[UyapDocument]:
        """Evrak bilgilerini çıkarır"""
        documents = []
        
        try:
            # Evraklar sekmesine git
            documents_tab = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Evraklar') or contains(text(), 'Documents')]")
            documents_tab.click()
            time.sleep(2)
            
            # Evrak listesini bul
            document_list = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'document-item')]")
            
            for doc_element in document_list:
                try:
                    name = doc_element.find_element(By.XPATH, ".//span[contains(@class, 'doc-name')]").text
                    date = doc_element.find_element(By.XPATH, ".//span[contains(@class, 'doc-date')]").text
                    
                    # İndirme linkini bul
                    download_link = doc_element.find_element(By.XPATH, ".//a[contains(@href, 'download')]")
                    download_url = download_link.get_attribute('href')
                    
                    document = UyapDocument(
                        name=name.strip(),
                        date=date.strip(),
                        size="",  # UYAP'tan boyut bilgisi alınabilirse
                        type=self._get_file_type_from_name(name),
                        url=download_url,
                        download_url=download_url
                    )
                    documents.append(document)
                    
                except Exception as e:
                    logger.warning(f"Evrak bilgisi parse edilemedi: {str(e)}")
                    continue
            
        except Exception as e:
            logger.warning(f"Evrak bilgileri çıkarılamadı: {str(e)}")
        
        return documents
    
    def download_document(self, document: UyapDocument, target_folder: str) -> Optional[str]:
        """
        Belirli bir evrakı indirir
        
        Args:
            document: İndirilecek evrak bilgileri
            target_folder: Hedef klasör
            
        Returns:
            str: İndirilen dosyanın yolu
        """
        try:
            # Hedef klasörü oluştur
            os.makedirs(target_folder, exist_ok=True)
            
            # Dosya adını temizle
            safe_filename = self._sanitize_filename(document.name)
            target_path = os.path.join(target_folder, safe_filename)
            
            # İndirme linkine tıkla
            download_element = self.driver.find_element(By.XPATH, f"//a[@href='{document.download_url}']")
            download_element.click()
            
            # İndirmenin tamamlanmasını bekle
            download_completed = self._wait_for_download(safe_filename, timeout=60)
            
            if download_completed:
                # İndirilen dosyayı hedef klasöre taşı
                downloaded_file = os.path.join(self.downloads_path, safe_filename)
                if os.path.exists(downloaded_file):
                    shutil.move(downloaded_file, target_path)
                    logger.info(f"Evrak indirildi: {safe_filename}")
                    return target_path
            
            return None
            
        except Exception as e:
            logger.error(f"Evrak indirilemedi {document.name}: {str(e)}")
            return None
    
    def _wait_for_download(self, filename: str, timeout: int = 60) -> bool:
        """
        Dosya indirme işleminin tamamlanmasını bekler
        
        Args:
            filename: İndirilen dosya adı
            timeout: Maksimum bekleme süresi
            
        Returns:
            bool: İndirme tamamlandıysa True
        """
        start_time = time.time()
        temp_file = os.path.join(self.downloads_path, filename + ".crdownload")
        target_file = os.path.join(self.downloads_path, filename)
        
        while time.time() - start_time < timeout:
            if os.path.exists(target_file) and not os.path.exists(temp_file):
                return True
            time.sleep(1)
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Dosya adını güvenli hale getirir"""
        # Geçersiz karakterleri temizle
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Uzunluğu sınırla
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _get_file_type_from_name(self, filename: str) -> str:
        """Dosya adından dosya türünü çıkarır"""
        ext = os.path.splitext(filename)[1].lower()
        
        type_mapping = {
            '.pdf': 'PDF',
            '.doc': 'Word',
            '.docx': 'Word',
            '.xls': 'Excel',
            '.xlsx': 'Excel',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.zip': 'Archive'
        }
        
        return type_mapping.get(ext, 'Unknown')
    
    def close(self):
        """Tarayıcıyı kapatır"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("UYAP entegrasyon sürücüsü kapatıldı")
            except Exception as e:
                logger.error(f"Sürücü kapatılırken hata: {str(e)}")
    
    def __enter__(self):
        """Context manager girişi"""
        if self.initialize_driver():
            return self
        else:
            raise Exception("UYAP sürücüsü başlatılamadı")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager çıkışı"""
        self.close()

# UYAP entegrasyon yöneticisi - Singleton pattern
class UYAPManager:
    """
    UYAP entegrasyonunu yöneten singleton sınıf
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.uyap_instance = None
            self.initialized = True
    
    def get_uyap_instance(self) -> Optional[UYAPAdvancedIntegration]:
        """
        UYAP entegrasyon instance'ını döndürür
        
        Returns:
            UYAPAdvancedIntegration: UYAP entegrasyon instance'ı
        """
        if self.uyap_instance is None:
            self.uyap_instance = UYAPAdvancedIntegration()
            
        return self.uyap_instance
    
    def ensure_connection(self) -> bool:
        """
        UYAP bağlantısının aktif olduğundan emin olur
        
        Returns:
            bool: Bağlantı aktifse True
        """
        uyap = self.get_uyap_instance()
        
        if not uyap.session_active:
            if uyap.initialize_driver():
                return uyap.wait_for_login()
        
        return uyap.session_active
    
    def search_files_with_filters(self, filters: Dict) -> List[UyapFile]:
        """
        Filtrelere göre dosya arar
        
        Args:
            filters: Arama filtreleri
            
        Returns:
            List[UyapFile]: Bulunan dosyalar
        """
        if not self.ensure_connection():
            raise Exception("UYAP bağlantısı kurulamadı")
        
        uyap = self.get_uyap_instance()
        
        # Dosya arama sayfasına git
        if not uyap.navigate_to_file_search():
            raise Exception("Dosya arama sayfasına gidilemedi")
        
        # Dosyaları ara
        return uyap.search_files(filters)
    
    def get_file_complete_details(self, file_id: str, esas_no: str) -> Optional[Dict]:
        """
        Dosyanın tüm detaylarını çeker
        
        Args:
            file_id: Dosya ID'si
            esas_no: Esas numarası
            
        Returns:
            Dict: Dosya detayları
        """
        if not self.ensure_connection():
            raise Exception("UYAP bağlantısı kurulamadı")
        
        uyap = self.get_uyap_instance()
        return uyap.get_file_details(file_id, esas_no)
    
    def download_file_documents(self, documents: List[UyapDocument], target_folder: str) -> List[str]:
        """
        Dosyanın evraklarını indirir
        
        Args:
            documents: İndirilecek evraklar
            target_folder: Hedef klasör
            
        Returns:
            List[str]: İndirilen dosya yolları
        """
        if not self.ensure_connection():
            raise Exception("UYAP bağlantısı kurulamadı")
        
        uyap = self.get_uyap_instance()
        downloaded_files = []
        
        for document in documents:
            try:
                downloaded_path = uyap.download_document(document, target_folder)
                if downloaded_path:
                    downloaded_files.append(downloaded_path)
            except Exception as e:
                logger.error(f"Evrak indirilemedi {document.name}: {str(e)}")
                continue
        
        return downloaded_files
    
    def cleanup(self):
        """Kaynakları temizler"""
        if self.uyap_instance:
            self.uyap_instance.close()
            self.uyap_instance = None