-- Thiết lập môi trường CSDL
CREATE DATABASE EWalletDB;
GO
USE EWalletDB;
GO

-- Tạo bảng tối ưu (Phần 4.2 của Uyên)
CREATE TABLE Wallets (
    WalletID INT PRIMARY KEY IDENTITY(1,1),
    OwnerName NVARCHAR(100),
    Balance DECIMAL(18,2) DEFAULT 0 CHECK (Balance >= 0) -- Chặn âm tiền
);

-- Viết Transaction xử lý nạp tiền (Phần 4.4 của Uyên)
CREATE PROCEDURE sp_Deposit
    @WalletID INT,
    @Amount DECIMAL(18,2)
AS
BEGIN
    BEGIN TRANSACTION; -- Đảm bảo tính ACID
    BEGIN TRY
        UPDATE Wallets SET Balance = Balance + @Amount WHERE WalletID = @WalletID;
        COMMIT; 
    END TRY
    BEGIN CATCH
        ROLLBACK; -- Hoàn tác nếu lỗi
    END CATCH
END;