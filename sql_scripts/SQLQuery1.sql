USE EWalletDB;
GO


-- Cách 1: Xóa đi tạo lại toàn bộ (Dữ liệu cũ sẽ mất nhưng sạch lỗi)
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Banks;
DROP TABLE IF EXISTS Wallets;
DROP TABLE IF EXISTS Users;
GO

CREATE TABLE Users (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(100),
    phone VARCHAR(20) UNIQUE,
    cccd VARCHAR(20) UNIQUE, -- Cột này đang thiếu nè
    password VARCHAR(255)
);

CREATE TABLE Wallets (
    wallet_id VARCHAR(20) PRIMARY KEY, -- ID ví là SĐT
    user_id INT,
    balance DECIMAL(18, 2) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Banks (
    bank_id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT,
    bank_name NVARCHAR(100),
    account_number VARCHAR(20) UNIQUE,
    bank_balance DECIMAL(18, 2) DEFAULT 10000000, -- Có sẵn 10tr để test
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Transactions (
    transaction_id INT PRIMARY KEY IDENTITY(1,1),
    from_wallet VARCHAR(20),
    to_wallet VARCHAR(20),
    amount DECIMAL(18, 2),
    status NVARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
   -- Chỉ giữ khóa ngoại cho người nhận để đảm bảo tiền không chuyển vào hư vô
    CONSTRAINT FK_ToWallet FOREIGN KEY (to_wallet) REFERENCES Wallets(wallet_id)
);
GO
IF OBJECT_ID('sp_TransferMoney_V2', 'P') IS NOT NULL
    DROP PROCEDURE sp_TransferMoney_V2;
GO
-- 3. Procedure chuyển tiền theo chuẩn mới (Phần 4.4 của Phương Uyên)
CREATE PROCEDURE sp_TransferMoney_V2
    @FromWalletID INT,
    @ToWalletID INT,
    @Amount DECIMAL(18,2)
AS
BEGIN
    BEGIN TRANSACTION;
    BEGIN TRY
        -- Kiểm tra số dư người gửi
        IF (SELECT balance FROM Wallets WHERE wallet_id = @FromWalletID) < @Amount
        BEGIN
            PRINT 'Khong du tien trong vi!';
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- Trừ tiền ví gửi
        UPDATE Wallets SET balance = balance - @Amount WHERE wallet_id = @FromWalletID;

        -- Cộng tiền ví nhận
        UPDATE Wallets SET balance = balance + @Amount WHERE wallet_id = @ToWalletID;

        -- Ghi lịch sử giao dịch
        INSERT INTO Transactions (from_wallet, to_wallet, amount, status)
        VALUES (@FromWalletID, @ToWalletID, @Amount, 'SUCCESS');

        COMMIT TRANSACTION;
        PRINT 'Chuyen tien thanh cong!';
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        INSERT INTO Transactions (from_wallet, to_wallet, amount, status)
        VALUES (@FromWalletID, @ToWalletID, @Amount, 'FAILED');
        PRINT 'Giao dich that bai!';
    END CATCH
END;
GO