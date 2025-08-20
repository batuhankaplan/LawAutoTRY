# UYAP'tan Dosya Aktarım Sistemi

Bu dokümantasyon, LawAutomation sistemi için geliştirilen UYAP entegrasyon özelliğini açıklar.

## Özellik Özeti

UYAP Avukat Portalı'ndaki dosya bilgilerini tek tıkla LawAutomation sistemine aktarabilme özelliği.

### Ana Özellikler

- **Gelişmiş Filtreleme**: Yargı türü, birim, durum, tarih aralığı ve hızlı arama
- **Dosya Önizleme**: Aktarmadan önce dosya detaylarını görüntüleme
- **Seçmeli Aktarım**: Sadece istenen bileşenleri aktarma (temel bilgiler, taraflar, masraflar, evraklar)
- **İdempotent İşlem**: Aynı dosya birden fazla kez aktarılsa bile güvenli
- **İlerleme İzleme**: Gerçek zamanlı aktarım durumu ve log'lar
- **Hata Yönetimi**: Kapsamlı hata yakalama ve kullanıcı bilgilendirmesi

## Teknik Yapı

### Frontend Bileşenleri

1. **UYAP Aktarım Modal**: Tam ekran modal arayüz
   - Sol Panel: Filtreleme kontrolları
   - Orta Panel: Dosya listesi ve önizleme
   - Sağ Panel: Aktarım ayarları ve ilerleme takibi

2. **JavaScript Modülleri**:
   - `UyapImportManager`: Aktarım işlemlerini yöneten sınıf
   - Toast notification sistemi
   - Dosya önizleme drawer'ı

### Backend Bileşenleri

1. **UYAP Entegrasyon Sınıfı** (`uyap_integration_advanced.py`):
   - `UYAPAdvancedIntegration`: Ana entegrasyon sınıfı
   - `UYAPManager`: Singleton yönetici sınıf
   - Selenium tabanlı tarayıcı otomasyonu

2. **Veri Modelleri**:
   - `UyapFile`: Dosya bilgileri
   - `UyapParty`: Taraf bilgileri
   - `UyapExpense`: Masraf bilgileri  
   - `UyapDocument`: Evrak bilgileri

3. **API Endpoint'leri**:
   - `POST /api/uyap/files`: Dosya arama
   - `GET /api/uyap/file/<id>/details`: Dosya detayları
   - `POST /api/uyap/import`: Dosya aktarımı
   - `POST /api/uyap/documents/download`: Evrak indirme

## Kurulum ve Kullanım

### Gereksinimler

1. **Python Kütüphaneleri**:
   ```bash
   pip install selenium beautifulsoup4 webdriver-manager
   ```

2. **Chrome Tarayıcı**: Selenium için gerekli

3. **UYAP Erişimi**: Avukat portalı e-imza ile giriş

### Kullanım Adımları

1. **Dosya Ekle** sayfasında **"UYAP'tan Aktar"** butonuna tıklayın
2. Açılan modalda filtreleri ayarlayın:
   - Yargı türü seçin (Ceza, Hukuk, İcra, vb.)
   - İsteğe bağlı olarak birim, durum, tarih aralığı belirleyin
   - **"Listele"** butonuna tıklayın

3. UYAP'a giriş yapın (e-imza gerekli)
4. Listelenen dosyalar arasından aktarmak istediklerinizi seçin
5. Sağ panelden aktarım ayarlarını yapılandırın:
   - Dahil edilecek içerik (temel bilgiler, taraflar, masraflar, evraklar)
   - Çakışma kuralları (atla, üzerine yaz, yeni oluştur)

6. **"Aktarmayı Başlat"** butonuna tıklayın
7. İlerleme durumunu takip edin ve tamamlandığında özet raporu görüntüleyin

## Özellik Detayları

### Aktarım Ayarları

#### Dahil Edilecek İçerik
- **Dosya Temel Bilgileri** (varsayılan: açık): Esas no, mahkeme, durum, açılış tarihi
- **Taraflar** (varsayılan: açık): Davacı, davalı, vekil bilgileri
- **Masraflar** (varsayılan: kapalı): Harçlar ve diğer masraflar
- **Evraklar** (varsayılan: kapalı): Dosya evrakları ve belgeleri

#### Çakışma Kuralları
- **Masraflar için**:
  - Atla: Mevcut masrafları değiştirmez
  - Üzerine yaz: Mevcut masrafları günceller
  - Yeni oluştur: Yeni masraf kayıtları oluşturur

- **Evraklar için**:
  - Atla: Aynı isimde evrak varsa indirmez
  - Sürümle: Dosya adına sürüm numarası ekler
  - Üzerine yaz: Mevcut dosyayı değiştirir

### Güvenlik Özellikleri

1. **Kullanıcı Kimlik Doğrulama**: Sadece giriş yapmış kullanıcılar erişebilir
2. **UYAP E-imza**: UYAP'a giriş için e-imza gerekli
3. **Veri Maskeleme**: Log'larda kişisel veriler maskelenir
4. **Dosya Kontrolü**: İndirilen evraklar tür ve boyut kontrolünden geçer

