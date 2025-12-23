# TODO - ROI 取樣工具開發任務清單

## 待辦清單

### 已完成 ✅
- [x] **Task 1**: 建立 .NET 專案結構
- [x] **Task 2**: 實作核心資料模型
- [x] **Task 3**: 實作統計計算引擎
- [x] **Task 4**: 實作 .NET Schema Validator
- [x] **Task 5**: 實作 Avalonia UI 原型
- [x] **Task 6**: 實作 Profile 管理系統
- [x] **Task 7**: 實作樣本管理功能
- [x] **Task 8**: 實作範本匯出功能

### 進行中 🚧
（無）

### 待處理 ⏸️
- [ ] **Task 9**: 重建 Python 版本 Validator（配合 .NET 版本）

---

## 已完成項目詳細摘要

### Task 1: 建立 .NET 專案結構 ✅
**完成日期**: 2025-12-23  
**實作內容**:
- 建立三層專案架構：
  - `RoiSampler.App`: Avalonia UI 應用程式層
  - `RoiSampler.Core`: 核心邏輯與資料模型層
  - `RoiSampler.Tests`: 單元測試層
- 配置專案相依性與 NuGet 套件：
  - Avalonia UI 11.3.10（跨平台 UI 框架）
  - CommunityToolkit.Mvvm 8.4.0（MVVM 輔助）
  - MathNet.Numerics 5.0.0（統計計算）
  - NJsonSchema 11.5.2（JSON Schema 驗證）
  - xUnit + FluentAssertions（測試框架）

### Task 2: 實作核心資料模型 ✅
**完成日期**: 2025-12-23  
**實作內容**:
- **RectRatio**: 正規化矩形座標模型（ratio-based）
- **RegionDefinition**: 區域定義（欄位名稱 + RectRatio）
- **TemplateSchema**: 範本結構（metadata + regions + validation rules）
- **SamplingMetadata**: 取樣元資料（樣本數量、影像尺寸統計、欄位清單）
- **ImageSample**: 單一影像樣本資料（路徑、尺寸、標註區域）
- 所有模型支援 JSON 序列化/反序列化（snake_case 命名）

### Task 3: 實作統計計算引擎 ✅
**完成日期**: 2025-12-23  
**實作內容**:
- 建立 `TemplateCalculator` 類別，使用 MathNet.Numerics 進行精確統計
- 核心方法：
  - `CalculateMedianFromSamples()`: 從多個樣本計算中位數矩形
  - `CalculateStandardDeviation()`: 計算座標標準差（評估一致性）
  - `CalculateMeanDimensions()`: 計算影像尺寸平均值
- 支援多重取樣整合（每個欄位可多次標註）
- 輸出結果：中位數矩形、標準差、樣本數統計

### Task 4: 實作 .NET Schema Validator ✅
**完成日期**: 2025-12-23  
**實作內容**:
- 建立 `TemplateSchemaValidator` 類別，整合 NJsonSchema
- 功能：
  - 讀取 JSON Schema 檔案（config/schemas/template-v1.0.json）
  - 驗證範本 JSON 結構完整性
  - 提供詳細錯誤訊息（路徑、錯誤類型）
- 單元測試：
  - 11 個測試案例全數通過 ✅
  - 涵蓋：必填欄位、型別檢查、範圍驗證、格式驗證、複雜物件驗證
- Schema 更新：支援 nullable 型別（mean, std_dev）

### Task 5: 實作 Avalonia UI 原型 ✅
**完成日期**: 2025-12-23  
**實作內容**:
- 建立 MVVM 架構主視窗：
  - `MainWindow.axaml`: XAML UI 布局
  - `MainWindowViewModel`: 視圖模型（使用 CommunityToolkit.Mvvm）
  - `RoiCanvas`: 自訂繪圖控制項（繼承 Canvas）
- UI 功能：
  - **左側面板**：欄位輸入、Profile 選擇器、欄位清單
  - **中央畫布**：影像顯示、ROI 矩形繪製（滑鼠拖曳）
  - **工具列**：載入影像、管理 Profile、匯出範本
  - **狀態列**：即時訊息顯示
- RoiCanvas 互動：
  - 滑鼠拖曳繪製矩形
  - 視覺化 ROI 邊界（紅色半透明框）
  - 支援多個 ROI 同時顯示

### Task 6: 實作 Profile 管理系統 ✅
**完成日期**: 2025-12-23  
**實作內容**:

