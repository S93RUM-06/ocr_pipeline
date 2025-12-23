using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace RoiSampler.Core.Models;

/// <summary>
/// 欄位組 Profile - 預設的欄位配置模板
/// </summary>
public class FieldSetProfile
{
    [JsonPropertyName("profile_id")]
    public string ProfileId { get; set; } = string.Empty;

    [JsonPropertyName("profile_name")]
    public string ProfileName { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("document_type")]
    public string DocumentType { get; set; } = "general";

    [JsonPropertyName("fields")]
    public List<FieldDefinition> Fields { get; set; } = new();

    [JsonPropertyName("created_at")]
    public string CreatedAt { get; set; } = DateTime.Now.ToString("yyyy-MM-dd");

    [JsonPropertyName("updated_at")]
    public string? UpdatedAt { get; set; }

    [JsonPropertyName("author")]
    public string? Author { get; set; }

    [JsonPropertyName("tags")]
    public List<string>? Tags { get; set; }
}

/// <summary>
/// 欄位定義 - Profile 中的單一欄位
/// </summary>
public class FieldDefinition
{
    [JsonPropertyName("field_name")]
    public string FieldName { get; set; } = string.Empty;

    [JsonPropertyName("display_name")]
    public string? DisplayName { get; set; }

    [JsonPropertyName("data_type")]
    public string DataType { get; set; } = "string";

    [JsonPropertyName("required")]
    public bool Required { get; set; } = false;

    [JsonPropertyName("pattern")]
    public string? Pattern { get; set; }

    [JsonPropertyName("expected_length")]
    public int? ExpectedLength { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("example_values")]
    public List<string>? ExampleValues { get; set; }

    /// <summary>
    /// 顯示名稱（用於 UI）
    /// </summary>
    [JsonIgnore]
    public string Label => DisplayName ?? FieldName;
}
