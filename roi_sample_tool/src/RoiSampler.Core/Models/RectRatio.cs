namespace RoiSampler.Core.Models;

/// <summary>
/// ROI 相對比例座標 (0-1 之間)
/// 用於範本 JSON 儲存，與圖片尺寸無關
/// </summary>
public class RectRatio
{
    /// <summary>
    /// 左上角 X 座標比例 (x / image_width)
    /// </summary>
    public double X { get; set; }

    /// <summary>
    /// 左上角 Y 座標比例 (y / image_height)
    /// </summary>
    public double Y { get; set; }

    /// <summary>
    /// 寬度比例 (width / image_width)
    /// </summary>
    public double Width { get; set; }

    /// <summary>
    /// 高度比例 (height / image_height)
    /// </summary>
    public double Height { get; set; }

    /// <summary>
    /// 從像素座標建立比例座標
    /// </summary>
    public static RectRatio FromPixels(int x, int y, int width, int height,
                                       int imageWidth, int imageHeight)
    {
        if (imageWidth <= 0 || imageHeight <= 0)
            throw new ArgumentException("Image dimensions must be positive");

        return new RectRatio
        {
            X = Math.Round((double)x / imageWidth, 4),
            Y = Math.Round((double)y / imageHeight, 4),
            Width = Math.Round((double)width / imageWidth, 4),
            Height = Math.Round((double)height / imageHeight, 4)
        };
    }

    /// <summary>
    /// 轉換為像素座標
    /// 注意：這個方法保留是為了向後相容，建議使用 PixelRect.FromRatio()
    /// </summary>
    public (int x, int y, int width, int height) ToPixels(int imageWidth, int imageHeight)
    {
        if (imageWidth <= 0 || imageHeight <= 0)
            throw new ArgumentException("Image dimensions must be positive");

        return (
            (int)Math.Round(X * imageWidth),
            (int)Math.Round(Y * imageHeight),
            (int)Math.Round(Width * imageWidth),
            (int)Math.Round(Height * imageHeight)
        );
    }

    /// <summary>
    /// 驗證比例是否在有效範圍內
    /// </summary>
    public bool IsValid()
    {
        return X >= 0 && X <= 1 &&
               Y >= 0 && Y <= 1 &&
               Width >= 0 && Width <= 1 &&
               Height >= 0 && Height <= 1 &&
               X + Width <= 1 &&
               Y + Height <= 1;
    }

    /// <summary>
    /// 顯示用字串
    /// </summary>
    public override string ToString() =>
        $"({X:F4}, {Y:F4}, {Width:F4}x{Height:F4})";
}