#### 核心資料模型
- **FieldSetProfile**: Profile 主資料
  - `profile_id` (string): 唯一識別碼
  - `profile_name` (string): 顯示名稱
  - `description` (string): 說明
  - `document_type` (string): 文件類型（發票、收據等）
  - `fields` (List<FieldDefinition>): 欄位定義清單
  - `tags` (List<string>): 分類標籤
  - `created_at`, `updated_at` (DateTime): 時間戳記
  
- **FieldDefinition**: 欄位定義
  - `field_name` (string): 欄位名稱（英文識別碼）
  - `display_name` (string): 顯示名稱（中文）
  - `data_type` (string): 資料型別（text/number/date/barcode）
  - `required` (bool): 是否必填
  - `pattern` (string?): 驗證正則表達式
  - `expected_length` (int?): 預期長度

#### 服務層（ProfileManager）
- **檔案儲存**: `profiles/*.json`（snake_case JSON 序列化）
- **CRUD 操作**:
  - `ListProfiles()`: 列出所有 Profile
  - `LoadProfile(id)`: 載入單一 Profile
  - `SaveProfile(profile)`: 儲存/更新 Profile（自動更新時間戳記）
  - `DeleteProfile(id)`: 刪除 Profile
  - `CreateNewProfile(name, type)`: 建立新 Profile（工廠方法）
  - `CloneProfile(source, newName)`: 複製 Profile
  - `ValidateProfile(profile)`: 驗證 Profile（檢查唯一性、必填欄位）
  
- **預設 Profile 自動建立**:
  - `tw_einvoice_v1`: 台灣電子發票證明聯（8 欄位）
    - invoice_number, invoice_date, seller_name, buyer_tax_id, total_amount, random_code, qrcode_left, qrcode_right
  - `general_receipt_v1`: 一般收據（6 欄位）
    - receipt_number, receipt_date, payer_name, total_amount, payment_method, description

#### UI 層（ProfileManagerWindow）
- **視圖模型（ProfileManagerViewModel）**:
  - Observable Properties: Profiles, SelectedProfile, SelectedFields, IsEditing, StatusMessage
  - Relay Commands: LoadProfiles, CreateNew, Clone, Save, Delete, AddField, DeleteField, StartEdit, CancelEdit
  - 自動資料綁定與更新

- **對話框 UI（ProfileManagerWindow.axaml）**:
  - **工具列**: 新增、複製、儲存、刪除、重新載入按鈕
  - **左側面板**: Profile 清單（300px 寬度）
  - **右側編輯區**:
    - Profile 資訊（名稱、說明、文件類型）
    - 欄位 DataGrid（欄位名稱、顯示名稱、資料型別、必填、驗證規則）
    - 新增欄位按鈕（預設值：new_field, 新欄位, text）
  - **狀態列**: 即時操作訊息顯示
  - **編輯模式**: 唯讀/編輯切換（防止意外修改）

#### 主視窗整合
- **Profile 選擇器**（MainWindow.axaml）:
  - ComboBox 下拉選單（顯示 Profile 名稱 + 說明）
  - "套用 Profile" 按鈕 → 載入欄位至工作區
  - "管理 Profile" 工具列按鈕 → 開啟 ProfileManagerWindow 對話框

- **快速標註按鈕**:
  - 欄位清單顯示 CurrentFields（來自已選 Profile）
  - 每個欄位列：Label (120px) + 資料型別 + "標註" 按鈕
  - 點擊"標註"按鈕 → 直接啟動該欄位的 ROI 繪製（省略手動輸入）

#### 文件
- **PROFILE_GUIDE.md**: 250+ 行完整使用指南
  - 概述、使用場景、檔案結構
  - 使用方法（3 步驟工作流程）
  - 管理功能詳細說明
  - 預設 Profile 規格
  - 最佳實踐與命名規範
  - 工作流程範例（處理 10 張台灣電子發票）
  - 進階功能、團隊協作
  - FAQ 常見問題

- **README.md 更新**: 
  - 新增"最新功能：欄位組 Profile 管理"章節
  - 核心功能清單更新（Profile 列為首項）
  - 參考 PROFILE_GUIDE.md 連結

#### 技術亮點
- JSON 檔案儲存（易於版本控制、團隊分享）
- MVVM 模式（CommunityToolkit.Mvvm 屬性與命令）
- ShowDialog 對話框模式
- 自動初始化預設 Profile（首次執行）
- 輸入驗證（唯一性檢查、必填欄位檢查）
- Clone 功能（快速客製化既有範本）

