import pyodbc

# --- CẤU HÌNH KẾT NỐI (SSMS DOCKER) ---
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost,1434;'
    'DATABASE=EWalletDB;'
    'UID=sa;'
    'PWD=UyenNguyen2026SQL;'
    'TrustServerCertificate=yes;'
)


def get_connection():
    return pyodbc.connect(conn_str)


# --- 4.3 CHỨC NĂNG HỆ THỐNG ---

def create_user_full(name, phone, cccd, password, bank_name, bank_acc):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Tạo User
        cursor.execute("INSERT INTO Users (name, phone, cccd, password) VALUES (?, ?, ?, ?)",
                       (name, phone, cccd, password))
        cursor.execute("SELECT @@IDENTITY")
        u_id = cursor.fetchone()[0]

        # 2. Tạo Ví (ID là Số điện thoại)
        cursor.execute("INSERT INTO Wallets (wallet_id, user_id, balance) VALUES (?, ?, 0)", (phone, u_id))

        # 3. Tạo Tài khoản ngân hàng liên kết (Sử dụng STK do người dùng nhập)
        cursor.execute("INSERT INTO Banks (user_id, bank_name, account_number) VALUES (?, ?, ?)",
                       (u_id, bank_name, bank_acc))

        conn.commit()
        print("\n" + "=" * 40)
        print("ĐĂNG KÝ TÀI KHOẢN THÀNH CÔNG!")
        print(f"Chủ tài khoản: {name}")
        print(f"ID Ví (SĐT): {phone} | Số dư ví: 0đ")
        print(f"Ngân hàng: {bank_name} | STK: {bank_acc}")
        print(f"Số dư ngân hàng khả dụng: 10,000,000đ")  # Hiện luôn con số mặc định
        print("=" * 40)
    except Exception as e:
        conn.rollback()
        print(f"\n Lỗi đăng ký: {e}")
    finally:
        conn.close()


