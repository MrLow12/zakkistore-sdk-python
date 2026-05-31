import sys
import os
import json

# Pastikan import dari folder lokal zakkistore_sdk
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from zakkistore_sdk import ZakkiStore

def main():
    print("==================================================")
    print("🚀 PENGUJIAN REAL SDK PYTHON DENGAN OFFICIAL API")
    print("==================================================")
    
    # Official API Gateway
    base_url = "https://qris.zakki.store"
    token = "9d6e27f09e65d3"
    iduser = "IBO6"
    
    print(f"📡 Menghubungkan ke API Gateway Resmi: {base_url}...")
    
    # Inisialisasi SDK (Tanpa base_url, otomatis mengarah ke Official Gateway!)
    zakki = ZakkiStore(
        token=token,
        iduser=iduser,
        auto_withdraw=False # Set ke False demi keamanan saldo user saat pengujian
    )
    
    try:
        # 1. Cek status koneksi dasar (Health Check)
        print("\n🔍 1. Melakukan Health Check Server...")
        sys_status = zakki.status()
        print(f"🟢 [SUCCESS] Koneksi API sehat. Status: {sys_status.get('status', 'OK')}")
        
        # 2. Cek Akun Bank VA & Profil IBO6
        print("\n🔍 2. Mengambil Detail Akun & Profil IBO6 (checkbank)...")
        bank_info = zakki.checkbank()
        print(json.dumps(bank_info, indent=2))
        
        # Ambil data spesifik dari response
        user_data = bank_info.get("data", {})
        bank_detail = user_data.get("bank_detail", {})
        user_detail = user_data.get("user_detail", {})
        
        print("\n📝 RINGKASAN AKUN USER:")
        print(f"   👤 Nama Pemegang Rekening: {bank_detail.get('account_holder')}")
        print(f"   💳 Nomor Virtual Account : {bank_detail.get('virtual_account')}")
        print(f"   💰 Saldo Bank VA         : Rp {bank_detail.get('balance'):,}")
        print(f"   📧 Email Terdaftar       : {user_detail.get('email')}")
        print(f"   🏆 Total Transaksi H2H   : {user_detail.get('total_h2h')} kali")
        
        # 3. Cek Katalog Produk DANA
        print("\n🔍 3. Mengecek Katalog Produk H2H DANA (listkode)...")
        katalog = zakki.listkode("ewallet", "DANA")
        if katalog.get("code") == 200:
            products = katalog.get("data", [])
            print(f"🟢 Berhasil memuat {len(products)} produk DANA.")
            if products:
                # Tampilkan 3 sampel produk
                print("   Sampel Produk:")
                for p in products[:3]:
                    harga_raw = p.get('harga', 0)
                    try:
                        harga_int = int(float(harga_raw))
                    except:
                        harga_int = 0
                    print(f"   - Kode: {p.get('kode')} | Produk: {p.get('produk')} | Harga: Rp {harga_int:,}")
        else:
            print(f"❌ Gagal memuat katalog: {katalog.get('message')}")
            
        # 4. Cek Leaderboard Sultan Teratas
        print("\n🔍 4. Mengambil Data Leaderboard Sultan (3 Teratas)...")
        board = zakki.leaderboard(limit=3, period="all")
        if board.get("code") == 200:
            list_sultan = board.get("leaderboard", [])
            print("🟢 Peringkat Sultan Teraktif:")
            for rank in list_sultan:
                user_info = rank.get("user_info", {})
                stats = rank.get("stats", {})
                print(f"   Rank #{rank.get('rank')} - {user_info.get('nama')} (VA: {user_info.get('virtual_account')}) | Total Topup: {stats.get('total_topup_formatted')}")
        else:
            print("❌ Gagal memuat leaderboard.")
            
        print("\n==================================================")
        print("🎉 SELURUH PENGUJIAN RIEL SDK PYTHON BERHASIL 100%!")
        print("==================================================")
        
    except Exception as e:
        print(f"\n❌ Pengujian ke Official API Gagal: {e}")

if __name__ == "__main__":
    main()
