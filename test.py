import sys
import os

# Tambahkan direktori saat ini ke sys.path untuk test import lokal
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from zakkistore_sdk import ZakkiStore

def test_sdk_initialization():
    print("🧪 Menjalankan uji coba inisialisasi SDK Python...")
    try:
        # Inisialisasi mock client
        zakki = ZakkiStore(
            token="mock_token_123",
            iduser="mock_user_IBO99",
            pin="123456",
            base_url="https://qris.zakki.store",
            auto_withdraw=False # Nonaktifkan untuk testing lokal mock
        )
        print("✅ Inisialisasi ZakkiStore Client berhasil!")
        
        # Cek properti dasar
        assert zakki.token == "mock_token_123"
        assert zakki.iduser == "mock_user_IBO99"
        assert zakki.pin == "123456"
        assert zakki.base_url == "https://qris.zakki.store"
        assert zakki.is_auto_withdraw is False
        print("✅ Seluruh validasi properti dasar berhasil!")
        
        # Validasi eksistensi metode utama
        methods = [
            "topup", "cektopup", "cancel",
            "listkode", "h2h", "cekh2h", "myh2h",
            "checkbank", "checkname", "transfer", "tabung", "tarik", "checkmutasi",
            "noktelStok", "noktelBuy", "noktelGetOtp", "noktelCancel", "noktelHistory",
            "cekmining", "mymining", "cekgacha",
            "whitelistip", "delwhitelistip", "leaderboard", "status"
        ]
        
        print("\n🔍 Memverifikasi eksistensi 25 Native Methods...")
        for method in methods:
            if hasattr(zakki, method) and callable(getattr(zakki, method)):
                print(f"  [OK] Metode '{method}' terdeteksi dan aktif.")
            else:
                print(f"  [FAIL] Metode '{method}' tidak terdeteksi atau tidak callable!")
                raise AttributeError(f"Metode '{method}' tidak lengkap!")
                
        print("\n🏆 Uji Coba Kepatuhan Metode & Struktur Sukses 100%!")
        print("SDK Python siap dipublikasikan dan digunakan secara luas!")
        
    except Exception as e:
        print(f"❌ Uji coba gagal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_sdk_initialization()