### Performans Optimizasyonu

1. **Batch İşlemler**: Birden fazla dosya aynı anda işlenebilir
2. **Progress Tracking**: Gerçek zamanlı ilerleme takibi
3. **Hata Toleransı**: Tek dosya hatası diğer dosyaları etkilemez
4. **Retry Mekanizması**: Başarısız işlemler otomatik tekrarlanır

## Test Senaryoları

### Temel Testler

1. **Dosya Arama Testi**:
   ```python
   python test_uyap_integration.py TestUYAPIntegration.test_api_endpoint_uyap_files
   ```

2. **Dosya Aktarım Testi**:
   ```python
   python test_uyap_integration.py TestUYAPIntegration.test_import_uyap_file_to_database_basic_info
   ```

3. **Taraf Bilgileri Testi**:
   ```python
   python test_uyap_integration.py TestUYAPIntegration.test_import_uyap_file_with_parties
   ```

### Kabul Testleri

#### Test 1: Ceza Dosyası Aktarımı
1. Yargı türü: "Ceza" seçin
2. En az 1 ceza dosyası bulunduğunu doğrulayın  
3. Dosyayı seçip aktarın
4. LawAutomation'da dosyanın doğru bilgilerle oluşturulduğunu kontrol edin

#### Test 2: Hukuk Dosyası Aktarımı  
1. Yargı türü: "Hukuk" seçin
2. En az 1 hukuk dosyası bulunduğunu doğrulayın
3. Taraflar ve masraflar dahil aktarın
4. Tüm bilgilerin doğru aktarıldığını kontrol edin

#### Test 3: Evrak İndirme
1. Evrak içeren bir dosya seçin
2. "Evraklar" seçeneğini aktif edin
3. Sadece PDF formatını seçin
4. Aktarım sonrası evrakların yerel depoda olduğunu kontrol edin

#### Test 4: İdempotent İşlem
1. Aynı dosyayı ikinci kez aktarmaya çalışın
2. "Üzerine yazma" seçili değilse uyarı alındığını kontrol edin
3. "Üzerine yazma" seçili ise güncellendiğini kontrol edin

## Sorun Giderme

### Sık Karşılaşılan Sorunlar

1. **UYAP'a Bağlanılamıyor**:
   - Chrome tarayıcısının güncel olduğundan emin olun
   - E-imza sertifikanızın geçerli olduğunu kontrol edin
   - Proxy/güvenlik duvarı ayarlarını kontrol edin

2. **Dosyalar Listelemiyor**:
   - Filtrelerin doğru ayarlandığından emin olun
   - UYAP'ta ilgili dosyaların bulunduğunu kontrol edin
   - Tarayıcı geliştirici konsolundaki hataları inceleyin

3. **Aktarım Başarısız**:
   - Log mesajlarını inceleyin
   - Veritabanı bağlantısını kontrol edin
   - Yetki kontrollerini gözden geçirin

### Debug Modu

Debug modunu aktifleştirmek için:
```python
import logging
logging.getLogger('uyap_integration_advanced').setLevel(logging.DEBUG)
```

## Geliştirme Notları

### Gelecek Geliştirmeler

1. **Toplu İşlemler**: Birden fazla dosyayı tek seferde aktarma
2. **Zamanlanmış Senkronizasyon**: Belirli aralıklarla otomatik güncelleme
3. **Gelişmiş Filtreleme**: Daha detaylı arama kriterleri
4. **Performans Optimizasyonu**: Daha hızlı veri çekme algoritmaları

### Teknik Borçlar

1. UYAP'ın DOM yapısı değişikliklerine karşı xpath'lerin güncellenmesi
2. Session management optimizasyonu
3. Daha kapsamlı error handling
4. Birim test kapsamının artırılması

## Katkıda Bulunma

1. Fork repository
2. Feature branch oluşturun: `git checkout -b feature/uyap-enhancement`
3. Değişikliklerinizi commit edin: `git commit -am 'Add UYAP enhancement'`
4. Branch'inizi push edin: `git push origin feature/uyap-enhancement`
5. Pull Request oluşturun

## Lisans ve Uyarılar

⚠️ **Önemli**: Bu sistem UYAP'ın resmi API'sini kullanmamaktadır. Web scraping tekniklerini kullandığı için UYAP'ın arayüz değişikliklerinden etkilenebilir.

⚠️ **Güvenlik**: E-imza bilgileri sistem tarafından saklanmaz. Her oturumda yeniden giriş gerekir.

⚠️ **Performans**: Çok sayıda dosya aktarımı UYAP sunucularını etkileyebilir. Makul kullanım sınırlarına uyun.

## İletişim

Sorularınız için: 
- GitHub Issues: Repository'deki issues bölümünü kullanın
- Email: [Sistem yöneticisi email adresi]

---

**Son Güncelleme**: 2024-01-20  
**Versiyon**: 1.0.0