def topup_from_bank(wallet_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    conn.autocommit = False
    try:
        # Kiểm tra ví có tồn tại không
        cursor.execute("SELECT user_id FROM Wallets WHERE wallet_id = ?", (wallet_id,))
        res = cursor.fetchone()
        if not res: raise Exception("Ví không tồn tại!")
        u_id = res[0]

        # Kiểm tra tiền trong ngân hàng (Bank)
        cursor.execute("SELECT bank_balance FROM Banks WHERE user_id = ?", (u_id,))
        bank_bal = cursor.fetchone()[0]
        if bank_bal < amount: raise Exception("Số dư ngân hàng không đủ!")

        # THỰC HIỆN GIAO DỊCH (Transaction)
        # 1. Trừ tiền Bank
        cursor.execute("UPDATE Banks SET bank_balance = bank_balance - ? WHERE user_id = ?", (amount, u_id))
        # 2. Cộng tiền Ví
        cursor.execute("UPDATE Wallets SET balance = balance + ? WHERE wallet_id = ?", (amount, wallet_id))
        # 3. Ghi lịch sử (Sử dụng chuỗi đại diện cho ngân hàng)
        cursor.execute("INSERT INTO Transactions (from_wallet, to_wallet, amount, status) VALUES (?, ?, ?, ?)",
                       ('BANK_SYSTEM', wallet_id, amount, 'TOPUP'))

        conn.commit()
        print(f" Nạp thành công {amount:,.0f}đ từ ngân hàng vào ví!")
    except Exception as e:
        conn.rollback()
        print(f" Lỗi nạp tiền: {e}")
    finally:
        conn.close()


def transfer_money(from_w, to_w, amount):
    conn = get_connection()
    cursor = conn.cursor()
    conn.autocommit = False
    try:
        # Kiểm tra số dư ví gửi
        cursor.execute("SELECT balance FROM Wallets WHERE wallet_id = ?", (from_w,))
        row = cursor.fetchone()
        if not row or row[0] < amount: raise Exception("Số dư ví không đủ!")

        # Chuyển tiền
        cursor.execute("UPDATE Wallets SET balance = balance - ? WHERE wallet_id = ?", (amount, from_w))
        cursor.execute("UPDATE Wallets SET balance = balance + ? WHERE wallet_id = ?", (amount, to_w))
        cursor.execute("INSERT INTO Transactions (from_wallet, to_wallet, amount, status) VALUES (?, ?, ?, ?)",
                       (from_w, to_w, amount, 'SUCCESS'))

        conn.commit()
        print(f" Đã chuyển {amount} từ ví {from_w} đến ví {to_w}")
    except Exception as e:
        conn.rollback()
        print(f"Giao dịch thất bại: {e}")
    finally:
        conn.close()


def show_history():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Hiển thị số dư hiện tại của Ví và Ngân hàng (Để check tiền có nhảy không)
        print("\n" + "=" * 20 + " BẢNG SỐ DƯ " + "=" * 20)
        query_bal = """
            SELECT U.name, W.wallet_id, W.balance, B.bank_name, B.bank_balance
            FROM Users U
            JOIN Wallets W ON U.user_id = W.user_id
            JOIN Banks B ON U.user_id = B.user_id
        """
        cursor.execute(query_bal)
        print(f"{'Chủ thẻ':<15} | {'Ví (SĐT)':<12} | {'Tiền Ví':<12} | {'Tiền Bank'}")
        print("-" * 65)
        for row in cursor.fetchall():
            print(f"{row[0]:<15} | {row[1]:<12} | {row[2]:<12,.0f} | {row[4]:<10,.0f}")

        # 2. Hiển thị lịch sử giao dịch chi tiết (Chương 4.3)
        print("\n" + "=" * 18 + " LỊCH SỬ GIAO DỊCH " + "=" * 18)
        print(f"{'ID':<4} | {'Từ':<12} | {'Đến':<12} | {'Số Tiền':<10} | {'Thời Gian'}")
        print("-" * 65)
        query_trans = """
            SELECT transaction_id, from_wallet, to_wallet, amount, 
            FORMAT(created_at, 'HH:mm:ss dd-MM-yyyy') 
            FROM Transactions 
            ORDER BY created_at DESC
        """
        cursor.execute(query_trans)
        for row in cursor.fetchall():
            print(f"{row[0]:<4} | {row[1]:<12} | {row[2]:<12} | {row[3]:<10,.0f} | {row[4]}")
        print("=" * 65)

    except Exception as e:
        print(f"Lỗi hiển thị: {e}")
    finally:
        conn.close()


# --- 4.5 GIAO DIỆN CLI ---
def main():
    while True:
        print("\n--- HỆ THỐNG VÍ ĐIỆN TỬ PHƯƠNG UYÊN ---")
        print("1. Đăng ký (User + CCCD + Bank)")
        print("2. Nạp tiền từ Ngân hàng vào Ví")
        print("3. Chuyển tiền giữa các Ví")
        print("4. Xem lịch sử & Số dư")
        print("0. Thoát")

        choice = input("Chọn: ")
        if choice == '1':
            n = input("Nhập họ tên: ")
            p = input("Nhập SĐT (ID Ví): ")
            cc = input("Nhập số CCCD: ")
            pw = input("Nhập mật khẩu: ")
            bn = input("Tên ngân hàng (ví dụ: VCB, MB, ACB): ")
            ba = input("Nhập số tài khoản ngân hàng của bạn: ")  # Người dùng tự nhập STK

            create_user_full(n, p, cc, pw, bn, ba)
        elif choice == '2':
            wid = input("Nhập ID Ví (SĐT): ")
            amt = float(input("Số tiền nạp: "))
            topup_from_bank(wid, amt)
        elif choice == '3':
            fw = input("Ví gửi (SĐT): ")
            tw = input("Ví nhận (SĐT): ")
            amt = float(input("Số tiền chuyển: "))
            transfer_money(fw, tw, amt)
        elif choice == '4':
            show_history()
        elif choice == '0':
            break


if __name__ == "__main__":
    main()