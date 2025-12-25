namespace RoiSampler.Core.Models;

/// <summary>
/// 圖片樣本
/// </summary>
public class ImageSample
{
    public int Id { get; set; }
    public string FilePath { get; set; } = string.Empty;
    public int Width { get; set; }
    public int Height { get; set; }

    /// <summary>
    /// 欄位名稱 -> 像素座標的對應
    /// </summary>
    public Dictionary<string, PixelRect> Annotations { get; set; } = new();
}

/// <summary>
/// 像素座標矩形（絕對座標）
/// </summary>
public class PixelRect
{
    public int X { get; set; }
    public int Y { get; set; }
    public int Width { get; set; }
    public int Height { get; set; }

    /// <summary>
    /// 轉換為相對比例座標（0-1 之間）
    /// </summary>
    public RectRatio ToRatio(int imageWidth, int imageHeight)
    {
        if (imageWidth <= 0 || imageHeight <= 0)
            throw new ArgumentException("Image dimensions must be positive");

        return new RectRatio
        {
            X = Math.Round((double)X / imageWidth, 4),
            Y = Math.Round((double)Y / imageHeight, 4),
            Width = Math.Round((double)Width / imageWidth, 4),
            Height = Math.Round((double)Height / imageHeight, 4)
        };
    }

    /// <summary>
    /// 從相對比例座標建立
    /// </summary>
    public static PixelRect FromRatio(RectRatio ratio, int imageWidth, int imageHeight)
    {
        if (imageWidth <= 0 || imageHeight <= 0)
            throw new ArgumentException("Image dimensions must be positive");

        return new PixelRect
        {
            X = (int)Math.Round(ratio.X * imageWidth),
            Y = (int)Math.Round(ratio.Y * imageHeight),
            Width = (int)Math.Round(ratio.Width * imageWidth),
            Height = (int)Math.Round(ratio.Height * imageHeight)
        };
    }

    /// <summary>
    /// 顯示用字串（用於 UI）
    /// </summary>
    public override string ToString() => $"({X}, {Y}, {Width}x{Height})";
}