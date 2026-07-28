-- =======================================================
-- AXEGLOBAL PORTAL MASTER SCHEMA (ERP INTEGRATION READY)
-- CONTAINS CORE AUTHENTICATION AND MULTI-MAPPING RELATIONSHIPS
-- =======================================================

-- 1. SYSTEM SETTING TABLE
CREATE TABLE system_setting (
    id INTEGER NOT NULL IDENTITY, 
    theme_color VARCHAR(50) NULL DEFAULT 'blue', 
    logo_path VARCHAR(255) NULL DEFAULT 'img/logo.png', 
    login_banner_path VARCHAR(255) NULL DEFAULT 'img/login_hero.png', 
    default_layout VARCHAR(50) NULL DEFAULT 'sidebar', 
    PRIMARY KEY (id)
);

-- 2. COMPANY TABLE
CREATE TABLE company (
    id INTEGER NOT NULL IDENTITY, 
    ftl_code VARCHAR(20) NULL, 
    name VARCHAR(200) NOT NULL, 
    address TEXT NULL, 
    zip_code VARCHAR(20) NULL, 
    city VARCHAR(100) NULL, 
    country VARCHAR(100) NULL, 
    vat_number VARCHAR(50) NULL, 
    eori_number VARCHAR(50) NULL, 
    status VARCHAR(20) NULL DEFAULT 'active', 
    assigned_ops_id INTEGER NULL, 
    created_at DATETIME NULL DEFAULT GETDATE(), 
    PRIMARY KEY (id), 
    UNIQUE (ftl_code), 
    UNIQUE (vat_number)
);

-- 3. USER TABLE (CORE AUTHENTICATION & PORTAL STATE MACHINE)
CREATE TABLE [user] (
    id INTEGER NOT NULL IDENTITY, 
    name VARCHAR(100) NOT NULL, 
    email VARCHAR(120) NOT NULL, 
    mobile VARCHAR(50) NULL, 
    password_hash VARCHAR(256) NOT NULL, 
    role VARCHAR(20) NOT NULL DEFAULT 'customer', 
    email_verified BIT NOT NULL DEFAULT 0,
    email_token VARCHAR(256) NULL, 
    email_token_expiry DATETIME NULL,
    password_reset_token VARCHAR(256) NULL,
    password_reset_token_expiry DATETIME NULL,
    deactivation_reason NVARCHAR(MAX) NULL,
    rejection_reason NVARCHAR(MAX) NULL,
    department VARCHAR(50) NULL, 
    status VARCHAR(20) NULL DEFAULT 'pending_verification', -- Starts as pending email verification
    company_id INTEGER NULL, 
    created_at DATETIME NULL DEFAULT GETDATE(), 
    PRIMARY KEY (id), 
    UNIQUE (email)
);

-- 4. JUNCTION TABLE FOR MULTI-ACCOUNT ASSIGNMENTS
CREATE TABLE user_account_mapping (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES [user](id) ON DELETE CASCADE,
    CONSTRAINT UC_User_Account UNIQUE (user_id, account_id)
);

-- 5. JUNCTION TABLE FOR MULTI-BRANCH ASSIGNMENTS
CREATE TABLE user_branch_mapping (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    branch_id VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES [user](id) ON DELETE CASCADE,
    CONSTRAINT UC_User_Branch UNIQUE (user_id, branch_id)
);

-- =======================================================
-- ADD MUTUALLY DEPENDENT FOREIGN KEYS
-- =======================================================
ALTER TABLE company ADD CONSTRAINT FK_company_user FOREIGN KEY(assigned_ops_id) REFERENCES [user] (id);
ALTER TABLE [user] ADD CONSTRAINT FK_user_company FOREIGN KEY(company_id) REFERENCES company (id);

-- =======================================================
-- SEED INITIAL SYSTEM & SECURITY DATA
-- =======================================================
INSERT INTO system_setting (theme_color, logo_path, login_banner_path, default_layout) 
VALUES ('blue', 'img/logo.png', 'img/login_hero.png', 'sidebar');

-- Default Administrator login (admin@axeglobal.com / password)
INSERT INTO [user] (name, email, password_hash, role, status, email_verified) 
VALUES ('System Admin', 'admin@axeglobal.com', 'scrypt:32768:8:1$WI14wtAhpo8Zhi3W$088b52add19b754420e7376c5c72dafe11ca877e2ff30365d46ccea237a6b05991df3019d57595c682c214f60fc321af53dc9d7a9671dbc43eeaef5d244525b2', 'admin', 'active', 1);
