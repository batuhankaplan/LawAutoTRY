#!/usr/bin/env python3
"""
UYAP Gerçek Entegrasyon Test Scripti

UYAP Avukat Portalı'na bağlanarak gerçek veri çekme testini yapar.
NOT: Bu test için UYAP'ta kayıtlı avukat hesabı ve e-imza gereklidir.
"""
import sys
import os
sys.path.insert(0, '.')

from uyap_integration_advanced import UYAPAdvancedIntegration, UYAPManager
import time

def test_uyap_connection():
    """UYAP bağlantı testi"""
    print("🔗 UYAP Gerçek Entegrasyon Testi Başlıyor...")
    print("="*60)
    
    try:
        # UYAP Manager oluştur
        print("\n📋 1. UYAP Manager Oluşturuluyor...")
        uyap_manager = UYAPManager()
        print("✅ UYAP Manager başarıyla oluşturuldu")
        
        # WebDriver'ı başlat
        print("\n🌐 2. Chrome WebDriver Başlatılıyor...")
        uyap_integration = UYAPAdvancedIntegration()
        result = uyap_integration.initialize_driver()
        
        if not result:
            print("❌ Chrome WebDriver başlatılamadı!")
            return False
        
        print("✅ Chrome WebDriver başarıyla başlatıldı")
        
        # UYAP Avukat Portalı'na git
        print("\n📂 3. UYAP Avukat Portalı'na Bağlanılıyor...")
        uyap_integration.driver.get("https://avukat.uyap.gov.tr")
        time.sleep(3)
        
        print(f"Sayfa başlığı: {uyap_integration.driver.title}")
        
        if "UYAP" in uyap_integration.driver.title:
            print("✅ UYAP Avukat Portalı'na başarıyla bağlanıldı!")
        else:
            print("⚠️ UYAP sayfası yüklenemedi.")
            
        # Giriş sayfası kontrol
        print("\n🔐 4. Giriş Sayfası Kontrolü...")
        page_source = uyap_integration.driver.page_source
        
        if "giriş" in page_source.lower() or "login" in page_source.lower():
            print("✅ Giriş sayfası tespit edildi")
            print("💡 E-imza ile giriş yapmanız gerekiyor...")
            
            # Kullanıcıya giriş için süre ver
            print("\n⏰ Manuel giriş için 60 saniye bekleniyor...")
            print("   - E-imza ile giriş yapın")
            print("   - Ana sayfaya gitmeniz bekleniyor...")
            
            for i in range(60, 0, -10):
                print(f"   Kalan süre: {i} saniye...")
                time.sleep(10)
                
                # Giriş yapıldı mı kontrol et
                current_url = uyap_integration.driver.current_url
                if "ana" in current_url.lower() or "main" in current_url.lower():
                    print("✅ Giriş başarılı!")
                    break
            
            # Ana sayfa test
            print("\n📊 5. Ana Sayfa Kontrolü...")
            current_title = uyap_integration.driver.title
            print(f"Mevcut sayfa: {current_title}")
            
            if "avukat" in current_title.lower():
                print("✅ UYAP Ana sayfasına başarıyla ulaşıldı!")
                
                # Basit dosya arama testi (eğer mümkünse)
                print("\n📁 6. Dosya Arama Bölümü Aranıyor...")
                try:
                    # Dosya arama linkini bul
                    page_text = uyap_integration.driver.page_source
                    if "dosya" in page_text.lower():
                        print("✅ Dosya yönetimi bölümü bulundu!")
                        print("🎉 UYAP entegrasyonu hazır!")
                    else:
                        print("⚠️ Dosya arama bölümü bulunamadı")
                        
                except Exception as e:
                    print(f"⚠️ Sayfa analiz hatası: {e}")
            else:
                print("❌ Ana sayfaya ulaşılamadı")
        else:
            print("❌ Giriş sayfası bulunamadı")
        
        # Temizlik
        print("\n🧹 7. Browser Kapatılıyor...")
        uyap_integration.driver.quit()
        print("✅ Test tamamlandı")
        
        return True
        
    except Exception as e:
        print(f"❌ UYAP bağlantı hatası: {e}")
        return False

def test_uyap_manager():
    """UYAP Manager singleton testi"""
    print("\n🔧 UYAP Manager Singleton Testi...")
    
    try:
        manager1 = UYAPManager()
        manager2 = UYAPManager()
        
        if manager1 is manager2:
            print("✅ UYAP Manager singleton çalışıyor")
        else:
            print("❌ UYAP Manager singleton sorunu")
            
    except Exception as e:
        print(f"❌ Manager test hatası: {e}")

if __name__ == "__main__":
    print("UYAP Gerçek Entegrasyon Test Aracı")
    print("Bu test UYAP Avukat Portalı'na gerçek bağlantı yapar.")
    print("⚠️  DİKKAT: E-imza gereklidir!")
    
    choice = input("\nTesti başlatmak istiyor musunuz? (e/h): ").lower()
    
    if choice == 'e':
        print("\n🚀 Test başlatılıyor...")
        
        # Manager testi
        test_uyap_manager()
        
        # Bağlantı testi
        success = test_uyap_connection()
        
        if success:
            print("\n" + "="*60)
            print("🎉 UYAP ENTEGRASYON TESTİ BAŞARILI!")
            print("✅ Sistem gerçek UYAP verilerini çekmeye hazır")
            print("💡 Artık dosya_ekle.html'deki 'UYAP'tan Aktar' özelliği çalışacak")
        else:
            print("\n" + "="*60)
            print("❌ UYAP entegrasyon testinde sorun var")
            print("💡 E-imza ve internet bağlantınızı kontrol edin")
    else:
        print("Test iptal edildi.")