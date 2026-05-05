import pyodbc


def get_connection():
    # Kiểm tra máy bạn cài Driver 17 hay 18. Nếu lỗi 08001 vẫn còn, hãy thử đổi 17 thành 18.
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost,1434;'
        'DATABASE=EWalletDB;'
        'UID=sa;'
        'PWD=UyenNguyen2026SQL;'
    )
    return pyodbc.connect(conn_str)


def run_demo_rollback(wallet_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.autocommit = False  # Bắt đầu giao dịch thủ công

        # 1. Trừ tiền ví A
        cursor.execute("UPDATE Wallets SET balance = balance - ? WHERE wallet_id = ?", (amount, wallet_id))
        print(f"Đã trừ {amount} từ ví {wallet_id} (Tạm thời)")

        # 2. Gây lỗi chủ động để demo
        print("Đang mô phỏng lỗi hệ thống...")
        raise Exception("CRASH_SYSTEM_ERROR")

        # 3. Lệnh này sẽ không bao giờ chạy tới
        cursor.execute("UPDATE Wallets SET balance = balance + ?", (amount,))
        conn.commit()

    except Exception as e:
        conn.rollback()  # Lệnh quan trọng nhất để chụp ảnh
        print(f"XÁC NHẬN: Đã Rollback thành công. Lỗi hệ thống: {e}")
        print("Dữ liệu trong SQL Server đã quay về trạng thái an toàn.")
    finally:
        conn.close()


if __name__ == "__main__":
    sdt = input("Nhập ID ví để demo: ")
    run_demo_rollback(sdt, 200000)