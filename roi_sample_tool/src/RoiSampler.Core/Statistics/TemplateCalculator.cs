using MathNet.Numerics.Statistics;
using RoiSampler.Core.Models;

namespace RoiSampler.Core.Statistics;

/// <summary>
/// 模板統計計算器
/// </summary>
public class TemplateCalculator
{
    /// <summary>
    /// 從多張標註圖片計算模板
    /// </summary>
    public TemplateSchema CalculateTemplate(
        List<ImageSample> samples,
        string templateId,
        string templateName,
        string? description = null)
    {
        if (samples == null || samples.Count == 0)
            throw new ArgumentException("樣本清單不能為空", nameof(samples));

        var template = new TemplateSchema
        {
            TemplateId = templateId,
            TemplateName = templateName,
            Description = description,
            SamplingMetadata = CalculateMetadata(samples)
        };

        // 收集所有欄位名稱
        var fieldNames = samples
            .SelectMany(s => s.Annotations.Keys)
            .Distinct()
            .ToList();

        // 對每個欄位計算統計值
        foreach (var fieldName in fieldNames)
        {
            var region = CalculateRegion(samples, fieldName);
            template.Regions[fieldName] = region;
        }

        return template;
    }

    /// <summary>
    /// 計算取樣元數據
    /// </summary>
    private SamplingMetadata CalculateMetadata(List<ImageSample> samples)
    {
        var widths = samples.Select(s => (double)s.Width).ToArray();
        var heights = samples.Select(s => (double)s.Height).ToArray();

        return new SamplingMetadata
        {
            SampleCount = samples.Count,
            ReferenceSize = new ReferenceSize
            {
                Width = (int)widths.Median(),
                Height = (int)heights.Median(),
                Unit = "pixel",
                Description = $"{samples.Count}張樣本圖片的中位數大小"
            },
            SizeRange = new SizeRange
            {
                Width = new MinMaxRange { Min = (int)widths.Min(), Max = (int)widths.Max() },
                Height = new MinMaxRange { Min = (int)heights.Min(), Max = (int)heights.Max() }
            }
        };
    }

    /// <summary>
    /// 計算單一欄位的區域定義
    /// </summary>
    private RegionDefinition CalculateRegion(List<ImageSample> samples, string fieldName)
    {
        var ratios = new List<RectRatio>();

        foreach (var sample in samples)
        {
            if (sample.Annotations.TryGetValue(fieldName, out var pixelRect))
            {
                var ratio = pixelRect.ToRatio(sample.Width, sample.Height);
                ratios.Add(ratio);
            }
        }

        if (ratios.Count == 0)
            throw new InvalidOperationException($"欄位 '{fieldName}' 沒有任何標註資料");

        // 計算平均值
        var avgX = ratios.Average(r => r.X);
        var avgY = ratios.Average(r => r.Y);
        var avgWidth = ratios.Average(r => r.Width);
        var avgHeight = ratios.Average(r => r.Height);

        // 計算標準差
        RectStdDev? stdDev = null;
        if (ratios.Count > 1)
        {
            var xValues = ratios.Select(r => r.X).ToArray();
            var yValues = ratios.Select(r => r.Y).ToArray();
            var widthValues = ratios.Select(r => r.Width).ToArray();
            var heightValues = ratios.Select(r => r.Height).ToArray();

            stdDev = new RectStdDev
            {
                X = Math.Round(xValues.StandardDeviation(), 4),
                Y = Math.Round(yValues.StandardDeviation(), 4),
                Width = Math.Round(widthValues.StandardDeviation(), 4),
                Height = Math.Round(heightValues.StandardDeviation(), 4)
            };
        }

        return new RegionDefinition
        {
            RectRatio = new RectRatio
            {
                X = Math.Round(avgX, 4),
                Y = Math.Round(avgY, 4),
                Width = Math.Round(avgWidth, 4),
                Height = Math.Round(avgHeight, 4)
            },
            RectStdDev = stdDev
        };
    }

    /// <summary>
    /// 驗證模板品質（檢查標準差）
    /// </summary>
    public List<string> ValidateQuality(TemplateSchema template, double threshold = 0.1)
    {
        var warnings = new List<string>();

        foreach (var (fieldName, region) in template.Regions)
        {
            if (region.RectStdDev != null)
            {
                warnings.AddRange(region.RectStdDev.GetWarnings(fieldName, threshold));
            }
        }

        return warnings;
    }
}
