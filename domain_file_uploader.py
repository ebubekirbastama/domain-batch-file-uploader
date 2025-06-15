import os
import threading
import paramiko
import tkinter as tk
from tkinter import filedialog, messagebox, Text
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Entry, Button, Label, Progressbar, Frame

class DosyaYukleyiciApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Toplu Dosya Yükleyici - Domain Bazlı")
        self.root.geometry("720x600")

        style = Style("darkly")

        self.file_path = tk.StringVar()
        self.host = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.base_path = tk.StringVar()

        self.build_gui()

    def build_gui(self):
        padding = {"padx": 10, "pady": 5}

        frame = Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        Label(frame, text="🌐 Sunucu IP / Host:").grid(row=0, column=0, sticky="e", **padding)
        Entry(frame, textvariable=self.host, width=40).grid(row=0, column=1, **padding)

        Label(frame, text="👤 Kullanıcı Adı:").grid(row=1, column=0, sticky="e", **padding)
        Entry(frame, textvariable=self.username, width=40).grid(row=1, column=1, **padding)

        Label(frame, text="🔒 Parola:").grid(row=2, column=0, sticky="e", **padding)
        Entry(frame, textvariable=self.password, show="*", width=40).grid(row=2, column=1, **padding)

        Label(frame, text="📁 Ana Klasör Yolu (Örn: /var/www/vhosts/):").grid(row=3, column=0, sticky="e", **padding)
        # base_path Entry widget'ı sağ tık menüsü için ayrı tutuyoruz
        self.base_path_entry = Entry(frame, textvariable=self.base_path, width=40)
        self.base_path_entry.grid(row=3, column=1, **padding)
        self.base_path_entry.bind("<Button-3>", self.show_context_menu)  # Sağ tık menüsü (Windows/Linux)
        # Mac için dilersen aşağıdakini açabilirsin
        # self.base_path_entry.bind("<Control-Button-1>", self.show_context_menu)

        # Sağ tık context menüsü
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Domainleri Otomatik Yükle", command=self.otomatik_domain_yukle)

        Label(frame, text="📄 Domainler (her satıra bir domain):").grid(row=4, column=0, sticky="ne", **padding)
        self.domain_text = Text(frame, width=40, height=10, background="#2d2d2d", fg="#f8f8f2", insertbackground="white")
        self.domain_text.grid(row=4, column=1, sticky="w", **padding)

        Label(frame, text="📤 Yüklenecek Dosya:").grid(row=5, column=0, sticky="e", **padding)
        Entry(frame, textvariable=self.file_path, width=30).grid(row=5, column=1, sticky="w", **padding)
        Button(frame, text="📂 Dosya Seç", bootstyle="info", command=self.select_file).grid(row=5, column=1, sticky="e", **padding)

        Button(frame, text="🚀 Yüklemeye Başla", bootstyle="success", command=self.baslat).grid(row=6, column=1, sticky="e", pady=15)

        self.progress = Progressbar(self.root, bootstyle="info", length=600)
        self.progress.pack(pady=5)

        Label(self.root, text="📝 İşlem Günlüğü:").pack(anchor="w", padx=10)
        self.log_area = Text(self.root, height=12, background="#2d2d2d", fg="#f8f8f2", insertbackground="white")
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def otomatik_domain_yukle(self):
        base_path = self.base_path.get().strip()
        if not base_path:
            messagebox.showerror("Hata", "Öncelikle Ana Klasör Yolu ve Sunucu bilgilerini girin.")
            return
        host = self.host.get().strip()
        username = self.username.get().strip()
        password = self.password.get().strip()
        if not all([host, username, password]):
            messagebox.showerror("Hata", "Sunucu IP, kullanıcı adı ve parola alanları boş olamaz.")
            return
    
        try:
            self.logla(f"🔗 Sunucuya bağlanılıyor: {host}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, port=228, username=username, password=password)
    
            # ls komutu ile klasörleri listele
            stdin, stdout, stderr = ssh.exec_command(f"ls -d {base_path.rstrip('/') }/*/")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
    
            ssh.close()
    
            if error:
                messagebox.showerror("Hata", f"Uzak sunucudan klasörler alınamadı:\n{error}")
                return
    
            # Her satırda klasör yolu var, sadece klasör adını alıyoruz
            klasorler = [os.path.basename(os.path.normpath(line)) for line in output.splitlines() if line.strip()]
            if not klasorler:
                messagebox.showinfo("Bilgi", "Uzak sunucuda belirtilen klasörde alt klasör bulunamadı.")
                return
    
            self.domain_text.delete("1.0", tk.END)
            for domain in sorted(klasorler):
                self.domain_text.insert(tk.END, domain + "\n")
    
            messagebox.showinfo("Başarılı", f"{len(klasorler)} domain uzak sunucudan yüklendi.")
    
        except Exception as e:
            messagebox.showerror("Hata", f"Domainler uzak sunucudan alınırken hata oluştu:\n{str(e)}")
            self.logla(f"⚠️ Otomatik domain yükleme hatası: {str(e)}")


    def logla(self, mesaj):
        self.log_area.insert(tk.END, mesaj + "\n")
        self.log_area.see(tk.END)
        print(mesaj)

    def select_file(self):
        dosya = filedialog.askopenfilename()
        if dosya:
            self.file_path.set(dosya)

    def baslat(self):
        t = threading.Thread(target=self.yukleme_islemi, daemon=True)
        t.start()

    def yukleme_islemi(self):
        try:
            host = self.host.get().strip()
            username = self.username.get().strip()
            password = self.password.get().strip()
            base_path = self.base_path.get().strip()
            local_file = self.file_path.get().strip()

            domains_text = self.domain_text.get("1.0", tk.END).strip()
            domains = [d.strip() for d in domains_text.splitlines() if d.strip()]

            if not all([host, username, password, base_path, local_file, domains]):
                messagebox.showerror("Hata", "Lütfen tüm alanları eksiksiz doldurun.")
                return

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.logla(f"🔗 Sunucuya bağlanılıyor: {host}")
            ssh.connect(hostname=host, port=20, username=username, password=password)
            sftp = ssh.open_sftp()

            toplam = len(domains)
            self.progress['maximum'] = toplam

            for i, domain in enumerate(domains, 1):
                hedef_klasor = os.path.join(base_path.rstrip("/"), domain, "httpdocs").replace("\\", "/") + "/"
                hedef_dosya = os.path.join(hedef_klasor, os.path.basename(local_file))
                try:
                    self.logla(f"[{i}/{toplam}] {domain} → Yükleniyor... ⏳")
                    sftp.put(local_file, hedef_dosya)
                    self.logla(f"✅ [{i}/{toplam}] {domain} → Başarılı")
                except Exception as ex:
                    self.logla(f"❌ [{i}/{toplam}] {domain} → Hata: {str(ex)}")
                self.progress['value'] = i
                self.root.update_idletasks()

            sftp.close()
            ssh.close()
            self.logla("🎉 Tüm işlemler tamamlandı.")
        except Exception as e:
            self.logla(f"⚠️ Genel Hata: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DosyaYukleyiciApp(root)
    root.mainloop()
