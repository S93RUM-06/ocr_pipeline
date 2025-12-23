namespace RoiSampler.Core.Models;

/// <summary>
/// ROI 位置標準差（評估穩定性）
/// </summary>
public class RectStdDev
{
    public double X { get; set; }
    public double Y { get; set; }
    public double Width { get; set; }
    public double Height { get; set; }

    /// <summary>
    /// 檢查標準差是否過大（超過閾值表示位置不穩定）
    /// </summary>
    public bool IsUnstable(double threshold = 0.1)
    {
        return X > threshold || Y > threshold || Width > threshold || Height > threshold;
    }

    /// <summary>
    /// 取得警告訊息
    /// </summary>
    public IEnumerable<string> GetWarnings(string fieldName, double threshold = 0.1)
    {
        if (X > threshold)
            yield return $"{fieldName}: rect_std_dev.x = {X:F4} > {threshold}（位置不穩定，建議重新取樣）";
        if (Y > threshold)
            yield return $"{fieldName}: rect_std_dev.y = {Y:F4} > {threshold}（位置不穩定，建議重新取樣）";
        if (Width > threshold)
            yield return $"{fieldName}: rect_std_dev.width = {Width:F4} > {threshold}（位置不穩定，建議重新取樣）";
        if (Height > threshold)
            yield return $"{fieldName}: rect_std_dev.height = {Height:F4} > {threshold}（位置不穩定，建議重新取樣）";
    }
}
