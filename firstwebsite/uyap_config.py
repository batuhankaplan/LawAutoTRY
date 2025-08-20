"""
UYAP Entegrasyon Yapılandırma Dosyası

Bu dosya UYAP entegrasyonu için gerekli ayarları içerir.
Kullanıcı bu dosyayı düzenleyerek UYAP bağlantısını özelleştirebilir.
"""

# UYAP Portal URL'leri
UYAP_URLS = {
    'avukat_portal': 'https://avukat.uyap.gov.tr',
    'login_page': 'https://avukat.uyap.gov.tr/giris',
    'dashboard': 'https://avukat.uyap.gov.tr/ana',
    'case_search': 'https://avukat.uyap.gov.tr/dosya/ara'
}

# Chrome WebDriver Ayarları
WEBDRIVER_CONFIG = {
    # Headless modu (False = tarayıcı görünür, True = arka planda)
    'headless': False,
    
    # Sayfa yükleme zaman aşımı (saniye)
    'page_load_timeout': 30,
    
    # Implicit wait süresi (saniye) 
    'implicit_wait': 10,
    
    # Chrome seçenekleri
    'chrome_options': [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    ]
}

# UYAP Giriş Ayarları
LOGIN_CONFIG = {
    # Giriş için maksimum bekleme süresi (saniye)
    'max_login_wait': 300,  # 5 dakika
    
    # Giriş kontrolü için tekrar sayısı
    'login_check_interval': 10,  # 10 saniye aralıklar
    
    # Başarılı giriş URL kontrolü
    'success_url_keywords': ['ana', 'dashboard', 'main'],
    
    # E-imza bekleme mesajı gösterilsin mi?
    'show_login_instructions': True
}

# Dosya Arama Ayarları  
SEARCH_CONFIG = {
    # Varsayılan arama filtreleri
    'default_filters': {
        'yargi_turu': '',  # Boş = tümü
        'yargi_birimi': '',
        'durum': '',
        'tarih_baslangic': '',
        'tarih_bitis': ''
    },
    
    # Maksimum sonuç sayısı
    'max_results': 100,
    
    # Sayfa başına sonuç sayısı
    'results_per_page': 20,
    
    # Arama zaman aşımı (saniye)
    'search_timeout': 60
}

# Dosya Detay Ayarları
DETAIL_CONFIG = {
    # Detay sayfası yükleme zaman aşımı
    'detail_load_timeout': 30,
    
    # Taraf bilgileri çekilsin mi?
    'fetch_parties': True,
    
    # Masraf bilgileri çekilsin mi?
    'fetch_expenses': True,
    
    # Evrak listesi çekilsin mi?
    'fetch_documents': True,
    
    # Duruşma bilgileri çekilsin mi?
    'fetch_hearings': True
}

# Evrak İndirme Ayarları
DOWNLOAD_CONFIG = {
    # İndirme klasörü (uploads klasörü altında)
    'download_folder': 'uyap_downloads',
    
    # Maksimum dosya boyutu (MB)
    'max_file_size_mb': 50,
    
    # İzin verilen dosya türleri
    'allowed_file_types': ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.tiff'],
    
    # İndirme zaman aşımı (saniye)
    'download_timeout': 120,
    
    # Aynı isimli dosya varsa ne yap? ('skip', 'overwrite', 'rename')
    'duplicate_handling': 'rename'
}

# Hata Yönetimi Ayarları
ERROR_CONFIG = {
    # Maksimum tekrar sayısı
    'max_retries': 3,
    
    # Tekrar aralığı (saniye)
    'retry_delay': 5,
    
    # Log seviyesi ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    'log_level': 'INFO',
    
    # Hata durumunda screenshot alınsın mı?
    'screenshot_on_error': True,
    
    # Screenshot klasörü
    'screenshot_folder': 'error_screenshots'
}

# Performans Ayarları
PERFORMANCE_CONFIG = {
    # Sayfa elementleri için maksimum bekleme süresi
    'element_wait_timeout': 15,
    
    # AJAX istekleri için bekleme süresi
    'ajax_wait_time': 2,
    
    # İşlemler arasında bekleme süresi (saniye)
    'operation_delay': 1,
    
    # Çoklu dosya işlemi için batch boyutu
    'batch_size': 5
}

# Güvenlik Ayarları
SECURITY_CONFIG = {
    # Session süre sınırı (dakika)
    'session_timeout_minutes': 60,
    
    # Otomatik çıkış kontrolü
    'auto_logout_check': True,
    
    # Güvenlik doğrulaması kontrolü
    'security_verification': True,
    
    # IP değişikliği kontrolü
    'ip_change_detection': False
}

# Test Modu Ayarları
TEST_CONFIG = {
    # Test modu aktif mi?
    'test_mode': False,
    
    # Mock veri kullan
    'use_mock_data': False,
    
    # Test süresi sınırı (saniye)
    'test_timeout': 300,
    
    # Debug modu
    'debug_mode': True
}

def get_config(section_name):
    """Belirli bir bölüm yapılandırmasını döndür"""
    configs = {
        'urls': UYAP_URLS,
        'webdriver': WEBDRIVER_CONFIG,
        'login': LOGIN_CONFIG,
        'search': SEARCH_CONFIG,
        'detail': DETAIL_CONFIG,
        'download': DOWNLOAD_CONFIG,
        'error': ERROR_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'security': SECURITY_CONFIG,
        'test': TEST_CONFIG
    }
    
    return configs.get(section_name, {})

def update_config(section_name, key, value):
    """Yapılandırma değerini güncelle"""
    configs = {
        'urls': UYAP_URLS,
        'webdriver': WEBDRIVER_CONFIG,
        'login': LOGIN_CONFIG,
        'search': SEARCH_CONFIG,
        'detail': DETAIL_CONFIG,
        'download': DOWNLOAD_CONFIG,
        'error': ERROR_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'security': SECURITY_CONFIG,
        'test': TEST_CONFIG
    }
    
    if section_name in configs and key in configs[section_name]:
        configs[section_name][key] = value
        print(f"Yapılandırma güncellendi: {section_name}.{key} = {value}")
        return True
    else:
        print(f"Geçersiz yapılandırma: {section_name}.{key}")
        return False

# Kullanım örnekleri için test fonksiyonu
if __name__ == "__main__":
    print("UYAP Yapılandırma Dosyası")
    print("=" * 40)
    
    # Tüm yapılandırmaları göster
    sections = ['urls', 'webdriver', 'login', 'search', 'detail', 'download']
    
    for section in sections:
        print(f"\n{section.upper()} Ayarları:")
        config = get_config(section)
        for key, value in config.items():
            print(f"  {key}: {value}")
    
    print("\n💡 Bu dosyayı düzenleyerek UYAP entegrasyonunu özelleştirebilirsiniz.")
    print("💡 Değişikliklerden sonra Flask uygulamasını yeniden başlatın.")