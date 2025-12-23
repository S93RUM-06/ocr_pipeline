namespace RoiSampler.Core.Models;

/// <summary>
/// ROI 相對比例座標 (0-1 之間)
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
    /// 從像素座標轉換為比例座標
    /// </summary>
    public static RectRatio FromPixels(int x, int y, int width, int height, int imageWidth, int imageHeight)
    {
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
    /// </summary>
    public (int x, int y, int width, int height) ToPixels(int imageWidth, int imageHeight)
    {
        return (
            (int)(X * imageWidth),
            (int)(Y * imageHeight),
            (int)(Width * imageWidth),
            (int)(Height * imageHeight)
        );
    }
}
