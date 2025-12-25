using System.Text.Json;
using System.Text.Json.Serialization;

namespace RoiSampler.Core.Utilities;

/// <summary>
/// JSON 序列化設定輔助類別
/// </summary>
public static class JsonHelper
{
    /// <summary>
    /// 取得標準的 JSON 序列化選項
    /// </summary>
    public static JsonSerializerOptions GetDefaultOptions()
    {
        return new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
            // 允許讀取註解
            ReadCommentHandling = JsonCommentHandling.Skip,
            // 允許尾隨逗號
            AllowTrailingCommas = true
        };
    }

    /// <summary>
    /// 序列化物件為 JSON 字串
    /// </summary>
    public static string Serialize<T>(T obj)
    {
        return JsonSerializer.Serialize(obj, GetDefaultOptions());
    }

    /// <summary>
    /// 從 JSON 字串反序列化物件
    /// </summary>
    public static T? Deserialize<T>(string json)
    {
        return JsonSerializer.Deserialize<T>(json, GetDefaultOptions());
    }
}