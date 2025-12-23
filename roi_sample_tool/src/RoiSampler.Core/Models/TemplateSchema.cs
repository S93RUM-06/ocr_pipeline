using System.Text.Json.Serialization;

namespace RoiSampler.Core.Models;

/// <summary>
/// OCR 作業範本 Schema
/// </summary>
public class TemplateSchema
{
    [JsonPropertyName("template_id")]
    public string TemplateId { get; set; } = string.Empty;

    [JsonPropertyName("template_name")]
    public string TemplateName { get; set; } = string.Empty;

    [JsonPropertyName("version")]
    public string Version { get; set; } = "1.0.0";

    [JsonPropertyName("created_at")]
    public string CreatedAt { get; set; } = DateTime.Now.ToString("yyyy-MM-dd");

    [JsonPropertyName("updated_at")]
    public string? UpdatedAt { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    [JsonPropertyName("processing_strategy")]
    public string ProcessingStrategy { get; set; } = "hybrid_ocr_roi";

    [JsonPropertyName("sampling_metadata")]
    public SamplingMetadata SamplingMetadata { get; set; } = new();

    [JsonPropertyName("regions")]
    public Dictionary<string, RegionDefinition> Regions { get; set; } = new();
}
