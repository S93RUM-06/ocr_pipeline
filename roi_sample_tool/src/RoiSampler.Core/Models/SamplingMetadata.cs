using System.Text.Json.Serialization;

namespace RoiSampler.Core.Models;

/// <summary>
/// 取樣統計元數據
/// </summary>
public class SamplingMetadata
{
    [JsonPropertyName("sample_count")]
    public int SampleCount { get; set; }

    [JsonPropertyName("reference_size")]
    public ReferenceSize ReferenceSize { get; set; } = new();

    [JsonPropertyName("size_range")]
    public SizeRange? SizeRange { get; set; }

    [JsonPropertyName("sampling_date")]
    public string SamplingDate { get; set; } = DateTime.Now.ToString("yyyy-MM-dd");

    [JsonPropertyName("sampler_version")]
    public string SamplerVersion { get; set; } = "1.0.0";

    [JsonPropertyName("notes")]
    public string? Notes { get; set; }
}

/// <summary>
/// 基準圖片大小
/// </summary>
public class ReferenceSize
{
    [JsonPropertyName("width")]
    public int Width { get; set; }

    [JsonPropertyName("height")]
    public int Height { get; set; }

    [JsonPropertyName("unit")]
    public string Unit { get; set; } = "pixel";

    [JsonPropertyName("description")]
    public string? Description { get; set; }
}

/// <summary>
/// 樣本圖片大小範圍
/// </summary>
public class SizeRange
{
    [JsonPropertyName("width")]
    public MinMaxRange Width { get; set; } = new();

    [JsonPropertyName("height")]
    public MinMaxRange Height { get; set; } = new();
}

public class MinMaxRange
{
    [JsonPropertyName("min")]
    public int Min { get; set; }

    [JsonPropertyName("max")]
    public int Max { get; set; }
}
