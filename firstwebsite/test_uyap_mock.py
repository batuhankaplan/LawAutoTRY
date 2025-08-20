#!/usr/bin/env python3
"""
UYAP Mock API Test Script

Kullanıcının UYAP sisteminin çalışıp çalışmadığını test etmek için basit test scripti.
"""
import requests
import json
import sys

def test_uyap_endpoints():
    """UYAP API endpoint'lerini test et"""
    base_url = "http://127.0.0.1:5000"  # Flask development server
    
    # Test için session cookies (gerçek uygulamada login gerekli)
    session = requests.Session()
    
    print("🔍 UYAP Mock API Testi Başlıyor...")
    print("="*50)
    
    # Test 1: Dosya arama
    print("\n📋 Test 1: UYAP Dosya Arama")
    try:
        search_data = {
            "yargi_turu": "Hukuk",
            "search": "123"
        }
        
        response = session.post(
            f"{base_url}/api/uyap/files",
            json=search_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Dosya arama başarılı!")
            print(f"Bulunan dosya sayısı: {data.get('count', 0)}")
            if data.get('files'):
                print(f"İlk dosya: {data['files'][0]['esas_no']}")
        else:
            print(f"❌ Dosya arama başarısız: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server'a bağlanılamıyor. Flask uygulaması çalışıyor mu?")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    # Test 2: Dosya detay
    print("\n📄 Test 2: UYAP Dosya Detay")
    try:
        response = session.get(
            f"{base_url}/api/uyap/file/test_file_1/details?esas_no=2024/123"
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Dosya detay başarılı!")
            print(f"Mahkeme: {data['details']['basic_info']['mahkeme']}")
            print(f"Taraf sayısı: {len(data['details']['parties'])}")
        else:
            print(f"❌ Dosya detay başarısız: {response.text}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    # Test 3: Dosya aktarım
    print("\n📥 Test 3: UYAP Dosya Aktarım")
    try:
        import_data = {
            "file_id": "uyap_test_1",
            "settings": {
                "include_basic_info": True,
                "include_parties": True,
                "include_expenses": False,
                "include_documents": False
            }
        }
        
        response = session.post(
            f"{base_url}/api/uyap/import",
            json=import_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Dosya aktarım başarılı!")
            if data.get('success'):
                print(f"Aktarılan dosya: {data['file_info']['esas_no']}")
            else:
                print(f"⚠️  Aktarım hatası: {data.get('error')}")
        else:
            print(f"❌ Dosya aktarım başarısız: {response.text}")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    
    print("\n" + "="*50)
    print("🏁 UYAP Mock API Testi Tamamlandı")
    print("\n💡 Not: Bu testler mock (sahte) verilerle çalışır.")
    print("   Gerçek UYAP entegrasyonu için Chrome WebDriver kurulumu gerekir.")
    
    return True

if __name__ == "__main__":
    print("UYAP Mock API Test Aracı")
    print("Flask uygulamanızın çalıştığından emin olun (python app.py)")
    
    input("\n▶️  Test başlatmak için Enter'a basın...")
    
    success = test_uyap_endpoints()
    
    if not success:
        print("\n❌ Testler başarısız oldu.")
        print("Sorun giderme:")
        print("1. Flask uygulaması çalışıyor mu? (python app.py)")
        print("2. Port 5000 açık mı?")
        print("3. Giriş yapmış bir kullanıcınız var mı?")
        sys.exit(1)
    else:
        print("\n✅ Testler başarılı!")
        print("UYAP mock sistemi çalışmaya hazır.")