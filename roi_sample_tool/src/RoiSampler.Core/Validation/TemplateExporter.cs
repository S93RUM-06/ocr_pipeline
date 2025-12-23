using System.Text.Json;
using System.Text.Json.Serialization;
using RoiSampler.Core.Models;

namespace RoiSampler.Core.Validation;

/// <summary>
/// 模板 JSON 輸出器
/// </summary>
public class TemplateExporter
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };

    /// <summary>
    /// 匯出模板為 JSON 檔案
    /// </summary>
    public async Task ExportToFileAsync(TemplateSchema template, string outputPath)
    {
        var json = JsonSerializer.Serialize(template, JsonOptions);
        await File.WriteAllTextAsync(outputPath, json, System.Text.Encoding.UTF8);
    }

    /// <summary>
    /// 從 JSON 檔案讀取模板
    /// </summary>
    public async Task<TemplateSchema?> ImportFromFileAsync(string filePath)
    {
        var json = await File.ReadAllTextAsync(filePath, System.Text.Encoding.UTF8);
        return JsonSerializer.Deserialize<TemplateSchema>(json, JsonOptions);
    }

    /// <summary>
    /// 序列化為 JSON 字串
    /// </summary>
    public string Serialize(TemplateSchema template)
    {
        return JsonSerializer.Serialize(template, JsonOptions);
    }
}
