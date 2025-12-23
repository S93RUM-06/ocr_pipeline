using System.Text.Json.Serialization;

namespace RoiSampler.Core.Models;

/// <summary>
/// 區域定義（單一欄位）
/// </summary>
public class RegionDefinition
{
    [JsonPropertyName("rect_ratio")]
    public RectRatio RectRatio { get; set; } = new();

    [JsonPropertyName("rect_std_dev")]
    public RectStdDev? RectStdDev { get; set; }

    [JsonPropertyName("pattern")]
    public string? Pattern { get; set; }

    [JsonPropertyName("extract_group")]
    public int ExtractGroup { get; set; } = 0;

    [JsonPropertyName("expected_length")]
    public int? ExpectedLength { get; set; }

    [JsonPropertyName("required")]
    public bool Required { get; set; } = false;

    [JsonPropertyName("position_weight")]
    public double PositionWeight { get; set; } = 0.3;

    [JsonPropertyName("tolerance_ratio")]
    public double ToleranceRatio { get; set; } = 0.2;

    [JsonPropertyName("fallback_pattern")]
    public string? FallbackPattern { get; set; }

    [JsonPropertyName("data_type")]
    public string DataType { get; set; } = "string";

    [JsonPropertyName("description")]
    public string? Description { get; set; }
}
