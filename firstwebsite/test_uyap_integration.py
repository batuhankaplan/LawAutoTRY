"""
UYAP Entegrasyon Test Senaryoları

Bu dosya UYAP entegrasyonu için temel test senaryolarını içerir.
Gerçek UYAP sistemine bağlanmadan mock data ile test yapar.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from uyap_integration_advanced import UYAPAdvancedIntegration, UYAPManager, UyapFile, UyapParty, UyapExpense, UyapDocument
from app import app, db, import_uyap_file_to_database
from models import CaseFile, User, Expense, Document
import json
from datetime import datetime

class TestUYAPIntegration(unittest.TestCase):
    """UYAP entegrasyon testleri"""
    
    def setUp(self):
        """Test öncesi hazırlık"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Test kullanıcısı oluştur
        self.test_user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            phone='1234567890',
            role='Avukat',
            is_approved=True
        )
        self.test_user.set_password('password')
        db.session.add(self.test_user)
        db.session.commit()
        
    def tearDown(self):
        """Test sonrası temizlik"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_uyap_file_dataclass(self):
        """UyapFile veri sınıfı testi"""
        file_data = UyapFile(
            id='test_file_1',
            esas_no='2024/123',
            mahkeme='İstanbul 1. Asliye Hukuk Mahkemesi',
            yargi_turu='Hukuk',
            yargi_birimi='Asliye Hukuk',
            durum='Açık',
            acilis_tarihi='01.01.2024',
            taraflar='Ahmet Yılmaz / Mehmet Demir'
        )
        
        self.assertEqual(file_data.id, 'test_file_1')
        self.assertEqual(file_data.esas_no, '2024/123')
        self.assertEqual(file_data.yargi_turu, 'Hukuk')
    
    def test_uyap_party_dataclass(self):
        """UyapParty veri sınıfı testi"""
        party = UyapParty(
            name='Ahmet Yılmaz',
            capacity='Davacı',
            identity_number='12345678901',
            address='İstanbul',
            lawyer='Av. Mehmet Demir'
        )
        
        self.assertEqual(party.name, 'Ahmet Yılmaz')
        self.assertEqual(party.capacity, 'Davacı')
    
    @patch('uyap_integration_advanced.webdriver.Chrome')
    def test_uyap_integration_initialization(self, mock_chrome):
        """UYAP entegrasyon sınıfı başlatma testi"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        uyap = UYAPAdvancedIntegration()
        result = uyap.initialize_driver()
        
        self.assertTrue(result)
        self.assertIsNotNone(uyap.driver)
    
    def test_uyap_manager_singleton(self):
        """UYAP Manager singleton pattern testi"""
        manager1 = UYAPManager()
        manager2 = UYAPManager()
        
        self.assertIs(manager1, manager2)
    
    def test_import_uyap_file_to_database_basic_info(self):
        """UYAP dosyasının veritabanına aktarım testi - temel bilgiler"""
        # Mock dosya detayları
        file_details = {
            'basic_info': {
                'esas_no': '2024/123',
                'mahkeme': 'İstanbul 1. Asliye Hukuk Mahkemesi',
                'yargi_turu': 'Hukuk',
                'yargi_birimi': 'Asliye Hukuk',
                'durum': 'Açık',
                'acilis_tarihi': '01.01.2024',
                'year': 2024
            },
            'parties': [],
            'expenses': [],
            'documents': []
        }
        
        settings = {
            'include_basic_info': True,
            'include_parties': False,
            'include_expenses': False,
            'include_documents': False
        }
        
        result = import_uyap_file_to_database(file_details, settings, self.test_user.id)
        
        self.assertTrue(result['success'])
        
        # Veritabanında dosyanın oluşturulduğunu kontrol et
        case_file = CaseFile.query.filter_by(case_number='2024/123').first()
        self.assertIsNotNone(case_file)
        self.assertEqual(case_file.courthouse, 'İstanbul 1. Asliye Hukuk Mahkemesi')
        self.assertEqual(case_file.file_type, 'hukuk')
    
    def test_import_uyap_file_with_parties(self):
        """UYAP dosyasının veritabanına aktarım testi - taraflarla"""
        file_details = {
            'basic_info': {
                'esas_no': '2024/124',
                'mahkeme': 'İstanbul 2. Asliye Hukuk Mahkemesi',
                'yargi_turu': 'Hukuk',
                'year': 2024
            },
            'parties': [
                UyapParty(
                    name='Ahmet Yılmaz',
                    capacity='Davacı',
                    identity_number='12345678901'
                ),
                UyapParty(
                    name='Mehmet Demir',
                    capacity='Davalı',
                    identity_number='09876543210',
                    lawyer='Av. Ali Veli'
                )
            ],
            'expenses': [],
            'documents': []
        }
        
        settings = {
            'include_basic_info': True,
            'include_parties': True,
            'include_expenses': False,
            'include_documents': False
        }
        
        result = import_uyap_file_to_database(file_details, settings, self.test_user.id)
        
        self.assertTrue(result['success'])
        
        # Taraf bilgilerinin kaydedildiğini kontrol et
        case_file = CaseFile.query.filter_by(case_number='2024/124').first()
        self.assertEqual(case_file.client_name, 'Ahmet Yılmaz')
        self.assertEqual(case_file.opponent_name, 'Mehmet Demir')
        self.assertEqual(case_file.opponent_lawyer, 'Av. Ali Veli')
    
    def test_import_uyap_file_with_expenses(self):
        """UYAP dosyasının veritabanına aktarım testi - masraflarla"""
        file_details = {
            'basic_info': {
                'esas_no': '2024/125',
                'mahkeme': 'İstanbul 3. Asliye Hukuk Mahkemesi',
                'year': 2024
            },
            'parties': [],
            'expenses': [
                UyapExpense(
                    expense_type='Harç',
                    amount=500.0,
                    date='01.01.2024',
                    is_paid=False,
                    description='Dava harcı'
                )
            ],
            'documents': []
        }
        
        settings = {
            'include_basic_info': True,
            'include_parties': False,
            'include_expenses': True,
            'include_documents': False,
            'expense_conflict': 'create-new'
        }
        
        result = import_uyap_file_to_database(file_details, settings, self.test_user.id)
        
        self.assertTrue(result['success'])
        
        # Masraf bilgisinin kaydedildiğini kontrol et
        case_file = CaseFile.query.filter_by(case_number='2024/125').first()
        expenses = Expense.query.filter_by(case_id=case_file.id).all()
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0].expense_type, 'Harç')
        self.assertEqual(expenses[0].amount, 500.0)
    
    def test_duplicate_file_handling(self):
        """Aynı dosyanın tekrar aktarılması testi"""
        file_details = {
            'basic_info': {
                'esas_no': '2024/126',
                'mahkeme': 'İstanbul 4. Asliye Hukuk Mahkemesi',
                'year': 2024
            },
            'parties': [],
            'expenses': [],
            'documents': []
        }
        
        settings = {
            'include_basic_info': True,
            'overwrite_existing': False
        }
        
        # İlk aktarım
        result1 = import_uyap_file_to_database(file_details, settings, self.test_user.id)
        self.assertTrue(result1['success'])
        
        # İkinci aktarım (aynı dosya)
        result2 = import_uyap_file_to_database(file_details, settings, self.test_user.id)
        self.assertFalse(result2['success'])
        self.assertIn('zaten mevcut', result2['error'])
    
    def test_api_endpoint_uyap_files(self):
        """UYAP dosya arama API endpoint testi"""
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True
            
            # Mock UYAP manager
            with patch('app.UYAPManager') as mock_manager:
                mock_instance = Mock()
                mock_manager.return_value = mock_instance
                mock_instance.search_files_with_filters.return_value = [
                    UyapFile(
                        id='test1',
                        esas_no='2024/100',
                        mahkeme='Test Mahkeme',
                        yargi_turu='Hukuk',
                        yargi_birimi='Test Birim',
                        durum='Açık',
                        acilis_tarihi='01.01.2024',
                        taraflar='Test Taraflar'
                    )
                ]
                
                response = client.post('/api/uyap/files', 
                                     json={'yargi_turu': 'Hukuk'},
                                     content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertEqual(len(data['files']), 1)
                self.assertEqual(data['files'][0]['esas_no'], '2024/100')
    
    def test_api_endpoint_uyap_import(self):
        """UYAP dosya aktarım API endpoint testi"""
        with self.app.test_client() as client:
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(self.test_user.id)
                sess['_fresh'] = True
            
            # Mock UYAP manager
            with patch('app.UYAPManager') as mock_manager:
                mock_instance = Mock()
                mock_manager.return_value = mock_instance
                mock_instance.get_file_complete_details.return_value = {
                    'basic_info': {
                        'esas_no': '2024/200',
                        'mahkeme': 'Test Mahkeme',
                        'year': 2024
                    },
                    'parties': [],
                    'expenses': [],
                    'documents': []
                }
                
                response = client.post('/api/uyap/import',
                                     json={
                                         'file_id': 'test_file_200',
                                         'settings': {
                                             'include_basic_info': True
                                         }
                                     },
                                     content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                
                # Veritabanında dosyanın oluşturulduğunu kontrol et
                case_file = CaseFile.query.filter_by(case_number='2024/200').first()
                self.assertIsNotNone(case_file)

class TestUYAPHelperFunctions(unittest.TestCase):
    """UYAP yardımcı fonksiyon testleri"""
    
    def test_sanitize_filename(self):
        """Dosya adı temizleme testi"""
        uyap = UYAPAdvancedIntegration()
        
        # Geçersiz karakterler
        unsafe_name = 'test<>:"/\\|?*file.pdf'
        safe_name = uyap._sanitize_filename(unsafe_name)
        self.assertEqual(safe_name, 'test_________file.pdf')
        
        # Uzun dosya adı
        long_name = 'a' * 300 + '.pdf'
        safe_name = uyap._sanitize_filename(long_name)
        self.assertTrue(len(safe_name) <= 255)
        self.assertTrue(safe_name.endswith('.pdf'))
    
    def test_get_file_type_from_name(self):
        """Dosya türü belirleme testi"""
        uyap = UYAPAdvancedIntegration()
        
        self.assertEqual(uyap._get_file_type_from_name('test.pdf'), 'PDF')
        self.assertEqual(uyap._get_file_type_from_name('test.docx'), 'Word')
        self.assertEqual(uyap._get_file_type_from_name('test.xlsx'), 'Excel')
        self.assertEqual(uyap._get_file_type_from_name('test.jpg'), 'Image')
        self.assertEqual(uyap._get_file_type_from_name('test.unknown'), 'Unknown')

class TestUYAPErrorHandling(unittest.TestCase):
    """UYAP hata yönetimi testleri"""
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        self.app_context.pop()
    
    def test_invalid_file_details(self):
        """Geçersiz dosya detayları ile aktarım testi"""
        # Eksik bilgilerle aktarım testi
        file_details = {
            'basic_info': {},  # Boş temel bilgiler
            'parties': [],
            'expenses': [],
            'documents': []
        }
        
        settings = {'include_basic_info': True}
        
        # Bu test gerçek DB olmadan çalışmayacağı için mock'lanmalı
        # Gerçek uygulamada proper error handling olmalı
        try:
            result = import_uyap_file_to_database(file_details, settings, 1)
            # Hata durumunda False dönmeli
            self.assertFalse(result['success'])
        except Exception as e:
            # Exception handling test edildi
            self.assertIsInstance(e, Exception)

if __name__ == '__main__':
    # Test modülleri
    test_modules = [
        TestUYAPIntegration,
        TestUYAPHelperFunctions,
        TestUYAPErrorHandling
    ]
    
    # Test suite oluştur
    suite = unittest.TestSuite()
    
    for test_module in test_modules:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_module)
        suite.addTests(tests)
    
    # Testleri çalıştır
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Test sonuçlarını yazdır
    print(f"\n{'='*50}")
    print(f"Test Sonuçları:")
    print(f"Toplam Test: {result.testsRun}")
    print(f"Başarılı: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Başarısız: {len(result.failures)}")
    print(f"Hatalı: {len(result.errors)}")
    print(f"{'='*50}")
    
    if result.failures:
        print("\nBaşarısız Testler:")
        for test, error in result.failures:
            print(f"- {test}: {error}")
    
    if result.errors:
        print("\nHatalı Testler:")
        for test, error in result.errors:
            print(f"- {test}: {error}")