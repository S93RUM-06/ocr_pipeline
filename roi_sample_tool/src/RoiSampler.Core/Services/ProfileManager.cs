using RoiSampler.Core.Models;
using System.Text.Json;

namespace RoiSampler.Core.Services;

/// <summary>
/// 欄位組 Profile 管理服務
/// </summary>
public class ProfileManager
{
    private readonly string _profilesDirectory;
    private readonly JsonSerializerOptions _jsonOptions;

    public ProfileManager(string? profilesDirectory = null)
    {
        // 預設儲存位置：roi_sample_tool/profiles/
        _profilesDirectory = profilesDirectory ??
            Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "profiles");

        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            WriteIndented = true,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
        };

        EnsureProfilesDirectory();
        InitializeDefaultProfiles();
    }

    /// <summary>
    /// 確保 profiles 目錄存在
    /// </summary>
    private void EnsureProfilesDirectory()
    {
        if (!Directory.Exists(_profilesDirectory))
        {
            Directory.CreateDirectory(_profilesDirectory);
        }
    }

    /// <summary>
    /// 初始化預設 Profiles（如果不存在）
    /// </summary>
    private void InitializeDefaultProfiles()
    {
        var profiles = ListProfiles();
        if (profiles.Count == 0)
        {
            // 🔧 建立預設 Profile：台灣電子發票證明聯
            var taiwanEInvoice = new FieldSetProfile
            {
                ProfileId = "tw_einvoice_v1",
                ProfileName = "台灣電子發票證明聯",
                Description = "統一發票證明聯（電子發票）常見欄位",
                DocumentType = "invoice",
                Tags = new List<string> { "台灣", "發票", "電子發票" }
            };

            // 🔧 使用屬性賦值而非集合初始化器
            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "invoice_number",
                DisplayName = "發票號碼",
                DataType = "string",
                Required = true,
                Pattern = "[A-Z]{2}-\\d{8}",
                ExpectedLength = 10,
                Description = "格式: AB-12345678"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "invoice_date",
                DisplayName = "發票日期",
                DataType = "date",
                Required = true,
                Description = "開立日期"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "seller_tax_id",
                DisplayName = "賣方統編",
                DataType = "string",
                Pattern = "\\d{8}",
                ExpectedLength = 8,
                Description = "銷售方統一編號（8碼）"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "buyer_tax_id",
                DisplayName = "買方統編",
                DataType = "string",
                Pattern = "\\d{8}",
                ExpectedLength = 8,
                Description = "買受人統一編號（8碼）"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "total_amount",
                DisplayName = "總金額",
                DataType = "number",
                Required = true,
                Description = "含稅總額"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "random_code",
                DisplayName = "隨機碼",
                DataType = "string",
                Pattern = "\\d{4}",
                ExpectedLength = 4,
                Description = "4位隨機碼"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "qrcode_left",
                DisplayName = "QR Code (左)",
                DataType = "string",
                Description = "左側 QR Code"
            });

            taiwanEInvoice.Fields.Add(new FieldDefinition
            {
                FieldName = "qrcode_right",
                DisplayName = "QR Code (右)",
                DataType = "string",
                Description = "右側 QR Code"
            });

            // 🔧 建立預設 Profile：一般收據
            var generalReceipt = new FieldSetProfile
            {
                ProfileId = "general_receipt_v1",
                ProfileName = "一般收據",
                Description = "一般商業收據常見欄位",
                DocumentType = "receipt",
                Tags = new List<string> { "收據", "通用" }
            };

            generalReceipt.Fields.Add(new FieldDefinition
            {
                FieldName = "receipt_number",
                DisplayName = "收據編號",
                DataType = "string",
                Required = true
            });

            generalReceipt.Fields.Add(new FieldDefinition
            {
                FieldName = "receipt_date",
                DisplayName = "收據日期",
                DataType = "date",
                Required = true
            });

            generalReceipt.Fields.Add(new FieldDefinition
            {
                FieldName = "payer_name",
                DisplayName = "付款人",
                DataType = "string"
            });

            generalReceipt.Fields.Add(new FieldDefinition
            {
                FieldName = "total_amount",
                DisplayName = "總金額",
                DataType = "number",
                Required = true
            });

            generalReceipt.Fields.Add(new FieldDefinition
            {
                FieldName = "payment_method",
                DisplayName = "付款方式",
                DataType = "string"
            });

            generalReceipt.Fields.Add(new FieldDefinition
            {
                FieldName = "description",
                DisplayName = "項目說明",
                DataType = "string"
            });

            SaveProfile(taiwanEInvoice);
            SaveProfile(generalReceipt);
        }
    }

    /// <summary>
    /// 列出所有 Profiles
    /// </summary>
    public List<FieldSetProfile> ListProfiles()
    {
        var profiles = new List<FieldSetProfile>();

        if (!Directory.Exists(_profilesDirectory))
            return profiles;

        foreach (var filePath in Directory.GetFiles(_profilesDirectory, "*.json"))
        {
            try
            {
                var profile = LoadProfile(Path.GetFileNameWithoutExtension(filePath));
                if (profile != null)
                {
                    profiles.Add(profile);
                }
            }
            catch
            {
                // 忽略無效的 JSON 檔案
            }
        }

        return profiles.OrderBy(p => p.ProfileName).ToList();
    }

    /// <summary>
    /// 載入 Profile
    /// </summary>
    public FieldSetProfile? LoadProfile(string profileId)
    {
        var filePath = Path.Combine(_profilesDirectory, $"{profileId}.json");

        if (!File.Exists(filePath))
            return null;

        try
        {
            var json = File.ReadAllText(filePath);
            return JsonSerializer.Deserialize<FieldSetProfile>(json, _jsonOptions);
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// 儲存 Profile
    /// </summary>
    public void SaveProfile(FieldSetProfile profile)
    {
        if (string.IsNullOrWhiteSpace(profile.ProfileId))
        {
            throw new ArgumentException("ProfileId 不可為空");
        }

        // 更新時間
        if (!string.IsNullOrEmpty(profile.CreatedAt))
        {
            profile.UpdatedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        }

        var filePath = Path.Combine(_profilesDirectory, $"{profile.ProfileId}.json");
        var json = JsonSerializer.Serialize(profile, _jsonOptions);
        File.WriteAllText(filePath, json);
    }

    /// <summary>
    /// 刪除 Profile
    /// </summary>
    public void DeleteProfile(string profileId)
    {
        var filePath = Path.Combine(_profilesDirectory, $"{profileId}.json");

        if (File.Exists(filePath))
        {
            File.Delete(filePath);
        }
    }

    /// <summary>
    /// 建立新的 Profile
    /// </summary>
    public FieldSetProfile CreateNewProfile(string profileName, string documentType = "general")
    {
        return new FieldSetProfile
        {
            ProfileId = GenerateProfileId(profileName),
            ProfileName = profileName,
            DocumentType = documentType,
            CreatedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
        };
    }

    /// <summary>
    /// 從 Profile 建立副本
    /// </summary>
    public FieldSetProfile CloneProfile(FieldSetProfile source, string newName)
    {
        var clone = new FieldSetProfile
        {
            ProfileId = GenerateProfileId(newName),
            ProfileName = newName,
            Description = source.Description,
            DocumentType = source.DocumentType,
            CreatedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            Tags = source.Tags != null ? new List<string>(source.Tags) : null
        };

        // 🔧 複製欄位
        foreach (var field in source.Fields)
        {
            clone.Fields.Add(new FieldDefinition
            {
                FieldName = field.FieldName,
                DisplayName = field.DisplayName,
                DataType = field.DataType,
                Required = field.Required,
                Pattern = field.Pattern,
                ExpectedLength = field.ExpectedLength,
                Description = field.Description,
                ExampleValues = field.ExampleValues != null ? new List<string>(field.ExampleValues) : null
            });
        }

        return clone;
    }

    /// <summary>
    /// 生成 Profile ID
    /// </summary>
    private string GenerateProfileId(string name)
    {
        var id = name.ToLowerInvariant()
            .Replace(" ", "_")
            .Replace("　", "_");

        // 移除特殊字元
        id = new string(id.Where(c => char.IsLetterOrDigit(c) || c == '_').ToArray());

        // 加上時間戳避免衝突
        return $"{id}_{DateTime.Now:yyyyMMddHHmmss}";
    }

    /// <summary>
    /// 驗證 Profile
    /// </summary>
    public List<string> ValidateProfile(FieldSetProfile profile)
    {
        var errors = new List<string>();

        if (string.IsNullOrWhiteSpace(profile.ProfileId))
            errors.Add("ProfileId 不可為空");

        if (string.IsNullOrWhiteSpace(profile.ProfileName))
            errors.Add("ProfileName 不可為空");

        if (profile.Fields == null || profile.Fields.Count == 0)
        {
            errors.Add("至少需要一個欄位");
            return errors;
        }

        // 檢查欄位名稱唯一性
        var duplicateFields = profile.Fields
            .GroupBy(f => f.FieldName)
            .Where(g => g.Count() > 1)
            .Select(g => g.Key);

        foreach (var fieldName in duplicateFields)
        {
            errors.Add($"欄位名稱重複: {fieldName}");
        }

        return errors;
    }
}