from flask import Flask, render_template, request
import sqlite3
from datetime import datetime


con = sqlite3.connect('./db/stock.db', check_same_thread=False)
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS barang(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nama_barang TEXT UNIQUE NOT NULL,
            harga_barang REAL NOT NULL,
            jumlah_awal INTEGER NOT NULL,
            jumlah_barang INTEGER NOT NULL
            )''')

cur.execute('''CREATE TABLE IF NOT EXISTS transaksi(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_barang INTEGER,
            nama_barang TEXT,
            jumlah_barang INTEGER NOT NULL,
            total_harga REAL
            )''')

cur.execute('''CREATE TABLE IF NOT EXISTS laporan(
            nama_barang TEXT,
            masuk INTEGER NOT NULL,
            keluar INTEGER NOT NULL,
            stok INTEGER NOT NULL,
            total_jual REAL NOT NULL
            )''')

con.commit()

def report():
    cur.execute('''DELETE FROM laporan''')
    
    cur.execute('''SELECT * FROM barang''')
    barang = list(cur.fetchall())
    total_terjual = 0
        
    for item in barang:
        id_barang = item[0]
        cur.execute('''SELECT nama_barang, jumlah_awal, jumlah_barang FROM barang WHERE id=?''', (id_barang,))
        data_barang = cur.fetchall()[0]
        nama_barang = data_barang[0]
        masuk = data_barang[1]
        jumlah_barang = data_barang[2]
            
        cur.execute('''SELECT * FROM transaksi WHERE id_barang=?''', (id_barang,))
        transaksi = cur.fetchall()
            
        jumlah_terjual = sum(trans[3] for trans in transaksi)
        total_terjual += jumlah_terjual
            
        total_jual = sum(total[4] for total in transaksi)
            
        laporan = [nama_barang, masuk, jumlah_terjual, jumlah_barang, total_jual]
        cur.execute('''INSERT INTO laporan (nama_barang, masuk, keluar, stok, total_jual) VALUES(?, ?, ?, ?, ?)''', laporan)
    con.commit()

app = Flask(__name__)

@app.route('/')
def dashboard():
    cur.execute('''SELECT * FROM laporan''')
    hasil_laporan = cur.fetchall()
    return render_template('index.html', hasil_laporan = hasil_laporan)

@app.route('/input_barang', methods = ['GET', 'POST'])
def input_barang():
    cur.execute('''SELECT * FROM barang''')
    barang = cur.fetchall()
    cur.execute('''SELECT nama_barang FROM barang''')
    list_barang = cur.fetchall()
    nama = []
    for i in range(0, len(list_barang)):
        nama.append(list_barang[i][0])
    if request.method == 'POST':
        nama_barang = request.form['nama_barang']
        jumlah_barang = int(request.form['jumlah_barang'])
        harga_barang = float(request.form['harga_barang'])
        item = [nama_barang, harga_barang, jumlah_barang, jumlah_barang]
        if nama_barang not in nama:
            cur.execute('''INSERT INTO barang (nama_barang, harga_barang, jumlah_awal, jumlah_barang) VALUES (?, ?, ?, ?)''', item)
        else:
            cur.execute('''SELECT jumlah_awal, jumlah_barang FROM barang WHERE nama_barang=?''', (nama_barang, ))
            data_jumlah = list(cur.fetchmany()[0])
            masuk_awal = data_jumlah[0]
            jumlah_awal = data_jumlah[1]
            masuk = masuk_awal + jumlah_barang
            jumlah_barang = jumlah_awal + jumlah_barang
            print(jumlah_barang)
            cur.execute('''UPDATE barang SET harga_barang=?, jumlah_awal=?, jumlah_barang=? WHERE nama_barang=?''', (harga_barang, masuk, jumlah_barang, nama_barang))
        con.commit()
    return render_template('input_barang.html', barang = barang)

@app.route('/transaksi', methods = ['GET', 'POST'])
def transaksi():
    cur.execute('''SELECT * FROM barang''')
    barang = cur.fetchall()
    if request.method == 'POST':
        id_barang = int(request.form['id_barang'])
        jumlah = int(request.form['jumlah_barang'])
        cur.execute('''SELECT * FROM barang WHERE id=?''', (id_barang, ))
        data_barang = list(cur.fetchall()[0])
        total = jumlah * data_barang[2]
        min_jumlah = int(data_barang[4]) - jumlah
        beli = [data_barang[0], data_barang[1], jumlah, total]
        cur.execute('''INSERT INTO transaksi (id_barang, nama_barang, jumlah_barang, total_harga) VALUES (?, ?, ?, ?)''', beli)
        cur.execute('''UPDATE barang SET jumlah_barang=? WHERE id=?''', (min_jumlah, id_barang, ))
        con.commit()
    return render_template('transaksi.html', barang = barang)

@app.route('/laporan')
def laporan():
    cur.execute('''SELECT * FROM laporan''')
    hasil_laporan = cur.fetchall()
    panjang = len(hasil_laporan)
    report()
    print(panjang)
    if panjang != 0:
        now = datetime.now().strftime('%d %B %Y pukul %H:%M')
        return render_template('laporan.html', hasil_laporan = hasil_laporan, panjang = panjang, now = now)
    else:
        pesan = "Belum ada data transaksi!"
        return render_template('laporan.html', pesan = pesan, panjang = panjang)

if __name__ == '__main__':
    app.run(debug=True)