#### 使用效益
- ✅ **避免重複輸入**: 常用文件類型預先定義欄位
- ✅ **確保一致性**: 標準化欄位命名與驗證規則
- ✅ **提升效率**: 點擊選擇 + 快速標註按鈕
- ✅ **易於分享**: JSON 檔案可版本控制與團隊共用
- ✅ **彈性客製**: Clone + 修改現有 Profile

---

## 備註

### 暫緩項目說明
- **Task 7 & 8**（樣本管理、範本匯出）暫緩原因：
  - 用戶提議優先實作 Profile 管理系統
  - 策略性決策：先建立標準化配置系統，再處理批次作業流程
  - 將於 Profile 系統測試完成後續行開發

### 專案狀態
- 目前狀態：**開發中 - Profile 管理系統已完成**
- 編譯狀態：✅ dotnet build 成功（0 錯誤，3 個非關鍵警告）
- 測試狀態：✅ 11/11 單元測試通過
- 可執行狀態：✅ Profile 系統可立即使用

### 技術債務
- 3 個 Nullable 參考警告（非關鍵）:
  - TemplateSchemaValidator.cs:74
  - ProfileManager.cs:250
  - MainWindowViewModel.cs OpenProfileManager async/await

### 下一步建議
1. 測試 Profile 管理功能（建立、編輯、刪除、Clone）
2. 使用預設 Profile 進行實際標註測試
3. 視需求新增更多預設 Profile（如：訂單、合約等）
4. 收集使用者回饋後恢復 Task 7 & 8 開發

### Task 7: 實作樣本管理功能 ✅
**完成日期**: 2025-12-23  
**實作內容**:

#### 影像載入功能
- **單張影像載入** (`LoadSingleImageCommand`):
  - 整合 Avalonia FilePickerOpenOptions API
  - 支援 jpg, jpeg, png, bmp 格式
  - 自動建立 ImageSample（分配唯一 ID）
  - 載入後自動設為當前樣本

- **批次影像載入** (`LoadMultipleImagesCommand`):
  - 支援一次選擇多張影像（AllowMultiple = true）
  - 批次建立樣本（快速讀取尺寸）
  - 自動載入第一張影像到畫布
  - 顯示成功數量統計

- **內部載入方法** (`LoadImageInternalAsync`):
  - 專用於樣本切換時載入影像
  - Bitmap 解碼優化（限寬 1200px）

#### 樣本管理功能
- **樣本切換** (`OnSelectedSampleChanged` partial void):
  - 自動載入選定樣本的影像
  - 調用 UpdateAnnotationsFromSample() 同步標註

- **標註同步** (`UpdateAnnotationsFromSample`):
  - Dictionary<string, PixelRect> → ObservableCollection<RoiAnnotation>
  - 即時更新畫布 ROI 顯示

- **移除樣本** (`RemoveSampleCommand`): 單一樣本刪除 + 自動選擇下一個
- **清除所有樣本** (`ClearAllSamplesCommand`): 重置所有狀態與 ID 計數器

#### 進度追蹤
- **GetSampleProgress()**: 計算「已標註/總欄位」（例如：3/8）
- **IsSampleComplete()**: 檢查 Profile 所有必需欄位是否已標註（HashSet.IsSubsetOf）

#### 統計計算整合
- **CalculateTemplateStatisticsCommand**:
  - 整合 `TemplateCalculator.CalculateTemplate()`
  - 從所有樣本計算完整 TemplateSchema
  - 計算參考尺寸（中位數）、RectRatio 平均值、標準差
  - 品質驗證（threshold=0.1）
  - 顯示詳細統計摘要：
    - 樣本數、參考尺寸、欄位數
    - 每個欄位的標準差（X, Y, Width, Height）
    - 品質警告列表（前 5 個）

#### UI 改進
- **工具列**: 載入單張、批次載入、清除標註、清除樣本、計算統計（粗體）
- **樣本列表面板**（高度 200px）:
  - 樣本 ID（#1, #2...）+ 檔案路徑（截斷顯示）
  - 影像尺寸 + 已標註欄位數（綠色）
  - 「移除」按鈕
  - 點擊切換自動載入

#### 技術細節
- 新增命名空間：`Avalonia.Platform.Storage`, `RoiSampler.Core.Statistics`
- 新欄位：`_templateCalculator`, `_nextSampleId`（自增計數器）
- 錯誤處理：Try-catch + 友善訊息

