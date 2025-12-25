using CommunityToolkit.Mvvm.ComponentModel;
using System.Collections.ObjectModel;
using System.Text.Json.Serialization;

namespace RoiSampler.Core.Models;

/// <summary>
/// 欄位組 Profile - 預設的欄位配置模板
/// </summary>
public partial class FieldSetProfile : ObservableObject
{
    [ObservableProperty]
    [JsonPropertyName("profile_id")]
    private string _profileId = string.Empty;

    [ObservableProperty]
    [JsonPropertyName("profile_name")]
    private string _profileName = string.Empty;

    [ObservableProperty]
    [JsonPropertyName("description")]
    private string? _description;

    [ObservableProperty]
    [JsonPropertyName("document_type")]
    private string _documentType = "general";

    // 🔧 改用 ObservableCollection（MVVM 推薦）
    [ObservableProperty]
    [JsonPropertyName("fields")]
    private ObservableCollection<FieldDefinition> _fields = new();

    [ObservableProperty]
    [JsonPropertyName("created_at")]
    private string _createdAt = DateTime.Now.ToString("yyyy-MM-dd");

    [ObservableProperty]
    [JsonPropertyName("updated_at")]
    private string? _updatedAt;

    [ObservableProperty]
    [JsonPropertyName("author")]
    private string? _author;

    [ObservableProperty]
    [JsonPropertyName("tags")]
    private List<string>? _tags;
}

/// <summary>
/// 欄位定義 - Profile 中的單一欄位
/// </summary>
public partial class FieldDefinition : ObservableObject
{
    [ObservableProperty]
    [JsonPropertyName("field_name")]
    private string _fieldName = string.Empty;

    [ObservableProperty]
    [JsonPropertyName("display_name")]
    private string? _displayName;

    [ObservableProperty]
    [JsonPropertyName("data_type")]
    private string _dataType = "string";

    [ObservableProperty]
    [JsonPropertyName("required")]
    private bool _required = false;

    [ObservableProperty]
    [JsonPropertyName("pattern")]
    private string? _pattern;

    [ObservableProperty]
    [JsonPropertyName("expected_length")]
    private int? _expectedLength;

    [ObservableProperty]
    [JsonPropertyName("description")]
    private string? _description;

    [ObservableProperty]
    [JsonPropertyName("example_values")]
    private List<string>? _exampleValues;

    /// <summary>
    /// 顯示名稱（用於 UI）
    /// </summary>
    [JsonIgnore]
    public string Label => DisplayName ?? FieldName;
}