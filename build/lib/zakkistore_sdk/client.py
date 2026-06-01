import requests

class ZakkiStore:
    def __init__(self, base_url="https://qris.zakki.store", token=None, iduser=None, email=None, pin=None, auto_withdraw=False):
        """
        Inisialisasi Zakkistore SDK Client untuk Python.
        
        :param base_url: URL API Server Zakki Store resmi (default: https://qris.zakki.store)
        :param token: Token API member Anda
        :param iduser: ID User member Anda (opsional, dibutuhkan untuk beberapa endpoint)
        :param email: Email member Anda (opsional, dapat digunakan sebagai alternatif iduser)
        :param pin: PIN transaksi member (opsional, dibutuhkan untuk tarik & tabung)
        :param auto_withdraw: Fitur auto-withdrawal saldo bank ke saldo aplikasi (default: False)
        """
        # Deteksi pintar jika user menaruh token di parameter pertama (karena base_url default ke official)
        if base_url and not (base_url.startswith("http://") or base_url.startswith("https://")) and token is None:
            token = base_url
            base_url = "https://qris.zakki.store"

        if not token:
            raise ValueError('token wajib disertakan dalam konfigurasi SDK.')
        if not base_url:
            raise ValueError('base_url wajib disertakan dalam konfigurasi SDK.')

        self.base_url = base_url.rstrip('/')
        self.token = token
        self.iduser = iduser
        self.email = email
        self.pin = pin
        self.is_auto_withdraw = bool(auto_withdraw)

    def _get_headers(self):
        return {"Content-Type": "application/json"}

    def _request(self, endpoint, method='GET', data=None):
        url = f"{self.base_url}{endpoint}"
        try:
            if data:
                if method.upper() == 'GET':
                    res = requests.get(url, params=data)
                else:
                    res = requests.post(url, json=data, headers=self._get_headers())
            else:
                if method.upper() == 'GET':
                    res = requests.get(url)
                else:
                    res = requests.post(url, headers=self._get_headers())

            res_json = res.json()

            # 🔥 SINKRONISASI PENANGANAN ERROR IP BLOCKED
            if not res.ok:
                err_msg = res_json.get("message", f"HTTP Error! Status: {res.status_code}")
                if res.status_code == 403 or "ip" in err_msg.lower():
                    err_msg += "\n⚠️ [IP BLOCKED / UNREGISTERED] IP Anda diblokir atau belum terdaftar di whitelist API. Silakan hubungi developer via WhatsApp (https://wa.me/6283844082339) atau Telegram (https://t.me/zakki_store) untuk mendapatkan bantuan."
                raise RuntimeError(f"[ZakkiStore SDK Error] {err_msg}")

            return res_json
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"[ZakkiStore SDK Error] Koneksi Gagal: {str(e)}")

    def enable_auto_withdraw(self, status):
        """Mengaktifkan atau menonaktifkan fitur Auto-Withdraw (Tarik Otomatis)"""
        self.is_auto_withdraw = bool(status)

    def enableAutoWithdraw(self, status):
        """Alias camelCase untuk kepatuhan platform Node.js"""
        self.enable_auto_withdraw(status)

    # ==========================================================
    # --- 1. PAYMENT GATEWAY (QRIS TOPUP) ---
    # ==========================================================

    def topup(self, nominal):
        """Membuat invoice QRIS Dinamis otomatis untuk topup saldo"""
        return self._request('/topup', 'POST', {
            "token": self.token,
            "nominal": int(nominal)
        })

    def cektopup(self, idtopup):
        """Memeriksa status pembayaran QRIS (SUCCESS/PENDING) berdasarkan ID topup"""
        return self._request('/cektopup', 'GET', {
            "idtopup": idtopup
        })

    def cancel(self, id_transaksi=None, all_pending=False):
        """
        Mengelola pembatalan transaksi pending (Mendukung 3 Mode Operasi)
        
        - Mode 1: Cek Daftar Pending (jika id_transaksi=None dan all_pending=False)
        - Mode 2: Membatalkan ID tertentu
        - Mode 3: Membatalkan massal (jika all_pending=True)
        """
        # Fleksibilitas Pintar: Jika parameter pertama dikirim sebagai boolean (true/false)
        if isinstance(id_transaksi, bool):
            all_pending = id_transaksi
            id_transaksi = None

        payload = {"token": self.token}
        if id_transaksi:
            payload["id_transaksi"] = id_transaksi
        if all_pending:
            payload["all"] = True
        return self._request('/cancel', 'POST', payload)

    # ==========================================================
    # --- 2. TRANSAKSI H2H (HOST-TO-HOST) ---
    # ==========================================================

    def listkode(self, jenis=None, product_type=None):
        """Membuka katalog kode produk aktif, deskripsi, dan harga termurah"""
        payload = {}
        if jenis:
            payload["jenis"] = jenis
        if product_type:
            payload["type"] = product_type
        return self._request('/listkode', 'GET', payload)

    def h2h(self, kode, tujuan=None, refID=None):
        """
        Mengirim order transaksi pembelian H2H.
        Mendukung pemanggilan positional arguments atau single dictionary (JS destructuring-style).
        """
        # Fleksibilitas Pintar: Mendukung pengiriman single dict mirip JS
        if isinstance(kode, dict):
            payload = kode
            kode = payload.get("kode")
            tujuan = payload.get("tujuan")
            refID = payload.get("refID")

        return self._request('/h2h', 'POST', {
            "token": self.token,
            "kode": kode,
            "tujuan": tujuan,
            "refID": refID
        })

    def cekh2h(self, id_trx):
        """Memeriksa status pengisian, serial number (SN), dan harga beli order H2H"""
        return self._request('/cekh2h', 'GET', {
            "id": id_trx
        })

    def myh2h(self):
        """Mengambil daftar 20 riwayat pembelian H2H terupdate milik Anda"""
        return self._request('/myh2h', 'GET', {
            "token": self.token
        })

    # ==========================================================
    # --- 3. PERBANKAN & TRANSFER SALDO ---
    # ==========================================================

    def checkbank(self):
        """
        Melihat sisa saldo bank VA, profil member, mutasi, dan memicu Auto-Withdraw.
        Jika Auto-Withdraw aktif, SDK akan otomatis memproses penarikan dan memuat data terupdate.
        """
        payload = {"token": self.token}
        if self.iduser:
            payload["iduser"] = self.iduser
        elif self.email:
            payload["email"] = self.email
            
        bank_res = self._request('/checkbank', 'GET', payload)
        
        # 🔥 ALUR AUTO-WITHDRAW 100% SINKRON DENGAN NODEJS
        if self.is_auto_withdraw and bank_res.get("data") and bank_res["data"].get("bank_detail"):
            bank_detail = bank_res["data"]["bank_detail"]
            balance = float(bank_detail.get("balance", 0))
            
            if balance > 0:
                try:
                    # Eksekusi fungsi penarikan otomatis
                    withdraw_res = self.tarik(int(balance))
                    
                    # Ambil kembali informasi bank terbaru setelah ditarik
                    bank_res = self._request('/checkbank', 'GET', payload)
                    
                    # Sematkan flag sukses auto-withdraw ke dalam respon data
                    bank_res["auto_withdraw_executed"] = True
                    bank_res["auto_withdraw_amount"] = int(balance)
                    bank_res["auto_withdraw_message"] = withdraw_res.get("message", "Auto-withdraw berhasil dijalankan.")
                except Exception as err:
                    # Sematkan flag gagal ke dalam respon data
                    bank_res["auto_withdraw_executed"] = False
                    bank_res["auto_withdraw_error"] = str(err)
                    
        return bank_res

    def checkname(self, number):
        """Memverifikasi nama pemilik nomor Virtual Account (VA) tujuan"""
        return self._request('/checkname', 'GET', {
            "number": String(number).trim() if hasattr(number, 'trim') else str(number).strip()
        })

    def transfer(self, to, amount=None):
        """
        Transfer saldo instan antar Virtual Account member Bank Zakki.
        Mendukung pemanggilan positional arguments atau single dictionary (JS destructuring-style).
        """
        if isinstance(to, dict):
            payload = to
            to = payload.get("to")
            amount = payload.get("amount")

        return self._request('/transfer', 'POST', {
            "token": self.token,
            "to": to,
            "amount": int(amount)
        })

    def tabung(self, jumlah):
        """Menabung / deposit saldo dari aplikasi zakki store ke Bank Zakki"""
        if not self.pin:
            raise RuntimeError("[ZakkiStore SDK Error] PIN transaksi diperlukan untuk melakukan transaksi tabung.")
        payload = {
            "token": self.token,
            "jumlah": int(jumlah),
            "pin": self.pin
        }
        if self.iduser:
            payload["iduser"] = self.iduser
        if self.email:
            payload["email"] = self.email
        return self._request('/tabung', 'POST', payload)

    def tarik(self, jumlah):
        """Menarik dana tabungan dari rekening Bank Zakki masuk kembali ke aplikasi"""
        if not self.pin:
            raise RuntimeError("[ZakkiStore SDK Error] PIN transaksi diperlukan untuk melakukan transaksi tarik.")
        payload = {
            "token": self.token,
            "jumlah": int(jumlah),
            "pin": self.pin
        }
        if self.iduser:
            payload["iduser"] = self.iduser
        if self.email:
            payload["email"] = self.email
        return self._request('/tarik', 'POST', payload)

    def checkmutasi(self, mutasi_type="all"):
        """Melihat riwayat mutasi Tarik/Tabung"""
        payload = {
            "token": self.token,
            "type": mutasi_type
        }
        if self.iduser:
            payload["iduser"] = self.iduser
        if self.email:
            payload["email"] = self.email
        return self._request('/checkmutasi', 'GET', payload)

    # ==========================================================
    # --- 4. NOKTEL MARKETPLACE (OTP VIRTUAL) ---
    # ==========================================================

    def noktelStok(self):
        """Cek persediaan stok nomor virtual ready siap dipesan"""
        return self._request('/noktel/stok', 'GET', {
            "token": self.token
        })

    def noktelBuy(self, category):
        """Membeli nomor virtual baru berdasarkan kategori"""
        return self._request('/noktel/buy', 'POST', {
            "token": self.token,
            "category": str(category).strip()
        })

    def noktelGetOtp(self, account_id):
        """Menarik kode OTP Telegram/layanan secara real-time"""
        return self._request('/noktel/getotp', 'GET', {
            "token": self.token,
            "account_id": str(account_id).strip()
        })

    def noktelCancel(self, invoice_id):
        """Membatalkan nomor virtual yang pending OTP & memicu auto-refund"""
        return self._request('/noktel/cancel', 'POST', {
            "token": self.token,
            "invoice_id": str(invoice_id).strip()
        })

    def noktelHistory(self):
        """Mengambil riwayat transaksi pembelian Noktel lengkap"""
        return self._request('/noktel/history', 'GET', {
            "token": self.token
        })

    # ==========================================================
    # --- 5. REWARD KOMPUTASI & UTILITY ---
    # ==========================================================

    def cekmining(self, idmining):
        """Melihat detail status transaksi mining koin spesifik berdasarkan ID"""
        if not idmining:
            raise ValueError('Parameter idmining wajib diisi.')
        return self._request('/cekmining', 'GET', {
            "idmining": str(idmining).strip()
        })

    def mymining(self):
        """Melihat riwayat reward komputasi mining koin SHA256 milik Anda"""
        return self._request('/mymining', 'GET', {
            "token": self.token
        })

    def mining_start(self):
        """Minta Tantangan (Challenge) Mining Baru"""
        return self._request('/mining/start', 'GET', {
            "token": self.token
        })

    def miningStart(self):
        """Alias camelCase untuk mining_start"""
        return self.mining_start()

    def mining_submit(self, nonce, signature):
        """Submit Jawaban Mining (Proof of Work)"""
        if nonce is None:
            raise ValueError('Parameter nonce wajib disertakan.')
        if not signature:
            raise ValueError('Parameter signature wajib disertakan.')
        return self._request('/mining/submit', 'POST', {
            "token": self.token,
            "nonce": nonce,
            "signature": signature
        })

    def miningSubmit(self, nonce, signature):
        """Alias camelCase untuk mining_submit"""
        return self.mining_submit(nonce, signature)

    def cekgacha(self):
        """Memeriksa statistik poin, keuntungan, dan kemenangan gacha member"""
        return self._request('/cekgacha', 'GET', {
            "token": self.token
        })

    def whitelistip(self, ip):
        """Mendaftarkan IP host server Anda untuk otorisasi API H2H"""
        return self._request('/whitelistip', 'POST', {
            "token": self.token,
            "ip": str(ip).strip()
        })

    def delwhitelistip(self, ip):
        """Menghapus alamat IP server dari whitelist otorisasi Anda"""
        return self._request('/delwhitelistip', 'POST', {
            "token": self.token,
            "ip": str(ip).strip()
        })

    def leaderboard(self, limit=10, period="all"):
        """Mendapatkan data peringkat sultan topup member teraktif"""
        return self._request('/leaderboard', 'GET', {
            "limit": int(limit),
            "period": str(period).strip()
        })

    def status(self):
        """Memantau kondisi kesehatan mesin, metrik financial, dan load CPU"""
        return self._request('/status', 'GET')

    # ==========================================================
    # --- 6. METODE INTEGRASI BARU ---
    # ==========================================================

    def set_callback(self, site):
        """Mendaftarkan URL callback HTTPS untuk menerima notifikasi otomatis"""
        return self._request('/setcallback', 'GET', {
            "token": self.token,
            "site": str(site).strip()
        })

    def setcallback(self, site):
        """Alias camelCase untuk set_callback"""
        return self.set_callback(site)

    def del_callback(self):
        """Menghapus URL callback yang terdaftar"""
        return self._request('/delcallback', 'GET', {
            "token": self.token
        })

    def delcallback(self):
        """Alias camelCase untuk del_callback"""
        return self.del_callback()

    def set_notif_bot(self, telegram_id):
        """Mendaftarkan ID Telegram untuk menerima laporan otomatis transaksi"""
        return self._request('/setnotifbot', 'GET', {
            "token": self.token,
            "id": str(telegram_id).strip()
        })

    def setnotifbot(self, telegram_id):
        """Alias camelCase untuk set_notif_bot"""
        return self.set_notif_bot(telegram_id)

    def del_notif_bot(self):
        """Menghapus ID Telegram yang terdaftar untuk notifikasi"""
        return self._request('/delnotifbot', 'GET', {
            "token": self.token
        })

    def delnotifbot(self):
        """Alias camelCase untuk del_notif_bot"""
        return self.del_notif_bot()

    def check_transfer(self, idtransfer):
        """Memverifikasi status transfer saldo antar member berdasarkan ID"""
        return self._request('/checktransfer', 'GET', {
            "idtransfer": str(idtransfer).strip()
        })

    def checktransfer(self, idtransfer):
        """Alias camelCase untuk check_transfer"""
        return self.check_transfer(idtransfer)

    def my_transfer(self, transfer_type="all"):
        """Melihat riwayat transfer saldo masuk/keluar"""
        return self._request('/mytransfer', 'GET', {
            "token": self.token,
            "type": str(transfer_type).strip()
        })

    def mytransfer(self, transfer_type="all"):
        """Alias camelCase untuk my_transfer"""
        return self.my_transfer(transfer_type)

    def my_topup(self):
        """Mengambil daftar riwayat topup sukses"""
        return self._request('/mytopup', 'GET', {
            "token": self.token
        })

    def mytopup(self):
        """Alias camelCase untuk my_topup"""
        return self.my_topup()

    def cek_my_ip(self):
        """Mengecek IP publik server Anda yang terdeteksi gateway"""
        return self._request('/cekmyip', 'GET')

    def cekmyip(self):
        """Alias camelCase untuk cek_my_ip"""
        return self.cek_my_ip()

    def cek_ip(self, ip):
        """Mengecek status keamanan IP spesifik"""
        return self._request('/cekip', 'GET', {
            "ip": str(ip).strip()
        })

    def cekip(self, ip):
        """Alias camelCase untuk cek_ip"""
        return self.cek_ip(ip)