#### 待完成（Task 8 前置）
- 儲存 TemplateSchema 到 ViewModel 屬性
- 樣本完成度進度條視覺化

### Task 8: 實作範本匯出功能 ✅
**完成日期**: 2025-12-23  
**實作內容**:

#### ViewModel 擴充
- **新增屬性**:
  - `CalculatedTemplate` (TemplateSchema?): 儲存計算結果
  - `QualityWarnings` (List<string>): 品質警告列表

- **更新 CalculateTemplateStatistics**:
  - 計算後儲存 TemplateSchema 到 CalculatedTemplate 屬性
  - 儲存品質警告到 QualityWarnings 列表
  - 啟用匯出與預覽按鈕（IsEnabled 綁定）

#### 匯出功能
- **ExportTemplateCommand**:
  - 檢查是否已計算範本（CalculatedTemplate != null）
  - 整合 Avalonia SaveFilePickerAsync（建議檔名：{template_id}.json）
  - JSON 序列化選項：
    - WriteIndented: true（格式化輸出）
    - PropertyNamingPolicy: SnakeCaseLower（snake_case 命名）
    - Encoder: UnsafeRelaxedJsonEscaping（中文字元不轉義）
  - 寫入檔案到使用者選擇的路徑
  
- **驗證整合**:
  - 匯出後自動驗證範本
  - 載入 `config/schemas/template-v1.0.json` Schema
  - 使用 `TemplateSchemaValidator.FromFileAsync()`
  - 調用 `validator.Validate(CalculatedTemplate)`
  - 顯示驗證結果：
    - ✅ 驗證通過
    - ⚠️ 驗證失敗（顯示前 3 個錯誤訊息）
    - 找不到 Schema 檔案時跳過驗證
  
- **錯誤處理**:
  - Try-catch 包裹檔案操作
  - 驗證失敗不影響匯出
  - 友善錯誤訊息顯示

#### 預覽功能
- **PreviewTemplateCommand**:
  - 檢查是否已計算範本
  - 將 TemplateSchema 序列化為格式化 JSON
  - 顯示 JSON 預覽（前 500 字元 + 總長度）
  - TODO: 未來開啟專用預覽視窗（語法高亮、可摺疊 JSON 樹狀檢視）

#### UI 更新
- **工具列新按鈕**:
  - 「預覽範本 JSON」按鈕
    - Command: PreviewTemplateCommand
    - IsEnabled 綁定: CalculatedTemplate != null
  - 「匯出範本 JSON」按鈕（粗體）
    - Command: ExportTemplateCommand  
    - IsEnabled 綁定: CalculatedTemplate != null

- **按鈕狀態管理**:
  - 使用 Avalonia ObjectConverters.IsNotNull 轉換器
  - 計算前按鈕禁用（灰色）
  - 計算後按鈕啟用

#### 配置檔案管理
- **Schema 檔案複製**:
  - 從父目錄複製 `config/schemas/template-v1.0.json` 到專案
  - 更新 RoiSampler.App.csproj：
    - `<None Include="..\..\config\**\*.*">`
    - `<CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>`
  - 確保 Schema 檔案在執行時可用（{AppDomain.BaseDirectory}/config/schemas/）

#### 完整工作流程
1. 批次載入影像（5-10 張）
2. 選擇 Profile（例如：tw_einvoice_v1）
3. 依序標註每張影像的欄位
4. 點擊「計算範本統計」→ CalculatedTemplate 已填充
5. 點擊「預覽範本 JSON」→ 檢視 JSON 內容（可選）
6. 點擊「匯出範本 JSON」→ 選擇儲存位置
7. 自動驗證 → 顯示結果 ✅ 或 ⚠️
8. 範本 JSON 檔案已產生，可供 Python OCR pipeline 使用

#### 技術細節
- **命名空間**: `System.Text.Json`, `System.Text.Encodings.Web`
- **Async/Await**: 所有檔案 I/O 操作非同步
- **路徑處理**: `Path.Combine`, `Path.GetFileName`
- **驗證模式**: TemplateSchemaValidator 使用物件驗證（非 JSON 字串）

#### 待優化項目
- 預覽視窗專用 UI（TextBox 多行顯示 JSON）
- JSON 編輯器整合（語法高亮）
- 匯出前確認對話框（覆蓋現有檔案警告）
- 批次匯出多個範本


